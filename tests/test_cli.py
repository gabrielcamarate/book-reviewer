import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from revisor.cli import main


class CliTest(unittest.TestCase):
    def test_import_and_check_new_book_without_overwriting_existing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'book'
            source = Path(directory) / 'source.docx'
            with zipfile.ZipFile(source, 'w') as z:
                z.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Capítulo 1: Teste</w:t></w:r></w:p><w:p><w:r><w:t>As estrelas brilham.</w:t></w:r></w:p></w:body></w:document>')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(['--root', str(root), 'import', '--input', str(source)]), 0)
            self.assertTrue(json.loads(output.getvalue())['ok'])
            before = (root / 'manuscript/chapters/index.json').read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(['--root', str(root), 'import', '--input', str(source)])
            self.assertEqual(before, (root / 'manuscript/chapters/index.json').read_bytes())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--root', str(root), 'check']), 0)

    def test_batch_limit_rejects_zero(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(['review', '--batch', '--max-chunks', '0'])
