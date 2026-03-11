from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from editorial_core.chapter_progress import build_chapter_progress, derive_chunk_progress_stage


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _derive_queue_status(
    *,
    chunk_id: str,
    review_status: str,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> str:
    stage = derive_chunk_progress_stage(
        chunk_id=chunk_id,
        review_status=review_status,
        reviews_ptbr_dir=reviews_ptbr_dir,
        reviews_es_dir=reviews_es_dir,
    )
    if stage == "reference":
        return "reference"
    if stage == "translated":
        return "translated"
    if stage in {"awaiting_copyedit_approval", "awaiting_style_approval"}:
        return "awaiting_approval"
    if stage in {"ready_for_style", "ready_for_translation"}:
        return "approved"
    return "pending_copyedit"


def build_review_queue(
    *,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, Any]:
    index_path = chunks_dir / "index.json"
    if not index_path.exists():
        return {
            "summary": {
                "total_chunks": 0,
                "pending_copyedit_count": 0,
                "awaiting_approval_count": 0,
                "approved_count": 0,
                "translated_count": 0,
                "reference_count": 0,
            },
            "queue_items": [],
            "next_recommended": None,
        }

    queue_items: list[dict[str, Any]] = []
    counts = {
        "pending_copyedit_count": 0,
        "awaiting_approval_count": 0,
        "approved_count": 0,
        "translated_count": 0,
        "reference_count": 0,
    }
    order_priority = {
        "awaiting_approval": 0,
        "pending_copyedit": 1,
        "approved": 2,
        "translated": 3,
        "reference": 4,
    }

    for position, chunk in enumerate(_read_json(index_path).get("chunks", [])):
        queue_status = _derive_queue_status(
            chunk_id=chunk["id"],
            review_status=chunk.get("review_status", "unknown"),
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
        )
        counts[f"{queue_status}_count"] += 1
        queue_items.append(
            {
                "chunk_id": chunk["id"],
                "section_id": chunk["section_id"],
                "section_title": chunk.get("section_title", ""),
                "chunk_order": chunk.get("chunk_order", position + 1),
                "review_status": chunk.get("review_status", "unknown"),
                "queue_status": queue_status,
                "link": f"/chunks/{chunk['id']}",
                "_priority": order_priority.get(queue_status, 99),
                "_position": position,
            }
        )

    actionable = [
        item
        for item in queue_items
        if item["queue_status"] in {"awaiting_approval", "pending_copyedit"}
    ]
    actionable.sort(key=lambda item: (item["_priority"], item["_position"]))
    next_recommended = actionable[0] if actionable else None

    for item in queue_items:
        item.pop("_priority", None)
        item.pop("_position", None)

    chapter_progress = build_chapter_progress(
        chunks_dir=chunks_dir,
        reviews_ptbr_dir=reviews_ptbr_dir,
        reviews_es_dir=reviews_es_dir,
    )

    return {
        "summary": {
            "total_chunks": len(queue_items),
            **counts,
        },
        "queue_items": queue_items,
        "next_recommended": next_recommended,
        "chapter_rollups": chapter_progress["chapters"],
    }
