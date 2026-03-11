from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx_adapter.writer import export_docx_from_template
from editorial_core.export_snapshot import create_export_snapshot_manifest


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_current_section(
    *,
    chapters_dir: Path,
    consolidated_dir: Path,
    section_file: str,
) -> dict[str, Any]:
    consolidated_path = consolidated_dir / section_file
    if consolidated_path.exists():
        return _read_json(consolidated_path)
    return _read_json(chapters_dir / section_file)


def _load_translation_map(translations_dir: Path) -> dict[str, str]:
    translation_map: dict[str, str] = {}
    if not translations_dir.exists():
        return translation_map

    for translation_path in sorted(translations_dir.glob("*.translation-es.json")):
        payload = _read_json(translation_path)
        for entry in payload.get("translations", []):
            translation_map[entry["paragraph_id"]] = entry["translated_text"]

    return translation_map


def _section_paragraphs_for_export(
    *,
    section_entry: dict[str, Any],
    section_payload: dict[str, Any],
    language: str,
    translation_map: dict[str, str],
) -> list[str]:
    paragraphs: list[str] = []
    if section_entry.get("heading_source_index") is not None:
        paragraphs.append(section_payload["title"])

    for paragraph in section_payload.get("paragraphs", []):
        if language == "pt-BR":
            paragraphs.append(paragraph["text"])
            continue

        translated_text = translation_map.get(paragraph["id"])
        if translated_text is None:
            raise ValueError(
                f"missing Spanish translation for paragraph {paragraph['id']}"
            )
        paragraphs.append(translated_text)

    return paragraphs


def export_manuscript_docx(
    *,
    template_path: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    translations_dir: Path,
    output_path: Path,
    language: str = "pt-BR",
) -> dict[str, Any]:
    if language not in {"pt-BR", "es"}:
        raise ValueError(f"unsupported export language: {language}")

    chapter_index = _read_json(chapters_dir / "index.json")
    translation_map = _load_translation_map(translations_dir) if language == "es" else {}
    snapshot_manifest = create_export_snapshot_manifest(
        template_path=template_path,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        translations_dir=translations_dir,
        output_path=output_path,
        language=language,
    )

    paragraphs: list[str] = []
    for section_entry in chapter_index.get("sections", []):
        section_payload = _load_current_section(
            chapters_dir=chapters_dir,
            consolidated_dir=consolidated_dir,
            section_file=section_entry["file"],
        )
        paragraphs.extend(
            _section_paragraphs_for_export(
                section_entry=section_entry,
                section_payload=section_payload,
                language=language,
                translation_map=translation_map,
            )
        )

    export_docx_from_template(
        template_path=template_path,
        output_path=output_path,
        paragraphs=paragraphs,
    )

    return {
        "language": language,
        "paragraph_count": len(paragraphs),
        "output_path": str(output_path),
        "section_count": chapter_index["section_count"],
        "snapshot_manifest_path": snapshot_manifest["manifest_path"],
        "snapshot_file_count": snapshot_manifest["file_count"],
    }
