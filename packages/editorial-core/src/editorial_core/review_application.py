from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from docx_adapter.reader import write_json


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _approval_path(review_path: Path) -> Path:
    review_name = review_path.name
    if review_name.endswith(".copyedit.json"):
        base_name = review_name.removesuffix(".copyedit.json")
        return review_path.with_name(f"{base_name}.approval.json")
    if review_name.endswith(".style.json"):
        base_name = review_name.removesuffix(".style.json")
        return review_path.with_name(f"{base_name}.style.approval.json")
    base_name = review_name.removesuffix(".json")
    return review_path.with_name(f"{base_name}.approval.json")


def _load_chunk_payload(chunks_dir: Path, chunk_id: str) -> dict[str, Any]:
    index_payload = _read_json(chunks_dir / "index.json")
    for chunk_entry in index_payload.get("chunks", []):
        if chunk_entry["id"] == chunk_id:
            return _read_json(chunks_dir / chunk_entry["file"])
    raise ValueError(f"chunk not found for approval: {chunk_id}")


def _ensure_consolidated_index(chapters_dir: Path, consolidated_dir: Path) -> dict[str, Any]:
    consolidated_index_path = consolidated_dir / "index.json"
    if consolidated_index_path.exists():
        return _read_json(consolidated_index_path)

    chapter_index = _read_json(chapters_dir / "index.json")
    index_payload = {
        "section_count": chapter_index["section_count"],
        "chapter_count": chapter_index["chapter_count"],
        "sections": [
            {
                "id": section["id"],
                "type": section["type"],
                "order": section["order"],
                "title": section["title"],
                "heading_source_index": section.get("heading_source_index"),
                "source_start_index": section.get("source_start_index"),
                "source_end_index": section.get("source_end_index"),
                "paragraph_count": section.get("paragraph_count"),
                "file": section["file"],
                "review_status": section.get("review_status"),
            }
            for section in chapter_index["sections"]
        ],
    }
    write_json(consolidated_index_path, index_payload)
    return index_payload


def _initialize_consolidated_section(chapters_dir: Path, consolidated_dir: Path, section_id: str) -> dict[str, Any]:
    source_path = chapters_dir / f"{section_id}.json"
    source_payload = _read_json(source_path)

    consolidated_payload = {
        key: value
        for key, value in source_payload.items()
        if key != "paragraphs"
    }
    consolidated_payload["paragraphs"] = [
        {
            "id": paragraph["id"],
            "source_index": paragraph["source_index"],
            "source_text": paragraph["text"],
            "text": paragraph["text"],
            "review_status": paragraph.get("review_status"),
            "applied_reviews": [],
        }
        for paragraph in source_payload.get("paragraphs", [])
    ]

    write_json(consolidated_dir / f"{section_id}.json", consolidated_payload)
    return consolidated_payload


def _load_or_initialize_consolidated_section(
    chapters_dir: Path,
    consolidated_dir: Path,
    section_id: str,
) -> dict[str, Any]:
    consolidated_path = consolidated_dir / f"{section_id}.json"
    if consolidated_path.exists():
        return _read_json(consolidated_path)
    return _initialize_consolidated_section(chapters_dir, consolidated_dir, section_id)


def _compute_section_review_status(paragraphs: list[dict[str, Any]]) -> str:
    statuses = [paragraph.get("review_status") for paragraph in paragraphs if paragraph.get("review_status")]
    if not statuses:
        return "pending_review"
    if all(status == "approved_reference" for status in statuses):
        return "approved_reference"
    if all(status == "approved" for status in statuses):
        return "approved"
    if all(status in {"approved_reference", "approved"} for status in statuses):
        return "approved"
    if all(status == "pending_review" for status in statuses):
        return "pending_review"
    return "mixed"


def _apply_suggestion(
    *,
    suggestion: dict[str, Any],
    suggestion_index: int,
    review_pass: str,
    target_paragraph_ids: set[str],
    consolidated_payload: dict[str, Any],
    review_path: Path,
    approval_path: Path,
    applied_at: str,
) -> dict[str, Any] | None:
    for paragraph in consolidated_payload["paragraphs"]:
        if paragraph["id"] not in target_paragraph_ids:
            continue
        current_text = paragraph["text"]
        original = suggestion["original"]
        if original not in current_text:
            continue

        paragraph["text"] = current_text.replace(original, suggestion["suggested"], 1)
        paragraph["review_status"] = "approved"
        paragraph.setdefault("applied_reviews", []).append(
            {
                "approval_file": approval_path.name,
                "review_file": review_path.name,
                "pass": review_pass,
                "suggestion_index": suggestion_index,
                "change_type": suggestion["change_type"],
                "reason": suggestion["reason"],
                "confidence": suggestion["confidence"],
                "applied_at": applied_at,
                "original": suggestion["original"],
                "suggested": suggestion["suggested"],
            }
        )
        return {
            "suggestion_index": suggestion_index,
            "paragraph_id": paragraph["id"],
            "original": suggestion["original"],
            "suggested": suggestion["suggested"],
            "change_type": suggestion["change_type"],
            "reason": suggestion["reason"],
            "confidence": suggestion["confidence"],
        }

    return None


def apply_review_approval(
    *,
    review_path: Path,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    approved_suggestion_indexes: list[int] | None = None,
) -> dict[str, Any]:
    if not review_path.exists():
        raise FileNotFoundError(review_path)

    review_payload = _read_json(review_path)
    chunk_payload = _load_chunk_payload(chunks_dir, review_payload["chunk_id"])
    consolidated_dir.mkdir(parents=True, exist_ok=True)
    consolidated_index = _ensure_consolidated_index(chapters_dir, consolidated_dir)
    consolidated_payload = _load_or_initialize_consolidated_section(
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        section_id=review_payload["source"]["section_id"],
    )

    suggestions = review_payload.get("suggestions", [])
    if approved_suggestion_indexes is None:
        approved_suggestion_indexes = list(range(len(suggestions)))

    approval_path = _approval_path(review_path)
    applied_at = datetime.now().isoformat(timespec="seconds")
    target_paragraph_ids = set(chunk_payload["paragraph_ids"])
    applied_changes: list[dict[str, Any]] = []
    skipped_suggestions: list[dict[str, Any]] = []

    for index in approved_suggestion_indexes:
        suggestion = suggestions[index]
        applied = _apply_suggestion(
            suggestion=suggestion,
            suggestion_index=index,
            review_pass=review_payload["pass"],
            target_paragraph_ids=target_paragraph_ids,
            consolidated_payload=consolidated_payload,
            review_path=review_path,
            approval_path=approval_path,
            applied_at=applied_at,
        )
        if applied is None:
            skipped_suggestions.append(
                {
                    "suggestion_index": index,
                    "original": suggestion["original"],
                    "reason": "original text not found in target consolidated paragraphs",
                }
            )
        else:
            applied_changes.append(applied)

    consolidated_payload["review_status"] = _compute_section_review_status(
        consolidated_payload["paragraphs"]
    )
    write_json(consolidated_dir / f"{consolidated_payload['id']}.json", consolidated_payload)

    for section_entry in consolidated_index["sections"]:
        if section_entry["id"] == consolidated_payload["id"]:
            section_entry["review_status"] = consolidated_payload["review_status"]
            break
    write_json(consolidated_dir / "index.json", consolidated_index)

    approval_payload = {
        "chunk_id": review_payload["chunk_id"],
        "review_file": review_path.name,
        "approval_file": approval_path.name,
        "pass": review_payload["pass"],
        "language": review_payload["language"],
        "status": "approved",
        "approved_suggestion_indexes": approved_suggestion_indexes,
        "applied_change_count": len(applied_changes),
        "skipped_change_count": len(skipped_suggestions),
        "applied_changes": applied_changes,
        "skipped_suggestions": skipped_suggestions,
        "consolidated_section_file": f"{consolidated_payload['id']}.json",
        "approved_at": applied_at,
    }
    write_json(approval_path, approval_payload)

    return {
        "chunk_id": review_payload["chunk_id"],
        "approved_suggestion_count": len(approved_suggestion_indexes),
        "applied_change_count": len(applied_changes),
        "approval_path": str(approval_path),
        "consolidated_section_path": str(consolidated_dir / f"{consolidated_payload['id']}.json"),
    }
