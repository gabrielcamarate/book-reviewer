from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from revisor.core.glossary import generate_glossary, _extract_formula_entry


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
                    "id": "chapter-0001-caminhos-da-serra",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Caminhos da Serra.",
                    "heading_source_index": 147,
                    "source_start_index": 148,
                    "source_end_index": 149,
                    "paragraph_count": 2,
                    "file": "chapter-0001-caminhos-da-serra.json",
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
                    "text": "LEC — Liga de Exploração Científica protege o Sistema Aurora.",
                },
                {
                    "id": "frontmatter-0005-prefacio-p-0002",
                    "source_index": 90,
                    "review_status": "approved_reference",
                    "text": "Lia Monteiro denuncia a IPVN — Instituto de Pesquisa da Vila Nova no Sistema Aurora.",
                },
                {
                    "id": "frontmatter-0005-prefacio-p-0003",
                    "source_index": 91,
                    "review_status": "approved_reference",
                    "text": "a história é uma viagem... o caminho é a descoberta... a esperança é uma estrela... todos os sonhos são possíveis.",
                },
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-caminhos-da-serra",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Caminhos da Serra.",
            "review_status": "mixed",
            "paragraphs": [
                {
                    "id": "chapter-0001-caminhos-da-serra-p-0001",
                    "source_index": 148,
                    "review_status": "approved_reference",
                    "text": "Liga de Exploração Científica amplia o chamado do Sistema Aurora.",
                },
                {
                    "id": "chapter-0001-caminhos-da-serra-p-0002",
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
            (chapters_dir / "chapter-0001-caminhos-da-serra.json").write_text(
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
            self.assertIn("### IPVN", glossary_text)
            self.assertIn("Preferred form: `IPVN`", glossary_text)
            self.assertIn("Expanded form: `Instituto de Pesquisa da Vila Nova`", glossary_text)
            self.assertIn("### LEC", glossary_text)
            self.assertIn("Observed aliases or variants: `Liga de Exploração Científica`", glossary_text)
            self.assertIn("### Lia Monteiro", glossary_text)
            self.assertIn("### Sistema Aurora", glossary_text)
            self.assertIn("### Philosophical Formula", glossary_text)
            self.assertIn("a história é uma viagem", glossary_text)
            self.assertNotIn("Pending paragraph that must not appear in the glossary.", glossary_text)

    def test_formula_uses_approved_source_and_ignores_a_short_pause(self) -> None:
        clauses = ["a aventura começa nesta cidade", "o caminho segue pela floresta", "a esperança permanece com todos"]
        result = _extract_formula_entry([{"paragraph_id": "p1", "text": "... ".join(clauses)}])
        self.assertEqual(result["preferred_form"], "... ".join(clauses) + ".")
        self.assertEqual(result["evidence_ids"], ["p1"])
        self.assertIsNone(_extract_formula_entry([{"paragraph_id": "p2", "text": "Ela partiu... ele ficou."}]))

    def test_generate_glossary_raises_without_approved_reference(self) -> None:
        index_payload = {
            "section_count": 1,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "chapter-0001-caminhos-da-serra",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Caminhos da Serra.",
                    "heading_source_index": 147,
                    "source_start_index": 148,
                    "source_end_index": 148,
                    "paragraph_count": 1,
                    "file": "chapter-0001-caminhos-da-serra.json",
                    "review_status": "pending_review",
                },
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-caminhos-da-serra",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Caminhos da Serra.",
            "review_status": "pending_review",
            "paragraphs": [
                {
                    "id": "chapter-0001-caminhos-da-serra-p-0001",
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
            (chapters_dir / "chapter-0001-caminhos-da-serra.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                generate_glossary(chapters_dir, output_path)
