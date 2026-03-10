from __future__ import annotations

import copy
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from docx_adapter.reader import NS, WORD_NS

XML_NS = "http://www.w3.org/XML/1998/namespace"


def _build_paragraph_element(text: str) -> ET.Element:
    paragraph = ET.Element(f"{{{WORD_NS}}}p")

    if text == "":
        return paragraph

    run = ET.SubElement(paragraph, f"{{{WORD_NS}}}r")
    lines = text.split("\n")
    for index, line in enumerate(lines):
        text_node = ET.SubElement(run, f"{{{WORD_NS}}}t")
        text_node.set(f"{{{XML_NS}}}space", "preserve")
        text_node.text = line
        if index < len(lines) - 1:
            ET.SubElement(run, f"{{{WORD_NS}}}br")

    return paragraph


def _render_document_xml(template_xml: bytes, paragraphs: list[str]) -> bytes:
    root = ET.fromstring(template_xml)
    body = root.find("w:body", namespaces=NS)
    if body is None:
        raise ValueError("template docx is missing word body")

    sect_pr = body.find("w:sectPr", namespaces=NS)
    sect_pr_copy = copy.deepcopy(sect_pr) if sect_pr is not None else None

    body.clear()
    for paragraph_text in paragraphs:
        body.append(_build_paragraph_element(paragraph_text))
    if sect_pr_copy is not None:
        body.append(sect_pr_copy)

    ET.register_namespace("w", WORD_NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def export_docx_from_template(
    *,
    template_path: Path,
    output_path: Path,
    paragraphs: list[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(template_path) as template_archive:
        members = {info.filename: template_archive.read(info.filename) for info in template_archive.infolist()}

    document_xml = members.get("word/document.xml")
    if document_xml is None:
        raise ValueError("template docx is missing word/document.xml")

    members["word/document.xml"] = _render_document_xml(document_xml, paragraphs)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as output_archive:
        for filename, content in members.items():
            output_archive.writestr(filename, content)
