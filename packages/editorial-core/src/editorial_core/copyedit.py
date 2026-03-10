from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from docx_adapter.reader import write_json
from editorial_prompts.copyedit import build_copyedit_prompt
from editorial_schemas.copyedit import copyedit_output_schema

Runner = Callable[..., dict[str, object]]


def _load_chunk_index(chunks_dir: Path) -> dict[str, Any]:
    return json.loads((chunks_dir / "index.json").read_text(encoding="utf-8"))


def _review_output_path(reviews_dir: Path, chunk_id: str) -> Path:
    return reviews_dir / f"{chunk_id}.copyedit.json"


def _select_chunk(chunks_dir: Path, reviews_dir: Path, chunk_id: str | None) -> dict[str, Any]:
    index_payload = _load_chunk_index(chunks_dir)
    if not index_payload.get("chunks"):
        raise ValueError("no pending chunk is available for copyedit")

    for chunk_entry in index_payload["chunks"]:
        if chunk_id is not None and chunk_entry["id"] != chunk_id:
            continue
        if chunk_id is None and _review_output_path(reviews_dir, chunk_entry["id"]).exists():
            continue
        return json.loads((chunks_dir / chunk_entry["file"]).read_text(encoding="utf-8"))

    if chunk_id is not None:
        raise ValueError(f"requested chunk not found or already unavailable: {chunk_id}")
    raise ValueError("no pending chunk is available for copyedit")


def _validate_response(payload: dict[str, object]) -> list[dict[str, object]]:
    suggestions = payload.get("suggestions")
    if not isinstance(suggestions, list):
        raise ValueError("copyedit runner response must contain a suggestions list")
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            raise ValueError("copyedit suggestions must be objects")
        for key in ("original", "suggested", "change_type", "reason", "confidence"):
            if key not in suggestion:
                raise ValueError(f"copyedit suggestion missing required field: {key}")
    return suggestions


def run_copyedit_pass(
    *,
    chunks_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    runner: Runner,
    model: str = "gpt-5-codex",
    chunk_id: str | None = None,
) -> dict[str, Any]:
    chunk_payload = _select_chunk(chunks_dir, reviews_dir, chunk_id)
    prompt = build_copyedit_prompt(
        chunk_payload=chunk_payload,
        style_guide_text=style_guide_path.read_text(encoding="utf-8"),
        glossary_text=glossary_path.read_text(encoding="utf-8"),
    )
    schema = copyedit_output_schema()
    runner_payload = runner(prompt=prompt, schema=schema, model=model)
    suggestions = _validate_response(runner_payload)

    review_payload = {
        "chunk_id": chunk_payload["id"],
        "pass": "copyedit",
        "language": "pt-BR",
        "status": "proposed",
        "model": model,
        "source": {
            "section_id": chunk_payload["section_id"],
            "section_title": chunk_payload["section_title"],
            "paragraph_ids": chunk_payload["paragraph_ids"],
            "source_start_index": chunk_payload["source_start_index"],
            "source_end_index": chunk_payload["source_end_index"],
        },
        "suggestions": suggestions,
    }

    output_path = _review_output_path(reviews_dir, chunk_payload["id"])
    write_json(output_path, review_payload)

    return {
        "chunk_id": chunk_payload["id"],
        "suggestion_count": len(suggestions),
        "output_path": str(output_path),
        "model": model,
    }
