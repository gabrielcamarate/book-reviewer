from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
import unittest

from editorial_core.import_docx import import_docx


CORE_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Sample Book</dc:title>
  <dc:creator>Test Author</dc:creator>
  <cp:lastModifiedBy>Test Editor</cp:lastModifiedBy>
  <cp:revision>7</cp:revision>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-03-10T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-03-10T12:00:00Z</dcterms:modified>
</cp:coreProperties>
"""

APP_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Unit Test</Application>
  <Pages>2</Pages>
  <Words>42</Words>
  <Characters>256</Characters>
  <Lines>5</Lines>
  <Paragraphs>3</Paragraphs>
</Properties>
"""

DOCUMENT_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Chapter I</w:t></w:r></w:p>
    <w:p><w:r><w:t>First paragraph.</w:t></w:r></w:p>
    <w:p><w:r><w:t> </w:t></w:r></w:p>
  </w:body>
</w:document>
"""


def build_sample_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("_rels/.rels", "<Relationships></Relationships>")
        archive.writestr("docProps/core.xml", CORE_XML)
        archive.writestr("docProps/app.xml", APP_XML)
        archive.writestr("word/document.xml", DOCUMENT_XML)


class ImportDocxTest(unittest.TestCase):
    def test_import_docx_persists_metadata_paragraphs_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.docx"
            output_dir = temp_path / "out"
            build_sample_docx(input_path)

            summary = import_docx(input_path, output_dir)

            self.assertEqual(summary["source_file"], "sample.docx")
            self.assertEqual(summary["paragraph_count"], 3)
            self.assertEqual(summary["non_empty_paragraph_count"], 2)
            self.assertEqual(summary["first_non_empty_excerpt"], "Chapter I")

            metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
            paragraphs = json.loads((output_dir / "paragraphs.json").read_text(encoding="utf-8"))
            summary_file = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
            document_text = (output_dir / "document.txt").read_text(encoding="utf-8")

            self.assertEqual(metadata["core"]["creator"], "Test Author")
            self.assertEqual(metadata["app"]["pages"], "2")
            self.assertEqual(paragraphs[0]["text"], "Chapter I")
            self.assertTrue(paragraphs[2]["is_empty"])
            self.assertEqual(summary_file["non_empty_paragraph_count"], 2)
            self.assertEqual(document_text, "Chapter I\n\nFirst paragraph.\n")
