from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from editorial_core.job_log import append_job_log, read_recent_job_logs


class JobLogTest(unittest.TestCase):
    def test_append_job_log_persists_recent_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir) / "reports" / "jobs"

            append_job_log(
                jobs_dir=jobs_dir,
                job_type="copyedit",
                status="succeeded",
                target_id="chapter-0001-conexao-dimensional-chunk-0001",
                details={"suggestion_count": 2},
            )
            append_job_log(
                jobs_dir=jobs_dir,
                job_type="translation-es",
                status="failed",
                target_id="chapter-0001-conexao-dimensional-chunk-0002",
                details={"error": "chunk not ready"},
            )

            entries = read_recent_job_logs(jobs_dir=jobs_dir)

            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["job_type"], "translation-es")
            self.assertEqual(entries[0]["status"], "failed")
            self.assertEqual(entries[1]["details"]["suggestion_count"], 2)

    def test_append_job_log_does_not_overwrite_same_second_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir) / "reports" / "jobs"

            append_job_log(
                jobs_dir=jobs_dir,
                job_type="copyedit",
                status="succeeded",
                target_id="chunk-0001",
                details={"order": 1},
            )
            append_job_log(
                jobs_dir=jobs_dir,
                job_type="copyedit",
                status="succeeded",
                target_id="chunk-0002",
                details={"order": 2},
            )

            entries = read_recent_job_logs(jobs_dir=jobs_dir)

            self.assertEqual(len(entries), 2)
            self.assertEqual({entry["target_id"] for entry in entries}, {"chunk-0001", "chunk-0002"})
