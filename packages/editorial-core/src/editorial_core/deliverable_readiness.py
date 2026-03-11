from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from editorial_core.chapter_progress import derive_chunk_progress_stage
from editorial_core.translation_es import list_translation_es_candidates


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _group_blockers_by_chapter(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapters: dict[str, dict[str, Any]] = {}
    for blocker in blockers:
        chapter_id = blocker["chapter_id"]
        chapter = chapters.setdefault(
            chapter_id,
            {
                "chapter_id": chapter_id,
                "chapter_title": blocker["chapter_title"],
                "blocker_count": 0,
                "chunk_ids": [],
            },
        )
        chapter["blocker_count"] += 1
        chapter["chunk_ids"].append(blocker["chunk_id"])
    return list(chapters.values())


def generate_deliverable_readiness_report(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    reports_dir: Path,
) -> dict[str, Any]:
    chunk_index = _read_json(chunks_dir / "index.json")
    chunk_entries = {
        chunk["id"]: chunk
        for chunk in chunk_index.get("chunks", [])
    }

    ptbr_blockers: list[dict[str, Any]] = []
    for chunk in chunk_index.get("chunks", []):
        stage = derive_chunk_progress_stage(
            chunk_id=chunk["id"],
            review_status=chunk.get("review_status", "unknown"),
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
        )
        reason = {
            "pending_copyedit": "copyedit_pending",
            "awaiting_copyedit_approval": "copyedit_approval_pending",
            "ready_for_style": "style_pending",
            "awaiting_style_approval": "style_approval_pending",
        }.get(stage)
        if reason is None:
            continue
        ptbr_blockers.append(
            {
                "chunk_id": chunk["id"],
                "chapter_id": chunk["section_id"],
                "chapter_title": chunk.get("section_title", ""),
                "reason": reason,
            }
        )

    translation_candidates = list_translation_es_candidates(
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_dir=reviews_es_dir,
    )
    es_blockers: list[dict[str, Any]] = []
    for item in translation_candidates["skipped"]:
        if item["reason"] != "not_ready":
            continue
        chunk = chunk_entries[item["chunk_id"]]
        es_blockers.append(
            {
                "chunk_id": item["chunk_id"],
                "chapter_id": chunk["section_id"],
                "chapter_title": chunk.get("section_title", ""),
                "reason": "ptbr_not_ready",
            }
        )
    for chunk_id in translation_candidates["eligible_chunk_ids"]:
        chunk = chunk_entries[chunk_id]
        es_blockers.append(
            {
                "chunk_id": chunk_id,
                "chapter_id": chunk["section_id"],
                "chapter_title": chunk.get("section_title", ""),
                "reason": "missing_translation",
            }
        )

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "pt-BR": {
            "eligible": not ptbr_blockers,
            "blocker_count": len(ptbr_blockers),
            "blockers": ptbr_blockers,
            "chapters": _group_blockers_by_chapter(ptbr_blockers),
        },
        "es": {
            "eligible": not es_blockers,
            "blocker_count": len(es_blockers),
            "blockers": es_blockers,
            "chapters": _group_blockers_by_chapter(es_blockers),
        },
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path = reports_dir / "deliverable-readiness.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
