from __future__ import annotations

import tempfile
from io import BytesIO
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
            lambda: {"has_actionable_chunk": False, "summary": {}},
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

    def test_handler_serves_simple_home_at_root_and_dashboard_at_advanced(self) -> None:
        handler = build_handler(
            lambda: {
                "summary": {"pending_chunk_count": 0, "section_count": 0, "copyedit_review_count": 0, "translation_review_count": 0, "deliverable_count": 0, "decision_count": 0, "job_count": 0, "completed_chapter_count": 0, "actionable_chapter_count": 0},
                "chapters": [],
                "recent_chunks": [],
                "consistency_report": {"finding_types": [], "finding_count": 0},
                "deliverables": [],
                "recent_decisions": [],
                "recent_jobs": [],
                "export_readiness": {"pt-BR": {"eligible": True, "reason": ""}, "es": {"eligible": False, "reason": "bloqueado"}},
                "deliverable_readiness_report": {},
            },
            lambda: {
                "has_actionable_chunk": True,
                "chunk": {"id": "chapter-0001-conexao-dimensional-chunk-0001"},
                "orientation": {
                    "current_chapter_title": "Capítulo 1: Conexão Dimensional.",
                    "remaining_chapter_count": 0,
                    "current_chunk_position": 1,
                    "chapter_chunk_count": 1,
                    "remaining_actionable_chunk_count": 0,
                    "queue_status": "awaiting_approval",
                },
                "original_text": "Trecho principal.",
                "revised_text": "Trecho principal revisado.",
                "review_available": True,
            },
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

        def make_request(path: str) -> tuple[int, str]:
            request = object.__new__(handler)
            request.path = path
            request.headers = {}
            request.client_address = ("127.0.0.1", 54321)
            request.command = "GET"
            request.request_version = "HTTP/1.1"
            request.server_version = "TestServer"
            request.sys_version = ""
            request.wfile = BytesIO()
            request.rfile = BytesIO()
            response: dict[str, int] = {}

            def send_response(code: int, message: str | None = None) -> None:
                response["status"] = code

            request.send_response = send_response
            request.send_header = lambda key, value: None
            request.end_headers = lambda: None
            request.send_error = lambda code, message=None: response.setdefault("status", code)
            request.do_GET()
            return response["status"], request.wfile.getvalue().decode("utf-8")

        root_status, root_payload = make_request("/")
        self.assertEqual(root_status, 200)
        self.assertIn("Revisar PT-BR", root_payload)
        self.assertIn("href=\"/advanced\"", root_payload)

        advanced_status, advanced_payload = make_request("/advanced")
        self.assertEqual(advanced_status, 200)
        self.assertIn("Painel de Revisão Editorial", advanced_payload)
        self.assertIn("Revisão Avançada", advanced_payload)

    def test_handler_serves_simple_home_json_contract(self) -> None:
        handler = build_handler(
            lambda: {
                "summary": {"pending_chunk_count": 0, "section_count": 0, "copyedit_review_count": 0, "translation_review_count": 0, "deliverable_count": 0, "decision_count": 0, "job_count": 0, "completed_chapter_count": 0, "actionable_chapter_count": 0},
                "chapters": [],
                "recent_chunks": [],
                "consistency_report": {"finding_types": [], "finding_count": 0},
                "deliverables": [],
                "recent_decisions": [],
                "recent_jobs": [],
                "export_readiness": {"pt-BR": {"eligible": True, "reason": ""}, "es": {"eligible": False, "reason": "bloqueado"}},
                "deliverable_readiness_report": {},
            },
            lambda: {
                "has_actionable_chunk": True,
                "chunk": {"id": "chapter-0001-conexao-dimensional-chunk-0001"},
                "orientation": {
                    "current_chapter_title": "Capítulo 1: Conexão Dimensional.",
                    "remaining_chapter_count": 4,
                    "current_chunk_position": 1,
                    "chapter_chunk_count": 7,
                    "remaining_actionable_chunk_count": 31,
                    "queue_status": "pending_copyedit",
                },
                "original_text": "Trecho principal.",
                "revised_text": "",
                "review_available": False,
                "changes": [],
            },
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

        request = object.__new__(handler)
        request.path = "/api/simple-home"
        request.headers = {}
        request.client_address = ("127.0.0.1", 54321)
        request.command = "GET"
        request.request_version = "HTTP/1.1"
        request.server_version = "TestServer"
        request.sys_version = ""
        request.wfile = BytesIO()
        request.rfile = BytesIO()
        response: dict[str, int] = {}

        def send_response(code: int, message: str | None = None) -> None:
            response["status"] = code

        request.send_response = send_response
        request.send_header = lambda key, value: None
        request.end_headers = lambda: None
        request.send_error = lambda code, message=None: response.setdefault("status", code)

        request.do_GET()

        self.assertEqual(response["status"], 200)
        payload = request.wfile.getvalue().decode("utf-8")
        self.assertIn('"has_actionable_chunk": true', payload)
        self.assertIn('"queue_status": "pending_copyedit"', payload)

    def test_handler_runs_simple_home_copyedit_action(self) -> None:
        copyedit_calls: list[str] = []

        handler = build_handler(
            lambda: {
                "summary": {"pending_chunk_count": 0, "section_count": 0, "copyedit_review_count": 0, "translation_review_count": 0, "deliverable_count": 0, "decision_count": 0, "job_count": 0, "completed_chapter_count": 0, "actionable_chapter_count": 0},
                "chapters": [],
                "recent_chunks": [],
                "consistency_report": {"finding_types": [], "finding_count": 0},
                "deliverables": [],
                "recent_decisions": [],
                "recent_jobs": [],
                "export_readiness": {"pt-BR": {"eligible": True, "reason": ""}, "es": {"eligible": False, "reason": "bloqueado"}},
                "deliverable_readiness_report": {},
            },
            lambda: {
                "has_actionable_chunk": True,
                "chunk": {"id": "chapter-0001-conexao-dimensional-chunk-0001"},
                "orientation": {"queue_status": "pending_copyedit"},
                "original_text": "Trecho principal.",
                "revised_text": "",
                "review_available": False,
                "changes": [],
            },
            lambda chapter_id: {"chapter": {"id": chapter_id, "title": chapter_id}, "progress": {}, "chunks": []},
            lambda chunk_id: {"chunk": {"id": chunk_id}, "copyedit_review": None, "approval": None, "style_review": None, "style_approval": None, "translation_review": None, "consolidated_paragraphs": [], "translation_comparison": [], "translation_eligibility": {"eligible": False, "reason": ""}},
            lambda finding_type: {"finding_type": finding_type, "finding_count": 0, "findings": [], "report_label": "ptbr"},
            lambda: {"decision_count": 0, "decisions": []},
            lambda: {"entry_count": 0, "sections": []},
            lambda: {"character_count": 0, "characters": []},
            lambda: {"organization_count": 0, "concept_count": 0, "organizations": [], "concepts": []},
            lambda query: {"query": query, "result_count": 0, "chunk_matches": [], "chapter_matches": [], "glossary_matches": [], "decision_matches": []},
            lambda: {"summary": {}, "items": []},
            lambda chunk_id: copyedit_calls.append(chunk_id) or {"chunk_id": chunk_id},
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

        request = object.__new__(handler)
        request.path = "/api/simple-home/review"
        request.headers = {"Content-Length": "0"}
        request.client_address = ("127.0.0.1", 54321)
        request.command = "POST"
        request.request_version = "HTTP/1.1"
        request.server_version = "TestServer"
        request.sys_version = ""
        request.wfile = BytesIO()
        request.rfile = BytesIO(b"")
        response: dict[str, int] = {}

        def send_response(code: int, message: str | None = None) -> None:
            response["status"] = code

        request.send_response = send_response
        request.send_header = lambda key, value: None
        request.end_headers = lambda: None
        request.send_error = lambda code, message=None: response.setdefault("status", code)

        request.do_POST()

        self.assertEqual(response["status"], 200)
        self.assertEqual(copyedit_calls, ["chapter-0001-conexao-dimensional-chunk-0001"])

    def test_handler_runs_simple_home_accept_action_with_all_suggestions(self) -> None:
        approval_calls: list[tuple[str, list[int] | None]] = []

        handler = build_handler(
            lambda: {
                "summary": {"pending_chunk_count": 0, "section_count": 0, "copyedit_review_count": 0, "translation_review_count": 0, "deliverable_count": 0, "decision_count": 0, "job_count": 0, "completed_chapter_count": 0, "actionable_chapter_count": 0},
                "chapters": [],
                "recent_chunks": [],
                "consistency_report": {"finding_types": [], "finding_count": 0},
                "deliverables": [],
                "recent_decisions": [],
                "recent_jobs": [],
                "export_readiness": {"pt-BR": {"eligible": True, "reason": ""}, "es": {"eligible": False, "reason": "bloqueado"}},
                "deliverable_readiness_report": {},
            },
            lambda: {
                "has_actionable_chunk": True,
                "chunk": {"id": "chapter-0001-conexao-dimensional-chunk-0001"},
                "orientation": {"queue_status": "awaiting_copyedit_approval"},
                "original_text": "Trecho principal.",
                "revised_text": "Trecho revisado.",
                "review_available": True,
                "changes": [{"id": "c1"}],
            },
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
            lambda chunk_id, indexes: approval_calls.append((chunk_id, indexes)) or {"chunk_id": chunk_id},
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

        request = object.__new__(handler)
        request.path = "/api/simple-home/accept"
        request.headers = {"Content-Length": "0"}
        request.client_address = ("127.0.0.1", 54321)
        request.command = "POST"
        request.request_version = "HTTP/1.1"
        request.server_version = "TestServer"
        request.sys_version = ""
        request.wfile = BytesIO()
        request.rfile = BytesIO(b"")
        response: dict[str, int] = {}

        def send_response(code: int, message: str | None = None) -> None:
            response["status"] = code

        request.send_response = send_response
        request.send_header = lambda key, value: None
        request.end_headers = lambda: None
        request.send_error = lambda code, message=None: response.setdefault("status", code)

        request.do_POST()

        self.assertEqual(response["status"], 200)
        self.assertEqual(
            approval_calls,
            [("chapter-0001-conexao-dimensional-chunk-0001", None)],
        )
