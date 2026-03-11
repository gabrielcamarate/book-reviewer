from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.repository_validation import validate_repository_state


class RepositoryValidationTest(unittest.TestCase):
    def test_validate_repository_state_reports_missing_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)

            summary = validate_repository_state(root_dir=root_dir)

            self.assertFalse(summary["ok"])
            self.assertIn("editorial/STYLE_GUIDE.md", "\n".join(summary["errors"]))

    def test_validate_repository_state_accepts_minimum_web_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            (root_dir / "editorial").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chunks").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chapters").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "consolidated").mkdir(parents=True, exist_ok=True)
            (root_dir / "reviews" / "ptbr").mkdir(parents=True, exist_ok=True)
            (root_dir / "reviews" / "es").mkdir(parents=True, exist_ok=True)
            (root_dir / "reports").mkdir(parents=True, exist_ok=True)
            (root_dir / "deliverables").mkdir(parents=True, exist_ok=True)

            (root_dir / "editorial" / "STYLE_GUIDE.md").write_text("# Style Guide\n", encoding="utf-8")
            (root_dir / "editorial" / "GLOSSARY.md").write_text("# Glossary\n", encoding="utf-8")
            (root_dir / "editorial" / "DECISIONS.md").write_text("# Editorial Decisions\n", encoding="utf-8")
            (root_dir / "manuscript" / "chunks" / "index.json").write_text(
                json.dumps({"chunk_count": 0, "chunks": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (root_dir / "manuscript" / "chapters" / "index.json").write_text(
                json.dumps({"section_count": 0, "chapter_count": 0, "sections": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (root_dir / "manuscript" / "consolidated" / "index.json").write_text(
                json.dumps({"section_count": 0, "chapter_count": 0, "sections": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = validate_repository_state(root_dir=root_dir)

            self.assertTrue(summary["ok"])
            self.assertEqual(summary["error_count"], 0)

    def test_validate_repository_state_allows_missing_consolidated_index_before_first_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            (root_dir / "editorial").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chunks").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "chapters").mkdir(parents=True, exist_ok=True)
            (root_dir / "manuscript" / "consolidated").mkdir(parents=True, exist_ok=True)

            (root_dir / "editorial" / "STYLE_GUIDE.md").write_text("# Style Guide\n", encoding="utf-8")
            (root_dir / "editorial" / "GLOSSARY.md").write_text("# Glossary\n", encoding="utf-8")
            (root_dir / "editorial" / "DECISIONS.md").write_text("# Editorial Decisions\n", encoding="utf-8")
            (root_dir / "manuscript" / "chunks" / "index.json").write_text(
                json.dumps({"chunk_count": 1, "chunks": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (root_dir / "manuscript" / "chapters" / "index.json").write_text(
                json.dumps({"section_count": 1, "chapter_count": 1, "sections": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = validate_repository_state(root_dir=root_dir)

            self.assertTrue(summary["ok"])
            self.assertEqual(summary["error_count"], 0)
