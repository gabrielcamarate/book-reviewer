from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from editorial_core.decisions import read_editorial_decisions


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _contains_query(*, haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


def _excerpt(text: str, query: str, radius: int = 80) -> str:
    lower_text = text.lower()
    lower_query = query.lower()
    index = lower_text.find(lower_query)
    if index == -1:
        return text[: radius * 2].strip()
    start = max(index - radius, 0)
    end = min(index + len(query) + radius, len(text))
    return text[start:end].strip()


def _search_chunks(chunks_dir: Path, query: str) -> list[dict[str, Any]]:
    index_path = chunks_dir / "index.json"
    if not index_path.exists():
        return []
    matches: list[dict[str, Any]] = []
    for chunk in _read_json(index_path).get("chunks", []):
        chunk_path = chunks_dir / chunk["file"]
        if not chunk_path.exists():
            continue
        payload = _read_json(chunk_path)
        haystack = f"{payload.get('id', '')}\n{payload.get('section_title', '')}\n{payload.get('base_text', '')}"
        if not _contains_query(haystack=haystack, needle=query):
            continue
        matches.append(
            {
                "chunk_id": payload["id"],
                "section_title": payload.get("section_title", ""),
                "excerpt": _excerpt(payload.get("base_text", ""), query),
                "link": f"/chunks/{payload['id']}",
            }
        )
    return matches


def _search_chapters(consolidated_dir: Path, query: str) -> list[dict[str, Any]]:
    index_path = consolidated_dir / "index.json"
    if not index_path.exists():
        return []
    matches: list[dict[str, Any]] = []
    for section in _read_json(index_path).get("sections", []):
        haystack = f"{section.get('id', '')}\n{section.get('title', '')}"
        if not _contains_query(haystack=haystack, needle=query):
            continue
        matches.append(
            {
                "chapter_id": section["id"],
                "title": section.get("title", ""),
                "link": f"/chapters/{section['id']}",
            }
        )
    return matches


def _search_glossary(glossary_path: Path, query: str) -> list[dict[str, Any]]:
    if not glossary_path.exists():
        return []
    matches: list[dict[str, Any]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_heading, current_lines
        if not current_heading:
            return
        block = "\n".join(current_lines)
        if _contains_query(haystack=f"{current_heading}\n{block}", needle=query):
            matches.append(
                {
                    "title": current_heading,
                    "excerpt": _excerpt(block, query),
                    "link": f"/search?q={query}#glossary-results",
                }
            )
        current_heading = None
        current_lines = []

    for line in glossary_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            flush()
            current_heading = line.removeprefix("### ").strip()
            continue
        if current_heading is not None:
            current_lines.append(line)
    flush()
    return matches


def _search_decisions(decisions_path: Path, query: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for entry in read_editorial_decisions(decisions_path):
        haystack = "\n".join(
            [
                entry.get("title", ""),
                entry.get("scope", ""),
                entry.get("rationale", ""),
            ]
        )
        if not _contains_query(haystack=haystack, needle=query):
            continue
        scope = entry.get("scope", "global")
        link = f"/chunks/{scope}" if scope.startswith("chapter-") and "-chunk-" in scope else "/decisions"
        matches.append(
            {
                **entry,
                "link": link,
            }
        )
    return matches


def search_repository_state(
    *,
    query: str,
    chunks_dir: Path,
    consolidated_dir: Path,
    glossary_path: Path,
    decisions_path: Path,
) -> dict[str, Any]:
    normalized_query = query.strip()
    if not normalized_query:
        return {
            "query": "",
            "result_count": 0,
            "chunk_matches": [],
            "chapter_matches": [],
            "glossary_matches": [],
            "decision_matches": [],
        }

    chunk_matches = _search_chunks(chunks_dir, normalized_query)
    chapter_matches = _search_chapters(consolidated_dir, normalized_query)
    glossary_matches = _search_glossary(glossary_path, normalized_query)
    decision_matches = _search_decisions(decisions_path, normalized_query)
    return {
        "query": normalized_query,
        "result_count": len(chunk_matches) + len(chapter_matches) + len(glossary_matches) + len(decision_matches),
        "chunk_matches": chunk_matches,
        "chapter_matches": chapter_matches,
        "glossary_matches": glossary_matches,
        "decision_matches": decision_matches,
    }
