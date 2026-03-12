from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from docx_adapter.reader import write_json
from editorial_core.provenance import build_llm_provenance
from editorial_prompts.copyedit import (
    COPYEDIT_PROMPT_TEMPLATE_ID,
    COPYEDIT_PROMPT_VERSION,
    build_copyedit_prompt,
)
from editorial_schemas.copyedit import (
    COPYEDIT_SCHEMA_NAME,
    COPYEDIT_SCHEMA_VERSION,
    copyedit_output_schema,
)

Runner = Callable[..., dict[str, object]]
ALLOWED_COPYEDIT_CHANGE_TYPES = {
    "spelling",
    "ortografia",
    "grammar",
    "gramática",
    "punctuation",
    "pontuação",
    "agreement",
    "concordância",
    "syntax",
    "sintaxe",
    "capitalization",
    "capitalização",
    "quotation",
    "citação",
    "aspas",
    "diacritics",
    "acentuação",
}
MIN_COPYEDIT_CONFIDENCE = 0.8


def _load_chunk_index(chunks_dir: Path) -> dict[str, Any]:
    return json.loads((chunks_dir / "index.json").read_text(encoding="utf-8"))


def _review_output_path(reviews_dir: Path, chunk_id: str) -> Path:
    return reviews_dir / f"{chunk_id}.copyedit.json"


def _rejection_output_path(reviews_dir: Path, chunk_id: str) -> Path:
    return reviews_dir / f"{chunk_id}.rejection.json"


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


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
        if str(suggestion["change_type"]) not in ALLOWED_COPYEDIT_CHANGE_TYPES:
            raise ValueError(
                f"copyedit suggestion uses unsupported change_type: {suggestion['change_type']}"
            )
        confidence = suggestion["confidence"]
        if not isinstance(confidence, (int, float)):
            raise ValueError("copyedit suggestion confidence must be numeric")
        if float(confidence) < MIN_COPYEDIT_CONFIDENCE:
            raise ValueError(
                f"copyedit suggestion confidence must be >= {MIN_COPYEDIT_CONFIDENCE:.1f}"
            )
    return suggestions


def _discard_ambiguous_repeated_spans(
    suggestions: list[dict[str, object]],
    *,
    base_text: str,
) -> list[dict[str, object]]:
    paragraphs = [paragraph for paragraph in base_text.split("\n\n") if paragraph]
    filtered: list[dict[str, object]] = []
    for suggestion in suggestions:
        original = str(suggestion.get("original", ""))
        if not original:
            continue
        ambiguous_in_paragraph = any(paragraph.count(original) > 1 for paragraph in paragraphs)
        if ambiguous_in_paragraph:
            continue
        filtered.append(suggestion)
    return filtered


def run_copyedit_pass(
    *,
    chunks_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    runner: Runner,
    model: str = "gpt-5-codex",
    chunk_id: str | None = None,
) -> dict[str, Any]:
    chunk_payload = _select_chunk(chunks_dir, reviews_dir, chunk_id)
    style_guide_text = _read_optional_text(style_guide_path)
    glossary_text = _read_optional_text(glossary_path)
    decisions_text = _read_optional_text(decisions_path)
    rejection_feedback_text = ""
    rejection_path = _rejection_output_path(reviews_dir, chunk_payload["id"])
    if rejection_path.exists():
        rejection_feedback_text = str(
            json.loads(rejection_path.read_text(encoding="utf-8")).get("reason", "")
        ).strip()
    prompt = build_copyedit_prompt(
        chunk_payload=chunk_payload,
        style_guide_text=style_guide_text,
        glossary_text=glossary_text,
        decisions_text=decisions_text,
        rejection_feedback_text=rejection_feedback_text,
    )
    schema = copyedit_output_schema()
    runner_payload = runner(prompt=prompt, schema=schema, model=model)
    suggestions = _validate_response(runner_payload)
    suggestions = _discard_ambiguous_repeated_spans(
        suggestions,
        base_text=str(chunk_payload["base_text"]),
    )
    provenance = build_llm_provenance(
        model=model,
        prompt_template_id=COPYEDIT_PROMPT_TEMPLATE_ID,
        prompt_version=COPYEDIT_PROMPT_VERSION,
        prompt_text=prompt,
        schema_name=COPYEDIT_SCHEMA_NAME,
        schema_version=COPYEDIT_SCHEMA_VERSION,
        schema=schema,
        context_inputs={
            "style_guide": style_guide_text,
            "glossary": glossary_text,
            "decisions": decisions_text,
        },
    )

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
        "provenance": provenance,
        "suggestions": suggestions,
    }

    output_path = _review_output_path(reviews_dir, chunk_payload["id"])
    write_json(output_path, review_payload)
    if rejection_path.exists():
        rejection_path.unlink()

    return {
        "chunk_id": chunk_payload["id"],
        "suggestion_count": len(suggestions),
        "output_path": str(output_path),
        "model": model,
    }
