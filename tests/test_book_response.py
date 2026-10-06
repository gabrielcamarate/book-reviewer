"""Full paragraph responses: exact coverage and deterministic, reversible differences."""
import unittest
from revisor.book_response import apply_paragraphs
from revisor.provider import InvalidModelResponse


class ParagraphResponseTests(unittest.TestCase):
    def response(self, text):
        return {'paragraphs':[{'paragraph_id':'1','text':text,'reason':'Concordância e pontuação.','category':'gramática'}]}

    def test_nearby_corrections_and_insertions_produce_nonoverlapping_reversible_diffs(self):
        source={'1':'Ela estavam aqui Olá!'}
        revised, edits=apply_paragraphs(source,self.response('Ela estava aqui. Olá!'))
        restored=source['1']
        for edit in reversed(edits):
            restored=restored[:edit['start']]+edit['replacement']+restored[edit['end']:]
        self.assertEqual(restored,revised['1'])
        self.assertEqual(revised['1'],'Ela estava aqui. Olá!')
        self.assertTrue(all(a['end']<=b['start'] for a,b in zip(edits,edits[1:])))
        self.assertTrue(any(not e['original'] for e in edits))

    def test_missing_duplicate_reordered_or_unknown_ids_are_rejected(self):
        source={'1':'a','2':'b'}
        for ids in (['1'],['1','1'],['2','1'],['1','3']):
            with self.subTest(ids=ids), self.assertRaises(InvalidModelResponse):
                apply_paragraphs(source,{'paragraphs':[{'paragraph_id':i,'text':'a','reason':'x','category':'x'} for i in ids]})

    def test_empty_paragraph_changed_breaks_and_unjustified_change_are_rejected(self):
        for text in ('',' ','a\n','a\t'):
            with self.subTest(text=text), self.assertRaises(InvalidModelResponse):
                apply_paragraphs({'1':'a'},self.response(text))
        response=self.response('b'); response['paragraphs'][0]['reason']=''
        with self.assertRaises(InvalidModelResponse): apply_paragraphs({'1':'a'},response)

    def test_unchanged_paragraph_has_no_invented_corrections(self):
        self.assertEqual(apply_paragraphs({'1':'a'},self.response('a')),({'1':'a'},[]))


class QueueRecoveryTests(unittest.TestCase):
    def test_invalid_first_chunk_does_not_starve_remaining_work_or_translate_partial_portuguese(self):
        import json
        import tempfile
        import zipfile
        from pathlib import Path
        from revisor.workspace import BookWorkspace, read_json
        from test_book_api import runner
        from test_book_workflows import fixture
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'test.docx'; fixture(source)
            with zipfile.ZipFile(source) as archive: parts={n:archive.read(n) for n in archive.namelist()}
            extra=''.join(f'<w:p><w:r><w:t>Parágrafo extra {i}.</w:t></w:r></w:p>' for i in range(50)).encode()
            parts['word/document.xml']=parts['word/document.xml'].replace(b'<w:sectPr>',extra+b'<w:sectPr>')
            with zipfile.ZipFile(source,'w') as archive:
                for name,body in parts.items(): archive.writestr(name,body)
            calls=[]
            def invalid(**kwargs):
                data=json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); calls.append(data['task'])
                if data['task']=='review' and data['paragraphs'][0]['id']=='1': return {'paragraphs':[]}
                return runner(**kwargs)
            ws=BookWorkspace(root,runner=invalid)
            try:
                pid=ws.import_book(source)['id']; ws.start(pid,'automatic'); ws.thread.join(5)
                detail=ws.detail(pid); state=read_json(ws._folder(pid)/'state.json')
                self.assertEqual(detail['job']['status'],'needs_attention')
                self.assertEqual(detail['job']['problems'][0]['chunk_id'],'chunk-00001')
                self.assertEqual(detail['job']['problems'][0]['index'],1)
                self.assertGreater(len(state['chunks']),4)
                self.assertTrue(all(c['status']=='approved' for c in state['chunks'][1:]))
                self.assertNotIn('translate',calls)
                self.assertEqual(detail['progress']['draft_paragraphs'],detail['progress']['total_paragraphs']-3)
                ws.runner=runner; ws.start(pid,'automatic'); ws.thread.join(5)
                self.assertTrue(ws.detail(pid)['automatic_result'])
            finally: ws.close()


    def test_final_audit_diffs_reflect_checker_reverting_a_proposal(self):
        import json
        import tempfile
        from pathlib import Path
        from revisor.workspace import BookWorkspace, read_json
        from test_book_api import runner
        from test_book_workflows import fixture
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'test.docx'; fixture(source)
            def revert(**kwargs):
                data=json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); result=runner(**kwargs)
                if data['task']=='check_pt':
                    for item,p in zip(result['paragraphs'],data['paragraphs']):
                        item.update(text=p['text'],reason='Preservar expressão neste teste.',category='fidelidade')
                return result
            ws=BookWorkspace(root,runner=revert)
            try:
                pid=ws.import_book(source)['id']; ws.start(pid,'automatic'); ws.thread.join(5)
                chunk=read_json(ws._folder(pid)/'state.json')['chunks'][2]
                self.assertEqual(chunk['edits'],[])
                self.assertTrue(chunk['checks']['pt']['edits'])
            finally: ws.close()

    def test_preserved_source_uncertainty_is_reported_without_approving_an_unresolved_correction(self):
        import json
        import tempfile
        from pathlib import Path
        from revisor.workspace import BookWorkspace
        from test_book_api import runner
        from test_book_workflows import fixture
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'test.docx'; fixture(source)
            def noted(**kwargs):
                data=json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); result=runner(**kwargs)
                if data['task']=='check_pt' and data['paragraphs'][0]['id']=='1':
                    result['notes']=['Expressão do original preservada; depende de escolha da autora.']
                return result
            ws=BookWorkspace(root,runner=noted)
            try:
                pid=ws.import_book(source)['id']; ws.start(pid,'automatic'); ws.thread.join(5)
                detail=ws.detail(pid)
                self.assertEqual(detail['job']['status'],'completed')
                self.assertEqual(len(detail['editorial_notes']),1)
                self.assertTrue(Path(detail['automatic_result']['notes_path']).is_file())
                chunk=detail['editorial_notes'][0]['chunk_id']
                ws.reopen(pid,chunk)
                self.assertEqual(ws.detail(pid)['editorial_notes'],[])
                self.assertIsNone(ws.detail(pid)['automatic_result'])
            finally: ws.close()
