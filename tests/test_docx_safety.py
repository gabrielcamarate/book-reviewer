import tempfile
import unittest
import zipfile
from pathlib import Path

from revisor.docx.reader import extract_docx_paragraphs
from revisor.docx.writer import export_docx_from_template


class DocxSafetyTest(unittest.TestCase):
    def test_import_and_export_reject_document_type_and_entities(self):
        xml = '''<?xml version="1.0"?><!DOCTYPE document [<!ENTITY text "EXPANDED">]>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body><w:p><w:r><w:t>&text;</w:t></w:r></w:p></w:body></w:document>'''
        for encoding in ['utf-8', 'utf-16']:
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'input.docx'
                with zipfile.ZipFile(path, 'w') as archive:
                    archive.writestr('word/document.xml', xml.encode(encoding))
                with self.assertRaisesRegex(ValueError, 'DTD'):
                    extract_docx_paragraphs(path)
                with self.assertRaisesRegex(ValueError, 'DTD'):
                    export_docx_from_template(template_path=path, output_path=Path(directory) / 'out.docx', paragraphs=['Texto.'])
