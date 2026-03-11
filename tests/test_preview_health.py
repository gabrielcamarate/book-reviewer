from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from editorial_core.preview_health import (
    build_preview_diagnostics_payload,
    build_preview_health_payload,
)
from review_web.server import build_handler


class PreviewHealthTest(unittest.TestCase):
    def test_build_preview_health_payload_is_minimal_and_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = build_preview_health_payload(root_dir=Path(temp_dir))

            self.assertEqual(payload["status"], "degraded")
            self.assertFalse(payload["repository_ok"])
            self.assertGreater(payload["blocking_count"], 0)
            self.assertIn("diagnostics_path", payload)
            self.assertNotIn("errors", payload)
            self.assertNotIn("blocking_findings", payload)

    def test_build_preview_diagnostics_payload_exposes_doctor_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = build_preview_diagnostics_payload(root_dir=Path(temp_dir))

            self.assertFalse(payload["ok"])
            self.assertIn("blocking_findings", payload)
            self.assertIn("advisory_findings", payload)

    def test_build_handler_wires_preview_health_and_diagnostics_loaders(self) -> None:
        handler = build_handler(
            lambda: {"summary": {}, "chapters": [], "recent_chunks": [], "consistency_report": {"finding_types": [], "finding_count": 0}, "deliverables": [], "recent_decisions": [], "recent_jobs": [], "export_readiness": {}, "deliverable_readiness_report": {}},
            lambda chapter_id: {"chapter": {"id": chapter_id, "title": chapter_id}, "progress": {}, "chunks": []},
            lambda chunk_id: {"chunk": {"id": chunk_id}, "copyedit_review": None, "approval": None, "style_review": None, "style_approval": None, "translation_review": None, "consolidated_paragraphs": [], "translation_comparison": [], "translation_eligibility": {"eligible": False, "reason": ""}},
            lambda finding_type: {"finding_type": finding_type, "finding_count": 0, "findings": [], "report_label": "ptbr"},
            lambda: {"decision_count": 0, "decisions": []},
            lambda: {"entry_count": 0, "sections": []},
            lambda: {"character_count": 0, "characters": []},
            lambda: {"organization_count": 0, "concept_count": 0, "organizations": [], "concepts": []},
            lambda query: {"query": query, "result_count": 0, "chunk_matches": [], "chapter_matches": [], "glossary_matches": [], "decision_matches": []},
            lambda: {"summary": {}, "items": []},
            lambda chunk_id: {},
            lambda chunk_id: {},
            lambda chunk_id, indexes: {},
            lambda chunk_id, indexes: {},
            lambda: {},
            lambda: {},
            lambda chunk_id: {},
            lambda language: {},
            lambda: {},
            lambda title, rationale, scope: {},
            lambda entry_title, preferred_form, aliases_text: {},
            lambda: {},
            lambda: {},
            lambda entry_title, preferred_form, aliases_text: {},
            lambda entry_title, preferred_form, aliases_text, expanded_form: {},
            lambda: {"status": "ok", "repository_ok": True, "blocking_count": 0, "advisory_count": 0, "diagnostics_path": "/diagnostics"},
            lambda: {"ok": True, "blocking_count": 0, "advisory_count": 0, "blocking_findings": [], "advisory_findings": []},
            None,
        )

        self.assertEqual(handler.preview_health_loader()["status"], "ok")
        self.assertTrue(handler.preview_diagnostics_loader()["ok"])
