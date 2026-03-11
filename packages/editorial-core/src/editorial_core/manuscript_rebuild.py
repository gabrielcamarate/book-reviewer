from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx_adapter.reader import write_json
from editorial_core.chunking import build_review_chunks
from editorial_core.review_boundary import apply_review_boundary
from editorial_core.segment_manuscript import segment_extracted_manuscript


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json(path)


def _chapter_section_ids(index_payload: dict[str, Any] | None) -> list[str]:
    if not index_payload:
        return []
    return [
        section["id"]
        for section in index_payload.get("sections", [])
        if str(section.get("id", "")).startswith("chapter-")
    ]


def _chunk_ids(index_payload: dict[str, Any] | None) -> list[str]:
    if not index_payload:
        return []
    return [chunk["id"] for chunk in index_payload.get("chunks", [])]


def _is_contiguous(numbers: list[int]) -> bool:
    if not numbers:
        return True
    return numbers == list(range(numbers[0], numbers[-1] + 1))


def _extract_chunk_id_from_review_filename(filename: str) -> str | None:
    for suffix in (
        ".style.approval.json",
        ".translation-es.json",
        ".approval.json",
        ".copyedit.json",
        ".style.json",
    ):
        if filename.endswith(suffix):
            return filename[: -len(suffix)]
    return None


def _collect_orphaned_review_files(reviews_dir: Path, valid_chunk_ids: set[str]) -> list[str]:
    if not reviews_dir.exists():
        return []

    orphaned: list[str] = []
    for review_file in sorted(reviews_dir.glob("*.json")):
        chunk_id = _extract_chunk_id_from_review_filename(review_file.name)
        if chunk_id is None:
            continue
        if chunk_id not in valid_chunk_ids:
            orphaned.append(review_file.name)
    return orphaned


def sync_consolidated_index(chapters_dir: Path, consolidated_dir: Path) -> dict[str, Any]:
    chapters_index = _read_json(chapters_dir / "index.json")
    previous_index = _read_json_if_exists(consolidated_dir / "index.json") or {"sections": []}

    previous_ids = {section["id"] for section in previous_index.get("sections", [])}
    next_sections = [
        {
            "id": section["id"],
            "type": section["type"],
            "order": section["order"],
            "title": section["title"],
            "heading_source_index": section.get("heading_source_index"),
            "source_start_index": section.get("source_start_index"),
            "source_end_index": section.get("source_end_index"),
            "paragraph_count": section.get("paragraph_count"),
            "declared_chapter_number": section.get("declared_chapter_number"),
            "review_status": section.get("review_status"),
            "file": section["file"],
        }
        for section in chapters_index.get("sections", [])
    ]
    next_ids = {section["id"] for section in next_sections}

    synced_index = {
        "section_count": chapters_index.get("section_count", len(next_sections)),
        "chapter_count": chapters_index.get("chapter_count", 0),
        "sections": next_sections,
    }
    write_json(consolidated_dir / "index.json", synced_index)

    return {
        "section_ids_added": sorted(next_ids - previous_ids),
        "section_ids_removed": sorted(previous_ids - next_ids),
        "section_ids_persisted": sorted(previous_ids & next_ids),
    }


def _build_rebuild_report(
    *,
    old_chapters_index: dict[str, Any] | None,
    new_chapters_index: dict[str, Any],
    old_chunks_index: dict[str, Any] | None,
    new_chunks_index: dict[str, Any],
    consolidated_sync: dict[str, Any],
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, Any]:
    old_chapter_ids = _chapter_section_ids(old_chapters_index)
    new_chapter_ids = _chapter_section_ids(new_chapters_index)
    old_chunk_ids = _chunk_ids(old_chunks_index)
    new_chunk_ids = _chunk_ids(new_chunks_index)
    new_chunk_id_set = set(new_chunk_ids)

    chapter_numbers = [
        int(section["declared_chapter_number"])
        for section in new_chapters_index.get("sections", [])
        if str(section.get("id", "")).startswith("chapter-")
        and section.get("declared_chapter_number") is not None
    ]

    return {
        "old": {
            "chapter_count": len(old_chapter_ids),
            "chunk_count": len(old_chunk_ids),
            "chapter_ids": old_chapter_ids,
        },
        "new": {
            "chapter_count": len(new_chapter_ids),
            "chunk_count": len(new_chunk_ids),
            "chapter_ids": new_chapter_ids,
            "chapter_number_sequence": new_chapters_index.get("chapter_number_sequence", []),
            "missing_chapter_numbers": new_chapters_index.get("missing_chapter_numbers", []),
        },
        "migration": {
            "chapter_ids_added": sorted(set(new_chapter_ids) - set(old_chapter_ids)),
            "chapter_ids_removed": sorted(set(old_chapter_ids) - set(new_chapter_ids)),
            "chapter_ids_persisted": sorted(set(old_chapter_ids) & set(new_chapter_ids)),
            "chunk_count_delta": len(new_chunk_ids) - len(old_chunk_ids),
            "consolidated_section_ids_added": consolidated_sync["section_ids_added"],
            "consolidated_section_ids_removed": consolidated_sync["section_ids_removed"],
        },
        "reviews": {
            "ptbr_orphaned_review_files": _collect_orphaned_review_files(
                reviews_ptbr_dir,
                new_chunk_id_set,
            ),
            "es_orphaned_review_files": _collect_orphaned_review_files(
                reviews_es_dir,
                new_chunk_id_set,
            ),
        },
        "integrity": {
            "chapter_numbers_contiguous": _is_contiguous(chapter_numbers),
            "missing_chapter_numbers": new_chapters_index.get("missing_chapter_numbers", []),
            "chapter_number_sequence": chapter_numbers,
        },
    }


def rebuild_manuscript_state(
    *,
    extracted_dir: Path,
    chapters_dir: Path,
    chunks_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    reports_dir: Path,
    cutoff_excerpt: str,
) -> dict[str, Any]:
    old_chapters_index = _read_json_if_exists(chapters_dir / "index.json")
    old_chunks_index = _read_json_if_exists(chunks_dir / "index.json")

    segmentation_summary = segment_extracted_manuscript(extracted_dir, chapters_dir)
    boundary_summary = apply_review_boundary(chapters_dir, cutoff_excerpt)
    chunking_summary = build_review_chunks(chapters_dir, chunks_dir)
    consolidated_sync = sync_consolidated_index(chapters_dir, consolidated_dir)

    new_chapters_index = _read_json(chapters_dir / "index.json")
    new_chunks_index = _read_json(chunks_dir / "index.json")
    report = _build_rebuild_report(
        old_chapters_index=old_chapters_index,
        new_chapters_index=new_chapters_index,
        old_chunks_index=old_chunks_index,
        new_chunks_index=new_chunks_index,
        consolidated_sync=consolidated_sync,
        reviews_ptbr_dir=reviews_ptbr_dir,
        reviews_es_dir=reviews_es_dir,
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "manuscript-rebuild.json", report)

    return {
        "segmentation": segmentation_summary,
        "review_boundary": boundary_summary,
        "chunking": chunking_summary,
        "consolidated_sync": consolidated_sync,
        "integrity": report["integrity"],
        "report_path": str(reports_dir / "manuscript-rebuild.json"),
    }

