import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from revisor.docx.reader import NS
from revisor.docx.editable import inspect_document, edit_document, splice_sections
from revisor.workspace import BookWorkspace
from revisor.provider import codex_runner


def fixture(path, spanish=False):
    ep = 'Epílogo'
    pos = 'Posfácio'
    lines = [('Sumário', ''), (ep, 'TOC1'), (pos, 'TOC1'),
             ('Capítulo 1', 'Heading1'), ('Texto preservado.', ''),
             (ep, 'Heading1'), ('Ela estavam aqui. ― Olá!', ''),
             (pos, 'Heading1'), ('Texto final.', '')]
    if spanish:
        lines = [('Capítulo 1', 'Heading1'), ('Texto español intacto.', ''),
                 (ep, 'Heading1'), ('Viejo epílogo.', ''),
                 ('Posfacio', 'Heading1'), ('Viejo posfacio.', '')]
    ps = ''.join(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:rPr><w:b/></w:rPr><w:t>{text}</w:t></w:r></w:p>' for text, style in lines)
    xml = f'<w:document xmlns:w="{NS["w"]}"><w:body>{ps}<w:sectPr><w:pgSz w:w="12000"/></w:sectPr></w:body></w:document>'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('word/document.xml', xml)
        archive.writestr('word/styles.xml', '<styles/>')
        archive.writestr('word/media/image.png', b'untouched-image')
        archive.writestr('[Content_Types].xml', '<Types/>')


class DocumentWorkflowTests(unittest.TestCase):
    def test_multiple_split_chapters_keep_all_navigation_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'pt.docx'; fixture(source)
            with zipfile.ZipFile(source) as archive: members={n:archive.read(n) for n in archive.namelist()}
            members['word/document.xml']=members['word/document.xml'].replace(b'Cap\xc3\xadtulo 1',b'C</w:t></w:r></w:p><w:p><w:r><w:t>ap\xc3\xadtulo 1')
            extra=b'<w:p><w:r><w:t>C</w:t></w:r></w:p><w:p><w:r><w:t>ap\xc3\xadtulo 2</w:t></w:r></w:p>'
            members['word/document.xml']=members['word/document.xml'].replace(b'<w:sectPr>',extra+b'<w:sectPr>')
            with zipfile.ZipFile(source,'w') as archive:
                for name,data in members.items(): archive.writestr(name,data)
            titles=[s['title'] for s in inspect_document(source)['sections']]
            self.assertIn('Capítulo 1',titles)
            self.assertIn('Capítulo 2',titles)

    def test_insert_drawing_ids_are_unique_and_destination_id_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'pt.docx'; dest=Path(folder)/'es.docx'; out=Path(folder)/'out.docx'
            fixture(source); fixture(dest,True)
            for path in (source,dest):
                with zipfile.ZipFile(path) as archive: members={n:archive.read(n) for n in archive.namelist()}
                drawing=b'<w:drawing xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><wp:docPr id="1" name="Picture"/></w:drawing>'
                marker=b'Ela estavam' if path==source else b'Texto espa'
                members['word/document.xml']=members['word/document.xml'].replace(marker,drawing+marker)
                with zipfile.ZipFile(path,'w') as archive:
                    for name,data in members.items(): archive.writestr(name,data)
            doc=inspect_document(source); sections=[s for s in doc['sections'] if s['key']=='epilogo']
            splice_sections(source,dest,out,sections,{})
            with zipfile.ZipFile(out) as archive:
                root=ET.fromstring(archive.read('word/document.xml'))
                ids=[n.get('id') for n in root.iter() if n.tag.endswith('}docPr')]
                self.assertEqual(len(ids),len(set(ids)))
                self.assertEqual(ids[0],'1')

    def test_split_dropcap_chapter_is_context_and_not_frontmatter(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'pt.docx'; fixture(source)
            with zipfile.ZipFile(source) as a: members={n:a.read(n) for n in a.namelist()}
            members['word/document.xml']=members['word/document.xml'].replace(b'Cap\xc3\xadtulo 1',b'C</w:t></w:r></w:p><w:p><w:r><w:t>ap\xc3\xadtulo 1')
            with zipfile.ZipFile(source,'w') as a:
                for n,b in members.items(): a.writestr(n,b)
            doc=inspect_document(source)
            self.assertTrue(any(s['title']=='Capítulo 1' and s['start']==4 for s in doc['sections']))

    def test_insert_preserves_images_tables_and_resolves_style_collisions(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'pt.docx'; dest=Path(folder)/'es.docx'; out=Path(folder)/'out.docx'
            fixture(source); fixture(dest,True)
            with zipfile.ZipFile(source) as a: members={n:a.read(n) for n in a.namelist()}
            xml=members['word/document.xml'].decode().replace('<w:document ', '<w:document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ')
            xml=xml.replace('<w:sectPr>', '<w:p><w:r><w:drawing r:embed="rId7"/></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Dentro da tabela.</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:sectPr>')
            members['word/document.xml']=xml.encode()
            members['word/_rels/document.xml.rels']=b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image.png"/></Relationships>'
            members['word/styles.xml']=f'<w:styles xmlns:w="{NS["w"]}"><w:style w:styleId="Heading1"><w:rPr><w:i/></w:rPr></w:style></w:styles>'.encode()
            with zipfile.ZipFile(source,'w') as a:
                for n,b in members.items(): a.writestr(n,b)
            doc=inspect_document(source); sections=[s for s in doc['sections'] if s['key'] in {'epilogo','posfacio'}]
            values={p['id']:p['text'] for p in doc['paragraphs'] if p['text']}
            splice_sections(source,dest,out,sections,values)
            with zipfile.ZipFile(out) as a:
                root=ET.fromstring(a.read('word/document.xml'))
                self.assertEqual(len(root.findall('.//w:drawing',NS)),1)
                self.assertEqual(len(root.findall('.//w:tbl',NS)),1)
                self.assertTrue(any(n.endswith('image.png') and a.read(n)==b'untouched-image' for n in a.namelist()))

    def test_line_breaks_and_tabs_keep_text_on_the_correct_sides(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'pt.docx'; out=Path(folder)/'out.docx'; fixture(source)
            with zipfile.ZipFile(source) as a: members={n:a.read(n) for n in a.namelist()}
            members['word/document.xml']=members['word/document.xml'].replace(b'Texto final.', b'Antes</w:t><w:br/><w:t>Depois</w:t><w:tab/><w:t>Fim')
            with zipfile.ZipFile(source,'w') as a:
                for n,b in members.items(): a.writestr(n,b)
            edit_document(source,out,{9:'Before\nAfter\tEnd'})
            self.assertEqual(inspect_document(out)['paragraphs'][8]['text'],'Before\nAfter\tEnd')

    def test_body_sections_skip_toc_and_keep_dotted_accented_titles(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.docx'; fixture(path)
            doc = inspect_document(path)
            sections = {s['key']: s for s in doc['sections']}
            self.assertEqual(sections['epilogo']['start'], 6)
            self.assertEqual(sections['posfacio']['start'], 8)
            self.assertIn(6, sections['epilogo']['paragraph_ids'])

    def test_edit_keeps_paragraph_properties_and_all_other_members(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.docx'; out = Path(folder) / 'out.docx'; fixture(source)
            before = source.read_bytes()
            edit_document(source, out, {7: 'Ela estava aqui. — Olá!'})
            self.assertEqual(source.read_bytes(), before)
            with zipfile.ZipFile(source) as a, zipfile.ZipFile(out) as b:
                for member in a.namelist():
                    if member != 'word/document.xml': self.assertEqual(a.read(member), b.read(member))
                original = ET.fromstring(a.read('word/document.xml')).findall('.//w:p', NS)
                changed = ET.fromstring(b.read('word/document.xml')).findall('.//w:p', NS)
                for i, paragraph in enumerate(original):
                    if i != 6: self.assertEqual(ET.tostring(paragraph), ET.tostring(changed[i]))
                self.assertIsNotNone(changed[6].find('.//w:b', NS))

    def test_splice_only_selected_body_sections(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'pt.docx'; dest = Path(folder) / 'es.docx'; out = Path(folder) / 'out.docx'
            fixture(source); fixture(dest, True)
            before = dest.read_bytes()
            doc = inspect_document(source)
            sections = [s for s in doc['sections'] if s['key'] in {'epilogo', 'posfacio'}]
            splice_sections(source, dest, out, sections, {6:'Epílogo',7:'Ella estaba aquí. — ¡Hola!',8:'Posfacio',9:'Texto final en español.'})
            self.assertEqual(dest.read_bytes(), before)
            result = inspect_document(out)
            texts = [p['text'] for p in result['paragraphs']]
            self.assertEqual(texts[:2], ['Capítulo 1', 'Texto español intacto.'])
            self.assertNotIn('Viejo epílogo.', texts)
            self.assertIn('Ella estaba aquí. — ¡Hola!', texts)


class WorkspaceTests(unittest.TestCase):
    def test_invalid_editorial_reason_never_becomes_a_saved_proposal(self):
        pid=self.workspace.import_book(self.source)['id']
        chunk=self.workspace.detail(pid)['chunks'][0]['id']
        self.workspace.runner=lambda **_: {'edits':[{'paragraph_id':'1','original':'Sumário','replacement':'Livro','reason':{'text':'Teste'},'category':'teste'}]}
        with self.assertRaises(ValueError): self.workspace.review_chunk(pid,chunk)
        self.assertEqual(self.workspace.detail(pid)['progress']['ready_chunks'],0)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root / 'pt.docx'; fixture(self.source)
        self.dest = self.root / 'es.docx'; fixture(self.dest, True)
        self.calls = []
        def runner(**kwargs):
            self.calls.append(kwargs)
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            if data['task'] == 'review':
                return {'edits': [{'paragraph_id': p['id'], 'original':'estavam', 'replacement':'estava', 'reason':'Concordância com sujeito singular.', 'category':'concordância'} for p in data['paragraphs'] if 'estavam' in p['text']]}
            return {'translations':[{'paragraph_id':p['id'], 'text': 'ES '+p['text']} for p in data['paragraphs']], 'terms':[]}
        self.workspace = BookWorkspace(self.root, runner=runner)

    def tearDown(self):
        self.workspace.close(); self.temp.cleanup()

    def test_complete_section_workflow_and_stale_approval(self):
        project = self.workspace.import_book(self.source, destination=self.dest, name='Livro 2')
        pid = project['id']
        self.workspace.configure(pid, {'scope':'sections', 'section_ids':['epilogo', 'posfacio']})
        detail = self.workspace.detail(pid)
        self.assertEqual(detail['progress']['total_paragraphs'], 4)
        chunk = detail['chunks'][0]['id']
        self.workspace.review_chunk(pid, chunk)
        current = self.workspace.detail(pid)['current']
        with self.assertRaises(ValueError): self.workspace.approve(pid, chunk, 'old-proposal')
        self.workspace.approve(pid, chunk, current['proposal_id'])
        with self.assertRaises(ValueError): self.workspace.configure(pid, {'scope':'whole'})
        self.workspace.run_sync(pid, 'review')
        self.workspace.approve_all(pid)
        self.workspace.run_sync(pid, 'translate')
        result = self.workspace.export(pid, 'es')
        self.assertTrue(Path(result['path']).is_file())
        self.assertEqual(self.workspace.detail(pid)['progress']['translated_paragraphs'], 4)
        self.assertIn('América Latina', self.calls[-1]['prompt'])

    def test_translation_requires_approval_and_exact_coverage(self):
        pid = self.workspace.import_book(self.source)['id']
        with self.assertRaises(ValueError): self.workspace.run_sync(pid, 'translate')
        with self.assertRaises(ValueError): self.workspace.export(pid, 'pt-BR')
        self.workspace.run_sync(pid, 'review'); self.workspace.approve_all(pid)
        self.workspace.runner = lambda **_: {'translations':[], 'terms':[]}
        with self.assertRaises(ValueError): self.workspace.run_sync(pid, 'translate')
        self.assertEqual(self.workspace.detail(pid)['progress']['translated_paragraphs'], 0)

    def test_job_resume_is_idempotent_and_original_immutable(self):
        before = self.source.read_bytes()
        pid = self.workspace.import_book(self.source)['id']
        self.workspace.run_sync(pid, 'review', limit=1)
        count = len(self.calls)
        self.workspace.run_sync(pid, 'review', limit=1)
        self.assertGreater(len(self.calls), count)
        self.workspace.run_sync(pid, 'review')
        count = len(self.calls)
        self.workspace.run_sync(pid, 'review')
        self.assertEqual(len(self.calls), count)
        self.assertEqual(self.source.read_bytes(), before)

    def test_changed_glossary_invalidates_only_affected_translations(self):
        pid=self.workspace.import_book(self.source)['id']
        self.workspace.run_sync(pid,'review'); self.workspace.approve_all(pid); self.workspace.run_sync(pid,'translate')
        detail=self.workspace.detail(pid); before=detail['progress']['translated_paragraphs']
        with self.assertRaises(ValueError): self.workspace.update_glossary(pid,{'estava':'estaba'},detail['revision']-1)
        result=self.workspace.update_glossary(pid,{'estava':'estaba'},detail['revision'])
        self.assertEqual(result['invalidated_chunks'],1)
        self.assertLess(self.workspace.detail(pid)['progress']['translated_paragraphs'],before)
        self.assertEqual(self.workspace.detail(pid)['progress']['review_percent'],100)
        self.assertEqual(self.workspace.detail(pid)['glossary'],{'estava':'estaba'})

    def test_repeated_spans_are_grounded_and_overlapping_edits_rejected(self):
        pid=self.workspace.import_book(self.source)['id']
        chunk=self.workspace.detail(pid)['chunks'][0]['id']
        self.workspace.runner=lambda **_: {'edits':[{'paragraph_id':'1','original':'Sumário','occurrence':0,'replacement':'Livro','reason':'Teste','category':'teste'},{'paragraph_id':'1','original':'Livro','occurrence':0,'replacement':'Outro','reason':'Teste','category':'teste'}]}
        with self.assertRaises(ValueError): self.workspace.review_chunk(pid,chunk)
        self.assertEqual(self.workspace.detail(pid)['progress']['ready_chunks'],0)


class ModelContractTests(unittest.TestCase):
    def test_default_is_explicit_sol_low(self):
        with patch('revisor.provider.subprocess.run') as run:
            run.return_value.returncode = 1; run.return_value.stderr = 'synthetic'; run.return_value.stdout = ''
            with self.assertRaises(RuntimeError): codex_runner(prompt='fixture', schema={}, model='codex-default')
            command = run.call_args.args[0]
            self.assertIn('gpt-6.1-sol', command)
            self.assertIn('model_reasoning_effort="low"', command)
