from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from editorial_core.decisions import append_editorial_decision, read_editorial_decisions


class DecisionsTest(unittest.TestCase):
    def test_append_editorial_decision_creates_file_and_persists_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            decisions_path = Path(temp_dir) / "editorial" / "DECISIONS.md"

            summary = append_editorial_decision(
                decisions_path=decisions_path,
                title="Preservar uso de travessão narrativo",
                rationale="O autor usa travessão como marca de respiração estilística.",
                scope="chapter-0001-conexao-dimensional-chunk-0002",
            )

            entries = read_editorial_decisions(decisions_path)

            self.assertEqual(summary["decision_count"], 1)
            self.assertEqual(entries[0]["title"], "Preservar uso de travessão narrativo")
            self.assertEqual(entries[0]["scope"], "chapter-0001-conexao-dimensional-chunk-0002")
            self.assertIn("travessão", decisions_path.read_text(encoding="utf-8"))

