from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.glossary import generate_glossary


class GlossaryTest(unittest.TestCase):
    def test_generate_glossary_writes_normalized_terms_and_aliases(self) -> None:
        index_payload = {
            "section_count": 2,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "frontmatter-0005-prefacio",
                    "type": "frontmatter",
                    "order": 5,
                    "title": "Prefácio",
                    "heading_source_index": 87,
                    "source_start_index": 89,
                    "source_end_index": 91,
                    "paragraph_count": 3,
                    "file": "frontmatter-0005-prefacio.json",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 147,
                    "source_start_index": 148,
                    "source_end_index": 149,
                    "paragraph_count": 2,
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "mixed",
                },
            ],
        }

        prefacio_payload = {
            "id": "frontmatter-0005-prefacio",
            "type": "frontmatter",
            "order": 5,
            "title": "Prefácio",
            "review_status": "approved_reference",
            "paragraphs": [
                {
                    "id": "frontmatter-0005-prefacio-p-0001",
                    "source_index": 89,
                    "review_status": "approved_reference",
                    "text": "SEU — Soberana Energia Universal protege o Sistema Terra.",
                },
                {
                    "id": "frontmatter-0005-prefacio-p-0002",
                    "source_index": 90,
                    "review_status": "approved_reference",
                    "text": "Tom Harrison denuncia a IMSD — Independência Mundial dos Servos de Deus no Sistema Terra.",
                },
                {
                    "id": "frontmatter-0005-prefacio-p-0003",
                    "source_index": 91,
                    "review_status": "approved_reference",
                    "text": "a minha raça humana é universal... o meu sexo é o amor... a minha religião é a consciência... todos os gêneros são iguais.",
                },
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "review_status": "mixed",
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 148,
                    "review_status": "approved_reference",
                    "text": "Soberana Energia Universal amplia o chamado do Sistema Terra.",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 149,
                    "review_status": "pending_review",
                    "text": "Pending paragraph that must not appear in the glossary.",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            output_path = temp_path / "editorial" / "GLOSSARY.md"
            chapters_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "frontmatter-0005-prefacio.json").write_text(
                json.dumps(prefacio_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = generate_glossary(chapters_dir, output_path)
            glossary_text = output_path.read_text(encoding="utf-8")

            self.assertEqual(summary["approved_paragraph_count"], 4)
            self.assertGreaterEqual(summary["entry_count"], 5)
            self.assertIn("# Glossary", glossary_text)
            self.assertIn("## Organizations and Acronyms", glossary_text)
            self.assertIn("## Proper Names", glossary_text)
            self.assertIn("## Concepts and Formulas", glossary_text)
            self.assertIn("### IMSD", glossary_text)
            self.assertIn("Preferred form: `IMSD`", glossary_text)
            self.assertIn("Expanded form: `Independência Mundial dos Servos de Deus`", glossary_text)
            self.assertIn("### SEU", glossary_text)
            self.assertIn("Observed aliases or variants: `Soberana Energia Universal`", glossary_text)
            self.assertIn("### Tom Harrison", glossary_text)
            self.assertIn("### Sistema Terra", glossary_text)
            self.assertIn("### Philosophical Formula", glossary_text)
            self.assertIn("a minha raça humana é universal", glossary_text)
            self.assertNotIn("Pending paragraph that must not appear in the glossary.", glossary_text)

    def test_generate_glossary_raises_without_approved_reference(self) -> None:
        index_payload = {
            "section_count": 1,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 147,
                    "source_start_index": 148,
                    "source_end_index": 148,
                    "paragraph_count": 1,
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "pending_review",
                },
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "review_status": "pending_review",
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 148,
                    "review_status": "pending_review",
                    "text": "Only pending material.",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            output_path = temp_path / "editorial" / "GLOSSARY.md"
            chapters_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                generate_glossary(chapters_dir, output_path)
