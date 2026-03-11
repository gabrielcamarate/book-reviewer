from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.translation_batch import run_translation_es_batch


def _write_translation_fixture(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    chunk_ids: list[str],
    paragraph_statuses: list[str],
) -> None:
    (chunks_dir / "index.json").write_text(
        json.dumps(
            {
                "chunk_count": len(chunk_ids),
                "chunks": [
                    {
                        "id": chunk_id,
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "chunk_order": index + 1,
                        "review_status": "pending_review",
                        "paragraph_count": 1,
                        "source_start_index": 100 + index,
                        "source_end_index": 100 + index,
                        "file": f"{chunk_id}.json",
                    }
                    for index, chunk_id in enumerate(chunk_ids)
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for index, chunk_id in enumerate(chunk_ids):
        paragraph_id = f"chapter-0001-conexao-dimensional-p-{index + 1:04d}"
        (chunks_dir / f"{chunk_id}.json").write_text(
            json.dumps(
                {
                    "id": chunk_id,
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": index + 1,
                    "review_status": "pending_review",
                    "paragraph_ids": [paragraph_id],
                    "source_start_index": 100 + index,
                    "source_end_index": 100 + index,
                    "paragraph_count": 1,
                    "base_text": f"Parágrafo-base {index + 1}.",
                    "previous_context": [],
                    "next_context": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    section_payload = {
        "id": "chapter-0001-conexao-dimensional",
        "title": "Capítulo 1: Conexão Dimensional.",
        "paragraphs": [
            {
                "id": f"chapter-0001-conexao-dimensional-p-{index + 1:04d}",
                "source_index": 100 + index,
                "source_text": f"Texto original {index + 1}.",
                "text": f"Texto consolidado {index + 1}.",
                "review_status": paragraph_statuses[index],
                "applied_reviews": [],
            }
            for index in range(len(chunk_ids))
        ],
    }
    (chapters_dir / "chapter-0001-conexao-dimensional.json").write_text(
        json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (consolidated_dir / "chapter-0001-conexao-dimensional.json").write_text(
        json.dumps(section_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class TranslationBatchTest(unittest.TestCase):
    def test_run_translation_es_batch_skips_ineligible_and_already_translated_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
            reviews_dir = temp_path / "reviews" / "es"
            jobs_dir = temp_path / "reports" / "jobs"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            chunk_ids = [
                "chapter-0001-conexao-dimensional-chunk-0001",
                "chapter-0001-conexao-dimensional-chunk-0002",
                "chapter-0001-conexao-dimensional-chunk-0003",
            ]
            _write_translation_fixture(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                chunk_ids=chunk_ids,
                paragraph_statuses=["pending_review", "approved", "approved_reference"],
            )
            (reviews_dir / f"{chunk_ids[1]}.translation-es.json").write_text(
                json.dumps({"translations": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            summary = run_translation_es_batch(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_dir,
                jobs_dir=jobs_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=lambda **_: {
                    "translations": [
                        {
                            "paragraph_id": "chapter-0001-conexao-dimensional-p-0003",
                            "translated_text": "Texto traducido 3.",
                            "rationale": "Mantém o registro.",
                            "confidence": 0.88,
                        }
                    ]
                },
            )

            self.assertEqual(summary["selected_chunk_ids"], [chunk_ids[2]])
            self.assertEqual(summary["processed_count"], 1)
            self.assertEqual(summary["skipped_count"], 2)
            self.assertEqual(summary["skipped"][0]["reason"], "not_ready")
            self.assertEqual(summary["skipped"][1]["reason"], "already_translated")
            self.assertTrue((reviews_dir / f"{chunk_ids[2]}.translation-es.json").exists())

    def test_run_translation_es_batch_is_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            chapters_dir = temp_path / "chapters"
            consolidated_dir = temp_path / "consolidated"
            reviews_dir = temp_path / "reviews" / "es"
            jobs_dir = temp_path / "reports" / "jobs"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            chunk_ids = [
                "chapter-0001-conexao-dimensional-chunk-0001",
                "chapter-0001-conexao-dimensional-chunk-0002",
            ]
            _write_translation_fixture(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                chunk_ids=chunk_ids,
                paragraph_statuses=["approved", "approved_reference"],
            )
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            first_summary = run_translation_es_batch(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_dir,
                jobs_dir=jobs_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=lambda **_: {
                    "translations": [
                        {
                            "paragraph_id": "chapter-0001-conexao-dimensional-p-0001",
                            "translated_text": "Texto traducido 1.",
                            "rationale": "Mantém o registro.",
                            "confidence": 0.9,
                        }
                    ]
                },
                max_chunks=1,
            )
            second_summary = run_translation_es_batch(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_dir,
                jobs_dir=jobs_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=lambda **_: {
                    "translations": [
                        {
                            "paragraph_id": "chapter-0001-conexao-dimensional-p-0002",
                            "translated_text": "Texto traducido 2.",
                            "rationale": "Mantém o registro.",
                            "confidence": 0.91,
                        }
                    ]
                },
            )

            self.assertEqual(first_summary["selected_chunk_ids"], [chunk_ids[0]])
            self.assertEqual(second_summary["selected_chunk_ids"], [chunk_ids[1]])
            self.assertTrue((reviews_dir / f"{chunk_ids[0]}.translation-es.json").exists())
            self.assertTrue((reviews_dir / f"{chunk_ids[1]}.translation-es.json").exists())
