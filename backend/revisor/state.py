from __future__ import annotations
import html
import json
from difflib import SequenceMatcher
from pathlib import Path
from revisor.core.review_application import build_review_preview_text
from typing import Any
from revisor.core.queue import build_review_queue

def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _load_chunk_index(chunks_dir: Path) -> dict[str, Any]:
    index_path = chunks_dir / "index.json"
    if not index_path.exists():
        return {"chunk_count": 0, "chunks": []}
    return _read_json(index_path)


def _build_simple_change_cards(suggestions: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    change_cards: list[dict[str, str | int]] = []
    change_type_labels = {
        "punctuation": "pontuação",
        "grammar": "gramática",
        "agreement": "concordância",
        "syntax": "sintaxe",
        "capitalization": "capitalização",
        "diacritics": "acentuação",
        "spelling": "ortografia",
    }
    for index, suggestion in enumerate(suggestions):
        original = str(suggestion.get("original", ""))
        suggested = str(suggestion.get("suggested", ""))
        original_html, suggested_html = _render_inline_diff(original, suggested)
        original_fragment, suggested_fragment = _extract_inline_change_fragments(original, suggested)
        change_cards.append(
            {
                "index": index,
                "change_type": change_type_labels.get(
                    str(suggestion.get("change_type", "change")),
                    str(suggestion.get("change_type", "change")),
                ),
                "reason": str(suggestion.get("reason", "")),
                "confidence": str(suggestion.get("confidence", "unknown")),
                "original_text": original,
                "suggested_text": suggested,
                "original_html": original_html,
                "suggested_html": suggested_html,
                "original_fragment": original_fragment,
                "suggested_fragment": suggested_fragment,
            }
        )
    return change_cards

def _extract_inline_change_fragments(original: str, suggested: str) -> tuple[str, str]:
    matcher = SequenceMatcher(a=original, b=suggested)
    original_parts: list[str] = []
    suggested_parts: list[str] = []

    for opcode, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        if opcode == "equal":
            continue

        original_fragment = original[a_start:a_end].strip()
        suggested_fragment = suggested[b_start:b_end].strip()

        if original_fragment:
            original_parts.append(html.escape(original_fragment))
        if suggested_fragment:
            suggested_parts.append(html.escape(suggested_fragment))

    original_html = " … ".join(part for part in original_parts if part)
    suggested_html = " … ".join(part for part in suggested_parts if part)

    if not original_html:
        original_html = html.escape(original.strip())
    if not suggested_html:
        suggested_html = html.escape(suggested.strip())

    return original_html, suggested_html

def build_simple_home_state(
    *,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, Any]:
    queue_state = build_review_queue(
        chunks_dir=chunks_dir,
        reviews_ptbr_dir=reviews_ptbr_dir,
        reviews_es_dir=reviews_es_dir,
    )
    next_recommended = queue_state.get("next_recommended")
    if next_recommended is None:
        return {
            "has_actionable_chunk": False,
            "summary": queue_state.get("summary", {}),
        }

    chunk_index = _load_chunk_index(chunks_dir)
    entry = next(chunk for chunk in chunk_index["chunks"] if chunk["id"] == next_recommended["chunk_id"])
    chunk_payload = _read_json(chunks_dir / entry["file"])
    copyedit_path = reviews_ptbr_dir / f"{chunk_payload['id']}.copyedit.json"
    chunk_state = {"chunk": chunk_payload,
                   "copyedit_review": _read_json(copyedit_path) if copyedit_path.exists() else None}
    section_chunks = [
        chunk
        for chunk in chunk_index.get("chunks", [])
        if chunk.get("section_id") == next_recommended["section_id"]
    ]
    current_chunk_position = next(
        (
            position
            for position, chunk in enumerate(section_chunks, start=1)
            if chunk.get("id") == next_recommended["chunk_id"]
        ),
        1,
    )
    chapter_rollups = queue_state.get("chapter_rollups", [])
    actionable_chapters = [
        chapter
        for chapter in chapter_rollups
        if chapter.get("chapter_status") in {"pending_copyedit", "awaiting_copyedit_approval"}
    ]
    remaining_chapter_count = max(
        sum(1 for chapter in actionable_chapters if chapter.get("id") != next_recommended["section_id"]),
        0,
    )
    copyedit_review = chunk_state.get("copyedit_review") or {}
    suggestions = copyedit_review.get("suggestions", [])
    base_text = str(chunk_state["chunk"].get("base_text", ""))
    revised_text = build_review_preview_text(base_text, suggestions)
    original_diff_html, revised_diff_html = _render_inline_diff(base_text, revised_text)
    rejection_path = reviews_ptbr_dir / f"{chunk_state['chunk']['id']}.rejection.json"
    rejection_reason = ""
    if rejection_path.exists():
        rejection_reason = str(_read_json(rejection_path).get("reason", "")).strip()
    spanish_preview_path = reviews_es_dir / f"{chunk_state['chunk']['id']}.translation-es.preview.json"
    spanish_review_path = reviews_es_dir / f"{chunk_state['chunk']['id']}.translation-es.json"
    translation_payload: dict[str, Any] | None = None
    if spanish_review_path.exists():
        translation_payload = _read_json(spanish_review_path)
    elif spanish_preview_path.exists():
        translation_payload = _read_json(spanish_preview_path)
    spanish_text = "\n\n".join(
        str(item.get("translated_text", "")).strip()
        for item in (translation_payload or {}).get("translations", [])
        if str(item.get("translated_text", "")).strip()
    )

    return {
        "has_actionable_chunk": True,
        "summary": queue_state.get("summary", {}),
        "chunk": chunk_state["chunk"],
        "orientation": {
            "current_chapter_title": next_recommended.get("section_title", "Capítulo sem título"),
            "remaining_chapter_count": remaining_chapter_count,
            "current_chunk_position": current_chunk_position,
            "chapter_chunk_count": len(section_chunks),
            "remaining_actionable_chunk_count": max(queue_state["summary"].get("pending_copyedit_count", 0) + queue_state["summary"].get("awaiting_approval_count", 0) - 1, 0),
            "queue_status": next_recommended.get("queue_status", "pending_copyedit"),
        },
        "original_text": base_text,
        "revised_text": revised_text,
        "original_diff_html": original_diff_html,
        "revised_diff_html": revised_diff_html,
        "review_available": copyedit_review.get("status") == "proposed",
        "rejection_reason": rejection_reason,
        "spanish_available": bool(spanish_text),
        "spanish_text": spanish_text,
        "changes": _build_simple_change_cards(suggestions),
    }

def _render_inline_diff(original: str, suggested: str) -> tuple[str, str]:
    matcher = SequenceMatcher(a=original, b=suggested)
    original_parts: list[str] = []
    suggested_parts: list[str] = []

    for opcode, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        original_text = html.escape(original[a_start:a_end])
        suggested_text = html.escape(suggested[b_start:b_end])

        if opcode == "equal":
            original_parts.append(original_text)
            suggested_parts.append(suggested_text)
        elif opcode == "delete":
            original_parts.append(f"<span class=\"diff-removed\">{original_text}</span>")
        elif opcode == "insert":
            suggested_parts.append(f"<span class=\"diff-added\">{suggested_text}</span>")
        elif opcode == "replace":
            original_parts.append(f"<span class=\"diff-removed\">{original_text}</span>")
            suggested_parts.append(f"<span class=\"diff-added\">{suggested_text}</span>")

    return "".join(original_parts), "".join(suggested_parts)
