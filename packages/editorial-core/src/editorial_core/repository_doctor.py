from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from editorial_core.repository_validation import validate_repository_state


CHAPTER_TITLE_RE = re.compile(
    r"^Cap[ií]tulo\s+([IVXLCDM]+|\d+)(?::\s*(.+?))?\.?$",
    re.IGNORECASE,
)

ROMAN_VALUES = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_chapter_number(raw_value: str) -> int | None:
    stripped = raw_value.strip()
    if not stripped:
        return None
    if stripped.isdigit():
        return int(stripped)

    total = 0
    previous_value = 0
    for character in reversed(stripped.upper()):
        value = ROMAN_VALUES.get(character)
        if value is None:
            return None
        if value < previous_value:
            total -= value
        else:
            total += value
            previous_value = value
    return total if total > 0 else None


def _extract_declared_chapter_number(title: str) -> int | None:
    match = CHAPTER_TITLE_RE.match(title.strip())
    if match is None:
        return None
    return _parse_chapter_number(match.group(1))


def _compute_missing_chapter_numbers(chapters_index: dict[str, Any]) -> list[int]:
    configured_numbers = chapters_index.get("missing_chapter_numbers")
    if isinstance(configured_numbers, list):
        return [int(number) for number in configured_numbers]

    declared_numbers: set[int] = set()
    for section in chapters_index.get("sections", []):
        if not str(section.get("id", "")).startswith("chapter-"):
            continue
        chapter_number = section.get("declared_chapter_number") or _extract_declared_chapter_number(
            section.get("title", "")
        )
        if chapter_number is None:
            continue
        declared_numbers.add(int(chapter_number))

    ordered_numbers = sorted(declared_numbers)
    if not ordered_numbers:
        return []

    missing_numbers: list[int] = []
    previous_number = 0
    for chapter_number in ordered_numbers:
        if chapter_number > previous_number + 1:
            missing_numbers.extend(range(previous_number + 1, chapter_number))
        previous_number = chapter_number
    return missing_numbers


def run_repository_doctor(*, root_dir: Path) -> dict[str, Any]:
    validation = validate_repository_state(root_dir=root_dir)
    blocking_findings: list[dict[str, Any]] = []
    advisory_findings: list[dict[str, Any]] = []

    for error in validation["errors"]:
        blocking_findings.append(
            {
                "code": "repository_state_invalid",
                "severity": "blocking",
                "message": error,
            }
        )

    if not validation["ok"]:
        return {
            "ok": False,
            "blocking_count": len(blocking_findings),
            "advisory_count": 0,
            "blocking_findings": blocking_findings,
            "advisory_findings": advisory_findings,
        }

    chapters_index = _read_json(root_dir / "manuscript" / "chapters" / "index.json")
    chunks_index = _read_json(root_dir / "manuscript" / "chunks" / "index.json")
    consolidated_index = _read_json(root_dir / "manuscript" / "consolidated" / "index.json")

    known_section_ids = {
        section["id"]
        for section in chapters_index.get("sections", [])
        if isinstance(section, dict) and "id" in section
    } | {
        section["id"]
        for section in consolidated_index.get("sections", [])
        if isinstance(section, dict) and "id" in section
    }

    for chunk in chunks_index.get("chunks", []):
        section_id = chunk.get("section_id")
        if not section_id or section_id in known_section_ids:
            continue
        blocking_findings.append(
            {
                "code": "chunk_section_missing",
                "severity": "blocking",
                "message": f"chunk {chunk.get('id', '<unknown>')} references missing section {section_id}",
                "chunk_id": chunk.get("id"),
                "section_id": section_id,
            }
        )

    missing_chapter_numbers = _compute_missing_chapter_numbers(chapters_index)
    if missing_chapter_numbers:
        advisory_findings.append(
            {
                "code": "missing_declared_chapter_numbers",
                "severity": "advisory",
                "message": "Declared chapter numbering has gaps in the segmented manuscript.",
                "chapter_numbers": missing_chapter_numbers,
            }
        )

    return {
        "ok": not blocking_findings,
        "blocking_count": len(blocking_findings),
        "advisory_count": len(advisory_findings),
        "blocking_findings": blocking_findings,
        "advisory_findings": advisory_findings,
    }
