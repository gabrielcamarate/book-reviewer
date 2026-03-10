from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx_adapter.reader import write_json


def apply_review_boundary(chapters_dir: Path, cutoff_excerpt: str) -> dict[str, Any]:
    index_path = chapters_dir / "index.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))

    boundary_section_id: str | None = None
    boundary_paragraph_id: str | None = None
    boundary_source_index: int | None = None
    boundary_found = False
    section_status_counts = {
        "approved_reference": 0,
        "mixed": 0,
        "pending_review": 0,
    }

    for section_entry in index_payload["sections"]:
        section_path = chapters_dir / section_entry["file"]
        section_payload = json.loads(section_path.read_text(encoding="utf-8"))

        paragraph_statuses: list[str] = []

        for paragraph in section_payload.get("paragraphs", []):
            if not boundary_found and cutoff_excerpt in paragraph["text"]:
                boundary_found = True
                boundary_section_id = section_payload["id"]
                boundary_paragraph_id = paragraph["id"]
                boundary_source_index = paragraph["source_index"]

            paragraph["review_status"] = (
                "pending_review" if boundary_found else "approved_reference"
            )
            paragraph_statuses.append(paragraph["review_status"])

        if not paragraph_statuses:
            section_payload["review_status"] = (
                "pending_review" if boundary_found else "approved_reference"
            )
        elif all(status == "approved_reference" for status in paragraph_statuses):
            section_payload["review_status"] = "approved_reference"
        elif all(status == "pending_review" for status in paragraph_statuses):
            section_payload["review_status"] = "pending_review"
        else:
            section_payload["review_status"] = "mixed"

        section_entry["review_status"] = section_payload["review_status"]
        section_status_counts[section_payload["review_status"]] += 1
        write_json(section_path, section_payload)

    if boundary_section_id is None or boundary_paragraph_id is None or boundary_source_index is None:
        raise ValueError(f"cutoff excerpt not found in manuscript chapters: {cutoff_excerpt}")

    review_state = {
        "cutoff_excerpt": cutoff_excerpt,
        "boundary_section_id": boundary_section_id,
        "boundary_paragraph_id": boundary_paragraph_id,
        "boundary_source_index": boundary_source_index,
        "section_status_counts": section_status_counts,
    }

    write_json(index_path, index_payload)
    write_json(chapters_dir / "review-state.json", review_state)

    return review_state
