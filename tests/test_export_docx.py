from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
import unittest

from docx_adapter.reader import extract_docx_paragraphs
from editorial_core.export_docx import export_manuscript_docx


CORE_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Template Book</dc:title>
</cp:coreProperties>
"""

APP_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Unit Test</Application>
</Properties>
"""

DOCUMENT_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Template paragraph.</w:t></w:r></w:p>
    <w:sectPr />
  </w:body>
</w:document>
"""


def build_template_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("_rels/.rels", "<Relationships></Relationships>")
        archive.writestr("docProps/core.xml", CORE_XML)
        archive.writestr("docProps/app.xml", APP_XML)
        archive.writestr("word/document.xml", DOCUMENT_XML)


class ExportDocxTest(unittest.TestCase):
    def test_export_manuscript_docx_writes_ptbr_output_from_current_state(self) -> None:
        chapter_index = {
            "section_count": 2,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "frontmatter-0001-opening",
                    "type": "frontmatter",
                    "order": 1,
                    "title": "Opening",
                    "heading_source_index": None,
                    "source_start_index": 1,
                    "source_end_index": 1,
                    "paragraph_count": 1,
                    "file": "frontmatter-0001-opening.json",
                },
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 2,
                    "source_start_index": 3,
                    "source_end_index": 3,
                    "paragraph_count": 1,
                    "file": "chapter-0001-conexao-dimensional.json",
                },
            ],
        }

        opening_payload = {
            "id": "frontmatter-0001-opening",
            "type": "frontmatter",
            "order": 1,
            "title": "Opening",
            "heading_source_index": None,
            "paragraphs": [
                {
                    "id": "frontmatter-0001-opening-p-0001",
                    "source_index": 1,
                    "text": "Página de abertura.",
                    "review_status": "approved_reference",
                }
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "heading_source_index": 2,
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 3,
                    "text": "Texto original do capítulo.",
                    "review_status": "pending_review",
                }
            ],
        }

        consolidated_chapter = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "heading_source_index": 2,
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 3,
                    "source_text": "Texto original do capítulo.",
                    "text": "Texto consolidado do capítulo.",
                    "review_status": "approved",
                    "applied_reviews": [],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_path = temp_path / "template.docx"
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
            output_path = temp_path / "deliverables" / "ptbr.docx"
            build_template_docx(template_path)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "frontmatter-0001-opening.json").write_text(
                json.dumps(opening_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(consolidated_chapter, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = export_manuscript_docx(
                template_path=template_path,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                translations_dir=temp_path / "reviews" / "es",
                output_path=output_path,
                language="pt-BR",
            )

            paragraphs = extract_docx_paragraphs(output_path)

            self.assertEqual(summary["language"], "pt-BR")
            self.assertEqual(summary["paragraph_count"], 3)
            self.assertEqual(paragraphs[0]["text"], "Página de abertura.")
            self.assertEqual(paragraphs[1]["text"], "Capítulo 1: Conexão Dimensional.")
            self.assertEqual(paragraphs[2]["text"], "Texto consolidado do capítulo.")

    def test_export_manuscript_docx_writes_spanish_output_when_translations_cover_all_paragraphs(self) -> None:
        chapter_index = {
            "section_count": 1,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 2,
                    "source_start_index": 3,
                    "source_end_index": 4,
                    "paragraph_count": 2,
                    "file": "chapter-0001-conexao-dimensional.json",
                }
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "heading_source_index": 2,
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 3,
                    "text": "Primeiro parágrafo em português.",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 4,
                    "text": "Segundo parágrafo em português.",
                    "review_status": "approved",
                },
            ],
        }

        translation_payload = {
            "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
            "pass": "translation-es",
            "source_language": "pt-BR",
            "target_language": "es",
            "status": "proposed",
            "model": "gpt-5-codex",
            "source": {
                "section_id": "chapter-0001-conexao-dimensional",
                "section_title": "Capítulo 1: Conexão Dimensional.",
                "paragraph_ids": [
                    "chapter-0001-conexao-dimensional-p-0001",
                    "chapter-0001-conexao-dimensional-p-0002",
                ],
                "source_start_index": 3,
                "source_end_index": 4,
            },
            "translations": [
                {
                    "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                    "translated_text": "Primer párrafo en español.",
                    "rationale": "Conserva el tono.",
                    "confidence": 0.81,
                },
                {
                    "paragraph_id": "chapter-0001-conexao-dimensional-p-0002",
                    "translated_text": "Segundo párrafo en español.",
                    "rationale": "Conserva la literalidad.",
                    "confidence": 0.84,
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_path = temp_path / "template.docx"
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
            translations_dir = temp_path / "reviews" / "es"
            output_path = temp_path / "deliverables" / "es.docx"
            build_template_docx(template_path)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            translations_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (translations_dir / "chapter-0001-conexao-dimensional-chunk-0001.translation-es.json").write_text(
                json.dumps(translation_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = export_manuscript_docx(
                template_path=template_path,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                translations_dir=translations_dir,
                output_path=output_path,
                language="es",
            )

            paragraphs = extract_docx_paragraphs(output_path)

            self.assertEqual(summary["language"], "es")
            self.assertEqual(summary["paragraph_count"], 3)
            self.assertEqual(paragraphs[0]["text"], "Capítulo 1: Conexão Dimensional.")
            self.assertEqual(paragraphs[1]["text"], "Primer párrafo en español.")
            self.assertEqual(paragraphs[2]["text"], "Segundo párrafo en español.")
