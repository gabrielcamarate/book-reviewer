from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.review_application import apply_review_approval


class ReviewApplicationTest(unittest.TestCase):
    def test_apply_review_approval_records_audit_and_updates_consolidated_state(self) -> None:
        chunk_index = {
            "chunk_count": 1,
            "chunks": [
                {
                    "id": "chapter-0001-conexao-dimensional-chunk-0001",
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": 1,
                    "review_status": "pending_review",
                    "paragraph_count": 2,
                    "source_start_index": 100,
                    "source_end_index": 101,
                    "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                }
            ],
        }

        chunk_payload = {
            "id": "chapter-0001-conexao-dimensional-chunk-0001",
            "section_id": "chapter-0001-conexao-dimensional",
            "section_title": "Capítulo 1: Conexão Dimensional.",
            "chunk_order": 1,
            "review_status": "pending_review",
            "paragraph_ids": [
                "chapter-0001-conexao-dimensional-p-0002",
                "chapter-0001-conexao-dimensional-p-0003",
            ],
            "source_start_index": 100,
            "source_end_index": 101,
            "paragraph_count": 2,
            "base_text": "Primeiro parágrafo pendente.\n\nSegundo parágrafo pendente.",
            "previous_context": [],
            "next_context": [],
        }

        chapter_index = {
            "section_count": 1,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 20,
                    "source_start_index": 99,
                    "source_end_index": 101,
                    "paragraph_count": 3,
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "mixed",
                }
            ],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "heading_source_index": 20,
            "review_status": "mixed",
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 99,
                    "text": "Parágrafo aprovado anterior.",
                    "review_status": "approved_reference",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 100,
                    "text": "Primeiro parágrafo pendente.",
                    "review_status": "pending_review",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0003",
                    "source_index": 101,
                    "text": "Segundo parágrafo pendente.",
                    "review_status": "pending_review",
                },
            ],
        }

        review_payload = {
            "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
            "pass": "copyedit",
            "language": "pt-BR",
            "status": "proposed",
            "model": "gpt-5-codex",
            "source": {
                "section_id": "chapter-0001-conexao-dimensional",
                "section_title": "Capítulo 1: Conexão Dimensional.",
                "paragraph_ids": [
                    "chapter-0001-conexao-dimensional-p-0002",
                    "chapter-0001-conexao-dimensional-p-0003",
                ],
                "source_start_index": 100,
                "source_end_index": 101,
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
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            chapters_dir = temp_path / "chapters"
            reviews_dir = temp_path / "reviews" / "ptbr"
            consolidated_dir = temp_path / "consolidated"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(chunk_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(chunk_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            review_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json"
            review_path.write_text(
                json.dumps(review_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = apply_review_approval(
                review_path=review_path,
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                approved_suggestion_indexes=[0, 1],
            )

            approval_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.approval.json"
            approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
            consolidated_index = json.loads((consolidated_dir / "index.json").read_text(encoding="utf-8"))
            consolidated_section = json.loads(
                (consolidated_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )
            original_section = json.loads(
                (chapters_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(summary["approved_suggestion_count"], 2)
            self.assertEqual(summary["applied_change_count"], 2)
            self.assertEqual(summary["approval_path"], str(approval_path))
            self.assertEqual(approval_payload["status"], "approved")
            self.assertEqual(approval_payload["approved_suggestion_indexes"], [0, 1])
            self.assertEqual(len(approval_payload["applied_changes"]), 2)
            self.assertEqual(consolidated_index["section_count"], 1)
            self.assertEqual(
                consolidated_section["paragraphs"][1]["text"],
                "Primeiro parágrafo revisado.",
            )
            self.assertEqual(
                consolidated_section["paragraphs"][2]["text"],
                "Segundo parágrafo revisado.",
            )
            self.assertEqual(
                consolidated_section["paragraphs"][1]["source_text"],
                "Primeiro parágrafo pendente.",
            )
            self.assertEqual(consolidated_section["paragraphs"][1]["review_status"], "approved")
            self.assertEqual(len(consolidated_section["paragraphs"][1]["applied_reviews"]), 1)
            self.assertEqual(
                original_section["paragraphs"][1]["text"],
                "Primeiro parágrafo pendente.",
            )

    def test_apply_review_approval_raises_when_review_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(FileNotFoundError):
                apply_review_approval(
                    review_path=temp_path / "missing.copyedit.json",
                    chunks_dir=temp_path / "chunks",
                    chapters_dir=temp_path / "chapters",
                    consolidated_dir=temp_path / "consolidated",
                )

    def test_apply_review_approval_records_style_origin_separately_from_copyedit(self) -> None:
        chunk_index = {
            "chunk_count": 1,
            "chunks": [
                {
                    "id": "chapter-0001-conexao-dimensional-chunk-0001",
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": 1,
                    "review_status": "pending_review",
                    "paragraph_count": 2,
                    "source_start_index": 100,
                    "source_end_index": 101,
                    "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                }
            ],
        }

        chunk_payload = {
            "id": "chapter-0001-conexao-dimensional-chunk-0001",
            "section_id": "chapter-0001-conexao-dimensional",
            "section_title": "Capítulo 1: Conexão Dimensional.",
            "chunk_order": 1,
            "review_status": "pending_review",
            "paragraph_ids": [
                "chapter-0001-conexao-dimensional-p-0002",
                "chapter-0001-conexao-dimensional-p-0003",
            ],
            "source_start_index": 100,
            "source_end_index": 101,
            "paragraph_count": 2,
            "base_text": "Primeiro texto consolidado.\n\nSegundo texto consolidado.",
            "previous_context": [],
            "next_context": [],
        }

        chapter_index = {
            "section_count": 1,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "heading_source_index": 20,
                    "source_start_index": 99,
                    "source_end_index": 101,
                    "paragraph_count": 3,
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "approved",
                }
            ],
        }

        consolidated_section = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "review_status": "approved",
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 99,
                    "source_text": "Parágrafo aprovado anterior.",
                    "text": "Parágrafo aprovado anterior.",
                    "review_status": "approved_reference",
                    "applied_reviews": [],
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 100,
                    "source_text": "Primeiro texto original.",
                    "text": "Primeiro texto consolidado.",
                    "review_status": "approved",
                    "applied_reviews": [
                        {
                            "approval_file": "chapter-0001-conexao-dimensional-chunk-0001.approval.json",
                            "review_file": "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json",
                            "pass": "copyedit",
                            "suggestion_index": 0,
                            "change_type": "grammar",
                            "reason": "Ajuste gramatical.",
                            "confidence": 0.9,
                            "applied_at": "2026-03-10T10:00:00",
                            "original": "Primeiro texto original.",
                            "suggested": "Primeiro texto consolidado.",
                        }
                    ],
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0003",
                    "source_index": 101,
                    "source_text": "Segundo texto original.",
                    "text": "Segundo texto consolidado.",
                    "review_status": "approved",
                    "applied_reviews": [],
                },
            ],
        }

        review_payload = {
            "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
            "pass": "style",
            "language": "pt-BR",
            "status": "proposed",
            "model": "gpt-5-codex",
            "source": {
                "section_id": "chapter-0001-conexao-dimensional",
                "section_title": "Capítulo 1: Conexão Dimensional.",
                "paragraph_ids": [
                    "chapter-0001-conexao-dimensional-p-0002",
                    "chapter-0001-conexao-dimensional-p-0003",
                ],
                "source_start_index": 100,
                "source_end_index": 101,
            },
            "suggestions": [
                {
                    "original": "Primeiro texto consolidado.",
                    "suggested": "Primeiro texto consolidado, com melhor cadência.",
                    "change_type": "style",
                    "reason": "Refino rítmico.",
                    "confidence": 0.84,
                },
                {
                    "original": "Segundo texto consolidado.",
                    "suggested": "Segundo texto consolidado, com melhor cadência.",
                    "change_type": "style",
                    "reason": "Refino rítmico.",
                    "confidence": 0.82,
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            chapters_dir = temp_path / "chapters"
            reviews_dir = temp_path / "reviews" / "ptbr"
            consolidated_dir = temp_path / "consolidated"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(chunk_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(chunk_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(consolidated_section, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "index.json").write_text(
                json.dumps(chapter_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(consolidated_section, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            review_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.style.json"
            review_path.write_text(
                json.dumps(review_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = apply_review_approval(
                review_path=review_path,
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                approved_suggestion_indexes=[0],
            )

            approval_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.style.approval.json"
            approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
            consolidated_section_after = json.loads(
                (consolidated_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(summary["approved_suggestion_count"], 1)
            self.assertEqual(summary["applied_change_count"], 1)
            self.assertEqual(approval_payload["pass"], "style")
            self.assertEqual(approval_payload["approved_suggestion_indexes"], [0])
            self.assertEqual(
                consolidated_section_after["paragraphs"][1]["text"],
                "Primeiro texto consolidado, com melhor cadência.",
            )
            self.assertEqual(
                consolidated_section_after["paragraphs"][2]["text"],
                "Segundo texto consolidado.",
            )
            self.assertEqual(
                consolidated_section_after["paragraphs"][1]["applied_reviews"][-1]["pass"],
                "style",
            )
            self.assertEqual(
                consolidated_section_after["paragraphs"][1]["applied_reviews"][0]["pass"],
                "copyedit",
            )
