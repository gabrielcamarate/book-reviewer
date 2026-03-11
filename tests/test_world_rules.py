from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from editorial_core.world_rules import generate_world_rules_registry, read_world_rules_registry


class WorldRulesRegistryTest(unittest.TestCase):
    def test_generate_world_rules_registry_writes_organizations_and_concepts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            output_path = temp_path / "editorial" / "WORLD_RULES.md"
            glossary_path.parent.mkdir(parents=True, exist_ok=True)
            glossary_path.write_text(
                "# Glossary\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: `Soberania Energia Universal`\n"
                "- Evidence: `chapter-0001-p-0001`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-p-0002`\n\n"
                "### Philosophical Formula\n"
                "- Preferred form: `a minha raça humana é universal.`\n"
                "- Observed aliases or variants: `a minha religião é a consciência`\n"
                "- Evidence: `chapter-0001-p-0003`\n",
                encoding="utf-8",
            )

            summary = generate_world_rules_registry(
                glossary_path=glossary_path,
                output_path=output_path,
            )
            registry = read_world_rules_registry(output_path)

            self.assertEqual(summary["organization_count"], 1)
            self.assertEqual(summary["concept_count"], 2)
            self.assertEqual(registry["organizations"][0]["title"], "SEU")
            self.assertEqual(registry["organizations"][0]["expanded_form"], "Soberana Energia Universal")
            self.assertEqual(registry["concepts"][1]["aliases"], ["a minha religião é a consciência"])
