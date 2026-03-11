from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.copyedit import run_copyedit_pass


class CopyeditPassTest(unittest.TestCase):
    def test_run_copyedit_pass_selects_next_chunk_and_persists_structured_review(self) -> None:
        chunk_index = {
            "chunk_count": 2,
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
                },
                {
                    "id": "chapter-0001-conexao-dimensional-chunk-0002",
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": 2,
                    "review_status": "pending_review",
                    "paragraph_count": 1,
                    "source_start_index": 102,
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
            "paragraph_ids": [
                "chapter-0001-conexao-dimensional-p-0002",
                "chapter-0001-conexao-dimensional-p-0003",
            ],
            "source_start_index": 100,
            "source_end_index": 101,
            "paragraph_count": 2,
            "base_text": "Primeiro parágrafo pendente.\n\nSegundo parágrafo pendente.",
            "previous_context": [
                {
                    "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                    "source_index": 99,
                    "review_status": "approved_reference",
                    "text": "Contexto anterior aprovado.",
                }
            ],
            "next_context": [
                {
                    "paragraph_id": "chapter-0001-conexao-dimensional-p-0004",
                    "source_index": 102,
                    "review_status": "pending_review",
                    "text": "Contexto seguinte imediato.",
                }
            ],
        }

        second_chunk = {
            "id": "chapter-0001-conexao-dimensional-chunk-0002",
            "section_id": "chapter-0001-conexao-dimensional",
            "section_title": "Capítulo 1: Conexão Dimensional.",
            "chunk_order": 2,
            "review_status": "pending_review",
            "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0004"],
            "source_start_index": 102,
            "source_end_index": 102,
            "paragraph_count": 1,
            "base_text": "Terceiro parágrafo pendente.",
            "previous_context": [],
            "next_context": [],
        }

        captured: dict[str, object] = {}

        def fake_runner(*, prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
            captured["prompt"] = prompt
            captured["schema"] = schema
            captured["model"] = model
            return {
                "suggestions": [
                    {
                        "original": "Primeiro parágrafo pendente.",
                        "suggested": "Primeiro parágrafo revisado.",
                        "change_type": "grammar",
                        "reason": "Ajuste de clareza gramatical.",
                        "confidence": 0.92,
                    }
                ]
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            reviews_dir = temp_path / "reviews" / "ptbr"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
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
            style_guide_path.write_text(
                "# Style Guide\n- Preserve dialogue markers.\n",
                encoding="utf-8",
            )
            glossary_path.write_text(
                "# Glossary\n- Sistema Terra\n",
                encoding="utf-8",
            )
            decisions_path.write_text(
                "# Editorial Decisions\n\n## Preservar travessão dramático\n"
                "- Timestamp: 2026-03-10T10:00:00\n"
                "- Scope: chapter-0001-conexao-dimensional\n"
                "- Rationale: O uso do travessão integra a respiração narrativa.\n",
                encoding="utf-8",
            )
            (reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json").write_text(
                json.dumps({"status": "proposed"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = run_copyedit_pass(
                chunks_dir=chunks_dir,
                reviews_dir=reviews_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=fake_runner,
                model="gpt-5-codex",
            )

            output_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0002.copyedit.json"
            persisted = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(summary["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0002")
            self.assertEqual(summary["suggestion_count"], 1)
            self.assertEqual(summary["output_path"], str(output_path))
            self.assertEqual(captured["model"], "gpt-5-codex")
            self.assertIn("Terceiro parágrafo pendente.", str(captured["prompt"]))
            self.assertNotIn("Primeiro parágrafo pendente.", str(captured["prompt"]))
            self.assertIn("Preserve dialogue markers.", str(captured["prompt"]))
            self.assertIn("Sistema Terra", str(captured["prompt"]))
            self.assertIn("Preservar travessão dramático", str(captured["prompt"]))
            self.assertEqual(captured["schema"]["type"], "object")
            self.assertEqual(persisted["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0002")
            self.assertEqual(persisted["pass"], "copyedit")
            self.assertEqual(persisted["model"], "gpt-5-codex")
            self.assertEqual(persisted["provenance"]["model"]["name"], "gpt-5-codex")
            self.assertEqual(persisted["provenance"]["prompt"]["template_id"], "copyedit-ptbr")
            self.assertIn("version", persisted["provenance"]["prompt"])
            self.assertIn("sha256", persisted["provenance"]["prompt"])
            self.assertEqual(persisted["provenance"]["schema"]["name"], "copyedit-output")
            self.assertIn("style_guide", persisted["provenance"]["context_inputs"])
            self.assertIn("sha256", persisted["provenance"]["context_inputs"]["glossary"])
            self.assertEqual(persisted["suggestions"][0]["reason"], "Ajuste de clareza gramatical.")

    def test_run_copyedit_pass_raises_when_no_pending_chunk_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            reviews_dir = temp_path / "reviews" / "ptbr"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps({"chunk_count": 0, "chunks": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                run_copyedit_pass(
                    chunks_dir=chunks_dir,
                    reviews_dir=reviews_dir,
                    style_guide_path=style_guide_path,
                    glossary_path=glossary_path,
                    decisions_path=decisions_path,
                    runner=lambda **_: {"suggestions": []},
                )
