from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.repository_doctor import run_repository_doctor


class RepositoryDoctorTest(unittest.TestCase):
    def test_run_repository_doctor_reports_blocking_findings_for_missing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)

            summary = run_repository_doctor(root_dir=root_dir)

            self.assertFalse(summary["ok"])
            self.assertGreater(summary["blocking_count"], 0)
            self.assertEqual(summary["advisory_count"], 0)
            self.assertEqual(summary["blocking_findings"][0]["severity"], "blocking")

    def test_run_repository_doctor_reports_chunk_section_mismatches_as_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            (root_dir / "editorial").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chapters").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chunks").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "consolidated").mkdir(parents=True, exist_ok=True)

            (root_dir / "editorial" / "STYLE_GUIDE.md").write_text("# Style Guide\n", encoding="utf-8")
            (root_dir / "editorial" / "GLOSSARY.md").write_text("# Glossary\n", encoding="utf-8")
            (root_dir / "editorial" / "DECISIONS.md").write_text("# Editorial Decisions\n", encoding="utf-8")
            (root_dir / "manuscript" / "chapters" / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (root_dir / "manuscript" / "chunks" / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 1,
                        "chunks": [
                            {
                                "id": "chapter-9999-fantasma-chunk-0001",
                                "section_id": "chapter-9999-fantasma",
                                "section_title": "Capítulo 9: Fantasma.",
                                "review_status": "pending_review",
                                "file": "chapter-9999-fantasma-chunk-0001.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (root_dir / "manuscript" / "consolidated" / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = run_repository_doctor(root_dir=root_dir)

            self.assertFalse(summary["ok"])
            self.assertIn("chunk_section_missing", {item["code"] for item in summary["blocking_findings"]})

    def test_run_repository_doctor_reports_missing_chapter_numbers_as_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            (root_dir / "editorial").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chapters").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chunks").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "consolidated").mkdir(parents=True, exist_ok=True)

            (root_dir / "editorial" / "STYLE_GUIDE.md").write_text("# Style Guide\n", encoding="utf-8")
            (root_dir / "editorial" / "GLOSSARY.md").write_text("# Glossary\n", encoding="utf-8")
            (root_dir / "editorial" / "DECISIONS.md").write_text("# Editorial Decisions\n", encoding="utf-8")
            (root_dir / "manuscript" / "chapters" / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 2,
                        "chapter_count": 2,
                        "chapter_number_sequence": [1, 4],
                        "missing_chapter_numbers": [2, 3],
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "declared_chapter_number": 1,
                                "file": "chapter-0001-conexao-dimensional.json",
                            },
                            {
                                "id": "chapter-0002-guerra-dimensional",
                                "type": "chapter",
                                "title": "Capítulo 4: Guerra Dimensional.",
                                "declared_chapter_number": 4,
                                "file": "chapter-0002-guerra-dimensional.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (root_dir / "manuscript" / "chunks" / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 2,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                            },
                            {
                                "id": "chapter-0002-guerra-dimensional-chunk-0001",
                                "section_id": "chapter-0002-guerra-dimensional",
                                "section_title": "Capítulo 4: Guerra Dimensional.",
                                "review_status": "pending_review",
                                "file": "chapter-0002-guerra-dimensional-chunk-0001.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (root_dir / "manuscript" / "consolidated" / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 2,
                        "chapter_count": 2,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                            },
                            {
                                "id": "chapter-0002-guerra-dimensional",
                                "title": "Capítulo 4: Guerra Dimensional.",
                                "file": "chapter-0002-guerra-dimensional.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = run_repository_doctor(root_dir=root_dir)

            self.assertTrue(summary["ok"])
            self.assertEqual(summary["blocking_count"], 0)
            self.assertEqual(summary["advisory_count"], 1)
            self.assertEqual(summary["advisory_findings"][0]["code"], "missing_declared_chapter_numbers")
