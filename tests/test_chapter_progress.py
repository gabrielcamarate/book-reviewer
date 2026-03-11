from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.chapter_progress import build_chapter_progress


class ChapterProgressTest(unittest.TestCase):
    def test_build_chapter_progress_aggregates_rollups_by_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)

            chunk_ids = [
                "chapter-0001-conexao-dimensional-chunk-0001",
                "chapter-0001-conexao-dimensional-chunk-0002",
                "chapter-0001-conexao-dimensional-chunk-0003",
                "chapter-0001-conexao-dimensional-chunk-0004",
                "chapter-0001-conexao-dimensional-chunk-0005",
                "chapter-0001-conexao-dimensional-chunk-0006",
                "chapter-0001-conexao-dimensional-chunk-0007",
                "chapter-0002-supremo-poder-anonimo-chunk-0001",
            ]
            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": len(chunk_ids),
                        "chunks": [
                            {
                                "id": chunk_ids[0],
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                            },
                            {
                                "id": chunk_ids[1],
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                            },
                            {
                                "id": chunk_ids[2],
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                            },
                            {
                                "id": chunk_ids[3],
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                            },
                            {
                                "id": chunk_ids[4],
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                            },
                            {
                                "id": chunk_ids[5],
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                            },
                            {
                                "id": chunk_ids[6],
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "approved_reference",
                            },
                            {
                                "id": chunk_ids[7],
                                "section_id": "chapter-0002-supremo-poder-anonimo",
                                "section_title": "Capítulo 2: Supremo Poder Anônimo.",
                                "review_status": "pending_review",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            (reviews_ptbr_dir / f"{chunk_ids[1]}.copyedit.json").write_text("{}", encoding="utf-8")
            (reviews_ptbr_dir / f"{chunk_ids[2]}.approval.json").write_text("{}", encoding="utf-8")
            (reviews_ptbr_dir / f"{chunk_ids[3]}.style.json").write_text("{}", encoding="utf-8")
            (reviews_ptbr_dir / f"{chunk_ids[4]}.style.approval.json").write_text("{}", encoding="utf-8")
            (reviews_es_dir / f"{chunk_ids[5]}.translation-es.json").write_text("{}", encoding="utf-8")
            (reviews_es_dir / f"{chunk_ids[7]}.translation-es.json").write_text("{}", encoding="utf-8")

            progress = build_chapter_progress(
                chunks_dir=chunks_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertEqual(progress["summary"]["chapter_count"], 2)
            self.assertEqual(progress["summary"]["completed_chapter_count"], 1)
            self.assertEqual(progress["summary"]["actionable_chapter_count"], 1)

            chapter_one = progress["chapters"][0]
            chapter_two = progress["chapters"][1]

            self.assertEqual(chapter_one["id"], "chapter-0001-conexao-dimensional")
            self.assertEqual(chapter_one["chunk_count"], 7)
            self.assertEqual(chapter_one["pending_copyedit_count"], 1)
            self.assertEqual(chapter_one["awaiting_copyedit_approval_count"], 1)
            self.assertEqual(chapter_one["ready_for_style_count"], 1)
            self.assertEqual(chapter_one["awaiting_style_approval_count"], 1)
            self.assertEqual(chapter_one["ready_for_translation_count"], 1)
            self.assertEqual(chapter_one["translated_count"], 1)
            self.assertEqual(chapter_one["reference_count"], 1)
            self.assertEqual(chapter_one["completed_count"], 2)
            self.assertEqual(chapter_one["completion_percent"], 29)
            self.assertEqual(chapter_one["chapter_status"], "awaiting_copyedit_approval")

            self.assertEqual(chapter_two["id"], "chapter-0002-supremo-poder-anonimo")
            self.assertEqual(chapter_two["translated_count"], 1)
            self.assertEqual(chapter_two["completed_count"], 1)
            self.assertEqual(chapter_two["completion_percent"], 100)
            self.assertEqual(chapter_two["chapter_status"], "completed")
