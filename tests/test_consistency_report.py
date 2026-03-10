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

            summary = generate_consistency_report(
                consolidated_dir=consolidated_dir,
                glossary_path=glossary_path,
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
            self.assertEqual(
                report_payload["findings_by_type"]["alias_usage"][0]["observed_variant"],
                "Soberania Energia Universal",
            )
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
                    reports_dir=temp_path / "reports",
                )
