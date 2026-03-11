from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from docx_adapter.reader import write_json
from editorial_core.review_application import _compute_section_review_status


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _list_active_approval_paths(reviews_dir: Path) -> list[Path]:
    approval_paths: list[Path] = []
    for path in sorted(reviews_dir.glob("*.approval.json")):
        payload = _read_json(path)
        if payload.get("status") == "approved" and payload.get("approved_at"):
            approval_paths.append(path)
    return approval_paths


def _select_latest_approval(reviews_dir: Path) -> tuple[Path, dict[str, Any]]:
    latest_path: Path | None = None
    latest_payload: dict[str, Any] | None = None
    latest_approved_at: str | None = None

    for path in _list_active_approval_paths(reviews_dir):
        payload = _read_json(path)
        approved_at = str(payload["approved_at"])
        if latest_approved_at is None or approved_at > latest_approved_at:
            latest_path = path
            latest_payload = payload
            latest_approved_at = approved_at

    if latest_path is None or latest_payload is None:
        raise ValueError("no active approval found to rollback")
    return latest_path, latest_payload


def _rollback_path(approval_path: Path, approved_at: str) -> Path:
    safe_timestamp = approved_at.replace(":", "-")
    if approval_path.name.endswith(".json"):
        stem = approval_path.name[: -len(".json")]
    else:
        stem = approval_path.stem
    return approval_path.with_name(f"{stem}.{safe_timestamp}.rollback.json")


def _replace_last(text: str, old: str, new: str) -> str:
    index = text.rfind(old)
    if index == -1:
        raise ValueError(f"rollback text not found: {old}")
    return text[:index] + new + text[index + len(old):]


def rollback_last_review_approval(
    *,
    reviews_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
) -> dict[str, Any]:
    approval_path, approval_payload = _select_latest_approval(reviews_dir)
    consolidated_section_path = consolidated_dir / approval_payload["consolidated_section_file"]
    consolidated_payload = _read_json(consolidated_section_path)
    source_section_path = chapters_dir / approval_payload["consolidated_section_file"]
    source_payload = _read_json(source_section_path)
    source_paragraphs = {
        paragraph["id"]: paragraph
        for paragraph in source_payload.get("paragraphs", [])
    }

    paragraphs_by_id = {
        paragraph["id"]: paragraph
        for paragraph in consolidated_payload.get("paragraphs", [])
    }
    reverted_changes: list[dict[str, Any]] = []

    for change in reversed(approval_payload.get("applied_changes", [])):
        paragraph = paragraphs_by_id.get(change["paragraph_id"])
        if paragraph is None:
            raise ValueError(f"paragraph missing for rollback: {change['paragraph_id']}")

        applied_reviews = paragraph.get("applied_reviews", [])
        if not applied_reviews:
            raise ValueError(f"paragraph has no applied review stack for rollback: {change['paragraph_id']}")

        last_applied = applied_reviews[-1]
        if last_applied.get("approval_file") != approval_payload["approval_file"]:
            raise ValueError("latest approval is no longer the topmost applied review")
        if last_applied.get("suggested") != change["suggested"]:
            raise ValueError("latest approval payload diverges from paragraph audit stack")

        if paragraph["text"].count(change["suggested"]) != 1:
            raise ValueError("rollback is not safe because the suggested text is not uniquely identifiable")

        paragraph["text"] = _replace_last(paragraph["text"], change["suggested"], change["original"])
        paragraph["applied_reviews"] = applied_reviews[:-1]

        if paragraph["applied_reviews"]:
            paragraph["review_status"] = "approved"
        else:
            paragraph["review_status"] = source_paragraphs[paragraph["id"]].get("review_status", "pending_review")

        reverted_changes.append(
            {
                "paragraph_id": paragraph["id"],
                "restored_text": change["original"],
                "reverted_text": change["suggested"],
                "suggestion_index": change.get("suggestion_index"),
            }
        )

    consolidated_payload["review_status"] = _compute_section_review_status(
        consolidated_payload.get("paragraphs", [])
    )
    write_json(consolidated_section_path, consolidated_payload)

    consolidated_index_path = consolidated_dir / "index.json"
    consolidated_index = _read_json(consolidated_index_path)
    for section in consolidated_index.get("sections", []):
        if section["id"] == consolidated_payload["id"]:
            section["review_status"] = consolidated_payload["review_status"]
            break
    write_json(consolidated_index_path, consolidated_index)

    rolled_back_at = datetime.now().isoformat(timespec="seconds")
    rollback_path = _rollback_path(approval_path, approval_payload["approved_at"])
    rollback_payload = {
        "approval_file": approval_payload["approval_file"],
        "review_file": approval_payload.get("review_file"),
        "pass": approval_payload.get("pass"),
        "status": "rolled_back",
        "rolled_back_at": rolled_back_at,
        "consolidated_section_file": approval_payload["consolidated_section_file"],
        "reverted_change_count": len(reverted_changes),
        "reverted_changes": list(reversed(reverted_changes)),
    }
    write_json(rollback_path, rollback_payload)

    approval_payload["status"] = "rolled_back"
    approval_payload["rolled_back_at"] = rolled_back_at
    approval_payload["rollback_file"] = rollback_path.name
    write_json(approval_path, approval_payload)

    return {
        "approval_file": approval_path.name,
        "rollback_path": str(rollback_path),
        "reverted_change_count": len(reverted_changes),
        "consolidated_section_path": str(consolidated_section_path),
    }

