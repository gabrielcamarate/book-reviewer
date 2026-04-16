from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from docx_adapter.reader import write_json
from editorial_core.provenance import build_llm_provenance
from editorial_prompts.translation_es import (
    TRANSLATION_ES_PROMPT_TEMPLATE_ID,
    TRANSLATION_ES_PROMPT_VERSION,
    build_translation_es_prompt,
)
from editorial_schemas.translation_es import (
    TRANSLATION_ES_SCHEMA_NAME,
    TRANSLATION_ES_SCHEMA_VERSION,
    translation_es_output_schema,
)

Runner = Callable[..., dict[str, object]]
STABLE_REVIEW_STATUSES = {"approved", "approved_reference"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_chunk_index(chunks_dir: Path) -> dict[str, Any]:
    return _read_json(chunks_dir / "index.json")


def _translation_output_path(reviews_dir: Path, chunk_id: str) -> Path:
    return reviews_dir / f"{chunk_id}.translation-es.json"


def _translation_preview_output_path(reviews_dir: Path, chunk_id: str) -> Path:
    return reviews_dir / f"{chunk_id}.translation-es.preview.json"


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_current_section(
    *,
    chapters_dir: Path,
    consolidated_dir: Path,
    section_id: str,
) -> dict[str, Any]:
    consolidated_path = consolidated_dir / f"{section_id}.json"
    if consolidated_path.exists():
        return _read_json(consolidated_path)

    chapter_path = chapters_dir / f"{section_id}.json"
    if chapter_path.exists():
        return _read_json(chapter_path)

    raise FileNotFoundError(f"section state not found for translation: {section_id}")


def _resolve_source_paragraphs(
    *,
    chunk_payload: dict[str, Any],
    section_payload: dict[str, Any],
) -> list[dict[str, Any]] | None:
    paragraph_map = {
        paragraph["id"]: paragraph
        for paragraph in section_payload.get("paragraphs", [])
    }
    source_paragraphs: list[dict[str, Any]] = []

    for paragraph_id in chunk_payload["paragraph_ids"]:
        paragraph = paragraph_map.get(paragraph_id)
        if paragraph is None:
            return None
        review_status = paragraph.get("review_status")
        if review_status not in STABLE_REVIEW_STATUSES:
            return None
        source_paragraphs.append(
            {
                "paragraph_id": paragraph_id,
                "source_index": paragraph.get("source_index"),
                "review_status": review_status,
                "text": paragraph["text"],
            }
        )

    return source_paragraphs


def _select_chunk(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    chunk_id: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    index_payload = _load_chunk_index(chunks_dir)
    if not index_payload.get("chunks"):
        raise ValueError("no chunk is available for Spanish translation")

    for chunk_entry in index_payload["chunks"]:
        if chunk_id is not None and chunk_entry["id"] != chunk_id:
            continue
        output_path = _translation_output_path(reviews_dir, chunk_entry["id"])
        if chunk_id is None and output_path.exists():
            continue
        if chunk_id is not None and output_path.exists():
            raise ValueError(f"requested chunk already translated: {chunk_id}")

        chunk_payload = _read_json(chunks_dir / chunk_entry["file"])
        section_payload = _load_current_section(
            chapters_dir=chapters_dir,
            consolidated_dir=consolidated_dir,
            section_id=chunk_payload["section_id"],
        )
        source_paragraphs = _resolve_source_paragraphs(
            chunk_payload=chunk_payload,
            section_payload=section_payload,
        )
        if source_paragraphs is None:
            if chunk_id is not None:
                raise ValueError(f"requested chunk is not ready for Spanish translation: {chunk_id}")
            continue
        return chunk_payload, source_paragraphs

    if chunk_id is not None:
        raise ValueError(f"requested chunk not found or unavailable for Spanish translation: {chunk_id}")
    raise ValueError("no stable pt-BR chunk is available for Spanish translation")


def list_translation_es_candidates(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
) -> dict[str, Any]:
    index_payload = _load_chunk_index(chunks_dir)
    eligible_chunk_ids: list[str] = []
    skipped: list[dict[str, str]] = []

    for chunk_entry in index_payload.get("chunks", []):
        chunk_id = chunk_entry["id"]
        output_path = _translation_output_path(reviews_dir, chunk_id)
        if output_path.exists():
            skipped.append({"chunk_id": chunk_id, "reason": "already_translated"})
            continue

        chunk_payload = _read_json(chunks_dir / chunk_entry["file"])
        section_payload = _load_current_section(
            chapters_dir=chapters_dir,
            consolidated_dir=consolidated_dir,
            section_id=chunk_payload["section_id"],
        )
        source_paragraphs = _resolve_source_paragraphs(
            chunk_payload=chunk_payload,
            section_payload=section_payload,
        )
        if source_paragraphs is None:
            skipped.append({"chunk_id": chunk_id, "reason": "not_ready"})
            continue

        eligible_chunk_ids.append(chunk_id)

    return {
        "eligible_chunk_ids": eligible_chunk_ids,
        "skipped": skipped,
    }


def _validate_response(
    payload: dict[str, object],
    paragraph_ids: list[str],
) -> list[dict[str, object]]:
    translations = payload.get("translations")
    if not isinstance(translations, list):
        raise ValueError("translation runner response must contain a translations list")

    required_ids = set(paragraph_ids)
    observed_ids: set[str] = set()
    for translation in translations:
        if not isinstance(translation, dict):
            raise ValueError("translations must be objects")
        for key in ("paragraph_id", "translated_text", "rationale", "confidence"):
            if key not in translation:
                raise ValueError(f"translation entry missing required field: {key}")
        paragraph_id = translation["paragraph_id"]
        if not isinstance(paragraph_id, str):
            raise ValueError("translation paragraph_id must be a string")
        if paragraph_id not in required_ids:
            raise ValueError(f"unexpected translated paragraph_id: {paragraph_id}")
        if paragraph_id in observed_ids:
            raise ValueError(f"duplicate translated paragraph_id: {paragraph_id}")
        observed_ids.add(paragraph_id)

    if observed_ids != required_ids:
        raise ValueError("translation runner response must cover all target paragraph_ids")

    return translations


def _build_review_preview_text(base_text: str, suggestions: list[dict[str, Any]]) -> str:
    preview_text = base_text
    grouped_suggestions: dict[str, list[dict[str, Any]]] = {}
    for suggestion in suggestions:
        original = str(suggestion.get("original", ""))
        if not original:
            continue
        grouped_suggestions.setdefault(original, []).append(suggestion)

    for original, grouped in grouped_suggestions.items():
        if original not in preview_text:
            continue

        if len(grouped) == 1:
            merged = str(grouped[0].get("suggested", original))
            preview_text = preview_text.replace(original, merged, 1)
            continue

        merged = original
        for suggestion in grouped:
            suggested = str(suggestion.get("suggested", ""))
            if not suggested or suggested == merged:
                continue
            if original == suggested:
                continue
            merged = suggested

        preview_text = preview_text.replace(original, merged, 1)
    return preview_text


def _build_preview_source_paragraphs(
    *,
    chunk_payload: dict[str, Any],
    copyedit_review: dict[str, Any],
) -> list[dict[str, Any]]:
    revised_text = _build_review_preview_text(
        str(chunk_payload.get("base_text", "")),
        list(copyedit_review.get("suggestions", [])),
    )
    paragraph_texts = [
        paragraph.strip()
        for paragraph in revised_text.split("\n\n")
        if paragraph.strip()
    ]
    paragraph_ids = list(chunk_payload.get("paragraph_ids", []))
    if len(paragraph_texts) != len(paragraph_ids):
        raise ValueError("copyedit preview paragraph mapping does not match chunk paragraph_ids")

    return [
        {
            "paragraph_id": paragraph_id,
            "source_index": None,
            "review_status": "proposed",
            "text": paragraph_text,
        }
        for paragraph_id, paragraph_text in zip(paragraph_ids, paragraph_texts, strict=True)
    ]


def run_translation_es_pass(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    runner: Runner,
    model: str = "gpt-5.4",
    chunk_id: str | None = None,
) -> dict[str, Any]:
    chunk_payload, source_paragraphs = _select_chunk(
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_dir=reviews_dir,
        chunk_id=chunk_id,
    )
    style_guide_text = _read_optional_text(style_guide_path)
    glossary_text = _read_optional_text(glossary_path)
    decisions_text = _read_optional_text(decisions_path)
    prompt = build_translation_es_prompt(
        chunk_payload=chunk_payload,
        source_paragraphs=source_paragraphs,
        style_guide_text=style_guide_text,
        glossary_text=glossary_text,
        decisions_text=decisions_text,
    )
    schema = translation_es_output_schema()
    runner_payload = runner(prompt=prompt, schema=schema, model=model)
    translations = _validate_response(runner_payload, chunk_payload["paragraph_ids"])
    provenance = build_llm_provenance(
        model=model,
        prompt_template_id=TRANSLATION_ES_PROMPT_TEMPLATE_ID,
        prompt_version=TRANSLATION_ES_PROMPT_VERSION,
        prompt_text=prompt,
        schema_name=TRANSLATION_ES_SCHEMA_NAME,
        schema_version=TRANSLATION_ES_SCHEMA_VERSION,
        schema=schema,
        context_inputs={
            "style_guide": style_guide_text,
            "glossary": glossary_text,
            "decisions": decisions_text,
        },
    )

    review_payload = {
        "chunk_id": chunk_payload["id"],
        "pass": "translation-es",
        "source_language": "pt-BR",
        "target_language": "es",
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
        "translations": translations,
    }

    output_path = _translation_output_path(reviews_dir, chunk_payload["id"])
    write_json(output_path, review_payload)

    return {
        "chunk_id": chunk_payload["id"],
        "translated_paragraph_count": len(translations),
        "output_path": str(output_path),
        "model": model,
    }


def run_translation_es_preview_pass(
    *,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    runner: Runner,
    model: str = "gpt-5.4",
    chunk_id: str,
) -> dict[str, Any]:
    index_payload = _load_chunk_index(chunks_dir)
    chunk_entry = next(
        (chunk for chunk in index_payload.get("chunks", []) if chunk.get("id") == chunk_id),
        None,
    )
    if chunk_entry is None:
        raise ValueError(f"requested chunk not found for Spanish preview: {chunk_id}")

    chunk_payload = _read_json(chunks_dir / chunk_entry["file"])
    copyedit_path = reviews_ptbr_dir / f"{chunk_id}.copyedit.json"
    if not copyedit_path.exists():
        raise ValueError(f"copyedit review not found for Spanish preview: {chunk_id}")

    copyedit_review = _read_json(copyedit_path)
    source_paragraphs = _build_preview_source_paragraphs(
        chunk_payload=chunk_payload,
        copyedit_review=copyedit_review,
    )

    style_guide_text = _read_optional_text(style_guide_path)
    glossary_text = _read_optional_text(glossary_path)
    decisions_text = _read_optional_text(decisions_path)
    prompt = build_translation_es_prompt(
        chunk_payload=chunk_payload,
        source_paragraphs=source_paragraphs,
        style_guide_text=style_guide_text,
        glossary_text=glossary_text,
        decisions_text=decisions_text,
    )
    schema = translation_es_output_schema()
    runner_payload = runner(prompt=prompt, schema=schema, model=model)
    translations = _validate_response(runner_payload, chunk_payload["paragraph_ids"])
    provenance = build_llm_provenance(
        model=model,
        prompt_template_id=TRANSLATION_ES_PROMPT_TEMPLATE_ID,
        prompt_version=TRANSLATION_ES_PROMPT_VERSION,
        prompt_text=prompt,
        schema_name=TRANSLATION_ES_SCHEMA_NAME,
        schema_version=TRANSLATION_ES_SCHEMA_VERSION,
        schema=schema,
        context_inputs={
            "style_guide": style_guide_text,
            "glossary": glossary_text,
            "decisions": decisions_text,
            "source_mode": "copyedit-preview",
        },
    )

    review_payload = {
        "chunk_id": chunk_payload["id"],
        "pass": "translation-es-preview",
        "preview": True,
        "source_language": "pt-BR",
        "target_language": "es",
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
        "translations": translations,
    }

    output_path = _translation_preview_output_path(reviews_dir, chunk_payload["id"])
    write_json(output_path, review_payload)

    return {
        "chunk_id": chunk_payload["id"],
        "translated_paragraph_count": len(translations),
        "output_path": str(output_path),
        "model": model,
    }
