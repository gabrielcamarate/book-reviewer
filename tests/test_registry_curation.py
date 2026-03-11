from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from editorial_core.registry_curation import curate_character_entry, curate_world_rule_entry


class RegistryCurationTest(unittest.TestCase):
    def test_curate_character_entry_updates_preferred_form_and_aliases_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            characters_path = Path(temp_dir) / "CHARACTERS.md"
            characters_path.write_text(
                "# Characters Registry\n\n"
                "## Scope\n"
                "- Character entries: `2`\n\n"
                "### Ana Carolina\n"
                "- Preferred form: `Ana Carolina`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `p-1`\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: `Joseph`\n"
                "- Evidence: `p-2`\n",
                encoding="utf-8",
            )

            summary = curate_character_entry(
                characters_path=characters_path,
                entry_title="Joseph Harrison",
                preferred_form="Sr. Joseph Harrison",
                aliases_text="Joseph, Sr. Harrison",
            )

            updated_text = characters_path.read_text(encoding="utf-8")
            self.assertEqual(summary["entry_title"], "Joseph Harrison")
            self.assertEqual(summary["preferred_form"], "Sr. Joseph Harrison")
            self.assertEqual(summary["aliases"], ["Joseph", "Sr. Harrison"])
            self.assertIn("- Preferred form: `Sr. Joseph Harrison`", updated_text)
            self.assertIn("- Observed aliases or variants: `Joseph`, `Sr. Harrison`", updated_text)
            self.assertIn("### Ana Carolina", updated_text)

    def test_curate_world_rule_entry_updates_organization_with_expanded_form(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            world_rules_path = Path(temp_dir) / "WORLD_RULES.md"
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
                "- Evidence: `p-1`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `p-2`\n",
                encoding="utf-8",
            )

            summary = curate_world_rule_entry(
                world_rules_path=world_rules_path,
                entry_title="SEU",
                preferred_form="Soberana Energia Universal",
                aliases_text="SEU, Soberania Energia Universal",
                expanded_form="Soberana Energia Universal",
            )

            updated_text = world_rules_path.read_text(encoding="utf-8")
            self.assertEqual(summary["entry_title"], "SEU")
            self.assertEqual(summary["preferred_form"], "Soberana Energia Universal")
            self.assertEqual(summary["aliases"], ["SEU", "Soberania Energia Universal"])
            self.assertEqual(summary["expanded_form"], "Soberana Energia Universal")
            self.assertIn("- Preferred form: `Soberana Energia Universal`", updated_text)
            self.assertIn("- Expanded form: `Soberana Energia Universal`", updated_text)
            self.assertIn("- Observed aliases or variants: `SEU`, `Soberania Energia Universal`", updated_text)
            self.assertIn("### Sistema Terra", updated_text)

    def test_curate_world_rule_entry_updates_concept_without_expanded_form(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            world_rules_path = Path(temp_dir) / "WORLD_RULES.md"
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

            summary = curate_world_rule_entry(
                world_rules_path=world_rules_path,
                entry_title="Sistema Terra",
                preferred_form="Sistema Terra Estabelecido",
                aliases_text="Sistema Terra, Sistema Estabelecido",
            )

            updated_text = world_rules_path.read_text(encoding="utf-8")
            self.assertEqual(summary["entry_title"], "Sistema Terra")
            self.assertEqual(summary["preferred_form"], "Sistema Terra Estabelecido")
            self.assertEqual(summary["aliases"], ["Sistema Terra", "Sistema Estabelecido"])
            self.assertNotIn("- Expanded form: `Sistema Terra Estabelecido`", updated_text)
            self.assertIn("- Preferred form: `Sistema Terra Estabelecido`", updated_text)
            self.assertIn("- Observed aliases or variants: `Sistema Terra`, `Sistema Estabelecido`", updated_text)

