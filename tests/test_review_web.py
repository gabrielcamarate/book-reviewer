from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from review_web.dashboard import (
    build_chapter_detail_state,
    build_chunk_detail_state,
    build_dashboard_state,
    render_chapter_detail_html,
    render_chunk_detail_html,
    render_dashboard_html,
)
from review_web.actions import trigger_copyedit


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
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
                        "base_text": "Primeiro chunk pendente.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0002.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0002",
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0002"],
                        "base_text": "Segundo chunk pendente.",
                        "previous_context": [],
                        "next_context": [],
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
            self.assertEqual(state["chapters"][0]["id"], "chapter-0001-conexao-dimensional")
            self.assertEqual(state["chapters"][0]["chunk_count"], 2)
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
                "chapters": [
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "review_status": "mixed",
                        "chunk_count": 2,
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

    def test_build_chapter_detail_state_groups_chunks_for_selected_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)

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
            (consolidated_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 2,
                        "chapter_count": 2,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "mixed",
                                "file": "chapter-0001-conexao-dimensional.json",
                            },
                            {
                                "id": "chapter-0002-supremo-poder-anonimo",
                                "title": "Capítulo 2: Supremo Poder Anônimo.",
                                "review_status": "pending_review",
                                "file": "chapter-0002-supremo-poder-anonimo.json",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            state = build_chapter_detail_state(
                chapter_id="chapter-0001-conexao-dimensional",
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
            )

            self.assertEqual(state["chapter"]["id"], "chapter-0001-conexao-dimensional")
            self.assertEqual(len(state["chunks"]), 2)
            self.assertEqual(state["chunks"][0]["id"], "chapter-0001-conexao-dimensional-chunk-0001")

            html = render_chapter_detail_html(state)
            self.assertIn("Chapter Navigation", html)
            self.assertIn("chapter-0001-conexao-dimensional-chunk-0001", html)

    def test_build_chunk_detail_state_reads_selected_chunk_payload(self) -> None:
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
                        "chunk_count": 1,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "review_status": "pending_review",
                        "paragraph_ids": [
                            "chapter-0001-conexao-dimensional-p-0001",
                            "chapter-0001-conexao-dimensional-p-0002",
                        ],
                        "base_text": "Trecho principal.",
                        "previous_context": [
                            {
                                "paragraph_id": "prev-1",
                                "text": "Contexto anterior.",
                            }
                        ],
                        "next_context": [
                            {
                                "paragraph_id": "next-1",
                                "text": "Contexto seguinte.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "suggestions": [
                            {
                                "original": "Trecho principal.",
                                "suggested": "Trecho principal revisado.",
                                "change_type": "pontuação",
                                "reason": "Ajuste de clareza.",
                                "confidence": 0.88,
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.approval.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "status": "approved",
                        "applied_change_count": 1,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_es_dir / "chapter-0001-conexao-dimensional-chunk-0001.translation-es.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "translations": [
                            {
                                "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                                "translated_text": "Fragmento principal.",
                                "rationale": "Mantém o tom.",
                                "confidence": 0.74,
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            state = build_chunk_detail_state(
                chunk_id="chapter-0001-conexao-dimensional-chunk-0001",
                chunks_dir=chunks_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertEqual(state["chunk"]["id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["chunk"]["base_text"], "Trecho principal.")
            self.assertEqual(state["chunk"]["previous_context"][0]["text"], "Contexto anterior.")
            self.assertEqual(state["copyedit_review"]["suggestions"][0]["suggested"], "Trecho principal revisado.")
            self.assertEqual(state["approval"]["applied_change_count"], 1)
            self.assertEqual(state["translation_review"]["translations"][0]["translated_text"], "Fragmento principal.")

            html = render_chunk_detail_html(state)
            self.assertIn("Chunk Detail", html)
            self.assertIn("Trecho principal.", html)
            self.assertIn("Contexto seguinte.", html)
            self.assertIn("Trecho principal", html)
            self.assertIn("revisado", html)
            self.assertIn("Fragmento principal.", html)
            self.assertIn("Run Copyedit", html)
            self.assertIn("Suggestion Review", html)
            self.assertIn("Original", html)
            self.assertIn("Suggested", html)
            self.assertIn("Confidence", html)
            self.assertIn("0.88", html)
            self.assertIn("diff-added", html)
            self.assertIn("diff-removed", html)

    def test_trigger_copyedit_persists_review_for_selected_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 1,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "source_start_index": 1,
                                "source_end_index": 3,
                                "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "paragraph_ids": [
                            "chapter-0001-conexao-dimensional-p-0001",
                        ],
                        "source_start_index": 1,
                        "source_end_index": 3,
                        "base_text": "Trecho principal.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n- Preserve voice.\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n- Sistema Terra\n", encoding="utf-8")

            summary = trigger_copyedit(
                chunk_id="chapter-0001-conexao-dimensional-chunk-0001",
                chunks_dir=chunks_dir,
                reviews_dir=reviews_ptbr_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                runner=lambda **_: {
                    "suggestions": [
                        {
                            "original": "Trecho principal.",
                            "suggested": "Trecho principal revisado.",
                            "change_type": "pontuação",
                            "reason": "Ajuste de clareza.",
                            "confidence": 0.81,
                        }
                    ]
                },
            )

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            persisted = json.loads(
                (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(persisted["suggestions"][0]["suggested"], "Trecho principal revisado.")
