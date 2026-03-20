from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from review_web.dashboard import (
    build_chapter_detail_state,
    build_characters_state,
    build_chunk_detail_state,
    build_consistency_detail_state,
    build_decisions_state,
    build_dashboard_state,
    build_glossary_state,
    build_queue_state,
    build_search_state,
    build_simple_home_state,
    build_world_rules_state,
    compute_export_readiness,
    render_characters_html,
    render_chapter_detail_html,
    render_chunk_detail_html,
    render_consistency_detail_html,
    render_decisions_html,
    render_dashboard_html,
    render_glossary_html,
    render_queue_html,
    render_search_html,
    render_simple_home_html,
    render_world_rules_html,
)
from review_web.actions import (
    trigger_generate_characters,
    trigger_append_decision,
    trigger_curate_character_entry,
    trigger_curate_glossary_entry,
    trigger_export_docx,
    trigger_generate_world_rules,
    trigger_curate_world_rule_entry,
    trigger_consistency_report,
    trigger_copyedit,
    trigger_deliverable_readiness_report,
    trigger_review_approval,
    trigger_rollback_last_approval,
    trigger_style,
    trigger_style_approval,
    trigger_translation_es,
)


class ReviewWebDashboardTest(unittest.TestCase):
    def test_build_dashboard_state_reads_persisted_project_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "manuscript" / "chapters"
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reports_dir = temp_path / "reports"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            deliverables_dir = temp_path / "deliverables"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            jobs_dir = temp_path / "reports" / "jobs"

            chapters_dir.mkdir(parents=True, exist_ok=True)
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
            (deliverables_dir / "ptbr").mkdir(parents=True, exist_ok=True)
            decisions_path.parent.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "order": 1,
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
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "text": "Primeiro chunk pendente.",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0002",
                                "text": "Segundo chunk pendente.",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
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
            (reports_dir / "deliverable-readiness.json").write_text(
                json.dumps(
                    {
                        "pt-BR": {
                            "eligible": False,
                            "blocker_count": 1,
                            "blockers": [{"chunk_id": "chapter-0001-conexao-dimensional-chunk-0001", "reason": "style_pending"}],
                            "chapters": [{"chapter_id": "chapter-0001-conexao-dimensional", "blocker_count": 1}],
                        },
                        "es": {
                            "eligible": False,
                            "blocker_count": 2,
                            "blockers": [{"chunk_id": "chapter-0001-conexao-dimensional-chunk-0001", "reason": "ptbr_not_ready"}],
                            "chapters": [{"chapter_id": "chapter-0001-conexao-dimensional", "blocker_count": 2}],
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
            decisions_path.write_text(
                "# Editorial Decisions\n\n## Preservar tratamento solene\n"
                "- Timestamp: 2026-03-10T10:00:00\n"
                "- Scope: chapter-0001-conexao-dimensional\n"
                "- Rationale: O narrador mantém registro elevado.\n",
                encoding="utf-8",
            )
            (jobs_dir / "2026-03-10T10-00-00-copyedit-succeeded.json").write_text(
                json.dumps(
                    {
                        "job_type": "copyedit",
                        "status": "succeeded",
                        "target_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "details": {"suggestion_count": 2},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (deliverables_dir / "ptbr" / "exilados-da-terra.ptbr.docx").write_text(
                "fake-docx",
                encoding="utf-8",
            )

            state = build_dashboard_state(
                chapters_dir=chapters_dir,
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reports_dir=reports_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                deliverables_dir=deliverables_dir,
                decisions_path=decisions_path,
                jobs_dir=jobs_dir,
            )

            self.assertEqual(state["summary"]["pending_chunk_count"], 2)
            self.assertEqual(state["summary"]["section_count"], 1)
            self.assertEqual(state["summary"]["copyedit_review_count"], 1)
            self.assertEqual(state["summary"]["translation_review_count"], 1)
            self.assertEqual(state["summary"]["deliverable_count"], 1)
            self.assertEqual(state["summary"]["decision_count"], 1)
            self.assertEqual(state["summary"]["job_count"], 1)
            self.assertEqual(state["summary"]["completed_chapter_count"], 0)
            self.assertEqual(state["summary"]["actionable_chapter_count"], 1)
            self.assertEqual(state["chapters"][0]["id"], "chapter-0001-conexao-dimensional")
            self.assertEqual(state["chapters"][0]["chunk_count"], 2)
            self.assertEqual(state["chapters"][0]["chapter_status"], "pending_copyedit")
            self.assertEqual(state["chapters"][0]["completion_percent"], 0)
            self.assertEqual(state["consistency_report"]["finding_count"], 12)
            self.assertEqual(state["deliverable_readiness_report"]["es"]["blocker_count"], 2)
            self.assertEqual(state["recent_chunks"][0]["id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["recent_decisions"][0]["title"], "Preservar tratamento solene")
            self.assertEqual(state["recent_jobs"][0]["job_type"], "copyedit")

    def test_compute_export_readiness_blocks_spanish_when_translations_are_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_es_dir = temp_path / "reviews" / "es"
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "order": 1,
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
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {"id": "p-1", "text": "A"},
                            {"id": "p-2", "text": "B"},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {"id": "p-1", "text": "A", "source_text": "A", "review_status": "approved"},
                            {"id": "p-2", "text": "B", "source_text": "B", "review_status": "approved"},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_es_dir / "chunk.translation-es.json").write_text(
                json.dumps(
                    {
                        "translations": [
                            {"paragraph_id": "p-1", "translated_text": "A-es"},
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            readiness = compute_export_readiness(
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertTrue(readiness["pt-BR"]["eligible"])
            self.assertFalse(readiness["es"]["eligible"])
            self.assertIn("1 parágrafo(s)", readiness["es"]["reason"])

    def test_build_dashboard_state_includes_chunk_only_chapters_when_consolidated_index_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "manuscript" / "chapters"
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reports_dir = temp_path / "reports"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            deliverables_dir = temp_path / "deliverables"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            jobs_dir = temp_path / "reports" / "jobs"

            chapters_dir.mkdir(parents=True, exist_ok=True)
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
            deliverables_dir.mkdir(parents=True, exist_ok=True)
            decisions_path.parent.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 2,
                        "chapter_count": 2,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "order": 1,
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                            },
                            {
                                "id": "chapter-0002-supremo-poder-anonimo",
                                "type": "chapter",
                                "order": 2,
                                "title": "Capítulo 2: Supremo Poder Anônimo.",
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
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0002-supremo-poder-anonimo.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0002-supremo-poder-anonimo",
                        "title": "Capítulo 2: Supremo Poder Anônimo.",
                        "paragraphs": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
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

            state = build_dashboard_state(
                chapters_dir=chapters_dir,
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reports_dir=reports_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                deliverables_dir=deliverables_dir,
                decisions_path=decisions_path,
                jobs_dir=jobs_dir,
            )

            chapter_ids = [chapter["id"] for chapter in state["chapters"]]
            self.assertEqual(
                chapter_ids,
                [
                    "chapter-0001-conexao-dimensional",
                    "chapter-0002-supremo-poder-anonimo",
                ],
            )
            self.assertEqual(state["chapters"][1]["title"], "Capítulo 2: Supremo Poder Anônimo.")

    def test_build_dashboard_state_reports_missing_declared_chapter_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "manuscript" / "chapters"
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reports_dir = temp_path / "reports"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            deliverables_dir = temp_path / "deliverables"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            jobs_dir = temp_path / "reports" / "jobs"

            chapters_dir.mkdir(parents=True, exist_ok=True)
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
            deliverables_dir.mkdir(parents=True, exist_ok=True)
            decisions_path.parent.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "index.json").write_text(
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
                                "order": 1,
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "declared_chapter_number": 1,
                                "file": "chapter-0001-conexao-dimensional.json",
                            },
                            {
                                "id": "chapter-0002-guerra-dimensional",
                                "type": "chapter",
                                "order": 2,
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
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [{"id": "p-1", "text": "A"}],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0002-guerra-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0002-guerra-dimensional",
                        "title": "Capítulo 4: Guerra Dimensional.",
                        "paragraphs": [{"id": "p-2", "text": "B"}],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
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
            (consolidated_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 2,
                        "chapter_count": 2,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "declared_chapter_number": 1,
                                "review_status": "mixed",
                                "file": "chapter-0001-conexao-dimensional.json",
                            },
                            {
                                "id": "chapter-0002-guerra-dimensional",
                                "title": "Capítulo 4: Guerra Dimensional.",
                                "declared_chapter_number": 4,
                                "review_status": "pending_review",
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

            state = build_dashboard_state(
                chapters_dir=chapters_dir,
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reports_dir=reports_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                deliverables_dir=deliverables_dir,
                decisions_path=decisions_path,
                jobs_dir=jobs_dir,
            )

            self.assertEqual(
                [chapter["title"] for chapter in state["chapters"]],
                [
                    "Capítulo 1: Conexão Dimensional.",
                    "Capítulo 2 — ausente no manuscrito segmentado",
                    "Capítulo 3 — ausente no manuscrito segmentado",
                    "Capítulo 4: Guerra Dimensional.",
                ],
            )
            self.assertTrue(state["chapters"][1]["missing"])
            self.assertEqual(state["chapters"][3]["declared_chapter_number"], 4)

    def test_render_dashboard_html_includes_web_operational_sections(self) -> None:
        html = render_dashboard_html(
            {
                "summary": {
                    "pending_chunk_count": 2,
                    "section_count": 1,
                    "copyedit_review_count": 1,
                    "translation_review_count": 1,
                    "deliverable_count": 1,
                    "job_count": 1,
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
                "recent_decisions": [
                    {
                        "title": "Preservar tratamento solene",
                        "scope": "chapter-0001-conexao-dimensional",
                        "rationale": "O narrador mantém registro elevado.",
                        "timestamp": "2026-03-10T10:00:00",
                    }
                ],
                "recent_jobs": [
                    {
                        "job_type": "copyedit",
                        "status": "succeeded",
                        "target_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "details": {"suggestion_count": 2},
                    }
                ],
                "export_readiness": {
                    "pt-BR": {"eligible": True, "reason": "O export em pt-BR está disponível."},
                    "es": {"eligible": False, "reason": "Faltam traduções para 3 parágrafo(s)."},
                },
                "deliverable_readiness_report": {
                    "pt-BR": {"eligible": False, "blocker_count": 1},
                    "es": {"eligible": False, "blocker_count": 1},
                },
            }
        )

        self.assertIn("Painel de Revisão Editorial", html)
        self.assertIn("Chunks Pendentes de Revisão", html)
        self.assertIn("Relatório de Consistência", html)
        self.assertIn("Capítulo 1: Conexão Dimensional.", html)
        self.assertIn("exilados-da-terra.ptbr.docx", html)
        self.assertIn("/consistency/alias_usage", html)
        self.assertIn("/consistency/run", html)
        self.assertIn("/exports/pt-BR/run", html)
        self.assertIn("/decisions", html)
        self.assertIn("/glossary", html)
        self.assertIn("Preservar tratamento solene", html)
        self.assertIn("copyedit", html)
        self.assertIn("Gerar Export pt-BR", html)
        self.assertIn("Export espanhol indisponível", html)
        self.assertIn("/approvals/rollback-last", html)
        self.assertIn("Capítulos Concluídos", html)
        self.assertIn("Capítulos Acionáveis", html)
        self.assertIn("Prontidão Bilíngue", html)
        self.assertIn("1 bloqueio(s)", html)
        self.assertIn("Revisão Avançada", html)
        self.assertIn("href=\"/\"", html)
        self.assertIn("href=\"/review/es\"", html)

    def test_build_simple_home_state_uses_next_actionable_chunk_with_orientation_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 3,
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
                                "id": "chapter-0002-supremo-poder-anonimo-chunk-0001",
                                "section_id": "chapter-0002-supremo-poder-anonimo",
                                "section_title": "Capítulo 2: Supremo Poder Anônimo.",
                                "chunk_order": 1,
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
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
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
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0002.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0002",
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0002"],
                        "base_text": "Outro trecho.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0002-supremo-poder-anonimo-chunk-0001.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0002-supremo-poder-anonimo-chunk-0001",
                        "section_id": "chapter-0002-supremo-poder-anonimo",
                        "section_title": "Capítulo 2: Supremo Poder Anônimo.",
                        "paragraph_ids": ["chapter-0002-supremo-poder-anonimo-p-0001"],
                        "base_text": "Trecho do segundo capítulo.",
                        "previous_context": [],
                        "next_context": [],
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
                                "confidence": 0.91,
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_es_dir / "chapter-0001-conexao-dimensional-chunk-0001.translation-es.preview.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "pass": "translation-es-preview",
                        "preview": True,
                        "translations": [
                            {
                                "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                                "translated_text": "Trecho principal revisado em espanhol.",
                                "rationale": "Mantém o sentido do revisado em pt-BR.",
                                "confidence": 0.87,
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            state = build_simple_home_state(
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertTrue(state["has_actionable_chunk"])
            self.assertEqual(state["chunk"]["id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["orientation"]["current_chapter_title"], "Capítulo 1: Conexão Dimensional.")
            self.assertEqual(state["orientation"]["remaining_chapter_count"], 1)
            self.assertEqual(state["orientation"]["current_chunk_position"], 1)
            self.assertEqual(state["orientation"]["chapter_chunk_count"], 2)
            self.assertEqual(state["orientation"]["remaining_actionable_chunk_count"], 2)
            self.assertEqual(state["original_text"], "Trecho principal.")
            self.assertEqual(state["revised_text"], "Trecho principal revisado.")
            self.assertIn("diff-added", state["revised_diff_html"])
            self.assertEqual(state["original_diff_html"], "Trecho principal.")
            self.assertTrue(state["review_available"])
            self.assertTrue(state["spanish_available"])
            self.assertEqual(state["spanish_text"], "Trecho principal revisado em espanhol.")
            self.assertEqual(len(state["changes"]), 1)
            self.assertEqual(state["changes"][0]["change_type"], "pontuação")
            self.assertEqual(state["changes"][0]["reason"], "Ajuste de clareza.")
            self.assertEqual(state["changes"][0]["confidence"], "0.91")
            self.assertEqual(state["changes"][0]["original_text"], "Trecho principal.")
            self.assertEqual(state["changes"][0]["suggested_text"], "Trecho principal revisado.")
            self.assertIn("diff-added", state["changes"][0]["suggested_html"])
            self.assertEqual(state["changes"][0]["original_fragment"], "Trecho principal.")
            self.assertEqual(state["changes"][0]["suggested_fragment"], "revisado")

    def test_build_simple_home_state_marks_review_as_missing_when_chunk_has_no_copyedit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
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
                                "chunk_order": 1,
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
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
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

            state = build_simple_home_state(
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertTrue(state["has_actionable_chunk"])
            self.assertFalse(state["review_available"])
            self.assertFalse(state["spanish_available"])
            self.assertEqual(state["spanish_text"], "")
            self.assertEqual(state["revised_text"], "Trecho principal.")
            self.assertEqual(state["changes"], [])

    def test_build_simple_home_state_exposes_rejection_reason_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
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
                                "chunk_order": 1,
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
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
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
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.rejection.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "status": "rejected",
                        "reason": "Mudou demais a voz do autor.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            state = build_simple_home_state(
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertTrue(state["has_actionable_chunk"])
            self.assertFalse(state["review_available"])
            self.assertEqual(state["rejection_reason"], "Mudou demais a voz do autor.")

    def test_build_simple_home_state_keeps_review_available_when_copyedit_has_no_suggestions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
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
                                "chunk_order": 1,
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
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
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
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "suggestions": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            state = build_simple_home_state(
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertTrue(state["has_actionable_chunk"])
            self.assertTrue(state["review_available"])
            self.assertEqual(state["revised_text"], "Trecho principal.")
            self.assertEqual(state["changes"], [])


    def test_render_simple_home_html_reserves_home_for_simple_operator_navigation(self) -> None:
        html = render_simple_home_html(
            {
                "has_actionable_chunk": True,
                "chunk": {
                    "id": "chapter-0001-conexao-dimensional-chunk-0001",
                },
                "orientation": {
                    "current_chapter_title": "Capítulo 1: Conexão Dimensional.",
                    "remaining_chapter_count": 2,
                    "current_chunk_position": 1,
                    "chapter_chunk_count": 5,
                    "remaining_actionable_chunk_count": 7,
                    "queue_status": "awaiting_approval",
                },
                "original_text": "Trecho principal.",
                "revised_text": "Trecho principal revisado.",
                "original_diff_html": "Trecho principal.",
                "revised_diff_html": "Trecho principal revisado.",
                "review_available": True,
                "changes": [
                    {
                        "index": 0,
                        "change_type": "pontuação",
                        "reason": "Ajuste de clareza.",
                        "confidence": "0.91",
                        "original_text": "Trecho principal.",
                        "suggested_text": "Trecho principal revisado.",
                        "original_html": "Trecho principal.",
                        "suggested_html": "Trecho principal revisado.",
                        "original_fragment": "Trecho principal.",
                        "suggested_fragment": "revisado",
                    }
                ],
            }
        )

        self.assertIn("Revisar PT-BR", html)
        self.assertIn("Revisar Espanhol", html)
        self.assertIn("Revisão Avançada", html)
        self.assertIn("href=\"/advanced\"", html)
        self.assertIn("href=\"/review/es\"", html)
        self.assertIn("Capítulo atual", html)
        self.assertIn("Original", html)
        self.assertIn("Revisado", html)
        self.assertIn("Alterações da revisão", html)
        self.assertIn("Aceitar", html)
        self.assertIn("Recusar", html)
        self.assertIn("Trecho principal revisado.", html)
        self.assertIn("Ajuste de clareza.", html)
        self.assertIn("0.91", html)
        self.assertIn("pontuação", html)

    def test_render_simple_home_html_shows_review_request_action_before_copyedit_exists(self) -> None:
        html = render_simple_home_html(
            {
                "has_actionable_chunk": True,
                "chunk": {
                    "id": "chapter-0001-conexao-dimensional-chunk-0001",
                },
                "orientation": {
                    "current_chapter_title": "Capítulo 1: Conexão Dimensional.",
                    "remaining_chapter_count": 2,
                    "current_chunk_position": 1,
                    "chapter_chunk_count": 5,
                    "remaining_actionable_chunk_count": 7,
                    "queue_status": "pending_copyedit",
                },
                "original_text": "Trecho principal.",
                "revised_text": "Trecho principal.",
                "original_diff_html": "Trecho principal.",
                "revised_diff_html": "Trecho principal.",
                "review_available": False,
                "changes": [],
            }
        )

        self.assertIn("Revisar este trecho", html)
        self.assertIn("Este trecho ainda não foi revisado.", html)
        self.assertIn("Nenhuma alteração disponível para este trecho.", html)
        self.assertIn("Revisando este trecho...", html)
        self.assertIn("Isso pode levar alguns instantes.", html)
        self.assertIn("js-loading-form", html)

    def test_render_simple_home_html_allows_accept_when_review_has_no_suggestions(self) -> None:
        html = render_simple_home_html(
            {
                "has_actionable_chunk": True,
                "chunk": {
                    "id": "chapter-0001-conexao-dimensional-chunk-0001",
                },
                "orientation": {
                    "current_chapter_title": "Capítulo 1: Conexão Dimensional.",
                    "remaining_chapter_count": 2,
                    "current_chunk_position": 1,
                    "chapter_chunk_count": 5,
                    "remaining_actionable_chunk_count": 7,
                    "queue_status": "awaiting_approval",
                },
                "original_text": "Trecho principal.",
                "revised_text": "Trecho principal.",
                "original_diff_html": "Trecho principal.",
                "revised_diff_html": "Trecho principal.",
                "review_available": True,
                "changes": [],
            }
        )

        self.assertIn("Aceitar", html)
        self.assertNotIn("Revisar este trecho", html)
        self.assertIn("Nenhuma alteração proposta para este trecho.", html)
        self.assertIn("A revisão não propôs alterações; você pode aceitar para avançar.", html)

    def test_build_decisions_state_reads_persisted_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            decisions_path.parent.mkdir(parents=True, exist_ok=True)
            decisions_path.write_text(
                "# Editorial Decisions\n\n"
                "## Preservar travessão dramático\n"
                "- Timestamp: 2026-03-10T10:00:00\n"
                "- Scope: chapter-0001-conexao-dimensional-chunk-0002\n"
                "- Rationale: O travessão integra a respiração narrativa.\n\n"
                "## Manter repetições deliberadas\n"
                "- Timestamp: 2026-03-10T10:05:00\n"
                "- Scope: chapter-0002-supremo-poder-anonimo\n"
                "- Rationale: A repetição é recurso filosófico.\n",
                encoding="utf-8",
            )

            state = build_decisions_state(decisions_path=decisions_path)

            self.assertEqual(state["decision_count"], 2)
            self.assertEqual(state["decisions"][0]["title"], "Manter repetições deliberadas")
            self.assertEqual(
                state["decisions"][1]["scope"],
                "chapter-0001-conexao-dimensional-chunk-0002",
            )

            html = render_decisions_html(state)
            self.assertIn("Decisões Editoriais", html)
            self.assertIn("Manter repetições deliberadas", html)
            self.assertIn("/chunks/chapter-0001-conexao-dimensional-chunk-0002", html)

    def test_build_glossary_state_reads_curatable_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            glossary_path.parent.mkdir(parents=True, exist_ok=True)
            glossary_path.write_text(
                "# Glossary\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: `Soberania Energia Universal`\n"
                "- Evidence: `p-1`\n",
                encoding="utf-8",
            )

            state = build_glossary_state(glossary_path=glossary_path)

            self.assertEqual(state["entry_count"], 1)
            self.assertEqual(state["sections"][0]["entries"][0]["title"], "SEU")

            html = render_glossary_html(state)
            self.assertIn("Curadoria do Glossário", html)
            self.assertIn("Soberania Energia Universal", html)
            self.assertIn("Salvar Ajustes do Glossário", html)

    def test_build_characters_state_reads_registry_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            characters_path = temp_path / "editorial" / "CHARACTERS.md"
            characters_path.parent.mkdir(parents=True, exist_ok=True)
            characters_path.write_text(
                "# Characters Registry\n\n"
                "## Scope\n"
                "- Character entries: `2`\n\n"
                "### Ana Carolina\n"
                "- Preferred form: `Ana Carolina`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-p-0003`\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: `Joseph`, `Sr. Harrison`\n"
                "- Evidence: `chapter-0001-p-0001`, `chapter-0001-p-0002`\n",
                encoding="utf-8",
            )

            state = build_characters_state(characters_path=characters_path)

            self.assertEqual(state["character_count"], 2)
            self.assertEqual(state["characters"][0]["title"], "Ana Carolina")
            self.assertEqual(state["characters"][1]["aliases"], ["Joseph", "Sr. Harrison"])

            html = render_characters_html(state)
            self.assertIn("Registro de Personagens", html)
            self.assertIn("Joseph Harrison", html)
            self.assertIn("Sr. Harrison", html)
            self.assertIn("Salvar Ajustes do Personagem", html)

    def test_trigger_append_decision_persists_repository_backed_editorial_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            decisions_path = temp_path / "editorial" / "DECISIONS.md"

            summary = trigger_append_decision(
                decisions_path=decisions_path,
                title="Preservar enumeração litúrgica",
                rationale="A enumeração reforça o tom solene do capítulo.",
                scope="chapter-0001-conexao-dimensional-chunk-0003",
            )

            self.assertEqual(summary["decision_count"], 1)
            self.assertEqual(summary["last_title"], "Preservar enumeração litúrgica")
            self.assertIn("enumeração", decisions_path.read_text(encoding="utf-8"))

    def test_trigger_generate_characters_creates_registry_for_web_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            characters_path = temp_path / "editorial" / "CHARACTERS.md"
            glossary_path.parent.mkdir(parents=True, exist_ok=True)
            glossary_path.write_text(
                "# Glossary\n\n"
                "## Proper Names\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: `Joseph`\n"
                "- Evidence: `chapter-0001-p-0001`\n",
                encoding="utf-8",
            )

            summary = trigger_generate_characters(
                glossary_path=glossary_path,
                characters_path=characters_path,
            )

            self.assertEqual(summary["character_count"], 1)
            self.assertTrue(characters_path.exists())

    def test_build_world_rules_state_reads_registry_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            world_rules_path = temp_path / "editorial" / "WORLD_RULES.md"
            world_rules_path.parent.mkdir(parents=True, exist_ok=True)
            world_rules_path.write_text(
                "# World Rules Registry\n\n"
                "## Scope\n"
                "- Organizations and acronyms: `1`\n"
                "- Concepts and formulas: `1`\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: `Soberania Energia Universal`\n"
                "- Evidence: `chapter-0001-p-0001`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-p-0002`\n",
                encoding="utf-8",
            )

            state = build_world_rules_state(world_rules_path=world_rules_path)

            self.assertEqual(state["organization_count"], 1)
            self.assertEqual(state["concept_count"], 1)
            self.assertEqual(state["organizations"][0]["expanded_form"], "Soberana Energia Universal")

            html = render_world_rules_html(state)
            self.assertIn("Registro de Regras do Mundo", html)
            self.assertIn("Sistema Terra", html)
            self.assertIn("Soberana Energia Universal", html)
            self.assertIn("Salvar Ajustes da Regra", html)

    def test_trigger_generate_world_rules_creates_registry_for_web_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            world_rules_path = temp_path / "editorial" / "WORLD_RULES.md"
            glossary_path.parent.mkdir(parents=True, exist_ok=True)
            glossary_path.write_text(
                "# Glossary\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-p-0001`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-p-0002`\n",
                encoding="utf-8",
            )

            summary = trigger_generate_world_rules(
                glossary_path=glossary_path,
                world_rules_path=world_rules_path,
            )

            self.assertEqual(summary["organization_count"], 1)
            self.assertEqual(summary["concept_count"], 1)
            self.assertTrue(world_rules_path.exists())

    def test_build_search_state_groups_matches_and_links_back_to_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            glossary_path.parent.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 1,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
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
                        "paragraph_ids": ["p-1"],
                        "base_text": "O Sistema Terra exige prudência.",
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
            glossary_path.write_text(
                "# Glossary\n\n## Concepts and Formulas\n\n### Sistema Terra\n- Preferred form: `Sistema Terra`\n",
                encoding="utf-8",
            )
            decisions_path.write_text(
                "# Editorial Decisions\n\n## Preservar Sistema Terra\n- Timestamp: 2026-03-10T10:00:00\n- Scope: chapter-0001-conexao-dimensional-chunk-0001\n- Rationale: Base cosmológica.\n",
                encoding="utf-8",
            )

            state = build_search_state(
                query="Sistema Terra",
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
            )

            self.assertEqual(state["result_count"], 3)
            self.assertEqual(state["chunk_matches"][0]["link"], "/chunks/chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["decision_matches"][0]["link"], "/chunks/chapter-0001-conexao-dimensional-chunk-0001")

            html = render_search_html(state)
            self.assertIn("Resultados da Busca", html)
            self.assertIn("/chunks/chapter-0001-conexao-dimensional-chunk-0001", html)
            self.assertIn("#glossary-results", html)

    def test_build_queue_state_exposes_resume_link_and_progress_counts(self) -> None:
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
                        "chunk_count": 2,
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
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json").write_text(
                "{}",
                encoding="utf-8",
            )

            state = build_queue_state(
                chunks_dir=chunks_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertEqual(state["summary"]["awaiting_approval_count"], 1)
            self.assertEqual(state["next_recommended"]["link"], "/chunks/chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["chapter_rollups"][0]["chapter_status"], "awaiting_copyedit_approval")
            self.assertEqual(state["chapter_rollups"][0]["completion_percent"], 0)

            html = render_queue_html(state)
            self.assertIn("Fila de Revisão", html)
            self.assertIn("/chunks/chapter-0001-conexao-dimensional-chunk-0001", html)
            self.assertIn("Retomar Próximo Chunk", html)
            self.assertIn("Resumo por Capítulo", html)
            self.assertIn("awaiting_copyedit_approval", html)

    def test_build_chapter_detail_state_groups_chunks_for_selected_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)

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
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertEqual(state["chapter"]["id"], "chapter-0001-conexao-dimensional")
            self.assertEqual(len(state["chunks"]), 2)
            self.assertEqual(state["chunks"][0]["id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["progress"]["chunk_count"], 2)
            self.assertEqual(state["progress"]["pending_copyedit_count"], 2)
            self.assertEqual(state["progress"]["completion_percent"], 0)

            html = render_chapter_detail_html(state)
            self.assertIn("Navegação por Capítulo", html)
            self.assertIn("chapter-0001-conexao-dimensional-chunk-0001", html)
            self.assertIn("Resumo do Capítulo", html)
            self.assertIn("Pendentes de Copyedit", html)

    def test_build_chapter_detail_state_falls_back_to_chunk_navigation_when_consolidated_entry_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 1,
                        "chunks": [
                            {
                                "id": "chapter-0002-supremo-poder-anonimo-chunk-0001",
                                "section_id": "chapter-0002-supremo-poder-anonimo",
                                "section_title": "Capítulo 2: Supremo Poder Anônimo.",
                                "review_status": "pending_review",
                                "file": "chapter-0002-supremo-poder-anonimo-chunk-0001.json",
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
                        "section_count": 0,
                        "chapter_count": 0,
                        "sections": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            state = build_chapter_detail_state(
                chapter_id="chapter-0002-supremo-poder-anonimo",
                chunks_dir=chunks_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertEqual(state["chapter"]["title"], "Capítulo 2: Supremo Poder Anônimo.")
            self.assertEqual(state["chapter"]["review_status"], "unknown")
            self.assertEqual(state["chunks"][0]["id"], "chapter-0002-supremo-poder-anonimo-chunk-0001")

    def test_build_consistency_detail_state_groups_findings_and_links_back_to_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            reports_dir = temp_path / "reports"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)

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
                                "id": "chapter-0002-supremo-poder-anonimo-chunk-0001",
                                "section_id": "chapter-0002-supremo-poder-anonimo",
                                "section_title": "Capítulo 2: Supremo Poder Anônimo.",
                                "review_status": "pending_review",
                                "file": "chapter-0002-supremo-poder-anonimo-chunk-0001.json",
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
            (chunks_dir / "chapter-0002-supremo-poder-anonimo-chunk-0001.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0002-supremo-poder-anonimo-chunk-0001",
                        "section_id": "chapter-0002-supremo-poder-anonimo",
                        "section_title": "Capítulo 2: Supremo Poder Anônimo.",
                        "paragraph_ids": [
                            "chapter-0002-supremo-poder-anonimo-p-0001",
                        ],
                        "base_text": "Trecho paralelo.",
                        "previous_context": [],
                        "next_context": [],
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
                        "finding_count": 3,
                        "scope": {"section_count": 1, "paragraph_count": 1},
                        "findings_by_type": {
                            "alias_usage": [
                                {
                                    "section_id": "chapter-0001-conexao-dimensional",
                                    "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                                    "entry_title": "SEU",
                                    "preferred_form": "SEU",
                                    "observed_variant": "Soberania Energia Universal",
                                }
                            ],
                            "similar_proper_names": [
                                {
                                    "left": "Tom Harrison",
                                    "right": "Tom Harris",
                                    "similarity": 0.88,
                                }
                            ],
                            "cross_chapter_entity_variants": [
                                {
                                    "entry_title": "Joseph Harrison",
                                    "preferred_form": "Joseph Harrison",
                                    "registry_sources": ["characters"],
                                    "chapter_ids": [
                                        "chapter-0001-conexao-dimensional",
                                        "chapter-0002-supremo-poder-anonimo",
                                    ],
                                    "paragraph_ids": [
                                        "chapter-0001-conexao-dimensional-p-0001",
                                        "chapter-0002-supremo-poder-anonimo-p-0001",
                                    ],
                                    "observed_forms": ["Joseph", "Joseph Harrison"],
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            state = build_consistency_detail_state(
                finding_type="alias_usage",
                reports_dir=reports_dir,
                chunks_dir=chunks_dir,
            )

            self.assertEqual(state["finding_type"], "alias_usage")
            self.assertEqual(state["findings"][0]["resolved_chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")

            html = render_consistency_detail_html(state)
            self.assertIn("Achados de Consistência", html)
            self.assertIn("chapter-0001-conexao-dimensional-chunk-0001", html)
            self.assertIn("Soberania Energia Universal", html)
            self.assertIn("/chunks/chapter-0001-conexao-dimensional-chunk-0001", html)

            grouped_state = build_consistency_detail_state(
                finding_type="cross_chapter_entity_variants",
                reports_dir=reports_dir,
                chunks_dir=chunks_dir,
            )

            self.assertEqual(
                grouped_state["findings"][0]["resolved_chunk_ids"],
                [
                    "chapter-0001-conexao-dimensional-chunk-0001",
                    "chapter-0002-supremo-poder-anonimo-chunk-0001",
                ],
            )

            grouped_html = render_consistency_detail_html(grouped_state)
            self.assertIn("/chunks/chapter-0002-supremo-poder-anonimo-chunk-0001", grouped_html)
            self.assertIn("/chapters/chapter-0002-supremo-poder-anonimo", grouped_html)

    def test_build_chunk_detail_state_reads_selected_chunk_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
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
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.style.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "suggestions": [
                            {
                                "original": "Trecho principal revisado.",
                                "suggested": "Trecho principal revisado, com melhor cadência.",
                                "change_type": "style",
                                "reason": "Refino rítmico.",
                                "confidence": 0.77,
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
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.style.approval.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "status": "approved",
                        "pass": "style",
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
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_text": "Trecho principal.",
                                "text": "Trecho principal revisado.",
                                "review_status": "approved",
                                "applied_reviews": [
                                    {
                                        "approval_file": "chapter-0001-conexao-dimensional-chunk-0001.approval.json",
                                        "review_file": "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json",
                                        "suggestion_index": 0,
                                        "change_type": "pontuação",
                                        "reason": "Ajuste de clareza.",
                                        "confidence": 0.88,
                                    }
                                ],
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0002",
                                "source_text": "Parágrafo sem alteração.",
                                "text": "Parágrafo sem alteração.",
                                "review_status": "pending_review",
                                "applied_reviews": [],
                            },
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
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
            )

            self.assertEqual(state["chunk"]["id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["chunk"]["base_text"], "Trecho principal.")
            self.assertEqual(state["chunk"]["previous_context"][0]["text"], "Contexto anterior.")
            self.assertEqual(state["copyedit_review"]["suggestions"][0]["suggested"], "Trecho principal revisado.")
            self.assertEqual(state["approval"]["applied_change_count"], 1)
            self.assertEqual(state["style_review"]["suggestions"][0]["change_type"], "style")
            self.assertEqual(state["style_approval"]["pass"], "style")
            self.assertEqual(state["translation_review"]["translations"][0]["translated_text"], "Fragmento principal.")
            self.assertEqual(state["consolidated_paragraphs"][0]["text"], "Trecho principal revisado.")
            self.assertEqual(state["consolidated_paragraphs"][0]["source_text"], "Trecho principal.")
            self.assertFalse(state["translation_eligibility"]["eligible"])
            self.assertIn("Já existe tradução", state["translation_eligibility"]["reason"])
            self.assertEqual(state["translation_comparison"][0]["paragraph_id"], "chapter-0001-conexao-dimensional-p-0001")
            self.assertEqual(state["translation_comparison"][0]["ptbr_text"], "Trecho principal revisado.")
            self.assertEqual(state["translation_comparison"][0]["translated_text"], "Fragmento principal.")
            self.assertEqual(
                state["consolidated_paragraphs"][0]["applied_reviews"][0]["approval_file"],
                "chapter-0001-conexao-dimensional-chunk-0001.approval.json",
            )

            html = render_chunk_detail_html(state)
            self.assertIn("Detalhe do Chunk", html)
            self.assertIn("Trecho principal.", html)
            self.assertIn("Contexto seguinte.", html)
            self.assertIn("Trecho principal", html)
            self.assertIn("revisado", html)
            self.assertIn("Fragmento principal.", html)
            self.assertIn("Executar Copyedit", html)
            self.assertIn("Executar Style", html)
            self.assertIn("Revisão de Sugestões", html)
            self.assertIn("Refino de Estilo", html)
            self.assertIn("Original", html)
            self.assertIn("Sugerido", html)
            self.assertIn("Confiança", html)
            self.assertIn("0.88", html)
            self.assertIn("diff-added", html)
            self.assertIn("diff-removed", html)
            self.assertIn("/chunks/chapter-0001-conexao-dimensional-chunk-0001/approve-copyedit", html)
            self.assertIn("/chunks/chapter-0001-conexao-dimensional-chunk-0001/approve-style", html)
            self.assertIn("name=\"approve_index\"", html)
            self.assertIn("value=\"0\"", html)
            self.assertIn("Aprovar Alterações Selecionadas", html)
            self.assertIn("Estado Consolidado dos Parágrafos", html)
            self.assertIn("Texto Atual", html)
            self.assertIn("Texto-Fonte", html)
            self.assertIn("Metadados da Revisão Aplicada", html)
            self.assertIn("chapter-0001-conexao-dimensional-chunk-0001.approval.json", html)
            self.assertIn("Tradução indisponível", html)
            self.assertIn("Comparação pt-BR e Espanhol", html)
            self.assertIn("Trecho principal revisado.", html)
            self.assertIn("Fragmento principal.", html)
            self.assertIn("Mantém o tom.", html)
            self.assertIn("0.74", html)

    def test_trigger_copyedit_persists_review_for_selected_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
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
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            summary = trigger_copyedit(
                chunk_id="chapter-0001-conexao-dimensional-chunk-0001",
                chunks_dir=chunks_dir,
                reviews_dir=reviews_ptbr_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
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

    def test_trigger_style_persists_review_for_stable_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
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
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
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
            section_payload = {
                "id": "chapter-0001-conexao-dimensional",
                "title": "Capítulo 1: Conexão Dimensional.",
                "paragraphs": [
                    {
                        "id": "chapter-0001-conexao-dimensional-p-0001",
                        "source_index": 1,
                        "source_text": "Texto-base antigo.",
                        "text": "Trecho principal revisado.",
                        "review_status": "approved",
                        "applied_reviews": [],
                    }
                ],
            }
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n- Preserve voice.\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n- Sistema Terra\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            summary = trigger_style(
                chunk_id="chapter-0001-conexao-dimensional-chunk-0001",
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_ptbr_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=lambda **_: {
                    "suggestions": [
                        {
                            "original": "Trecho principal revisado.",
                            "suggested": "Trecho principal revisado, com melhor cadência.",
                            "change_type": "style",
                            "reason": "Refino rítmico.",
                            "confidence": 0.79,
                        }
                    ]
                },
            )

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            persisted = json.loads(
                (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.style.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(persisted["suggestions"][0]["change_type"], "style")

    def test_trigger_review_approval_persists_partial_selection_and_updates_consolidated_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)

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
                        "paragraph_ids": [
                            "chapter-0001-conexao-dimensional-p-0001",
                            "chapter-0001-conexao-dimensional-p-0002",
                        ],
                        "base_text": "Primeiro parágrafo pendente.\n\nSegundo parágrafo pendente.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "order": 1,
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                                "review_status": "mixed",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "type": "chapter",
                        "order": 1,
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "review_status": "mixed",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_index": 1,
                                "text": "Primeiro parágrafo pendente.",
                                "review_status": "pending_review",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0002",
                                "source_index": 2,
                                "text": "Segundo parágrafo pendente.",
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
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "pass": "copyedit",
                        "language": "pt-BR",
                        "source": {
                            "section_id": "chapter-0001-conexao-dimensional",
                            "section_title": "Capítulo 1: Conexão Dimensional.",
                            "paragraph_ids": [
                                "chapter-0001-conexao-dimensional-p-0001",
                                "chapter-0001-conexao-dimensional-p-0002",
                            ],
                        },
                        "suggestions": [
                            {
                                "original": "Primeiro parágrafo pendente.",
                                "suggested": "Primeiro parágrafo revisado.",
                                "change_type": "grammar",
                                "reason": "Ajuste gramatical.",
                                "confidence": 0.9,
                            },
                            {
                                "original": "Segundo parágrafo pendente.",
                                "suggested": "Segundo parágrafo revisado.",
                                "change_type": "punctuation",
                                "reason": "Ajuste de pontuação.",
                                "confidence": 0.8,
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = trigger_review_approval(
                chunk_id="chapter-0001-conexao-dimensional-chunk-0001",
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_ptbr_dir,
                approved_suggestion_indexes=[1],
            )

            approval_payload = json.loads(
                (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.approval.json").read_text(
                    encoding="utf-8"
                )
            )
            consolidated_payload = json.loads(
                (consolidated_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(summary["approved_suggestion_count"], 1)
            self.assertEqual(approval_payload["approved_suggestion_indexes"], [1])
            self.assertEqual(approval_payload["applied_change_count"], 1)
            self.assertEqual(
                consolidated_payload["paragraphs"][0]["text"],
                "Primeiro parágrafo pendente.",
            )
            self.assertEqual(
                consolidated_payload["paragraphs"][1]["text"],
                "Segundo parágrafo revisado.",
            )

    def test_trigger_style_approval_persists_partial_selection_and_updates_consolidated_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)

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
                        "paragraph_ids": [
                            "chapter-0001-conexao-dimensional-p-0001",
                            "chapter-0001-conexao-dimensional-p-0002",
                        ],
                        "base_text": "Primeiro parágrafo consolidado.\n\nSegundo parágrafo consolidado.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            chapter_index = {
                "section_count": 1,
                "chapter_count": 1,
                "sections": [
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "type": "chapter",
                        "order": 1,
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "file": "chapter-0001-conexao-dimensional.json",
                        "review_status": "approved",
                    }
                ],
            }
            (chapters_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            section_payload = {
                "id": "chapter-0001-conexao-dimensional",
                "type": "chapter",
                "order": 1,
                "title": "Capítulo 1: Conexão Dimensional.",
                "review_status": "approved",
                "paragraphs": [
                    {
                        "id": "chapter-0001-conexao-dimensional-p-0001",
                        "source_index": 1,
                        "source_text": "Primeiro texto original.",
                        "text": "Primeiro parágrafo consolidado.",
                        "review_status": "approved",
                        "applied_reviews": [],
                    },
                    {
                        "id": "chapter-0001-conexao-dimensional-p-0002",
                        "source_index": 2,
                        "source_text": "Segundo texto original.",
                        "text": "Segundo parágrafo consolidado.",
                        "review_status": "approved",
                        "applied_reviews": [],
                    },
                ],
            }
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.style.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "pass": "style",
                        "language": "pt-BR",
                        "source": {
                            "section_id": "chapter-0001-conexao-dimensional",
                            "section_title": "Capítulo 1: Conexão Dimensional.",
                            "paragraph_ids": [
                                "chapter-0001-conexao-dimensional-p-0001",
                                "chapter-0001-conexao-dimensional-p-0002",
                            ],
                        },
                        "suggestions": [
                            {
                                "original": "Primeiro parágrafo consolidado.",
                                "suggested": "Primeiro parágrafo consolidado, com melhor cadência.",
                                "change_type": "style",
                                "reason": "Refino rítmico.",
                                "confidence": 0.84,
                            },
                            {
                                "original": "Segundo parágrafo consolidado.",
                                "suggested": "Segundo parágrafo consolidado, com melhor cadência.",
                                "change_type": "style",
                                "reason": "Refino rítmico.",
                                "confidence": 0.82,
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = trigger_style_approval(
                chunk_id="chapter-0001-conexao-dimensional-chunk-0001",
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_ptbr_dir,
                approved_suggestion_indexes=[0],
            )

            approval_payload = json.loads(
                (reviews_ptbr_dir / "chapter-0001-conexao-dimensional-chunk-0001.style.approval.json").read_text(
                    encoding="utf-8"
                )
            )
            consolidated_payload = json.loads(
                (consolidated_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(summary["approved_suggestion_count"], 1)
            self.assertEqual(approval_payload["pass"], "style")
            self.assertEqual(approval_payload["approved_suggestion_indexes"], [0])
            self.assertEqual(
                consolidated_payload["paragraphs"][0]["text"],
                "Primeiro parágrafo consolidado, com melhor cadência.",
            )
            self.assertEqual(
                consolidated_payload["paragraphs"][1]["text"],
                "Segundo parágrafo consolidado.",
            )

    def test_trigger_consistency_report_persists_report_for_web_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reports_dir = temp_path / "reports"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            characters_path = temp_path / "editorial" / "CHARACTERS.md"
            world_rules_path = temp_path / "editorial" / "WORLD_RULES.md"
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            glossary_path.parent.mkdir(parents=True, exist_ok=True)

            (consolidated_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "order": 1,
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                                "review_status": "mixed",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "type": "chapter",
                        "order": 1,
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "review_status": "mixed",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_index": 1,
                                "source_text": "Texto original.",
                                "text": "Soberania Energia Universal  guia a cena.",
                                "review_status": "approved",
                                "applied_reviews": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            glossary_path.write_text(
                "# Glossary\n\n## Organizations and Acronyms\n\n### SEU\n- Preferred form: `SEU`\n- Observed aliases or variants: `Soberania Energia Universal`\n",
                encoding="utf-8",
            )
            characters_path.write_text(
                "# Characters Registry\n\n## Scope\n- Character entries: `0`\n",
                encoding="utf-8",
            )
            world_rules_path.write_text(
                "# World Rules Registry\n\n## Scope\n- Organizations and acronyms: `0`\n- Concepts and formulas: `0`\n",
                encoding="utf-8",
            )

            summary = trigger_consistency_report(
                consolidated_dir=consolidated_dir,
                glossary_path=glossary_path,
                characters_path=characters_path,
                world_rules_path=world_rules_path,
                reports_dir=reports_dir,
            )

            self.assertEqual(summary["finding_count"], 2)
            self.assertTrue((reports_dir / "ptbr-consistency-report.json").exists())

    def test_trigger_deliverable_readiness_report_persists_report_for_web_workflow(self) -> None:
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
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
                        "source_start_index": 1,
                        "source_end_index": 1,
                        "base_text": "Trecho pendente.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            section_payload = {
                "id": "chapter-0001-conexao-dimensional",
                "title": "Capítulo 1: Conexão Dimensional.",
                "paragraphs": [
                    {
                        "id": "chapter-0001-conexao-dimensional-p-0001",
                        "source_index": 1,
                        "source_text": "Trecho original.",
                        "text": "Trecho pendente.",
                        "review_status": "pending_review",
                        "applied_reviews": [],
                    }
                ],
            }
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = trigger_deliverable_readiness_report(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                reports_dir=reports_dir,
            )

            self.assertFalse(summary["pt-BR"]["eligible"])
            self.assertTrue((reports_dir / "deliverable-readiness.json").exists())

    def test_trigger_translation_es_persists_output_for_stable_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_es_dir = temp_path / "reviews" / "es"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
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
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
                        "source_start_index": 1,
                        "source_end_index": 1,
                        "base_text": "Trecho principal revisado.",
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
                                "type": "chapter",
                                "order": 1,
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                                "review_status": "approved",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_index": 1,
                                "source_text": "Trecho principal.",
                                "text": "Trecho principal revisado.",
                                "review_status": "approved",
                                "applied_reviews": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n- Preserve voice.\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n- Sistema Terra\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            summary = trigger_translation_es(
                chunk_id="chapter-0001-conexao-dimensional-chunk-0001",
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_es_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=lambda **_: {
                    "translations": [
                        {
                            "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                            "translated_text": "Fragmento principal revisado.",
                            "rationale": "Mantém o tom.",
                            "confidence": 0.84,
                        }
                    ]
                },
            )

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertTrue(
                (reviews_es_dir / "chapter-0001-conexao-dimensional-chunk-0001.translation-es.json").exists()
            )

    def test_trigger_export_docx_persists_ptbr_deliverable_for_web_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_path = temp_path / "template.docx"
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            translations_dir = temp_path / "reviews" / "es"
            deliverables_dir = temp_path / "deliverables"
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            translations_dir.mkdir(parents=True, exist_ok=True)
            deliverables_dir.mkdir(parents=True, exist_ok=True)

            from tests.test_export_docx import build_template_docx

            build_template_docx(template_path)

            (chapters_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "order": 1,
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "heading_source_index": 2,
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
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "type": "chapter",
                        "order": 1,
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "heading_source_index": 2,
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_index": 3,
                                "text": "Texto original.",
                                "review_status": "pending_review",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "type": "chapter",
                        "order": 1,
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "heading_source_index": 2,
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_index": 3,
                                "source_text": "Texto original.",
                                "text": "Texto consolidado.",
                                "review_status": "approved",
                                "applied_reviews": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = trigger_export_docx(
                template_path=template_path,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                translations_dir=translations_dir,
                deliverables_dir=deliverables_dir,
                language="pt-BR",
            )

            self.assertEqual(summary["language"], "pt-BR")
            self.assertTrue((deliverables_dir / "ptbr" / "exilados-da-terra.ptbr.docx").exists())
            self.assertIn("snapshot_manifest_path", summary)
            self.assertTrue(Path(summary["snapshot_manifest_path"]).exists())

    def test_trigger_rollback_last_approval_restores_latest_approval_for_web_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_dir = temp_path / "reviews" / "ptbr"
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)

            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_index": 1,
                                "text": "Texto original.",
                                "review_status": "pending_review",
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
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                                "review_status": "approved",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "review_status": "approved",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "source_index": 1,
                                "source_text": "Texto original.",
                                "text": "Texto revisado.",
                                "review_status": "approved",
                                "applied_reviews": [
                                    {
                                        "approval_file": "chapter-0001-conexao-dimensional-chunk-0001.approval.json",
                                        "review_file": "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json",
                                        "pass": "copyedit",
                                        "suggestion_index": 0,
                                        "change_type": "grammar",
                                        "reason": "Ajuste.",
                                        "confidence": 0.9,
                                        "applied_at": "2026-03-10T22:00:00",
                                        "original": "Texto original.",
                                        "suggested": "Texto revisado.",
                                    }
                                ],
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.approval.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "review_file": "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json",
                        "approval_file": "chapter-0001-conexao-dimensional-chunk-0001.approval.json",
                        "pass": "copyedit",
                        "language": "pt-BR",
                        "status": "approved",
                        "approved_suggestion_indexes": [0],
                        "applied_change_count": 1,
                        "skipped_change_count": 0,
                        "applied_changes": [
                            {
                                "suggestion_index": 0,
                                "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                                "original": "Texto original.",
                                "suggested": "Texto revisado.",
                                "change_type": "grammar",
                                "reason": "Ajuste.",
                                "confidence": 0.9,
                            }
                        ],
                        "skipped_suggestions": [],
                        "consolidated_section_file": "chapter-0001-conexao-dimensional.json",
                        "approved_at": "2026-03-10T22:00:00",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = trigger_rollback_last_approval(
                reviews_dir=reviews_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
            )

            consolidated_section = json.loads(
                (consolidated_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["reverted_change_count"], 1)
            self.assertTrue(Path(summary["rollback_path"]).exists())
            self.assertEqual(consolidated_section["paragraphs"][0]["text"], "Texto original.")

    def test_trigger_curate_glossary_entry_persists_repo_backed_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            glossary_path.parent.mkdir(parents=True, exist_ok=True)
            glossary_path.write_text(
                "# Glossary\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: `Soberania Energia Universal`\n"
                "- Evidence: `p-1`\n",
                encoding="utf-8",
            )

            summary = trigger_curate_glossary_entry(
                glossary_path=glossary_path,
                entry_title="SEU",
                preferred_form="Soberana Energia Universal",
                aliases_text="SEU, Soberania Energia Universal",
            )

            updated_text = glossary_path.read_text(encoding="utf-8")
            self.assertEqual(summary["entry_title"], "SEU")
            self.assertIn("- Preferred form: `Soberana Energia Universal`", updated_text)
            self.assertIn("`SEU`, `Soberania Energia Universal`", updated_text)

    def test_trigger_curate_character_entry_persists_repo_backed_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            characters_path = temp_path / "editorial" / "CHARACTERS.md"
            characters_path.parent.mkdir(parents=True, exist_ok=True)
            characters_path.write_text(
                "# Characters Registry\n\n"
                "## Scope\n"
                "- Character entries: `1`\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: `Joseph`\n"
                "- Evidence: `p-2`\n",
                encoding="utf-8",
            )

            summary = trigger_curate_character_entry(
                characters_path=characters_path,
                entry_title="Joseph Harrison",
                preferred_form="Sr. Joseph Harrison",
                aliases_text="Joseph, Sr. Harrison",
            )

            updated_text = characters_path.read_text(encoding="utf-8")
            self.assertEqual(summary["entry_title"], "Joseph Harrison")
            self.assertIn("- Preferred form: `Sr. Joseph Harrison`", updated_text)
            self.assertIn("`Joseph`, `Sr. Harrison`", updated_text)

    def test_trigger_curate_world_rule_entry_persists_repo_backed_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            world_rules_path = temp_path / "editorial" / "WORLD_RULES.md"
            world_rules_path.parent.mkdir(parents=True, exist_ok=True)
            world_rules_path.write_text(
                "# World Rules Registry\n\n"
                "## Scope\n"
                "- Organizations and acronyms: `1`\n"
                "- Concepts and formulas: `1`\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `p-1`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `p-2`\n",
                encoding="utf-8",
            )

            summary = trigger_curate_world_rule_entry(
                world_rules_path=world_rules_path,
                entry_title="SEU",
                preferred_form="Soberana Energia Universal",
                aliases_text="SEU, Soberania Energia Universal",
                expanded_form="Soberana Energia Universal",
            )

            updated_text = world_rules_path.read_text(encoding="utf-8")
            self.assertEqual(summary["entry_title"], "SEU")
            self.assertIn("- Preferred form: `Soberana Energia Universal`", updated_text)
            self.assertIn("`SEU`, `Soberania Energia Universal`", updated_text)
