from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from docx_adapter.reader import write_json


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_entry(path: Path, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def create_export_snapshot_manifest(
    *,
    template_path: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    translations_dir: Path,
    output_path: Path,
    language: str,
) -> dict[str, Any]:
    chapter_index_path = chapters_dir / "index.json"
    chapter_index = _read_json(chapter_index_path)
    files: list[dict[str, Any]] = [
        _snapshot_entry(template_path, "template_docx"),
        _snapshot_entry(chapter_index_path, "chapter_index"),
    ]

    for section in chapter_index.get("sections", []):
        chapter_section_path = chapters_dir / section["file"]
        files.append(_snapshot_entry(chapter_section_path, "chapter_section"))

    consolidated_index_path = consolidated_dir / "index.json"
    if consolidated_index_path.exists():
        files.append(_snapshot_entry(consolidated_index_path, "consolidated_index"))

    for section in chapter_index.get("sections", []):
        consolidated_section_path = consolidated_dir / section["file"]
        if consolidated_section_path.exists():
            files.append(_snapshot_entry(consolidated_section_path, "consolidated_section"))

    if language == "es" and translations_dir.exists():
        for translation_path in sorted(translations_dir.glob("*.translation-es.json")):
            files.append(_snapshot_entry(translation_path, "translation_review"))

    snapshot_dir = output_path.parent.parent / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    language_slug = "ptbr" if language == "pt-BR" else "es"
    manifest_path = snapshot_dir / f"export-{language_slug}-{timestamp}.json"

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "language": language,
        "output_path": str(output_path),
        "file_count": len(files),
        "files": files,
    }
    write_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest

