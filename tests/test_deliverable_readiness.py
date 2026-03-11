from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.deliverable_readiness import generate_deliverable_readiness_report


class DeliverableReadinessTest(unittest.TestCase):
    def test_generate_deliverable_readiness_report_groups_blockers_by_language_and_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            reports_dir = temp_path / "reports"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 3,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0002",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0002.json",
                            },
                            {
                                "id": "chapter-0002-supremo-poder-anonimo-chunk-0001",
                                "section_id": "chapter-0002-supremo-poder-anonimo",
                                "section_title": "Capítulo 2: Supremo Poder Anônimo.",
                                "review_status": "pending_review",
                                "file": "chapter-0002-supremo-poder-anonimo-chunk-0001.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            for chunk_id, paragraph_id in [
                ("chapter-0001-conexao-dimensional-chunk-0001", "chapter-0001-conexao-dimensional-p-0001"),
                ("chapter-0001-conexao-dimensional-chunk-0002", "chapter-0001-conexao-dimensional-p-0002"),
                ("chapter-0002-supremo-poder-anonimo-chunk-0001", "chapter-0002-supremo-poder-anonimo-p-0001"),
            ]:
                (chunks_dir / f"{chunk_id}.json").write_text(
                    json.dumps(
                        {
                            "id": chunk_id,
                            "section_id": chunk_id.rsplit("-chunk-", 1)[0],
                            "section_title": "Capítulo 1: Conexão Dimensional."
                            if "conexao" in chunk_id
                            else "Capítulo 2: Supremo Poder Anônimo.",
                            "paragraph_ids": [paragraph_id],
                            "source_start_index": 1,
                            "source_end_index": 1,
                            "base_text": "Trecho.",
                            "previous_context": [],
                            "next_context": [],
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

            chapter_one = {
                "id": "chapter-0001-conexao-dimensional",
                "title": "Capítulo 1: Conexão Dimensional.",
                "paragraphs": [
                    {
                        "id": "chapter-0001-conexao-dimensional-p-0001",
                        "source_index": 1,
                        "source_text": "Original 1.",
                        "text": "Consolidado 1.",
                        "review_status": "pending_review",
                        "applied_reviews": [],
                    },
                    {
                        "id": "chapter-0001-conexao-dimensional-p-0002",
                        "source_index": 2,
                        "source_text": "Original 2.",
                        "text": "Consolidado 2.",
                        "review_status": "approved",
                        "applied_reviews": [],
                    },
                ],
            }
            chapter_two = {
                "id": "chapter-0002-supremo-poder-anonimo",
                "title": "Capítulo 2: Supremo Poder Anônimo.",
                "paragraphs": [
                    {
                        "id": "chapter-0002-supremo-poder-anonimo-p-0001",
                        "source_index": 1,
                        "source_text": "Original 3.",
                        "text": "Consolidado 3.",
                        "review_status": "approved_reference",
                        "applied_reviews": [],
                    }
                ],
            }
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_one, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0002-supremo-poder-anonimo.json").write_text(
                json.dumps(chapter_two, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_one, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0002-supremo-poder-anonimo.json").write_text(
                json.dumps(chapter_two, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "chapter-0002-supremo-poder-anonimo-chunk-0001.style.approval.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (reviews_es_dir / "chapter-0001-conexao-dimensional-chunk-0002.translation-es.json").write_text(
                json.dumps({"translations": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            report = generate_deliverable_readiness_report(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                reports_dir=reports_dir,
            )

            self.assertFalse(report["pt-BR"]["eligible"])
            self.assertEqual(report["pt-BR"]["blocker_count"], 1)
            self.assertEqual(report["es"]["blocker_count"], 2)
            self.assertEqual(report["es"]["blockers"][0]["reason"], "ptbr_not_ready")
            self.assertEqual(report["es"]["blockers"][1]["reason"], "missing_translation")
            self.assertEqual(report["pt-BR"]["chapters"][0]["chapter_id"], "chapter-0001-conexao-dimensional")
            self.assertTrue((reports_dir / "deliverable-readiness.json").exists())
