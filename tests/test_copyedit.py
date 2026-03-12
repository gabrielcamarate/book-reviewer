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
            self.assertIn("Only emit a suggestion if ALL four answers are yes.", str(captured["prompt"]))
            self.assertIn("Agreement and syntax ambiguity rule:", str(captured["prompt"]))
            self.assertIn("Treat the symbols “▬” and “―” as invalid literary dialogue or sentence dash markers", str(captured["prompt"]))
            self.assertIn("When “▬” or “―” is functioning as a dialogue marker", str(captured["prompt"]))
            self.assertIn("Do not preserve “▬” or “―” as a stylistic choice in these punctuation contexts", str(captured["prompt"]))
            self.assertIn('Original: "▬ Verdade — Carol esbraveja ternura."', str(captured["prompt"]))
            self.assertIn('Original: "Verdade ― Carol esbraveja ternura."', str(captured["prompt"]))
            self.assertIn("would require choosing one plausible structural reading over another", str(captured["prompt"]))
            self.assertIn("apparently singular subject is followed by extended post-nominal modifiers", str(captured["prompt"]))
            self.assertIn("either nucleus-based agreement or distributed semantic agreement", str(captured["prompt"]))
            self.assertIn("singular grammatical subject is followed by a long plural expansion", str(captured["prompt"]))
            self.assertIn("prefer omission unless the agreement error is unequivocal", str(captured["prompt"]))
            self.assertIn("apparent subject begins with a hierarchical or collective noun", str(captured["prompt"]))
            self.assertIn("hierarchical or collective head is read together with its full expansion", str(captured["prompt"]))
            self.assertIn("inserting connective, relative, or linking words such as “que”", str(captured["prompt"]))
            self.assertIn("apparent subject begins with a hierarchical or structural noun", str(captured["prompt"]))
            self.assertIn("suppress agreement correction entirely in this copyedit pass", str(captured["prompt"]))
            self.assertIn("Local evidence rule:", str(captured["prompt"]))
            self.assertIn("must be grounded in the local sentence and local span", str(captured["prompt"]))
            self.assertIn("depend primarily on global consistency inference", str(captured["prompt"]))
            self.assertIn("INPUT CONTEXT:", str(captured["prompt"]))
            self.assertIn('"paragraph_id": "chapter-0001-conexao-dimensional-p-0004"', str(captured["prompt"]))
            self.assertEqual(captured["schema"]["type"], "object")
            self.assertEqual(
                captured["schema"]["properties"]["suggestions"]["items"]["properties"]["change_type"]["enum"],
                [
                    "spelling",
                    "ortografia",
                    "grammar",
                    "gramática",
                    "punctuation",
                    "pontuação",
                    "agreement",
                    "concordância",
                    "syntax",
                    "sintaxe",
                    "capitalization",
                    "capitalização",
                    "quotation",
                    "citação",
                    "aspas",
                    "diacritics",
                    "acentuação",
                ],
            )
            self.assertEqual(
                captured["schema"]["properties"]["suggestions"]["items"]["properties"]["confidence"]["minimum"],
                0.8,
            )
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

    def test_run_copyedit_pass_rejects_non_objective_or_low_confidence_suggestions(self) -> None:
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
                                "paragraph_count": 1,
                                "source_start_index": 100,
                                "source_end_index": 100,
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
                        "chunk_order": 1,
                        "review_status": "pending_review",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
                        "source_start_index": 100,
                        "source_end_index": 100,
                        "paragraph_count": 1,
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
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                run_copyedit_pass(
                    chunks_dir=chunks_dir,
                    reviews_dir=reviews_dir,
                    style_guide_path=style_guide_path,
                    glossary_path=glossary_path,
                    decisions_path=decisions_path,
                    runner=lambda **_: {
                        "suggestions": [
                            {
                                "original": "Trecho principal.",
                                "suggested": "Trecho mais elegante.",
                                "change_type": "style",
                                "reason": "Soa melhor.",
                                "confidence": 0.55,
                            }
                        ]
                    },
                )

    def test_run_copyedit_pass_discards_repeated_span_suggestions_without_occurrence_index(self) -> None:
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
                                "paragraph_count": 1,
                                "source_start_index": 100,
                                "source_end_index": 100,
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
                        "chunk_order": 1,
                        "review_status": "pending_review",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
                        "source_start_index": 100,
                        "source_end_index": 100,
                        "paragraph_count": 1,
                        "base_text": "Turmas de LGBTQIAPN+ deveriam considerar adicionar o H de hetero nesta sopa de letras caracterizadoras de gêneros. Diversidades sexualizadas criam tribos excludentes da heterossexualidade.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            summary = run_copyedit_pass(
                chunks_dir=chunks_dir,
                reviews_dir=reviews_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=lambda **_: {
                    "suggestions": [
                        {
                            "original": "hetero",
                            "suggested": "hétero",
                            "change_type": "diacritics",
                            "reason": "A forma reduzida exige acento.",
                            "confidence": 0.9,
                        }
                    ]
                },
            )

            output_path = reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.copyedit.json"
            persisted = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(summary["suggestion_count"], 0)
            self.assertEqual(persisted["suggestions"], [])

    def test_run_copyedit_pass_includes_latest_rejection_feedback_in_prompt(self) -> None:
        captured: dict[str, object] = {}

        def fake_runner(*, prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
            captured["prompt"] = prompt
            return {"suggestions": []}

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
                                "paragraph_count": 1,
                                "source_start_index": 100,
                                "source_end_index": 100,
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
                        "chunk_order": 1,
                        "review_status": "pending_review",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
                        "source_start_index": 100,
                        "source_end_index": 100,
                        "paragraph_count": 1,
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
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")
            (reviews_dir / "chapter-0001-conexao-dimensional-chunk-0001.rejection.json").write_text(
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

            run_copyedit_pass(
                chunks_dir=chunks_dir,
                reviews_dir=reviews_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=fake_runner,
            )

            self.assertIn('"latest_rejection_feedback": "Mudou demais a voz do autor."', str(captured["prompt"]))

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
