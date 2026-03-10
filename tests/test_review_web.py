from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from review_web.dashboard import build_dashboard_state, render_dashboard_html


class ReviewWebDashboardTest(unittest.TestCase):
    def test_build_dashboard_state_reads_persisted_project_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reports_dir = temp_path / "reports"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            deliverables_dir = temp_path / "deliverables"

            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
            (deliverables_dir / "ptbr").mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 2,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0002",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0002.json",
                            },
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
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "mixed",
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
            (reports_dir / "ptbr-consistency-report.json").write_text(
                json.dumps(
                    {
                        "finding_count": 12,
                        "scope": {"section_count": 1, "paragraph_count": 10},
                        "findings_by_type": {
                            "alias_usage": [{"paragraph_id": "p1"}],
                            "quote_anomalies": [],
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "a.copyedit.json").write_text("{}", encoding="utf-8")
            (reviews_es_dir / "a.translation-es.json").write_text("{}", encoding="utf-8")
            (deliverables_dir / "ptbr" / "exilados-da-terra.ptbr.docx").write_text(
                "fake-docx",
                encoding="utf-8",
            )

            state = build_dashboard_state(
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reports_dir=reports_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                deliverables_dir=deliverables_dir,
            )

            self.assertEqual(state["summary"]["pending_chunk_count"], 2)
            self.assertEqual(state["summary"]["section_count"], 1)
            self.assertEqual(state["summary"]["copyedit_review_count"], 1)
            self.assertEqual(state["summary"]["translation_review_count"], 1)
            self.assertEqual(state["summary"]["deliverable_count"], 1)
            self.assertEqual(state["consistency_report"]["finding_count"], 12)
            self.assertEqual(state["recent_chunks"][0]["id"], "chapter-0001-conexao-dimensional-chunk-0001")

    def test_render_dashboard_html_includes_web_operational_sections(self) -> None:
        html = render_dashboard_html(
            {
                "summary": {
                    "pending_chunk_count": 2,
                    "section_count": 1,
                    "copyedit_review_count": 1,
                    "translation_review_count": 1,
                    "deliverable_count": 1,
                },
                "consistency_report": {
                    "finding_count": 12,
                    "finding_types": [
                        {"type": "alias_usage", "count": 3},
                        {"type": "quote_anomalies", "count": 1},
                    ],
                },
                "recent_chunks": [
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "review_status": "pending_review",
                    }
                ],
                "deliverables": [
                    {
                        "path": "deliverables/ptbr/exilados-da-terra.ptbr.docx",
                        "name": "exilados-da-terra.ptbr.docx",
                    }
                ],
            }
        )

        self.assertIn("Editorial Review Dashboard", html)
        self.assertIn("Pending Review Chunks", html)
        self.assertIn("Consistency Report", html)
        self.assertIn("Capítulo 1: Conexão Dimensional.", html)
        self.assertIn("exilados-da-terra.ptbr.docx", html)
