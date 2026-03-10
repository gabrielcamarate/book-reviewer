from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.style_guide import generate_style_guide


class StyleGuideTest(unittest.TestCase):
    def test_generate_style_guide_ignores_non_prose_frontmatter_sections(self) -> None:
        index_payload = {
            "section_count": 2,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "frontmatter-0001-sumario",
                    "type": "frontmatter",
                    "order": 1,
                    "title": "Sumário",
                    "heading_source_index": 10,
                    "source_start_index": 11,
                    "source_end_index": 12,
                    "paragraph_count": 2,
                    "file": "frontmatter-0001-sumario.json",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 20,
                    "source_start_index": 21,
                    "source_end_index": 22,
                    "paragraph_count": 2,
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "approved_reference",
                },
            ],
        }

        sumario_payload = {
            "id": "frontmatter-0001-sumario",
            "type": "frontmatter",
            "order": 1,
            "title": "Sumário",
            "review_status": "approved_reference",
            "paragraphs": [
                {
                    "id": "frontmatter-0001-sumario-p-0001",
                    "source_index": 11,
                    "text": "Capítulo I\t09",
                    "review_status": "approved_reference",
                },
                {
                    "id": "frontmatter-0001-sumario-p-0002",
                    "source_index": 12,
                    "text": "Conexão Dimensional",
                    "review_status": "approved_reference",
                },
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "review_status": "approved_reference",
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 21,
                    "text": "▬ Perdoe-nos ― vocifera representante da CGU ― Ossos do ofício... grato pela recepção.",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 22,
                    "text": "IMSD e CGU permanecem em letras altas.",
                    "review_status": "approved_reference",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            output_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            chapters_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "frontmatter-0001-sumario.json").write_text(
                json.dumps(sumario_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = generate_style_guide(chapters_dir, output_path)
            guide_text = output_path.read_text(encoding="utf-8")

            self.assertEqual(summary["approved_section_count"], 1)
            self.assertEqual(summary["approved_paragraph_count"], 2)
            self.assertNotIn("frontmatter-0001-sumario", guide_text)
            self.assertIn("chapter-0001-conexao-dimensional", guide_text)

    def test_generate_style_guide_writes_confirmed_rules_and_hypotheses(self) -> None:
        index_payload = {
            "section_count": 2,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "frontmatter-0001-prefacio",
                    "type": "frontmatter",
                    "order": 1,
                    "title": "Prefácio",
                    "heading_source_index": 10,
                    "source_start_index": 11,
                    "source_end_index": 13,
                    "paragraph_count": 3,
                    "file": "frontmatter-0001-prefacio.json",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 20,
                    "source_start_index": 21,
                    "source_end_index": 23,
                    "paragraph_count": 3,
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "mixed",
                },
            ],
        }

        prefacio_payload = {
            "id": "frontmatter-0001-prefacio",
            "type": "frontmatter",
            "order": 1,
            "title": "Prefácio",
            "review_status": "approved_reference",
            "paragraphs": [
                {
                    "id": "frontmatter-0001-prefacio-p-0001",
                    "source_index": 11,
                    "text": "A literatura não pede licença ao tempo — ela o atravessa.",
                    "review_status": "approved_reference",
                },
                {
                    "id": "frontmatter-0001-prefacio-p-0002",
                    "source_index": 12,
                    "text": "A minha raça humana é universal... o meu sexo é o amor... a minha religião é a consciência... todos os gêneros são iguais.",
                    "review_status": "approved_reference",
                },
                {
                    "id": "frontmatter-0001-prefacio-p-0003",
                    "source_index": 13,
                    "text": "IMSD e CGU permanecem em letras altas.",
                    "review_status": "approved_reference",
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
                    "source_index": 21,
                    "text": "▬ Perdoe-nos ― vocifera representante da CGU ― Ossos do ofício... grato pela recepção.",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 22,
                    "text": "Todo cuidado é pouco, tratando-se do Sistema Terra estabelecido",
                    "review_status": "pending_review",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            output_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            chapters_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "frontmatter-0001-prefacio.json").write_text(
                json.dumps(prefacio_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = generate_style_guide(chapters_dir, output_path)
            guide_text = output_path.read_text(encoding="utf-8")

            self.assertEqual(summary["approved_section_count"], 2)
            self.assertEqual(summary["approved_paragraph_count"], 4)
            self.assertGreaterEqual(summary["confirmed_rule_count"], 4)
            self.assertIn("# Style Guide", guide_text)
            self.assertIn("## Corpus Scope", guide_text)
            self.assertIn("## Confirmed Rules", guide_text)
            self.assertIn("## Observed Patterns", guide_text)
            self.assertIn("## Editorial Hypotheses", guide_text)
            self.assertIn("Approved reference paragraphs: `4`", guide_text)
            self.assertIn("Preserve dialogue turns marked with `▬`.", guide_text)
            self.assertIn("Preserve ellipsis chains `...`.", guide_text)
            self.assertIn("Preserve uppercase acronyms and institutional short forms.", guide_text)
            self.assertIn("frontmatter-0001-prefacio-p-0002", guide_text)
            self.assertIn("chapter-0001-conexao-dimensional-p-0001", guide_text)

    def test_generate_style_guide_raises_when_no_approved_reference_exists(self) -> None:
        index_payload = {
            "section_count": 1,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 20,
                    "source_start_index": 21,
                    "source_end_index": 21,
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
                    "source_index": 21,
                    "text": "Only pending paragraph.",
                    "review_status": "pending_review",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            output_path = temp_path / "editorial" / "STYLE_GUIDE.md"
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
                generate_style_guide(chapters_dir, output_path)
