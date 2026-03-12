from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from editorial_core.review_rejection import reject_review_proposal


class ReviewRejectionTest(unittest.TestCase):
    def test_reject_review_proposal_persists_reason_and_removes_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            reviews_ptbr_dir = temp_path / "reviews" / "ptbr"
            reviews_es_dir = temp_path / "reviews" / "es"
            reviews_ptbr_dir.mkdir(parents=True, exist_ok=True)
            reviews_es_dir.mkdir(parents=True, exist_ok=True)

            chunk_id = "chapter-0001-conexao-dimensional-chunk-0001"
            review_path = reviews_ptbr_dir / f"{chunk_id}.copyedit.json"
            preview_path = reviews_es_dir / f"{chunk_id}.translation-es.preview.json"

            review_path.write_text(
                json.dumps({"chunk_id": chunk_id, "status": "proposed"}, ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            preview_path.write_text(
                json.dumps({"chunk_id": chunk_id, "preview": True}, ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )

            result = reject_review_proposal(
                chunk_id=chunk_id,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                reason="Mudou demais a voz do autor.",
            )

            rejection_path = reviews_ptbr_dir / f"{chunk_id}.rejection.json"
            payload = json.loads(rejection_path.read_text(encoding="utf-8"))

            self.assertFalse(review_path.exists())
            self.assertFalse(preview_path.exists())
            self.assertTrue(rejection_path.exists())
            self.assertTrue(result["removed_copyedit_review"])
            self.assertTrue(result["removed_translation_preview"])
            self.assertEqual(payload["status"], "rejected")
            self.assertEqual(payload["reason"], "Mudou demais a voz do autor.")

