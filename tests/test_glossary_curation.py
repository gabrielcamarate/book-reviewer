from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from editorial_core.glossary_curation import curate_glossary_entry, parse_glossary_entries


class GlossaryCurationTest(unittest.TestCase):
    def test_curate_glossary_entry_updates_preferred_form_and_aliases_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            glossary_path = Path(temp_dir) / "GLOSSARY.md"
            glossary_path.write_text(
                "# Glossary\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: `Soberana Energia Universal`, `Soberania Energia Universal`\n"
                "- Evidence: `p-1`\n\n"
                "## Proper Names\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `p-2`\n",
                encoding="utf-8",
            )

            summary = curate_glossary_entry(
                glossary_path=glossary_path,
                entry_title="SEU",
                preferred_form="Soberana Energia Universal",
                aliases_text="SEU, Soberania Energia Universal",
            )

            updated_text = glossary_path.read_text(encoding="utf-8")
            entries = parse_glossary_entries(glossary_path)

            self.assertEqual(summary["entry_title"], "SEU")
            self.assertEqual(summary["preferred_form"], "Soberana Energia Universal")
            self.assertEqual(summary["aliases"], ["SEU", "Soberania Energia Universal"])
            self.assertIn("- Preferred form: `Soberana Energia Universal`", updated_text)
            self.assertIn(
                "- Observed aliases or variants: `SEU`, `Soberania Energia Universal`",
                updated_text,
            )
            self.assertEqual(entries[0]["entries"][0]["title"], "SEU")
            self.assertEqual(entries[0]["entries"][0]["preferred_form"], "Soberana Energia Universal")
            self.assertEqual(entries[1]["entries"][0]["title"], "Joseph Harrison")

