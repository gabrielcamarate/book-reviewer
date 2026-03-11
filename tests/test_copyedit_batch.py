from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.copyedit_batch import run_copyedit_batch


def _write_chunk_fixture(chunks_dir: Path, chunk_ids: list[str], review_statuses: list[str]) -> None:
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
                        "review_status": review_statuses[index],
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
        (chunks_dir / f"{chunk_id}.json").write_text(
            json.dumps(
                {
                    "id": chunk_id,
                    "section_id": "chapter-0001-conexao-dimensional",
                    "section_title": "Capítulo 1: Conexão Dimensional.",
                    "chunk_order": index + 1,
                    "review_status": review_statuses[index],
                    "paragraph_ids": [f"chapter-0001-conexao-dimensional-p-{index + 1:04d}"],
                    "source_start_index": 100 + index,
                    "source_end_index": 100 + index,
                    "paragraph_count": 1,
                    "base_text": f"Parágrafo do {chunk_id}.",
                    "previous_context": [],
                    "next_context": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


class CopyeditBatchTest(unittest.TestCase):
    def test_run_copyedit_batch_consumes_queue_and_persists_individual_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            reviews_dir = temp_path / "reviews" / "ptbr"
            jobs_dir = temp_path / "reports" / "jobs"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            chunk_ids = [
                "chapter-0001-conexao-dimensional-chunk-0001",
                "chapter-0001-conexao-dimensional-chunk-0002",
                "chapter-0001-conexao-dimensional-chunk-0003",
            ]
            _write_chunk_fixture(chunks_dir, chunk_ids, ["pending_review", "pending_review", "pending_review"])
            (reviews_dir / f"{chunk_ids[1]}.copyedit.json").write_text(
                json.dumps({"status": "proposed"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            processed: list[str] = []

            def fake_runner(*, prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
                for chunk_id in chunk_ids:
                    if chunk_id in prompt:
                        processed.append(chunk_id)
                        break
                return {
                    "suggestions": [
                        {
                            "original": "texto",
                            "suggested": "texto revisado",
                            "change_type": "grammar",
                            "reason": "Ajuste.",
                            "confidence": 0.8,
                        }
                    ]
                }

            summary = run_copyedit_batch(
                chunks_dir=chunks_dir,
                reviews_dir=reviews_dir,
                jobs_dir=jobs_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=fake_runner,
                max_chunks=2,
            )

            self.assertEqual(summary["selected_chunk_ids"], [chunk_ids[0], chunk_ids[2]])
            self.assertEqual(summary["processed_count"], 2)
            self.assertEqual(summary["failed_count"], 0)
            self.assertEqual(processed, [chunk_ids[0], chunk_ids[2]])
            self.assertTrue((reviews_dir / f"{chunk_ids[0]}.copyedit.json").exists())
            self.assertTrue((reviews_dir / f"{chunk_ids[2]}.copyedit.json").exists())
            self.assertEqual(len(list(jobs_dir.glob("*.json"))), 3)

    def test_run_copyedit_batch_stops_cleanly_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "chunks"
            reviews_dir = temp_path / "reviews" / "ptbr"
            jobs_dir = temp_path / "reports" / "jobs"
            style_guide_path = temp_path / "editorial" / "STYLE_GUIDE.md"
            glossary_path = temp_path / "editorial" / "GLOSSARY.md"
            decisions_path = temp_path / "editorial" / "DECISIONS.md"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            reviews_dir.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)
            style_guide_path.parent.mkdir(parents=True, exist_ok=True)

            chunk_ids = [
                "chapter-0001-conexao-dimensional-chunk-0001",
                "chapter-0001-conexao-dimensional-chunk-0002",
                "chapter-0001-conexao-dimensional-chunk-0003",
            ]
            _write_chunk_fixture(chunks_dir, chunk_ids, ["pending_review", "pending_review", "pending_review"])
            style_guide_path.write_text("# Style Guide\n", encoding="utf-8")
            glossary_path.write_text("# Glossary\n", encoding="utf-8")
            decisions_path.write_text("# Editorial Decisions\n", encoding="utf-8")

            def fake_runner(*, prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
                if chunk_ids[1] in prompt:
                    raise RuntimeError("runner failed for chunk 2")
                return {
                    "suggestions": [
                        {
                            "original": "texto",
                            "suggested": "texto revisado",
                            "change_type": "grammar",
                            "reason": "Ajuste.",
                            "confidence": 0.8,
                        }
                    ]
                }

            summary = run_copyedit_batch(
                chunks_dir=chunks_dir,
                reviews_dir=reviews_dir,
                jobs_dir=jobs_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=fake_runner,
            )

            self.assertEqual(summary["selected_chunk_ids"], chunk_ids)
            self.assertEqual(summary["processed_count"], 1)
            self.assertEqual(summary["failed_count"], 1)
            self.assertTrue(summary["stopped_early"])
            self.assertEqual(summary["failures"][0]["chunk_id"], chunk_ids[1])
            self.assertTrue((reviews_dir / f"{chunk_ids[0]}.copyedit.json").exists())
            self.assertFalse((reviews_dir / f"{chunk_ids[1]}.copyedit.json").exists())
            self.assertFalse((reviews_dir / f"{chunk_ids[2]}.copyedit.json").exists())
