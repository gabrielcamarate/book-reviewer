from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.segment_manuscript import (
    segment_extracted_manuscript,
    segment_paragraphs,
)


class SegmentManuscriptTest(unittest.TestCase):
    def test_segment_paragraphs_creates_stable_sections_and_paragraph_ids(self) -> None:
        paragraphs = [
            {"index": 1, "text": "", "is_empty": True},
            {"index": 2, "text": "Cover line", "is_empty": False},
            {"index": 3, "text": "Prefácio", "is_empty": False},
            {"index": 4, "text": "Opening reflection.", "is_empty": False},
            {"index": 5, "text": "Capítulo 1: Conexão Dimensional.", "is_empty": False},
            {"index": 6, "text": "Chapter one body.", "is_empty": False},
            {"index": 7, "text": "Capítulo II", "is_empty": False},
            {"index": 8, "text": "Supremo Poder Anônimo", "is_empty": False},
            {"index": 9, "text": "Chapter two body.", "is_empty": False},
            {"index": 10, "text": "Epílogo", "is_empty": False},
            {"index": 11, "text": "Final lines.", "is_empty": False},
        ]

        segmented = segment_paragraphs(paragraphs)

        section_ids = [section["id"] for section in segmented["sections"]]
        self.assertEqual(
            section_ids,
            [
                "frontmatter-0001-opening",
                "frontmatter-0002-prefacio",
                "chapter-0001-conexao-dimensional",
                "chapter-0002-supremo-poder-anonimo",
                "backmatter-0001-epilogo",
            ],
        )
        self.assertEqual(segmented["section_count"], 5)
        self.assertEqual(segmented["chapter_count"], 2)
        self.assertEqual(segmented["sections"][2]["title"], "Capítulo 1: Conexão Dimensional.")
        self.assertEqual(segmented["sections"][3]["title"], "Capítulo II — Supremo Poder Anônimo")
        self.assertEqual(
            segmented["sections"][3]["paragraphs"][0]["id"],
            "chapter-0002-supremo-poder-anonimo-p-0001",
        )
        self.assertEqual(segmented["sections"][3]["paragraphs"][0]["source_index"], 9)

    def test_segment_extracted_manuscript_persists_index_and_section_files(self) -> None:
        paragraphs = [
            {"index": 1, "text": "Prefácio", "is_empty": False},
            {"index": 2, "text": "Opening reflection.", "is_empty": False},
            {"index": 3, "text": "Capítulo 1: Conexão Dimensional.", "is_empty": False},
            {"index": 4, "text": "Body.", "is_empty": False},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extracted_dir = temp_path / "extracted"
            output_dir = temp_path / "chapters"
            extracted_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            (extracted_dir / "paragraphs.json").write_text(
                json.dumps(paragraphs, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            stale_path = output_dir / "chapter-9999-stale.json"
            stale_path.write_text("{}", encoding="utf-8")

            summary = segment_extracted_manuscript(extracted_dir, output_dir)

            self.assertEqual(summary["section_count"], 2)
            self.assertEqual(summary["chapter_count"], 1)

            index_payload = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
            chapter_payload = json.loads(
                (output_dir / "chapter-0001-conexao-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(index_payload["sections"][0]["id"], "frontmatter-0001-prefacio")
            self.assertEqual(index_payload["sections"][1]["id"], "chapter-0001-conexao-dimensional")
            self.assertEqual(chapter_payload["paragraphs"][0]["text"], "Body.")
            self.assertFalse(stale_path.exists())

    def test_segment_extracted_manuscript_persists_missing_chapter_number_metadata(self) -> None:
        paragraphs = [
            {"index": 1, "text": "Capítulo 1: Conexão Dimensional.", "is_empty": False},
            {"index": 2, "text": "Body one.", "is_empty": False},
            {"index": 3, "text": "Capítulo 4: Guerra Dimensional.", "is_empty": False},
            {"index": 4, "text": "Body four.", "is_empty": False},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extracted_dir = temp_path / "extracted"
            output_dir = temp_path / "chapters"
            extracted_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            (extracted_dir / "paragraphs.json").write_text(
                json.dumps(paragraphs, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            segment_extracted_manuscript(extracted_dir, output_dir)

            index_payload = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
            chapter_payload = json.loads(
                (output_dir / "chapter-0002-guerra-dimensional.json").read_text(encoding="utf-8")
            )

            self.assertEqual(index_payload["chapter_number_sequence"], [1, 4])
            self.assertEqual(index_payload["missing_chapter_numbers"], [2, 3])
            self.assertEqual(index_payload["sections"][0]["declared_chapter_number"], 1)
            self.assertEqual(index_payload["sections"][1]["declared_chapter_number"], 4)
            self.assertEqual(chapter_payload["declared_chapter_number"], 4)

    def test_segment_paragraphs_detects_split_chapter_heading_from_word_export(self) -> None:
        paragraphs = [
            {"index": 1, "text": "Capítulo 1: Conexão Dimensional.", "is_empty": False},
            {"index": 2, "text": "Body one.", "is_empty": False},
            {"index": 3, "text": "C", "is_empty": False},
            {"index": 4, "text": "Apítulo 3: Reset.", "is_empty": False},
            {"index": 5, "text": "Body three.", "is_empty": False},
            {"index": 6, "text": "C", "is_empty": False},
            {"index": 7, "text": "Apítulo 5: eXilados da Terra.", "is_empty": False},
            {"index": 8, "text": "Body five.", "is_empty": False},
        ]

        segmented = segment_paragraphs(paragraphs)

        self.assertEqual(segmented["chapter_count"], 3)
        self.assertEqual(segmented["sections"][1]["title"], "Capítulo 3: Reset.")
        self.assertEqual(segmented["sections"][1]["declared_chapter_number"], 3)
        self.assertEqual(segmented["sections"][2]["title"], "Capítulo 5: eXilados da Terra.")
        self.assertEqual(segmented["sections"][2]["declared_chapter_number"], 5)
