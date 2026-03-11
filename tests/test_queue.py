from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.queue import build_review_queue


class QueueTest(unittest.TestCase):
    def test_build_review_queue_derives_progress_and_next_recommended_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 4,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "chunk_order": 1,
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0002",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "chunk_order": 2,
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0002.json",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0003",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "chunk_order": 3,
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0003.json",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0004",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "chunk_order": 4,
                                "review_status": "approved_reference",
                                "file": "chapter-0001-conexao-dimensional-chunk-0004.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json").write_text("{}", encoding="utf-8")
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0002.copyedit.json").write_text("{}", encoding="utf-8")
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0002.approval.json").write_text("{}", encoding="utf-8")
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0003.copyedit.json").write_text("{}", encoding="utf-8")
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0003.approval.json").write_text("{}", encoding="utf-8")
            (reviews_es_dir / "chapter-0001-conexao-dimensional-chunk-0003.translation-es.json").write_text("{}", encoding="utf-8")

            state = build_review_queue(
                chunks_dir=chunks_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertEqual(state["summary"]["total_chunks"], 4)
            self.assertEqual(state["summary"]["pending_copyedit_count"], 0)
            self.assertEqual(state["summary"]["awaiting_approval_count"], 1)
            self.assertEqual(state["summary"]["approved_count"], 1)
            self.assertEqual(state["summary"]["translated_count"], 1)
            self.assertEqual(state["summary"]["reference_count"], 1)
            self.assertEqual(state["next_recommended"]["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["queue_items"][0]["queue_status"], "awaiting_approval")
            self.assertEqual(state["queue_items"][2]["queue_status"], "translated")
