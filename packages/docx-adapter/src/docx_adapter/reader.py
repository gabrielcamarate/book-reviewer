from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
APP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"

NS = {
    "w": WORD_NS,
    "cp": CORE_NS,
    "dc": DC_NS,
    "dcterms": DCTERMS_NS,
    "app": APP_NS,
}


def _read_xml(zip_file: zipfile.ZipFile, inner_path: str) -> ET.Element | None:
    try:
        with zip_file.open(inner_path) as handle:
            return ET.parse(handle).getroot()
    except KeyError:
        return None


def _read_text(node: ET.Element, xpath: str) -> str | None:
    value = node.findtext(xpath, namespaces=NS)
    return value.strip() if value and value.strip() else None


def extract_docx_metadata(input_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(input_path) as archive:
        core = _read_xml(archive, "docProps/core.xml")
        app = _read_xml(archive, "docProps/app.xml")

    metadata: dict[str, Any] = {
        "source_file": input_path.name,
    }

    if core is not None:
        metadata["core"] = {
            "title": _read_text(core, "dc:title"),
            "subject": _read_text(core, "dc:subject"),
            "creator": _read_text(core, "dc:creator"),
            "description": _read_text(core, "dc:description"),
            "last_modified_by": _read_text(core, "cp:lastModifiedBy"),
            "revision": _read_text(core, "cp:revision"),
            "created_at": _read_text(core, "dcterms:created"),
            "modified_at": _read_text(core, "dcterms:modified"),
        }

    if app is not None:
        metadata["app"] = {
            "application": _read_text(app, "app:Application"),
            "pages": _read_text(app, "app:Pages"),
            "words": _read_text(app, "app:Words"),
            "characters": _read_text(app, "app:Characters"),
            "lines": _read_text(app, "app:Lines"),
            "paragraphs": _read_text(app, "app:Paragraphs"),
        }

    return metadata


def extract_docx_paragraphs(input_path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(input_path) as archive:
        document = _read_xml(archive, "word/document.xml")

    if document is None:
        raise ValueError("word/document.xml not found inside the .docx file")

    paragraphs: list[dict[str, Any]] = []

    for index, paragraph in enumerate(document.findall(".//w:p", namespaces=NS), start=1):
        fragments: list[str] = []

        for node in paragraph.iter():
            if node.tag == f"{{{WORD_NS}}}t":
                fragments.append(node.text or "")
            elif node.tag == f"{{{WORD_NS}}}tab":
                fragments.append("\t")
            elif node.tag in {f"{{{WORD_NS}}}br", f"{{{WORD_NS}}}cr"}:
                fragments.append("\n")

        raw_text = "".join(fragments)
        normalized_text = raw_text.strip()

        paragraphs.append(
            {
                "index": index,
                "text": normalized_text,
                "is_empty": normalized_text == "",
            }
        )

    return paragraphs


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
