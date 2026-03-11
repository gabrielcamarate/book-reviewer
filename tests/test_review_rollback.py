from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.review_rollback import rollback_last_review_approval


class ReviewRollbackTest(unittest.TestCase):
    def test_rollback_last_review_approval_restores_previous_text_and_audit_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
            reviews_dir = temp_path / "reviews" / "ptbr"
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)

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
            chapter_payload = {
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
            }
            consolidated_index = {
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
            }
            consolidated_payload = {
                "id": "chapter-0001-conexao-dimensional",
                "title": "Capítulo 1: Conexão Dimensional.",
                "review_status": "approved",
                "paragraphs": [
                    {
                        "id": "chapter-0001-conexao-dimensional-p-0001",
                        "source_index": 1,
                        "source_text": "Texto original.",
                        "text": "Texto revisado final.",
                        "review_status": "approved",
                        "applied_reviews": [
                            {
                                "approval_file": "chapter-0001-conexao-dimensional-chunk-0001.approval.json",
                                "review_file": "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json",
                                "pass": "copyedit",
                                "suggestion_index": 0,
                                "change_type": "grammar",
                                "reason": "Ajuste.",
                                "confidence": 0.91,
                                "applied_at": "2026-03-10T21:00:00",
                                "original": "Texto original.",
                                "suggested": "Texto revisado final.",
                            }
                        ],
                    }
                ],
            }
            approval_payload = {
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
                        "suggested": "Texto revisado final.",
                        "change_type": "grammar",
                        "reason": "Ajuste.",
                        "confidence": 0.91,
                    }
                ],
                "skipped_suggestions": [],
                "consolidated_section_file": "chapter-0001-conexao-dimensional.json",
                "approved_at": "2026-03-10T21:00:00",
            }

            (chapters_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "index.json").write_text(
                json.dumps(consolidated_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(consolidated_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            approval_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.approval.json"
            approval_path.write_text(
                json.dumps(approval_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = rollback_last_review_approval(
                reviews_dir=reviews_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
            )

            updated_approval = json.loads(approval_path.read_text(encoding="utf-8"))
            rollback_payload = json.loads(Path(summary["rollback_path"]).read_text(encoding="utf-8"))
            consolidated_section = json.loads(
                (consolidated_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )
            consolidated_index_after = json.loads((consolidated_dir / "index.json").read_text(encoding="utf-8"))

            self.assertEqual(summary["approval_file"], approval_path.name)
            self.assertEqual(summary["reverted_change_count"], 1)
            self.assertEqual(updated_approval["status"], "rolled_back")
            self.assertIn("rolled_back_at", updated_approval)
            self.assertEqual(rollback_payload["approval_file"], approval_path.name)
            self.assertEqual(
                consolidated_section["paragraphs"][0]["text"],
                "Texto original.",
            )
            self.assertEqual(consolidated_section["paragraphs"][0]["review_status"], "pending_review")
            self.assertEqual(consolidated_section["paragraphs"][0]["applied_reviews"], [])
            self.assertEqual(consolidated_index_after["sections"][0]["review_status"], "pending_review")

    def test_rollback_last_review_approval_raises_when_latest_approval_is_not_safe_to_revert(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
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
                                "text": "Texto final divergente.",
                                "review_status": "approved",
                                "applied_reviews": [
                                    {
                                        "approval_file": "approval-mais-recente.json",
                                        "review_file": "x.json",
                                        "pass": "copyedit",
                                        "suggestion_index": 0,
                                        "change_type": "grammar",
                                        "reason": "Ajuste.",
                                        "confidence": 0.9,
                                        "applied_at": "2026-03-10T21:05:00",
                                        "original": "Texto intermediário.",
                                        "suggested": "Texto final divergente.",
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
            (reviews_dir / "approval-mais-recente.json").write_text(
                json.dumps(
                    {
                        "approval_file": "approval-mais-recente.json",
                        "pass": "copyedit",
                        "status": "approved",
                        "applied_changes": [
                            {
                                "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                                "original": "Texto original.",
                                "suggested": "Texto revisado final.",
                            }
                        ],
                        "consolidated_section_file": "chapter-0001-conexao-dimensional.json",
                        "approved_at": "2026-03-10T21:05:00",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                rollback_last_review_approval(
                    reviews_dir=reviews_dir,
                    chapters_dir=chapters_dir,
                    consolidated_dir=consolidated_dir,
                )

