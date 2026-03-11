from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.search import search_repository_state


class SearchTest(unittest.TestCase):
    def test_search_repository_state_returns_chunk_glossary_and_decision_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            chapters_dir = temp_path / "manuscript" / "consolidated"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
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
                        "base_text": "O Sistema Terra exige vigilância e prudência.",
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
                "# Glossary\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n",
                encoding="utf-8",
            )
            decisions_path.write_text(
                "# Editorial Decisions\n\n"
                "## Preservar o uso de Sistema Terra\n"
                "- Timestamp: 2026-03-10T10:00:00\n"
                "- Scope: chapter-0001-conexao-dimensional-chunk-0001\n"
                "- Rationale: O termo é estrutural para a cosmologia.\n",
                encoding="utf-8",
            )

            state = search_repository_state(
                query="Sistema Terra",
                chunks_dir=chunks_dir,
                consolidated_dir=chapters_dir,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
            )

            self.assertEqual(state["query"], "Sistema Terra")
            self.assertEqual(state["result_count"], 3)
            self.assertEqual(state["chunk_matches"][0]["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(state["glossary_matches"][0]["title"], "Sistema Terra")
            self.assertEqual(state["decision_matches"][0]["scope"], "chapter-0001-conexao-dimensional-chunk-0001")
