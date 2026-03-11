from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.consistency_report import generate_consistency_report


class ConsistencyReportTest(unittest.TestCase):
    def test_generate_consistency_report_writes_grouped_findings_without_mutation(self) -> None:
        consolidated_index = {
            "section_count": 1,
            "chapter_count": 1,
            "sections": [
                {
                    "id": "chapter-0001-conexao-dimensional",
                    "type": "chapter",
                    "order": 1,
                    "title": "Capítulo 1: Conexão Dimensional.",
                    "file": "chapter-0001-conexao-dimensional.json",
                    "review_status": "mixed",
                }
            ],
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
                    "source_text": "Texto original.",
                    "text": "Soberania Energia Universal  guia a cena. Dizendo: ”Deus perdoa e não castiga”.",
                    "review_status": "approved",
                    "applied_reviews": [],
                }
            ],
        }

        glossary_text = """# Glossary

## Organizations and Acronyms

### SEU
- Preferred form: `SEU`
- Expanded form: `Soberana Energia Universal`
- Observed aliases or variants: `Soberana Energia Universal`, `Soberania Energia Universal`

## Proper Names

### Tom Harrison
- Preferred form: `Tom Harrison`
- Observed aliases or variants: none confirmed

### Tom Harris
- Preferred form: `Tom Harris`
- Observed aliases or variants: none confirmed
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            consolidated_dir = temp_path / "consolidated"
            reports_dir = temp_path / "reports"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            characters_path = temp_path / "editorial" / "CHARACTERS.md"
            world_rules_path = temp_path / "editorial" / "WORLD_RULES.md"
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            glossary_path.parent.mkdir(parents=True, exist_ok=True)

            (consolidated_dir / "index.json").write_text(
                json.dumps(consolidated_index, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(consolidated_section, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            glossary_path.write_text(glossary_text, encoding="utf-8")
            characters_path.write_text(
                "# Characters Registry\n\n"
                "## Scope\n"
                "- Character entries: `1`\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: `Joseph`\n"
                "- Evidence: `chapter-0001-conexao-dimensional-p-0001`\n",
                encoding="utf-8",
            )
            world_rules_path.write_text(
                "# World Rules Registry\n\n"
                "## Scope\n"
                "- Organizations and acronyms: `0`\n"
                "- Concepts and formulas: `1`\n\n"
                "## Organizations and Acronyms\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: `Sistema Estabelecido`\n"
                "- Evidence: `chapter-0001-conexao-dimensional-p-0001`\n",
                encoding="utf-8",
            )

            summary = generate_consistency_report(
                consolidated_dir=consolidated_dir,
                glossary_path=glossary_path,
                characters_path=characters_path,
                world_rules_path=world_rules_path,
                reports_dir=reports_dir,
            )

            report_path = reports_dir / "ptbr-consistency-report.json"
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
            original_section = json.loads(
                (consolidated_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(summary["report_path"], str(report_path))
            self.assertGreaterEqual(summary["finding_count"], 4)
            self.assertIn("alias_usage", report_payload["findings_by_type"])
            self.assertIn("quote_anomalies", report_payload["findings_by_type"])
            self.assertIn("spacing_anomalies", report_payload["findings_by_type"])
            self.assertIn("similar_proper_names", report_payload["findings_by_type"])
            self.assertIn("cross_chapter_entity_variants", report_payload["findings_by_type"])
            self.assertEqual(
                report_payload["findings_by_type"]["alias_usage"][0]["observed_variant"],
                "Soberania Energia Universal",
            )
            self.assertEqual(report_payload["scope"]["character_entry_count"], 1)
            self.assertEqual(report_payload["scope"]["world_rule_entry_count"], 1)
            self.assertEqual(
                original_section["paragraphs"][0]["text"],
                "Soberania Energia Universal  guia a cena. Dizendo: ”Deus perdoa e não castiga”.",
            )

    def test_generate_consistency_report_raises_without_consolidated_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(FileNotFoundError):
                generate_consistency_report(
                    consolidated_dir=temp_path / "consolidated",
                    glossary_path=temp_path / "editorial" / "GLOSSARY.md",
                    characters_path=temp_path / "editorial" / "CHARACTERS.md",
                    world_rules_path=temp_path / "editorial" / "WORLD_RULES.md",
                    reports_dir=temp_path / "reports",
                )

    def test_generate_consistency_report_groups_cross_chapter_entity_variants(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            consolidated_dir = temp_path / "consolidated"
            reports_dir = temp_path / "reports"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            characters_path = temp_path / "editorial" / "CHARACTERS.md"
            world_rules_path = temp_path / "editorial" / "WORLD_RULES.md"
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            glossary_path.parent.mkdir(parents=True, exist_ok=True)

            (consolidated_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 2,
                        "chapter_count": 2,
                        "sections": [
                            {
                                "id": "chapter-0001-conexao-dimensional",
                                "type": "chapter",
                                "order": 1,
                                "title": "Capítulo 1: Conexão Dimensional.",
                                "file": "chapter-0001-conexao-dimensional.json",
                                "review_status": "mixed",
                            },
                            {
                                "id": "chapter-0002-supremo-poder-anonimo",
                                "type": "chapter",
                                "order": 2,
                                "title": "Capítulo 2: Supremo Poder Anônimo.",
                                "file": "chapter-0002-supremo-poder-anonimo.json",
                                "review_status": "mixed",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "text": "Joseph observou o Sistema Estabelecido.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0002-supremo-poder-anonimo.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0002-supremo-poder-anonimo",
                        "title": "Capítulo 2: Supremo Poder Anônimo.",
                        "paragraphs": [
                            {
                                "id": "chapter-0002-supremo-poder-anonimo-p-0001",
                                "text": "Joseph Harrison retornou ao Sistema Terra.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            characters_path.write_text(
                "# Characters Registry\n\n"
                "## Scope\n"
                "- Character entries: `1`\n\n"
                "### Joseph Harrison\n"
                "- Preferred form: `Joseph Harrison`\n"
                "- Observed aliases or variants: `Joseph`\n"
                "- Evidence: `chapter-0001-conexao-dimensional-p-0001`\n",
                encoding="utf-8",
            )
            world_rules_path.write_text(
                "# World Rules Registry\n\n"
                "## Scope\n"
                "- Organizations and acronyms: `0`\n"
                "- Concepts and formulas: `1`\n\n"
                "## Organizations and Acronyms\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: `Sistema Estabelecido`\n"
                "- Evidence: `chapter-0001-conexao-dimensional-p-0001`\n",
                encoding="utf-8",
            )

            generate_consistency_report(
                consolidated_dir=consolidated_dir,
                glossary_path=glossary_path,
                characters_path=characters_path,
                world_rules_path=world_rules_path,
                reports_dir=reports_dir,
            )

            report_payload = json.loads((reports_dir / "ptbr-consistency-report.json").read_text(encoding="utf-8"))
            findings = report_payload["findings_by_type"]["cross_chapter_entity_variants"]

            self.assertEqual(len(findings), 2)
            self.assertEqual(findings[0]["chapter_ids"][0], "chapter-0001-conexao-dimensional")
            self.assertIn("Joseph", findings[0]["observed_forms"] + findings[1]["observed_forms"])
            self.assertIn("Sistema Estabelecido", findings[0]["observed_forms"] + findings[1]["observed_forms"])
