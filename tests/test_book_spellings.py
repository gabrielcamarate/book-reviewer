"""Author spellings (eXilados, CamaraTTe) survive review, check and later edits."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from revisor.book_spellings import detect, protect
from revisor.docx.reader import NS
from revisor.workspace import BookWorkspace, read_json
from test_book_automatic import automatic_runner

LINES = [('Capítulo 1', 'Heading1'), ('Os eXilados chegaram com CamaraTTe.', ''), ('Os eXilados estavam cansados.', ''),
         ('Capítulo 2', 'Heading1'), ('Um nOme raro apareceu.', ''), ('CamaraTTe ficou.', '')]


def book(path, lines=LINES):
    ps = ''.join(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t>{text}</w:t></w:r></w:p>' for text, style in lines)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('word/document.xml', f'<w:document xmlns:w="{NS["w"]}"><w:body>{ps}<w:sectPr/></w:body></w:document>')
        archive.writestr('word/styles.xml', '<styles/>')
        archive.writestr('[Content_Types].xml', '<Types/>')


def normalizing_runner(**kwargs):
    """A model that 'fixes' every stylized spelling and also makes a real correction."""
    data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
    if data['task'] == 'review':
        return {'paragraphs': [{'paragraph_id': p['id'],
                                'text': p['text'].replace('eXilados', 'Exilados').replace('CamaraTTe', 'Camarate').replace('nOme', 'Nome').replace('estavam', 'estavão'),
                                'reason': 'Capitalização e grafia.', 'category': 'grafia'} for p in data['paragraphs']]}
    if data['task'] == 'check_pt':
        return {'paragraphs': [{'paragraph_id': p['id'], 'text': p['draft'].replace('estavão', 'estavam'), 'reason': 'Concordância.', 'category': 'gramática'}
                               for p in data['paragraphs']], 'issues': [], 'notes': []}
    return automatic_runner(**kwargs)


class DetectAndProtectTests(unittest.TestCase):
    def test_detects_mixed_case_words_and_ignores_normal_casing(self):
        found = detect(['Os eXilados e o CamaraTTe.', 'eXilados, CamaraTTe, nOme.', 'Casa ONU iPhone Ela'])
        self.assertEqual(found, {'eXilados': 2, 'CamaraTTe': 2, 'nOme': 1, 'iPhone': 1})

    def test_reverts_only_changes_that_touch_a_protected_word(self):
        original = 'Os eXilados estavão aqui, eXilados.'
        revised = 'Os Exilados estavam aqui, exilados!'
        self.assertEqual(protect(original, revised, ['eXilados']), 'Os eXilados estavam aqui, eXilados!')
        self.assertEqual(protect('eXilados.', 'eXiladoss.', ['eXilados']), 'eXilados.')
        self.assertEqual(protect('Nada a ver.', 'Nada a ver!', ['eXilados']), 'Nada a ver!')
        self.assertEqual(protect('deeXilados', 'de eXilados', ['eXilados']), 'de eXilados')


class WorkspaceSpellingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root / 'livro.docx'; book(self.source)
        self.ws = BookWorkspace(self.root, runner=normalizing_runner)
        self.pid = self.ws.import_book(self.source)['id']

    def tearDown(self):
        self.ws.close(); self.temp.cleanup()

    def run_job(self):
        self.ws.start(self.pid, 'automatic'); self.ws.thread.join(5)
        self.assertFalse(self.ws.thread.is_alive())

    def texts(self):
        state = read_json(self.ws._folder(self.pid) / 'state.json')
        return ' '.join(text for chunk in state['chunks'] for text in chunk.get('revised', {}).values())

    def test_repeated_author_spellings_are_protected_automatically(self):
        spellings = self.ws.detail(self.pid)['spellings']
        self.assertEqual(spellings['active'], ['CamaraTTe', 'eXilados'])
        self.assertEqual(spellings['suggested'], [{'word': 'nOme', 'count': 1}])
        self.run_job()
        text = self.texts()
        self.assertIn('eXilados', text); self.assertIn('CamaraTTe', text)
        self.assertNotIn('Exilados', text); self.assertNotIn('Camarate', text)
        self.assertIn('Nome raro', text)  # Single occurrence: only a suggestion, not protected.
        detail = self.ws.detail(self.pid)
        self.assertTrue(detail['automatic_result'])
        for item in detail['chunks']:
            for edit in self.ws.detail(self.pid, item['id'])['current']['edits']:
                self.assertNotIn(edit['original'], {'eXilados', 'CamaraTTe'})

    def test_adding_a_spelling_restores_reviewed_text_and_retranslates_only_those_chunks(self):
        self.run_job()
        self.assertIn('Nome raro', self.texts())
        before = self.ws.detail(self.pid)
        translated = {c['id'] for c in before['chunks'] if c['translated']}
        self.ws.set_spellings(self.pid, added=['nOme'], removed=[])
        self.assertIn('nOme raro', self.texts())
        after = self.ws.detail(self.pid)
        self.assertEqual(after['spellings']['added'], ['nOme'])
        self.assertIn('nOme', after['spellings']['active'])
        untranslated = translated - {c['id'] for c in after['chunks'] if c['translated']}
        self.assertEqual(len(untranslated), 1)
        state = read_json(self.ws._folder(self.pid) / 'state.json')
        self.assertIn('protect-spelling', [a['action'] for a in state['audit']])
        self.run_job()
        self.assertTrue(self.ws.detail(self.pid)['automatic_result'])

    def test_spellings_saved_while_processing_apply_before_the_word_files(self):
        import threading
        gate, release = threading.Event(), threading.Event()
        def slow(**kwargs):
            if json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])['task'] == 'translate':
                gate.set(); release.wait(5)
            return normalizing_runner(**kwargs)
        self.ws.runner = slow
        self.ws.start(self.pid, 'automatic')
        self.assertTrue(gate.wait(5))
        self.ws.set_spellings(self.pid, added=['nOme'], removed=[])
        self.assertNotIn('nOme raro', self.texts())  # Nothing in flight is rewritten.
        release.set(); self.ws.thread.join(10)
        self.assertIn('nOme raro', self.texts())
        detail = self.ws.detail(self.pid)
        self.assertEqual(detail['job']['status'], 'completed')
        self.assertTrue(detail['automatic_result'])
        self.assertTrue(all(c['translated'] for c in detail['chunks']))

    def test_removed_automatic_spelling_is_no_longer_protected(self):
        self.ws.set_spellings(self.pid, added=[], removed=['CamaraTTe'])
        self.assertEqual(self.ws.detail(self.pid)['spellings']['active'], ['eXilados'])
        self.run_job()
        self.assertIn('Camarate', self.texts())

    def test_invalid_spelling_lists_change_nothing(self):
        for added, removed in ((['duas palavras'], []), (['  '], []), ('eXilados', []), ([], [3])):
            with self.subTest(added=added, removed=removed), self.assertRaises(ValueError):
                self.ws.set_spellings(self.pid, added=added, removed=removed)
        self.assertEqual(self.ws.detail(self.pid)['spellings']['added'], [])


if __name__ == '__main__':
    unittest.main()
