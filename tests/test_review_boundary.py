from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.review_boundary import apply_review_boundary


class ReviewBoundaryTest(unittest.TestCase):
    def test_apply_review_boundary_marks_sections_and_paragraphs(self) -> None:
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
                    "source_end_index": 12,
                    "paragraph_count": 2,
                    "file": "frontmatter-0001-prefacio.json",
                },
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 20,
                    "source_start_index": 21,
                    "source_end_index": 24,
                    "paragraph_count": 4,
                    "file": "chapter-0001-conexao-dimensional.json",
                },
            ],
        }

        prefacio_payload = {
            "id": "frontmatter-0001-prefacio",
            "type": "frontmatter",
            "order": 1,
            "title": "Prefácio",
            "paragraphs": [
                {"id": "frontmatter-0001-prefacio-p-0001", "source_index": 11, "text": "Intro."},
                {"id": "frontmatter-0001-prefacio-p-0002", "source_index": 12, "text": "More intro."},
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "paragraphs": [
                {"id": "chapter-0001-conexao-dimensional-p-0001", "source_index": 21, "text": "Before boundary."},
                {"id": "chapter-0001-conexao-dimensional-p-0002", "source_index": 22, "text": "Boundary excerpt starts here."},
                {"id": "chapter-0001-conexao-dimensional-p-0003", "source_index": 23, "text": "After boundary."},
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            chapters_dir = Path(temp_dir)
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

            summary = apply_review_boundary(chapters_dir, "Boundary excerpt starts here.")

            self.assertEqual(summary["boundary_section_id"], "chapter-0001-conexao-dimensional")
            self.assertEqual(
                summary["boundary_paragraph_id"],
                "chapter-0001-conexao-dimensional-p-0002",
            )

            review_state = json.loads((chapters_dir / "review-state.json").read_text(encoding="utf-8"))
            updated_index = json.loads((chapters_dir / "index.json").read_text(encoding="utf-8"))
            updated_prefacio = json.loads(
                (chapters_dir / "frontmatter-0001-prefacio.json").read_text(encoding="utf-8")
            )
            updated_chapter = json.loads(
                (chapters_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(review_state["boundary_source_index"], 22)
            self.assertEqual(updated_index["sections"][0]["review_status"], "approved_reference")
            self.assertEqual(updated_index["sections"][1]["review_status"], "mixed")
            self.assertEqual(updated_prefacio["review_status"], "approved_reference")
            self.assertEqual(
                updated_chapter["paragraphs"][0]["review_status"],
                "approved_reference",
            )
            self.assertEqual(
                updated_chapter["paragraphs"][1]["review_status"],
                "pending_review",
            )
            self.assertEqual(
                updated_chapter["paragraphs"][2]["review_status"],
                "pending_review",
            )

    def test_apply_review_boundary_raises_when_excerpt_is_missing(self) -> None:
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
                },
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "paragraphs": [
                {"id": "chapter-0001-conexao-dimensional-p-0001", "source_index": 21, "text": "Only paragraph."},
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            chapters_dir = Path(temp_dir)
            (chapters_dir / "index.json").write_text(
                json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                apply_review_boundary(chapters_dir, "missing excerpt")
