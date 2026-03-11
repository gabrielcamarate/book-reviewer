from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def derive_chunk_progress_stage(
    *,
    chunk_id: str,
    review_status: str,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> str:
    if review_status == "approved_reference":
        return "reference"
    if (reviews_es_dir / f"{chunk_id}.translation-es.json").exists():
        return "translated"
    if (reviews_ptbr_dir / f"{chunk_id}.style.approval.json").exists():
        return "ready_for_translation"
    if (reviews_ptbr_dir / f"{chunk_id}.style.json").exists():
        return "awaiting_style_approval"
    if (reviews_ptbr_dir / f"{chunk_id}.approval.json").exists():
        return "ready_for_style"
    if (reviews_ptbr_dir / f"{chunk_id}.copyedit.json").exists():
        return "awaiting_copyedit_approval"
    return "pending_copyedit"


def _resolve_chapter_status(chapter: dict[str, Any]) -> str:
    if chapter["chunk_count"] == 0:
        return "empty"
    if chapter["completed_count"] == chapter["chunk_count"]:
        return "completed"
    if chapter["awaiting_copyedit_approval_count"] > 0:
        return "awaiting_copyedit_approval"
    if chapter["awaiting_style_approval_count"] > 0:
        return "awaiting_style_approval"
    if chapter["pending_copyedit_count"] > 0:
        return "pending_copyedit"
    if chapter["ready_for_style_count"] > 0:
        return "ready_for_style"
    if chapter["ready_for_translation_count"] > 0:
        return "ready_for_translation"
    if chapter["translated_count"] > 0:
        return "partially_translated"
    return "unknown"


def build_chapter_progress(
    *,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, Any]:
    index_path = chunks_dir / "index.json"
    if not index_path.exists():
        return {
            "summary": {
                "chapter_count": 0,
                "completed_chapter_count": 0,
                "actionable_chapter_count": 0,
            },
            "chapters": [],
        }

    chapter_order: list[str] = []
    chapters: dict[str, dict[str, Any]] = {}
    for chunk in _read_json(index_path).get("chunks", []):
        chapter_id = chunk["section_id"]
        if chapter_id not in chapters:
            chapter_order.append(chapter_id)
            chapters[chapter_id] = {
                "id": chapter_id,
                "title": chunk.get("section_title", "Capítulo sem título"),
                "chunk_count": 0,
                "pending_copyedit_count": 0,
                "awaiting_copyedit_approval_count": 0,
                "ready_for_style_count": 0,
                "awaiting_style_approval_count": 0,
                "ready_for_translation_count": 0,
                "translated_count": 0,
                "reference_count": 0,
                "completed_count": 0,
                "completion_percent": 0,
                "chapter_status": "unknown",
            }

        chapter = chapters[chapter_id]
        chapter["chunk_count"] += 1
        stage = derive_chunk_progress_stage(
            chunk_id=chunk["id"],
            review_status=chunk.get("review_status", "unknown"),
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
        )
        chapter[f"{stage}_count"] += 1

    ordered_chapters: list[dict[str, Any]] = []
    for chapter_id in chapter_order:
        chapter = chapters[chapter_id]
        chapter["completed_count"] = chapter["translated_count"] + chapter["reference_count"]
        chapter["completion_percent"] = int(
            round((chapter["completed_count"] / chapter["chunk_count"]) * 100)
        ) if chapter["chunk_count"] else 0
        chapter["chapter_status"] = _resolve_chapter_status(chapter)
        ordered_chapters.append(chapter)

    completed_chapter_count = sum(
        1
        for chapter in ordered_chapters
        if chapter["chunk_count"] > 0 and chapter["completed_count"] == chapter["chunk_count"]
    )
    actionable_chapter_count = sum(
        1
        for chapter in ordered_chapters
        if chapter["chunk_count"] > 0 and chapter["completed_count"] < chapter["chunk_count"]
    )

    return {
        "summary": {
            "chapter_count": len(ordered_chapters),
            "completed_chapter_count": completed_chapter_count,
            "actionable_chapter_count": actionable_chapter_count,
        },
        "chapters": ordered_chapters,
    }
