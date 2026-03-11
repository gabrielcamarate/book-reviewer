from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.adapter_fixtures import generate_adapter_contract_fixtures
from editorial_core.job_log import append_job_log


class AdapterFixturesTest(unittest.TestCase):
    def test_generate_adapter_contract_fixtures_writes_deterministic_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chunks_dir = temp_path / "manuscript" / "chunks"
            chapters_dir = temp_path / "manuscript" / "chapters"
            consolidated_dir = temp_path / "manuscript" / "consolidated"
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            jobs_dir = temp_path / "reports" / "jobs"
            fixtures_dir = temp_path / "fixtures" / "bot-contracts"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            chapters_dir.mkdir(parents=True, exist_ok=True)
            consolidated_dir.mkdir(parents=True, exist_ok=True)
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)
            jobs_dir.mkdir(parents=True, exist_ok=True)

            (chunks_dir / "index.json").write_text(
                json.dumps(
                    {
                        "chunk_count": 1,
                        "chunks": [
                            {
                                "id": "chapter-0001-conexao-dimensional-chunk-0001",
                                "section_id": "chapter-0001-conexao-dimensional",
                                "section_title": "Capítulo 1: Conexão Dimensional.",
                                "review_status": "pending_review",
                                "chunk_order": 1,
                                "file": "chapter-0001-conexao-dimensional-chunk-0001.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chunks_dir / "chapter-0001-conexao-dimensional-chunk-0001.json").write_text(
                json.dumps(
                    {
                        "id": "chapter-0001-conexao-dimensional-chunk-0001",
                        "section_id": "chapter-0001-conexao-dimensional",
                        "section_title": "Capítulo 1: Conexão Dimensional.",
                        "paragraph_ids": ["chapter-0001-conexao-dimensional-p-0001"],
                        "base_text": "Trecho principal.",
                        "previous_context": [],
                        "next_context": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (chapters_dir / "index.json").write_text(
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
                                "review_status": "mixed",
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
                                "text": "Trecho principal.",
                                "review_status": "pending_review",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            append_job_log(
                jobs_dir=jobs_dir,
                job_type="copyedit",
                status="succeeded",
                target_id="chapter-0001-conexao-dimensional-chunk-0001",
                details={"suggestion_count": 2},
            )

            summary = generate_adapter_contract_fixtures(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                jobs_dir=jobs_dir,
                output_dir=fixtures_dir,
            )

            queue_fixture = json.loads((fixtures_dir / "queue-summary.json").read_text(encoding="utf-8"))
            chunk_fixture = json.loads((fixtures_dir / "chunk-summary.json").read_text(encoding="utf-8"))
            job_fixture = json.loads((fixtures_dir / "job-summary.json").read_text(encoding="utf-8"))
            export_fixture = json.loads((fixtures_dir / "export-readiness.json").read_text(encoding="utf-8"))

            self.assertEqual(summary["fixture_count"], 4)
            self.assertEqual(queue_fixture["summary"]["total_chunks"], 1)
            self.assertEqual(chunk_fixture["chunk_id"], "chapter-0001-conexao-dimensional-chunk-0001")
            self.assertEqual(job_fixture["job_type"], "copyedit")
            self.assertIn("pt-BR", export_fixture)
            self.assertIn("es", export_fixture)
