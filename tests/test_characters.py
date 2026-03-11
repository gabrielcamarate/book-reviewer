from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from editorial_core.characters import generate_characters_registry, read_characters_registry


class CharactersRegistryTest(unittest.TestCase):
    def test_generate_characters_registry_writes_entries_from_glossary_proper_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            output_path = temp_path / "editorial" / "CHARACTERS.md"
            glossary_path.parent.mkdir(parents=True, exist_ok=True)
            glossary_path.write_text(
                "# Glossary\n\n"
                "## Proper Names\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: `Joseph`, `Sr. Harrison`\n"
                "- Evidence: `chapter-0001-p-0001`, `chapter-0001-p-0002`\n\n"
                "### Ana Carolina\n"
                "- Preferred form: `Ana Carolina`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-p-0003`\n\n"
                "### Fazenda Araruama\n"
                "- Preferred form: `Fazenda Araruama`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-p-0004`\n",
                encoding="utf-8",
            )

            summary = generate_characters_registry(
                glossary_path=glossary_path,
                output_path=output_path,
            )
            entries = read_characters_registry(output_path)

            self.assertEqual(summary["character_count"], 2)
            self.assertEqual(entries[0]["title"], "Ana Carolina")
            self.assertEqual(entries[1]["title"], "Joseph Harrison")
            self.assertEqual(entries[1]["aliases"], ["Joseph", "Sr. Harrison"])
            self.assertNotIn("Fazenda Araruama", output_path.read_text(encoding="utf-8"))
