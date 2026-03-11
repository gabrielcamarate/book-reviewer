from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.style import run_style_pass


class StylePassTest(unittest.TestCase):
    def test_run_style_pass_persists_structured_review_for_next_stable_chunk(self) -> None:
        chunk_index = {
            "chunk_count": 2,
            "chunks": [
                {
                    "id": "chapter-0001-conexao-dimensional-chunk-0001",
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": 1,
                    "review_status": "pending_review",
                    "paragraph_count": 1,
                    "source_start_index": 100,
                    "source_end_index": 100,
                    "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                },
                {
                    "id": "chapter-0001-conexao-dimensional-chunk-0002",
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": 2,
                    "review_status": "pending_review",
                    "paragraph_count": 2,
                    "source_start_index": 101,
                    "source_end_index": 102,
                    "file": "chapter-0001-conexao-dimensional-chunk-0002.json",
                },
            ],
        }

        first_chunk = {
            "id": "chapter-0001-conexao-dimensional-chunk-0001",
            "section_id": "chapter-0001-conexao-dimensional",
            "section_title": "Capítulo 1: Conexão Dimensional.",
            "chunk_order": 1,
            "review_status": "pending_review",
            "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
            "source_start_index": 100,
            "source_end_index": 100,
            "paragraph_count": 1,
            "base_text": "Parágrafo ainda pendente.",
            "previous_context": [],
            "next_context": [],
        }

        second_chunk = {
            "id": "chapter-0001-conexao-dimensional-chunk-0002",
            "section_id": "chapter-0001-conexao-dimensional",
            "section_title": "Capítulo 1: Conexão Dimensional.",
            "chunk_order": 2,
            "review_status": "pending_review",
            "paragraph_ids": [
                "chapter-0001-conexao-dimensional-p-0002",
                "chapter-0001-conexao-dimensional-p-0003",
            ],
            "source_start_index": 101,
            "source_end_index": 102,
            "paragraph_count": 2,
            "base_text": "Texto-base antigo.\n\nOutro texto-base antigo.",
            "previous_context": [
                {
                    "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 100,
                    "review_status": "pending_review",
                    "text": "Parágrafo ainda pendente.",
                }
            ],
            "next_context": [],
        }

        consolidated_section = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "review_status": "mixed",
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 100,
                    "source_text": "Parágrafo ainda pendente.",
                    "text": "Parágrafo ainda pendente.",
                    "review_status": "pending_review",
                    "applied_reviews": [],
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0002",
                    "source_index": 101,
                    "source_text": "Texto-base antigo.",
                    "text": "Primeiro parágrafo consolidado em pt-BR.",
                    "review_status": "approved",
                    "applied_reviews": [],
                },
                {
                    "id": "chapter-0001-conexao-dimensional-p-0003",
                    "source_index": 102,
                    "source_text": "Outro texto-base antigo.",
                    "text": "Segundo parágrafo consolidado em pt-BR.",
                    "review_status": "approved_reference",
                    "applied_reviews": [],
                },
            ],
        }

        captured: dict[str, object] = {}

        def fake_runner(*, prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
            captured["prompt"] = prompt
            captured["schema"] = schema
            captured["model"] = model
            return {
                "suggestions": [
                    {
                        "original": "Primeiro parágrafo consolidado em pt-BR.",
                        "suggested": "Primeiro parágrafo consolidado em pt-BR, com melhor cadência.",
                        "change_type": "style",
                        "reason": "Ajuste rítmico preservando a voz autoral.",
                        "confidence": 0.84,
                    }
                ]
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
            reviews_dir = temp_path / "reviews" / "ptbr"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(chunk_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(first_chunk, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0002.json").write_text(
                json.dumps(second_chunk, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(consolidated_section, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(consolidated_section, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n- Preserve cadence.\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n- Sistema Terra\n", encoding="utf-8")
            decisions_path.write_text(
                "# Editorial Decisions\n\n## Manter repetições deliberadas\n"
                "- Timestamp: 2026-03-10T10:00:00\n"
                "- Scope: chapter-0001-conexao-dimensional\n"
                "- Rationale: A repetição é um recurso filosófico do manuscrito.\n",
                encoding="utf-8",
            )

            summary = run_style_pass(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=fake_runner,
                model="gpt-5-codex",
            )

            output_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0002.style.json"
            persisted = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0002")
            self.assertEqual(summary["suggestion_count"], 1)
            self.assertEqual(summary["output_path"], str(output_path))
            self.assertEqual(captured["model"], "gpt-5-codex")
            self.assertIn("Primeiro parágrafo consolidado em pt-BR.", str(captured["prompt"]))
            self.assertNotIn("Texto-base antigo.", str(captured["prompt"]))
            self.assertIn("Preserve cadence.", str(captured["prompt"]))
            self.assertEqual(captured["schema"]["type"], "object")
            self.assertEqual(persisted["pass"], "style")
            self.assertEqual(persisted["language"], "pt-BR")
            self.assertEqual(persisted["provenance"]["prompt"]["template_id"], "style-ptbr")
            self.assertEqual(persisted["suggestions"][0]["change_type"], "style")

    def test_run_style_pass_raises_when_no_stable_ptbr_chunk_is_available(self) -> None:
        chunk_index = {
            "chunk_count": 1,
            "chunks": [
                {
                    "id": "chapter-0001-conexao-dimensional-chunk-0001",
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": 1,
                    "review_status": "pending_review",
                    "paragraph_count": 1,
                    "source_start_index": 100,
                    "source_end_index": 100,
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
            "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
            "source_start_index": 100,
            "source_end_index": 100,
            "paragraph_count": 1,
            "base_text": "Parágrafo ainda pendente.",
            "previous_context": [],
            "next_context": [],
        }

        chapter_payload = {
            "id": "chapter-0001-conexao-dimensional",
            "type": "chapter",
            "order": 1,
            "title": "Capítulo 1: Conexão Dimensional.",
            "review_status": "pending_review",
            "paragraphs": [
                {
                    "id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 100,
                    "text": "Parágrafo ainda pendente.",
                    "review_status": "pending_review",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
            reviews_dir = temp_path / "reviews" / "ptbr"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(chunk_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(chunk_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(chapter_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                run_style_pass(
                    chunks_dir=chunks_dir,
                    chapters_dir=chapters_dir,
                    consolidated_dir=consolidated_dir,
                    reviews_dir=reviews_dir,
                    style_guide_path=style_guide_path,
                    glossary_path=glossary_path,
                    decisions_path=decisions_path,
                    runner=lambda **_: {"suggestions": []},
                )
