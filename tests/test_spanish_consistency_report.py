from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from revisor.core.spanish_consistency_report import generate_spanish_consistency_report


class SpanishConsistencyReportTest(unittest.TestCase):
    def test_generate_spanish_consistency_report_writes_separate_report_and_flags_term_issues(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            consolidated_dir = temp_path / "consolidated"
            translations_dir = temp_path / "reviews" / "es"
            reports_dir = temp_path / "reports"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            characters_path = temp_path / "editorial" / "CHARACTERS.md"
            world_rules_path = temp_path / "editorial" / "WORLD_RULES.md"
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            translations_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            glossary_path.parent.mkdir(parents=True, exist_ok=True)

            (consolidated_dir / "index.json").write_text(
                json.dumps(
                    {
                        "section_count": 1,
                        "chapter_count": 1,
                        "sections": [
                            {
                                "id": "chapter-0001-caminhos-da-serra",
                                "title": "Capítulo 1: Caminhos da Serra.",
                                "file": "chapter-0001-caminhos-da-serra.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (consolidated_dir / "chapter-0001-caminhos-da-serra.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-caminhos-da-serra",
                        "title": "Capítulo 1: Caminhos da Serra.",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-caminhos-da-serra-p-0001",
                                "text": "Noah Martins falou sobre o Sistema Aurora e o LEC.",
                            },
                            {
                                "id": "chapter-0001-caminhos-da-serra-p-0002",
                                "text": "Noah guiou o Sistema Aurora outra vez.",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (translations_dir / "chapter-0001-caminhos-da-serra-chunk-0001.translation-es.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-caminhos-da-serra-chunk-0001",
                        "translations": [
                            {
                                "paragraph_id": "chapter-0001-caminhos-da-serra-p-0001",
                                "translated_text": "Noah Martins habló sobre el Sistema Aurora y la energía soberana.",
                                "rationale": "Teste",
                                "confidence": 0.82,
                            },
                            {
                                "paragraph_id": "chapter-0001-caminhos-da-serra-p-0002",
                                "translated_text": "Noah volvió a guiar el Sistema Aurora.",
                                "rationale": "Teste",
                                "confidence": 0.8,
                            },
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
                "## Organizations and Acronyms\n\n"
                "### LEC\n"
                "- Preferred form: `LEC`\n"
                "- Observed aliases or variants: `Liga de Exploração Científica`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Aurora\n"
                "- Preferred form: `Sistema Aurora`\n"
                "- Observed aliases or variants: none confirmed\n",
                encoding="utf-8",
            )
            characters_path.write_text(
                "# Characters Registry\n\n"
                "## Scope\n"
                "- Character entries: `1`\n\n"
                "### Noah Martins\n"
                "- Preferred form: `Noah Martins`\n"
                "- Observed aliases or variants: `Noah`\n"
                "- Evidence: `chapter-0001-caminhos-da-serra-p-0001`\n",
                encoding="utf-8",
            )
            world_rules_path.write_text(
                "# World Rules Registry\n\n"
                "## Scope\n"
                "- Organizations and acronyms: `1`\n"
                "- Concepts and formulas: `1`\n\n"
                "## Organizations and Acronyms\n\n"
                "### LEC\n"
                "- Preferred form: `LEC`\n"
                "- Expanded form: `Liga de Exploração Científica`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-caminhos-da-serra-p-0001`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Aurora\n"
                "- Preferred form: `Sistema Aurora`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-caminhos-da-serra-p-0001`\n",
                encoding="utf-8",
            )

            summary = generate_spanish_consistency_report(
                consolidated_dir=consolidated_dir,
                translations_dir=translations_dir,
                glossary_path=glossary_path,
                characters_path=characters_path,
                world_rules_path=world_rules_path,
                reports_dir=reports_dir,
            )

            report_path = reports_dir / "es-consistency-report.json"
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["report_path"], str(report_path))
            self.assertEqual(report_payload["scope"]["translated_paragraph_count"], 2)
            self.assertIn("missing_term_preservation", report_payload["findings_by_type"])
            self.assertIn("spanish_term_variants", report_payload["findings_by_type"])
            self.assertEqual(
                report_payload["findings_by_type"]["missing_term_preservation"][0]["entry_title"],
                "LEC",
            )
            self.assertEqual(
                report_payload["findings_by_type"]["spanish_term_variants"][0]["entry_title"],
                "Noah Martins",
            )

    def test_generate_spanish_consistency_report_raises_without_consolidated_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(FileNotFoundError):
                generate_spanish_consistency_report(
                    consolidated_dir=temp_path / "consolidated",
                    translations_dir=temp_path / "reviews" / "es",
                    glossary_path=temp_path / "editorial" / "GLOSSARY.md",
                    characters_path=temp_path / "editorial" / "CHARACTERS.md",
                    world_rules_path=temp_path / "editorial" / "WORLD_RULES.md",
                    reports_dir=temp_path / "reports",
                )
