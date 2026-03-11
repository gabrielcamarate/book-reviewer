from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.manuscript_rebuild import rebuild_manuscript_state


class ManuscriptRebuildTest(unittest.TestCase):
    def test_rebuild_manuscript_state_regenerates_structure_and_syncs_consolidated_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extracted_dir = temp_path / "manuscript" / "extracted"
            chapters_dir = temp_path / "manuscript" / "chapters"
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            reports_dir = temp_path / "reports"

            extracted_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)

            paragraphs = [
                {"index": 1, "text": "Capítulo 1: Um.", "is_empty": False},
                {"index": 2, "text": "Texto aprovado.", "is_empty": False},
                {
                    "index": 3,
                    "text": "Todo cuidado é pouco, tratando-se do Sistema Terra estabelecido.",
                    "is_empty": False,
                },
                {"index": 4, "text": "Capítulo 2: Dois.", "is_empty": False},
                {"index": 5, "text": "Texto do capítulo dois.", "is_empty": False},
                {"index": 6, "text": "*******", "is_empty": False},
                {"index": 7, "text": "C", "is_empty": False},
                {"index": 8, "text": "Apítulo 3: Três.", "is_empty": False},
                {"index": 9, "text": "", "is_empty": True},
                {"index": 10, "text": "Texto do capítulo três.", "is_empty": False},
            ]
            (extracted_dir / "paragraphs.json").write_text(
                json.dumps(paragraphs, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            old_chapters_index = {
                "section_count": 2,
                "chapter_count": 2,
                "sections": [
                    {
                        "id": "chapter-0001-um",
                        "type": "chapter",
                        "order": 1,
                        "title": "Capítulo 1: Um.",
                        "paragraph_count": 2,
                        "file": "chapter-0001-um.json",
                    },
                    {
                        "id": "chapter-0002-tres",
                        "type": "chapter",
                        "order": 2,
                        "title": "Capítulo 3: Três.",
                        "paragraph_count": 1,
                        "file": "chapter-0002-tres.json",
                    },
                ],
            }
            (chapters_dir / "index.json").write_text(
                json.dumps(old_chapters_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 1,
                        "chunks": [
                            {
                                "id": "chapter-0002-tres-chunk-0001",
                                "section_id": "chapter-0002-tres",
                                "section_title": "Capítulo 3: Três.",
                                "chunk_order": 1,
                                "review_status": "pending_review",
                                "paragraph_count": 1,
                                "source_start_index": 10,
                                "source_end_index": 10,
                                "file": "chapter-0002-tres-chunk-0001.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 2,
                        "chapter_count": 2,
                        "sections": [
                            {
                                "id": "chapter-0001-um",
                                "type": "chapter",
                                "order": 1,
                                "title": "Capítulo 1: Um.",
                                "file": "chapter-0001-um.json",
                            },
                            {
                                "id": "chapter-0002-tres",
                                "type": "chapter",
                                "order": 2,
                                "title": "Capítulo 3: Três.",
                                "file": "chapter-0002-tres.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-um.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-um",
                        "title": "Capítulo 1: Um.",
                        "paragraphs": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "chapter-0002-tres-chunk-0001.copyedit.json").write_text(
                "{}",
                encoding="utf-8",
            )

            summary = rebuild_manuscript_state(
                extracted_dir=extracted_dir,
                chapters_dir=chapters_dir,
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                reports_dir=reports_dir,
                cutoff_excerpt="Todo cuidado é pouco, tratando-se do Sistema Terra estabelecido",
            )

            new_chapters_index = json.loads((chapters_dir / "index.json").read_text(encoding="utf-8"))
            new_chunks_index = json.loads((chunks_dir / "index.json").read_text(encoding="utf-8"))
            new_consolidated_index = json.loads((consolidated_dir / "index.json").read_text(encoding="utf-8"))
            report = json.loads((reports_dir / "manuscript-rebuild.json").read_text(encoding="utf-8"))

            self.assertEqual(new_chapters_index["chapter_count"], 3)
            self.assertEqual(new_chapters_index["chapter_number_sequence"], [1, 2, 3])
            self.assertEqual(new_chapters_index["missing_chapter_numbers"], [])
            self.assertEqual(new_chunks_index["chunk_count"], 3)
            self.assertEqual(
                [section["id"] for section in new_consolidated_index["sections"]],
                [
                    "chapter-0001-um",
                    "chapter-0002-dois",
                    "chapter-0003-tres",
                ],
            )
            self.assertEqual(report["migration"]["chapter_ids_added"], ["chapter-0002-dois", "chapter-0003-tres"])
            self.assertEqual(report["migration"]["chapter_ids_removed"], ["chapter-0002-tres"])
            self.assertEqual(report["reviews"]["ptbr_orphaned_review_files"], ["chapter-0002-tres-chunk-0001.copyedit.json"])
            self.assertTrue(report["integrity"]["chapter_numbers_contiguous"])
            self.assertTrue(summary["integrity"]["chapter_numbers_contiguous"])
            self.assertTrue((consolidated_dir / "chapter-0001-um.json").exists())
