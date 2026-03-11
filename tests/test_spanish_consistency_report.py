from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.spanish_consistency_report import generate_spanish_consistency_report


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
            (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional",
                        "title": "Capítulo 1: Conexão Dimensional.",
                        "paragraphs": [
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0001",
                                "text": "Joseph Harrison falou sobre o Sistema Terra e o SEU.",
                            },
                            {
                                "id": "chapter-0001-conexao-dimensional-p-0002",
                                "text": "Joseph guiou o Sistema Terra outra vez.",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (translations_dir / "chapter-0001-conexao-dimensional-chunk-0001.translation-es.json").write_text(
                json.dumps(
                    {
                        "chunk_id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "translations": [
                            {
                                "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                                "translated_text": "Joseph Harrison habló sobre el Sistema Tierra y la energía soberana.",
                                "rationale": "Teste",
                                "confidence": 0.82,
                            },
                            {
                                "paragraph_id": "chapter-0001-conexao-dimensional-p-0002",
                                "translated_text": "Joseph volvió a guiar el Sistema Terra.",
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
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Observed aliases or variants: `Soberana Energia Universal`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: none confirmed\n",
                encoding="utf-8",
            )
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
                "- Organizations and acronyms: `1`\n"
                "- Concepts and formulas: `1`\n\n"
                "## Organizations and Acronyms\n\n"
                "### SEU\n"
                "- Preferred form: `SEU`\n"
                "- Expanded form: `Soberana Energia Universal`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-conexao-dimensional-p-0001`\n\n"
                "## Concepts and Formulas\n\n"
                "### Sistema Terra\n"
                "- Preferred form: `Sistema Terra`\n"
                "- Observed aliases or variants: none confirmed\n"
                "- Evidence: `chapter-0001-conexao-dimensional-p-0001`\n",
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
                "SEU",
            )
            self.assertEqual(
                report_payload["findings_by_type"]["spanish_term_variants"][0]["entry_title"],
                "Joseph Harrison",
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
