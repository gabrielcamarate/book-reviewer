from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from editorial_core.characters import read_characters_registry
from editorial_core.consistency_report import _build_registry_groups, _parse_glossary
from editorial_core.world_rules import read_world_rules_registry
from docx_adapter.reader import write_json


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_consolidated_paragraphs(consolidated_dir: Path) -> dict[str, dict[str, Any]]:
    index_path = consolidated_dir / "index.json"
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    paragraphs_by_id: dict[str, dict[str, Any]] = {}
    index_payload = _read_json(index_path)
    for section_entry in index_payload.get("sections", []):
        section_path = consolidated_dir / section_entry["file"]
        if not section_path.exists():
            continue
        section_payload = _read_json(section_path)
        for paragraph in section_payload.get("paragraphs", []):
            paragraphs_by_id[paragraph["id"]] = {
                "paragraph_id": paragraph["id"],
                "section_id": section_payload["id"],
                "section_title": section_payload.get("title", ""),
                "source_text": paragraph.get("text", ""),
            }
    return paragraphs_by_id


def _load_translated_paragraphs(
    *,
    translations_dir: Path,
    paragraphs_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    translated_paragraphs: list[dict[str, Any]] = []
    for translation_path in sorted(translations_dir.glob("*.translation-es.json")):
        payload = _read_json(translation_path)
        for translation in payload.get("translations", []):
            paragraph_id = translation.get("paragraph_id")
            if not isinstance(paragraph_id, str):
                continue
            source = paragraphs_by_id.get(paragraph_id)
            if source is None:
                continue
            translated_paragraphs.append(
                {
                    "chunk_id": payload.get("chunk_id"),
                    "paragraph_id": paragraph_id,
                    "section_id": source["section_id"],
                    "section_title": source["section_title"],
                    "source_text": source["source_text"],
                    "translated_text": translation.get("translated_text", ""),
                }
            )
    return translated_paragraphs


def _find_missing_term_preservation(
    registry_groups: list[dict[str, Any]],
    translated_paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for group in registry_groups:
        search_forms = [group["preferred_form"], *group.get("aliases", [])]
        for paragraph in translated_paragraphs:
            source_term: str | None = None
            for form in search_forms:
                if form and form in paragraph["source_text"]:
                    source_term = form
                    break
            if source_term is None:
                continue
            if any(form and form in paragraph["translated_text"] for form in search_forms):
                continue
            findings.append(
                {
                    "entry_title": group["entry_title"],
                    "preferred_form": group["preferred_form"],
                    "registry_sources": sorted(group["registry_sources"]),
                    "paragraph_id": paragraph["paragraph_id"],
                    "chapter_id": paragraph["section_id"],
                    "chunk_id": paragraph.get("chunk_id"),
                    "source_term": source_term,
                    "translated_excerpt": paragraph["translated_text"][:180],
                }
            )
    return findings


def _find_spanish_term_variants(
    registry_groups: list[dict[str, Any]],
    translated_paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for group in registry_groups:
        search_forms = [group["preferred_form"], *group.get("aliases", [])]
        observed_forms: list[str] = []
        paragraph_ids: list[str] = []
        chapter_ids: list[str] = []

        for paragraph in translated_paragraphs:
            if not any(form and form in paragraph["source_text"] for form in search_forms):
                continue
            matched_form: str | None = None
            for form in search_forms:
                if form and form in paragraph["translated_text"]:
                    matched_form = form
                    break
            if matched_form is None:
                continue
            if matched_form not in observed_forms:
                observed_forms.append(matched_form)
            if paragraph["paragraph_id"] not in paragraph_ids:
                paragraph_ids.append(paragraph["paragraph_id"])
            if paragraph["section_id"] not in chapter_ids:
                chapter_ids.append(paragraph["section_id"])

        if len(observed_forms) < 2:
            continue

        findings.append(
            {
                "entry_title": group["entry_title"],
                "preferred_form": group["preferred_form"],
                "registry_sources": sorted(group["registry_sources"]),
                "observed_forms": observed_forms,
                "paragraph_ids": paragraph_ids,
                "chapter_ids": chapter_ids,
            }
        )
    return findings


def generate_spanish_consistency_report(
    *,
    consolidated_dir: Path,
    translations_dir: Path,
    glossary_path: Path,
    characters_path: Path,
    world_rules_path: Path,
    reports_dir: Path,
) -> dict[str, Any]:
    paragraphs_by_id = _load_consolidated_paragraphs(consolidated_dir)
    translated_paragraphs = _load_translated_paragraphs(
        translations_dir=translations_dir,
        paragraphs_by_id=paragraphs_by_id,
    )
    glossary_entries = _parse_glossary(glossary_path) if glossary_path.exists() else []
    character_entries = read_characters_registry(characters_path)
    world_rule_entries = read_world_rules_registry(world_rules_path)
    registry_groups = _build_registry_groups(
        glossary_entries=glossary_entries,
        character_entries=character_entries,
        world_rule_entries=world_rule_entries,
    )

    findings_by_type = {
        "missing_term_preservation": _find_missing_term_preservation(
            registry_groups,
            translated_paragraphs,
        ),
        "spanish_term_variants": _find_spanish_term_variants(
            registry_groups,
            translated_paragraphs,
        ),
    }

    report_payload = {
        "scope": {
            "translated_chunk_count": len(
                {
                    paragraph["chunk_id"]
                    for paragraph in translated_paragraphs
                    if paragraph.get("chunk_id")
                }
            ),
            "translated_paragraph_count": len(translated_paragraphs),
            "tracked_entry_count": len(registry_groups),
        },
        "finding_count": sum(len(findings) for findings in findings_by_type.values()),
        "findings_by_type": findings_by_type,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "es-consistency-report.json"
    write_json(report_path, report_payload)
    return {
        "report_path": str(report_path),
        "finding_count": report_payload["finding_count"],
        "translated_paragraph_count": report_payload["scope"]["translated_paragraph_count"],
    }
