from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote
from typing import Callable

from editorial_core.codex_runner import run_codex_with_schema
from editorial_core.job_log import append_job_log
from editorial_core.repository_validation import validate_repository_state
from review_web.dashboard import (
    build_chapter_detail_state,
    build_characters_state,
    build_chunk_detail_state,
    build_consistency_detail_state,
    build_decisions_state,
    build_dashboard_state,
    build_glossary_state,
    build_queue_state,
    build_search_state,
    build_world_rules_state,
    render_characters_html,
    render_chapter_detail_html,
    render_chunk_detail_html,
    render_consistency_detail_html,
    render_decisions_html,
    render_dashboard_html,
    render_glossary_html,
    render_queue_html,
    render_search_html,
    render_world_rules_html,
)
from review_web.actions import (
    trigger_generate_characters,
    trigger_append_decision,
    trigger_curate_character_entry,
    trigger_curate_glossary_entry,
    trigger_export_docx,
    trigger_generate_world_rules,
    trigger_curate_world_rule_entry,
    trigger_consistency_report,
    trigger_copyedit,
    trigger_deliverable_readiness_report,
    trigger_review_approval,
    trigger_rollback_last_approval,
    trigger_style,
    trigger_style_approval,
    trigger_translation_es,
)

DashboardLoader = Callable[[], dict[str, object]]


def _run_logged_job(
    *,
    jobs_dir: Path,
    job_type: str,
    target_id: str,
    action: Callable[[], dict[str, object]],
) -> dict[str, object]:
    try:
        result = action()
    except Exception as error:
        append_job_log(
            jobs_dir=jobs_dir,
            job_type=job_type,
            status="failed",
            target_id=target_id,
            details={"error": str(error)},
        )
        raise

    append_job_log(
        jobs_dir=jobs_dir,
        job_type=job_type,
        status="succeeded",
        target_id=target_id,
        details=result,
    )
    return result


def _build_loader(
    *,
    chapters_dir: Path,
    chunks_dir: Path,
    consolidated_dir: Path,
    reports_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    deliverables_dir: Path,
    decisions_path: Path,
    jobs_dir: Path,
) -> DashboardLoader:
    def _load() -> dict[str, object]:
        return build_dashboard_state(
            chapters_dir=chapters_dir,
            chunks_dir=chunks_dir,
            consolidated_dir=consolidated_dir,
            reports_dir=reports_dir,
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
            deliverables_dir=deliverables_dir,
            decisions_path=decisions_path,
            jobs_dir=jobs_dir,
        )

    return _load


def _build_search_loader(
    *,
    chunks_dir: Path,
    consolidated_dir: Path,
    glossary_path: Path,
    decisions_path: Path,
) -> Callable[[str], dict[str, object]]:
    def _load(query: str) -> dict[str, object]:
        return build_search_state(
            query=query,
            chunks_dir=chunks_dir,
            consolidated_dir=consolidated_dir,
            glossary_path=glossary_path,
            decisions_path=decisions_path,
        )

    return _load


def _build_queue_loader(
    *,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> Callable[[], dict[str, object]]:
    def _load() -> dict[str, object]:
        return build_queue_state(
            chunks_dir=chunks_dir,
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
        )

    return _load


def _build_chapter_loader(
    *,
    chunks_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> Callable[[str], dict[str, object]]:
    def _load(chapter_id: str) -> dict[str, object]:
        return build_chapter_detail_state(
            chapter_id=chapter_id,
            chunks_dir=chunks_dir,
            consolidated_dir=consolidated_dir,
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
        )

    return _load


def _build_chunk_loader(
    *,
    chunks_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> Callable[[str], dict[str, object]]:
    def _load(chunk_id: str) -> dict[str, object]:
        return build_chunk_detail_state(
            chunk_id=chunk_id,
            chunks_dir=chunks_dir,
            consolidated_dir=consolidated_dir,
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
        )

    return _load


def _build_consistency_loader(
    *,
    reports_dir: Path,
    chunks_dir: Path,
) -> Callable[[str], dict[str, object]]:
    def _load(finding_type: str) -> dict[str, object]:
        return build_consistency_detail_state(
            finding_type=finding_type,
            reports_dir=reports_dir,
            chunks_dir=chunks_dir,
        )

    return _load


def _build_decisions_loader(
    *,
    decisions_path: Path,
) -> Callable[[], dict[str, object]]:
    def _load() -> dict[str, object]:
        return build_decisions_state(decisions_path=decisions_path)

    return _load


def _build_glossary_loader(
    *,
    glossary_path: Path,
) -> Callable[[], dict[str, object]]:
    def _load() -> dict[str, object]:
        return build_glossary_state(glossary_path=glossary_path)

    return _load


def _build_characters_loader(
    *,
    characters_path: Path,
) -> Callable[[], dict[str, object]]:
    def _load() -> dict[str, object]:
        return build_characters_state(characters_path=characters_path)

    return _load


def _build_world_rules_loader(
    *,
    world_rules_path: Path,
) -> Callable[[], dict[str, object]]:
    def _load() -> dict[str, object]:
        return build_world_rules_state(world_rules_path=world_rules_path)

    return _load


def _codex_runner(prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
    return run_codex_with_schema(
        prompt=prompt,
        schema=schema,
        model=model,
        schema_filename="copyedit-schema.json",
        output_filename="copyedit-output.json",
    )


def _build_copyedit_action(
    *,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    jobs_dir: Path,
    model: str,
) -> Callable[[str], dict[str, object]]:
    def _run(chunk_id: str) -> dict[str, object]:
        return _run_logged_job(
            jobs_dir=jobs_dir,
            job_type="copyedit",
            target_id=chunk_id,
            action=lambda: trigger_copyedit(
                chunk_id=chunk_id,
                chunks_dir=chunks_dir,
                reviews_dir=reviews_ptbr_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=_codex_runner,
                model=model,
            ),
        )

    return _run


def _build_style_action(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    jobs_dir: Path,
    model: str,
) -> Callable[[str], dict[str, object]]:
    def _run(chunk_id: str) -> dict[str, object]:
        return _run_logged_job(
            jobs_dir=jobs_dir,
            job_type="style",
            target_id=chunk_id,
            action=lambda: trigger_style(
                chunk_id=chunk_id,
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_ptbr_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=_codex_runner,
                model=model,
            ),
        )

    return _run


def _build_approval_action(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
) -> Callable[[str, list[int] | None], dict[str, object]]:
    def _run(chunk_id: str, approved_suggestion_indexes: list[int] | None) -> dict[str, object]:
        return trigger_review_approval(
            chunk_id=chunk_id,
            chunks_dir=chunks_dir,
            chapters_dir=chapters_dir,
            consolidated_dir=consolidated_dir,
            reviews_dir=reviews_ptbr_dir,
            approved_suggestion_indexes=approved_suggestion_indexes,
        )

    return _run


def _build_style_approval_action(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
) -> Callable[[str, list[int] | None], dict[str, object]]:
    def _run(chunk_id: str, approved_suggestion_indexes: list[int] | None) -> dict[str, object]:
        return trigger_style_approval(
            chunk_id=chunk_id,
            chunks_dir=chunks_dir,
            chapters_dir=chapters_dir,
            consolidated_dir=consolidated_dir,
            reviews_dir=reviews_ptbr_dir,
            approved_suggestion_indexes=approved_suggestion_indexes,
        )

    return _run


def _build_consistency_action(
    *,
    consolidated_dir: Path,
    glossary_path: Path,
    reports_dir: Path,
    jobs_dir: Path,
) -> Callable[[], dict[str, object]]:
    def _run() -> dict[str, object]:
        return _run_logged_job(
            jobs_dir=jobs_dir,
            job_type="consistency",
            target_id="ptbr-consistency-report",
            action=lambda: trigger_consistency_report(
                consolidated_dir=consolidated_dir,
                glossary_path=glossary_path,
                reports_dir=reports_dir,
            ),
        )

    return _run


def _build_deliverable_readiness_action(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    reports_dir: Path,
    jobs_dir: Path,
) -> Callable[[], dict[str, object]]:
    def _run() -> dict[str, object]:
        return _run_logged_job(
            jobs_dir=jobs_dir,
            job_type="deliverable-readiness",
            target_id="bilingual-report",
            action=lambda: trigger_deliverable_readiness_report(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_ptbr_dir=reviews_ptbr_dir,
                reviews_es_dir=reviews_es_dir,
                reports_dir=reports_dir,
            ),
        )

    return _run


def _translation_runner(prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
    return run_codex_with_schema(
        prompt=prompt,
        schema=schema,
        model=model,
        schema_filename="translation-es-schema.json",
        output_filename="translation-es-output.json",
    )


def _build_translation_action(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_es_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    jobs_dir: Path,
    model: str,
) -> Callable[[str], dict[str, object]]:
    def _run(chunk_id: str) -> dict[str, object]:
        return _run_logged_job(
            jobs_dir=jobs_dir,
            job_type="translation-es",
            target_id=chunk_id,
            action=lambda: trigger_translation_es(
                chunk_id=chunk_id,
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_es_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=_translation_runner,
                model=model,
            ),
        )

    return _run


def _build_export_action(
    *,
    template_path: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_es_dir: Path,
    deliverables_dir: Path,
    jobs_dir: Path,
) -> Callable[[str], dict[str, object]]:
    def _run(language: str) -> dict[str, object]:
        return _run_logged_job(
            jobs_dir=jobs_dir,
            job_type="export",
            target_id=language,
            action=lambda: trigger_export_docx(
                template_path=template_path,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                translations_dir=reviews_es_dir,
                deliverables_dir=deliverables_dir,
                language=language,
            ),
        )

    return _run


def _build_rollback_action(
    *,
    reviews_ptbr_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    jobs_dir: Path,
) -> Callable[[], dict[str, object]]:
    def _run() -> dict[str, object]:
        return _run_logged_job(
            jobs_dir=jobs_dir,
            job_type="rollback",
            target_id="last-approval",
            action=lambda: trigger_rollback_last_approval(
                reviews_dir=reviews_ptbr_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
            ),
        )

    return _run


def _build_decision_action(
    *,
    decisions_path: Path,
) -> Callable[[str, str, str], dict[str, object]]:
    def _run(title: str, rationale: str, scope: str) -> dict[str, object]:
        return trigger_append_decision(
            decisions_path=decisions_path,
            title=title,
            rationale=rationale,
            scope=scope,
        )

    return _run


def _build_glossary_action(
    *,
    glossary_path: Path,
) -> Callable[[str, str, str], dict[str, object]]:
    def _run(entry_title: str, preferred_form: str, aliases_text: str) -> dict[str, object]:
        return trigger_curate_glossary_entry(
            glossary_path=glossary_path,
            entry_title=entry_title,
            preferred_form=preferred_form,
            aliases_text=aliases_text,
        )

    return _run


def _build_characters_action(
    *,
    glossary_path: Path,
    characters_path: Path,
) -> Callable[[], dict[str, object]]:
    def _run() -> dict[str, object]:
        return trigger_generate_characters(
            glossary_path=glossary_path,
            characters_path=characters_path,
        )

    return _run


def _build_character_curation_action(
    *,
    characters_path: Path,
) -> Callable[[str, str, str], dict[str, object]]:
    def _run(entry_title: str, preferred_form: str, aliases_text: str) -> dict[str, object]:
        return trigger_curate_character_entry(
            characters_path=characters_path,
            entry_title=entry_title,
            preferred_form=preferred_form,
            aliases_text=aliases_text,
        )

    return _run


def _build_world_rules_action(
    *,
    glossary_path: Path,
    world_rules_path: Path,
) -> Callable[[], dict[str, object]]:
    def _run() -> dict[str, object]:
        return trigger_generate_world_rules(
            glossary_path=glossary_path,
            world_rules_path=world_rules_path,
        )

    return _run


def _build_world_rule_curation_action(
    *,
    world_rules_path: Path,
) -> Callable[[str, str, str, str], dict[str, object]]:
    def _run(
        entry_title: str,
        preferred_form: str,
        aliases_text: str,
        expanded_form: str,
    ) -> dict[str, object]:
        return trigger_curate_world_rule_entry(
            world_rules_path=world_rules_path,
            entry_title=entry_title,
            preferred_form=preferred_form,
            aliases_text=aliases_text,
            expanded_form=expanded_form,
        )

    return _run


class DashboardHandler(BaseHTTPRequestHandler):
    dashboard_loader: DashboardLoader | None = None
    chapter_loader: Callable[[str], dict[str, object]] | None = None
    chunk_loader: Callable[[str], dict[str, object]] | None = None
    consistency_loader: Callable[[str], dict[str, object]] | None = None
    decisions_loader: Callable[[], dict[str, object]] | None = None
    glossary_loader: Callable[[], dict[str, object]] | None = None
    characters_loader: Callable[[], dict[str, object]] | None = None
    world_rules_loader: Callable[[], dict[str, object]] | None = None
    search_loader: Callable[[str], dict[str, object]] | None = None
    queue_loader: Callable[[], dict[str, object]] | None = None
    copyedit_action: Callable[[str], dict[str, object]] | None = None
    style_action: Callable[[str], dict[str, object]] | None = None
    approval_action: Callable[[str, list[int] | None], dict[str, object]] | None = None
    style_approval_action: Callable[[str, list[int] | None], dict[str, object]] | None = None
    consistency_action: Callable[[], dict[str, object]] | None = None
    deliverable_readiness_action: Callable[[], dict[str, object]] | None = None
    translation_action: Callable[[str], dict[str, object]] | None = None
    export_action: Callable[[str], dict[str, object]] | None = None
    rollback_action: Callable[[], dict[str, object]] | None = None
    decision_action: Callable[[str, str, str], dict[str, object]] | None = None
    glossary_action: Callable[[str, str, str], dict[str, object]] | None = None
    characters_action: Callable[[], dict[str, object]] | None = None
    world_rules_action: Callable[[], dict[str, object]] | None = None
    character_curation_action: Callable[[str, str, str], dict[str, object]] | None = None
    world_rule_curation_action: Callable[[str, str, str, str], dict[str, object]] | None = None

    def do_GET(self) -> None:  # noqa: N802
        if self.dashboard_loader is None:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "dashboard loader not configured")
            return

        if self.path == "/":
            state = self.dashboard_loader()
            payload = render_dashboard_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path.startswith("/search"):
            if self.search_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "search loader not configured")
                return
            raw_query = self.path.partition("?")[2]
            query = parse_qs(raw_query).get("q", [""])[0]
            state = self.search_loader(query)
            payload = render_search_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/queue":
            if self.queue_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "queue loader not configured")
                return
            state = self.queue_loader()
            payload = render_queue_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/api/dashboard":
            state = self.dashboard_loader()
            payload = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path.startswith("/chapters/"):
            if self.chapter_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "chapter loader not configured")
                return
            chapter_id = unquote(self.path.removeprefix("/chapters/"))
            try:
                state = self.chapter_loader(chapter_id)
            except ValueError:
                self.send_error(HTTPStatus.NOT_FOUND, "chapter not found")
                return
            payload = render_chapter_detail_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path.startswith("/chunks/"):
            if self.chunk_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "chunk loader not configured")
                return
            chunk_id = unquote(self.path.removeprefix("/chunks/"))
            try:
                state = self.chunk_loader(chunk_id)
            except ValueError:
                self.send_error(HTTPStatus.NOT_FOUND, "chunk not found")
                return
            payload = render_chunk_detail_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path.startswith("/consistency/"):
            if self.consistency_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "consistency loader not configured")
                return
            finding_type = unquote(self.path.removeprefix("/consistency/"))
            try:
                state = self.consistency_loader(finding_type)
            except ValueError:
                self.send_error(HTTPStatus.NOT_FOUND, "consistency finding type not found")
                return
            payload = render_consistency_detail_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/decisions":
            if self.decisions_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "decisions loader not configured")
                return
            state = self.decisions_loader()
            payload = render_decisions_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/glossary":
            if self.glossary_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "glossary loader not configured")
                return
            state = self.glossary_loader()
            payload = render_glossary_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/characters":
            if self.characters_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "characters loader not configured")
                return
            state = self.characters_loader()
            payload = render_characters_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/world-rules":
            if self.world_rules_loader is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "world rules loader not configured")
                return
            state = self.world_rules_loader()
            payload = render_world_rules_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path.startswith("/chunks/") and self.path.endswith("/copyedit"):
            if self.copyedit_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "copyedit action not configured")
                return
            chunk_id = unquote(self.path.removeprefix("/chunks/").removesuffix("/copyedit"))
            try:
                self.copyedit_action(chunk_id)
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            except RuntimeError as error:
                self.send_error(HTTPStatus.BAD_GATEWAY, str(error))
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/chunks/{chunk_id}")
            self.end_headers()
            return

        if self.path.startswith("/chunks/") and self.path.endswith("/approve-copyedit"):
            if self.approval_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "approval action not configured")
                return
            chunk_id = unquote(self.path.removeprefix("/chunks/").removesuffix("/approve-copyedit"))
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            form_data = parse_qs(raw_body, keep_blank_values=False)
            approved_indexes = [
                int(value)
                for value in form_data.get("approve_index", [])
            ]
            try:
                self.approval_action(
                    chunk_id,
                    approved_indexes or None,
                )
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND, "copyedit review not found")
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/chunks/{chunk_id}")
            self.end_headers()
            return

        if self.path.startswith("/chunks/") and self.path.endswith("/style"):
            if self.style_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "style action not configured")
                return
            chunk_id = unquote(self.path.removeprefix("/chunks/").removesuffix("/style"))
            try:
                self.style_action(chunk_id)
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            except RuntimeError as error:
                self.send_error(HTTPStatus.BAD_GATEWAY, str(error))
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/chunks/{chunk_id}")
            self.end_headers()
            return

        if self.path.startswith("/chunks/") and self.path.endswith("/approve-style"):
            if self.style_approval_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "style approval action not configured")
                return
            chunk_id = unquote(self.path.removeprefix("/chunks/").removesuffix("/approve-style"))
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            form_data = parse_qs(raw_body, keep_blank_values=False)
            approved_indexes = [
                int(value)
                for value in form_data.get("approve_index", [])
            ]
            try:
                self.style_approval_action(
                    chunk_id,
                    approved_indexes or None,
                )
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND, "style review not found")
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/chunks/{chunk_id}")
            self.end_headers()
            return

        if self.path == "/consistency/run":
            if self.consistency_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "consistency action not configured")
                return
            try:
                self.consistency_action()
            except FileNotFoundError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path == "/readiness/run":
            if self.deliverable_readiness_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "deliverable readiness action not configured")
                return
            self.deliverable_readiness_action()
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path.startswith("/chunks/") and self.path.endswith("/translation-es"):
            if self.translation_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "translation action not configured")
                return
            chunk_id = unquote(self.path.removeprefix("/chunks/").removesuffix("/translation-es"))
            try:
                self.translation_action(chunk_id)
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            except RuntimeError as error:
                self.send_error(HTTPStatus.BAD_GATEWAY, str(error))
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/chunks/{chunk_id}")
            self.end_headers()
            return

        if self.path.startswith("/exports/") and self.path.endswith("/run"):
            if self.export_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "export action not configured")
                return
            language = unquote(self.path.removeprefix("/exports/").removesuffix("/run"))
            if language not in {"pt-BR", "es"}:
                self.send_error(HTTPStatus.BAD_REQUEST, "unsupported export language")
                return
            try:
                self.export_action(language)
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            except FileNotFoundError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path == "/approvals/rollback-last":
            if self.rollback_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "rollback action not configured")
                return
            try:
                self.rollback_action()
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            except FileNotFoundError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path == "/decisions":
            if self.decision_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "decision action not configured")
                return
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            form_data = parse_qs(raw_body, keep_blank_values=False)
            title = (form_data.get("title", [""])[0]).strip()
            scope = (form_data.get("scope", ["global"])[0]).strip() or "global"
            rationale = (form_data.get("rationale", [""])[0]).strip()
            if not title or not rationale:
                self.send_error(HTTPStatus.BAD_REQUEST, "title and rationale are required")
                return
            self.decision_action(title, rationale, scope)
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/decisions")
            self.end_headers()
            return

        if self.path == "/glossary":
            if self.glossary_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "glossary action not configured")
                return
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            form_data = parse_qs(raw_body, keep_blank_values=False)
            entry_title = (form_data.get("entry_title", [""])[0]).strip()
            preferred_form = (form_data.get("preferred_form", [""])[0]).strip()
            aliases_text = (form_data.get("aliases_text", [""])[0]).strip()
            if not entry_title or not preferred_form:
                self.send_error(HTTPStatus.BAD_REQUEST, "entry_title and preferred_form are required")
                return
            try:
                self.glossary_action(entry_title, preferred_form, aliases_text)
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/glossary")
            self.end_headers()
            return

        if self.path == "/characters/run":
            if self.characters_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "characters action not configured")
                return
            self.characters_action()
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/characters")
            self.end_headers()
            return

        if self.path == "/characters":
            if self.character_curation_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "character curation action not configured")
                return
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            form_data = parse_qs(raw_body, keep_blank_values=False)
            entry_title = (form_data.get("entry_title", [""])[0]).strip()
            preferred_form = (form_data.get("preferred_form", [""])[0]).strip()
            aliases_text = (form_data.get("aliases_text", [""])[0]).strip()
            if not entry_title or not preferred_form:
                self.send_error(HTTPStatus.BAD_REQUEST, "entry_title and preferred_form are required")
                return
            try:
                self.character_curation_action(entry_title, preferred_form, aliases_text)
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/characters")
            self.end_headers()
            return

        if self.path == "/world-rules/run":
            if self.world_rules_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "world rules action not configured")
                return
            self.world_rules_action()
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/world-rules")
            self.end_headers()
            return

        if self.path == "/world-rules":
            if self.world_rule_curation_action is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "world rule curation action not configured")
                return
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            form_data = parse_qs(raw_body, keep_blank_values=False)
            entry_title = (form_data.get("entry_title", [""])[0]).strip()
            preferred_form = (form_data.get("preferred_form", [""])[0]).strip()
            aliases_text = (form_data.get("aliases_text", [""])[0]).strip()
            expanded_form = (form_data.get("expanded_form", [""])[0]).strip()
            if not entry_title or not preferred_form:
                self.send_error(HTTPStatus.BAD_REQUEST, "entry_title and preferred_form are required")
                return
            try:
                self.world_rule_curation_action(
                    entry_title,
                    preferred_form,
                    aliases_text,
                    expanded_form,
                )
            except ValueError as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/world-rules")
            self.end_headers()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def build_handler(
    dashboard_loader: DashboardLoader,
    chapter_loader: Callable[[str], dict[str, object]],
    chunk_loader: Callable[[str], dict[str, object]],
    consistency_loader: Callable[[str], dict[str, object]],
    decisions_loader: Callable[[], dict[str, object]],
    glossary_loader: Callable[[], dict[str, object]],
    characters_loader: Callable[[], dict[str, object]],
    world_rules_loader: Callable[[], dict[str, object]],
    search_loader: Callable[[str], dict[str, object]],
    queue_loader: Callable[[], dict[str, object]],
    copyedit_action: Callable[[str], dict[str, object]],
    style_action: Callable[[str], dict[str, object]],
    approval_action: Callable[[str, list[int] | None], dict[str, object]],
    style_approval_action: Callable[[str, list[int] | None], dict[str, object]],
    consistency_action: Callable[[], dict[str, object]],
    deliverable_readiness_action: Callable[[], dict[str, object]],
    translation_action: Callable[[str], dict[str, object]],
    export_action: Callable[[str], dict[str, object]],
    rollback_action: Callable[[], dict[str, object]],
    decision_action: Callable[[str, str, str], dict[str, object]],
    glossary_action: Callable[[str, str, str], dict[str, object]],
    characters_action: Callable[[], dict[str, object]],
    world_rules_action: Callable[[], dict[str, object]],
    character_curation_action: Callable[[str, str, str], dict[str, object]],
    world_rule_curation_action: Callable[[str, str, str, str], dict[str, object]],
) -> type[DashboardHandler]:
    class ConfiguredDashboardHandler(DashboardHandler):
        pass

    ConfiguredDashboardHandler.dashboard_loader = staticmethod(dashboard_loader)
    ConfiguredDashboardHandler.chapter_loader = staticmethod(chapter_loader)
    ConfiguredDashboardHandler.chunk_loader = staticmethod(chunk_loader)
    ConfiguredDashboardHandler.consistency_loader = staticmethod(consistency_loader)
    ConfiguredDashboardHandler.decisions_loader = staticmethod(decisions_loader)
    ConfiguredDashboardHandler.glossary_loader = staticmethod(glossary_loader)
    ConfiguredDashboardHandler.characters_loader = staticmethod(characters_loader)
    ConfiguredDashboardHandler.world_rules_loader = staticmethod(world_rules_loader)
    ConfiguredDashboardHandler.search_loader = staticmethod(search_loader)
    ConfiguredDashboardHandler.queue_loader = staticmethod(queue_loader)
    ConfiguredDashboardHandler.copyedit_action = staticmethod(copyedit_action)
    ConfiguredDashboardHandler.style_action = staticmethod(style_action)
    ConfiguredDashboardHandler.approval_action = staticmethod(approval_action)
    ConfiguredDashboardHandler.style_approval_action = staticmethod(style_approval_action)
    ConfiguredDashboardHandler.consistency_action = staticmethod(consistency_action)
    ConfiguredDashboardHandler.deliverable_readiness_action = staticmethod(deliverable_readiness_action)
    ConfiguredDashboardHandler.translation_action = staticmethod(translation_action)
    ConfiguredDashboardHandler.export_action = staticmethod(export_action)
    ConfiguredDashboardHandler.rollback_action = staticmethod(rollback_action)
    ConfiguredDashboardHandler.decision_action = staticmethod(decision_action)
    ConfiguredDashboardHandler.glossary_action = staticmethod(glossary_action)
    ConfiguredDashboardHandler.characters_action = staticmethod(characters_action)
    ConfiguredDashboardHandler.world_rules_action = staticmethod(world_rules_action)
    ConfiguredDashboardHandler.character_curation_action = staticmethod(character_curation_action)
    ConfiguredDashboardHandler.world_rule_curation_action = staticmethod(world_rule_curation_action)
    return ConfiguredDashboardHandler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local-first editorial review web dashboard."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind.")
    parser.add_argument("--chunks-dir", type=Path, default=Path("manuscript/chunks"))
    parser.add_argument("--chapters-dir", type=Path, default=Path("manuscript/chapters"))
    parser.add_argument("--consolidated-dir", type=Path, default=Path("manuscript/consolidated"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--reviews-ptbr-dir", type=Path, default=Path("reviews/ptbr"))
    parser.add_argument("--reviews-es-dir", type=Path, default=Path("reviews/es"))
    parser.add_argument("--deliverables-dir", type=Path, default=Path("deliverables"))
    parser.add_argument("--template", type=Path, default=Path("livro.docx"))
    parser.add_argument("--style-guide", type=Path, default=Path("editorial/STYLE_GUIDE.md"))
    parser.add_argument("--glossary", type=Path, default=Path("editorial/GLOSSARY.md"))
    parser.add_argument("--jobs-dir", type=Path, default=Path("reports/jobs"))
    parser.add_argument("--decisions", type=Path, default=Path("editorial/DECISIONS.md"))
    parser.add_argument("--characters", type=Path, default=Path("editorial/CHARACTERS.md"))
    parser.add_argument("--world-rules", type=Path, default=Path("editorial/WORLD_RULES.md"))
    parser.add_argument("--skip-state-validation", action="store_true")
    parser.add_argument("--model", default="gpt-5-codex")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.skip_state_validation:
        validation = validate_repository_state(root_dir=Path.cwd())
        if not validation["ok"]:
            print(json.dumps(validation, ensure_ascii=False, indent=2))
            return 1

    handler = build_handler(
        _build_loader(
            chapters_dir=args.chapters_dir,
            chunks_dir=args.chunks_dir,
            consolidated_dir=args.consolidated_dir,
            reports_dir=args.reports_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            reviews_es_dir=args.reviews_es_dir,
            deliverables_dir=args.deliverables_dir,
            decisions_path=args.decisions,
            jobs_dir=args.jobs_dir,
        ),
        _build_chapter_loader(
            chunks_dir=args.chunks_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            reviews_es_dir=args.reviews_es_dir,
        ),
        _build_chunk_loader(
            chunks_dir=args.chunks_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            reviews_es_dir=args.reviews_es_dir,
        ),
        _build_consistency_loader(
            reports_dir=args.reports_dir,
            chunks_dir=args.chunks_dir,
        ),
        _build_decisions_loader(
            decisions_path=args.decisions,
        ),
        _build_glossary_loader(
            glossary_path=args.glossary,
        ),
        _build_characters_loader(
            characters_path=args.characters,
        ),
        _build_world_rules_loader(
            world_rules_path=args.world_rules,
        ),
        _build_search_loader(
            chunks_dir=args.chunks_dir,
            consolidated_dir=args.consolidated_dir,
            glossary_path=args.glossary,
            decisions_path=args.decisions,
        ),
        _build_queue_loader(
            chunks_dir=args.chunks_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            reviews_es_dir=args.reviews_es_dir,
        ),
        _build_copyedit_action(
            chunks_dir=args.chunks_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            style_guide_path=args.style_guide,
            glossary_path=args.glossary,
            decisions_path=args.decisions,
            jobs_dir=args.jobs_dir,
            model=args.model,
        ),
        _build_style_action(
            chunks_dir=args.chunks_dir,
            chapters_dir=args.chapters_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            style_guide_path=args.style_guide,
            glossary_path=args.glossary,
            decisions_path=args.decisions,
            jobs_dir=args.jobs_dir,
            model=args.model,
        ),
        _build_approval_action(
            chunks_dir=args.chunks_dir,
            chapters_dir=args.chapters_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
        ),
        _build_style_approval_action(
            chunks_dir=args.chunks_dir,
            chapters_dir=args.chapters_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
        ),
        _build_consistency_action(
            consolidated_dir=args.consolidated_dir,
            glossary_path=args.glossary,
            reports_dir=args.reports_dir,
            jobs_dir=args.jobs_dir,
        ),
        _build_deliverable_readiness_action(
            chunks_dir=args.chunks_dir,
            chapters_dir=args.chapters_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            reviews_es_dir=args.reviews_es_dir,
            reports_dir=args.reports_dir,
            jobs_dir=args.jobs_dir,
        ),
        _build_translation_action(
            chunks_dir=args.chunks_dir,
            chapters_dir=args.chapters_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_es_dir=args.reviews_es_dir,
            style_guide_path=args.style_guide,
            glossary_path=args.glossary,
            decisions_path=args.decisions,
            jobs_dir=args.jobs_dir,
            model=args.model,
        ),
        _build_export_action(
            template_path=args.template,
            chapters_dir=args.chapters_dir,
            consolidated_dir=args.consolidated_dir,
            reviews_es_dir=args.reviews_es_dir,
            deliverables_dir=args.deliverables_dir,
            jobs_dir=args.jobs_dir,
        ),
        _build_rollback_action(
            reviews_ptbr_dir=args.reviews_ptbr_dir,
            chapters_dir=args.chapters_dir,
            consolidated_dir=args.consolidated_dir,
            jobs_dir=args.jobs_dir,
        ),
        _build_decision_action(
            decisions_path=args.decisions,
        ),
        _build_glossary_action(
            glossary_path=args.glossary,
        ),
        _build_characters_action(
            glossary_path=args.glossary,
            characters_path=args.characters,
        ),
        _build_world_rules_action(
            glossary_path=args.glossary,
            world_rules_path=args.world_rules,
        ),
        _build_character_curation_action(
            characters_path=args.characters,
        ),
        _build_world_rule_curation_action(
            world_rules_path=args.world_rules,
        ),
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        json.dumps(
            {
                "host": args.host,
                "port": args.port,
                "url": f"http://{args.host}:{args.port}/",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
