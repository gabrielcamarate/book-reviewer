from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.chunking import build_review_chunks


class ChunkingTest(unittest.TestCase):
    def test_build_review_chunks_persists_pending_chunks_with_side_context(self) -> None:
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
                    "source_end_index": 26,
                    "paragraph_count": 6,
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "mixed",
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
                    "text": "Approved setup paragraph.",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 22,
                    "text": "Pending paragraph one with enough characters to force grouping.",
                    "review_status": "pending_review",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0003",
                    "source_index": 23,
                    "text": "Pending paragraph two also belongs to the first chunk.",
                    "review_status": "pending_review",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0004",
                    "source_index": 24,
                    "text": "Pending paragraph three should open the second chunk.",
                    "review_status": "pending_review",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0005",
                    "source_index": 25,
                    "text": "Pending paragraph four completes the second chunk.",
                    "review_status": "pending_review",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0006",
                    "source_index": 26,
                    "text": "Trailing context paragraph after the chunk sequence.",
                    "review_status": "pending_review",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            output_dir = temp_path / "chunks"
            chapters_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = build_review_chunks(
                chapters_dir=chapters_dir,
                output_dir=output_dir,
                target_characters=120,
                max_paragraphs=2,
                context_paragraphs=1,
            )

            self.assertEqual(summary["chunk_count"], 3)

            index_data = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
            first_chunk = json.loads(
                (output_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").read_text(
                    encoding="utf-8"
                )
            )
            second_chunk = json.loads(
                (output_dir / "chapter-0001-conexao-dimensional-chunk-0002.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(index_data["chunk_count"], 3)
            self.assertEqual(index_data["chunks"][0]["id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(
                first_chunk["paragraph_ids"],
                [
                    "chapter-0001-conexao-dimensional-p-0002",
                    "chapter-0001-conexao-dimensional-p-0003",
                ],
            )
            self.assertEqual(
                first_chunk["previous_context"][0]["paragraph_id"],
                "chapter-0001-conexao-dimensional-p-0001",
            )
            self.assertEqual(
                first_chunk["next_context"][0]["paragraph_id"],
                "chapter-0001-conexao-dimensional-p-0004",
            )
            self.assertEqual(second_chunk["previous_context"][0]["paragraph_id"], "chapter-0001-conexao-dimensional-p-0003")
            self.assertEqual(second_chunk["review_status"], "pending_review")
            self.assertNotIn("Approved setup paragraph.", first_chunk["base_text"])

    def test_build_review_chunks_raises_without_pending_review_paragraphs(self) -> None:
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
                    "text": "Only approved paragraph.",
                    "review_status": "approved_reference",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            output_dir = temp_path / "chunks"
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
                build_review_chunks(chapters_dir=chapters_dir, output_dir=output_dir)
