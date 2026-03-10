from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from docx_adapter.reader import write_json

CHAPTER_RE = re.compile(
    r"^Cap[ií]tulo\s+([IVXLCDM]+|\d+)(?::\s*(.+?))?\.?$",
    re.IGNORECASE,
)

FRONTMATTER_TITLES = {
    "o escritor",
    "créditos",
    "creditos",
    "agradecimentos",
    "prefácio",
    "prefacio",
    "introdução",
    "introducao",
    "prólogo",
    "prologo",
    "sumário",
    "sumario",
}

BACKMATTER_TITLES = {
    "epílogo",
    "epilogo",
    "pósfácio",
    "posfacio",
}


def _normalize_heading(text: str) -> str:
    return " ".join(text.split()).strip().casefold()


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _slugify(text: str) -> str:
    simplified = _strip_accents(text).casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", simplified).strip("-")
    return slug or "untitled"


def _is_divider(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and set(stripped) <= {"*", "-", "▬", "_", " "} and len(stripped) >= 3


def _is_heading_candidate(text: str) -> bool:
    stripped = text.strip()
    if not stripped or "\t" in stripped or _is_divider(stripped):
        return False
    normalized = _normalize_heading(stripped)
    if normalized in FRONTMATTER_TITLES or normalized in BACKMATTER_TITLES:
        return True
    return CHAPTER_RE.match(stripped) is not None


def _build_section_id(section_type: str, order: int, title_slug: str) -> str:
    return f"{section_type}-{order:04d}-{title_slug}"


def _start_section(
    sections: list[dict[str, Any]],
    counters: dict[str, int],
    section_type: str,
    title: str,
    slug_source: str,
    heading_source_index: int | None,
) -> dict[str, Any]:
    counters[section_type] += 1
    section_id = _build_section_id(section_type, counters[section_type], _slugify(slug_source))
    section = {
        "id": section_id,
        "type": section_type,
        "order": counters[section_type],
        "title": title,
        "heading_source_index": heading_source_index,
        "paragraphs": [],
    }
    sections.append(section)
    return section


def _append_paragraph(section: dict[str, Any], source_index: int, text: str) -> None:
    paragraph_id = f"{section['id']}-p-{len(section['paragraphs']) + 1:04d}"
    section["paragraphs"].append(
        {
            "id": paragraph_id,
            "source_index": source_index,
            "text": text,
        }
    )


def _finalize_sections(sections: list[dict[str, Any]]) -> None:
    for section in sections:
        if section["paragraphs"]:
            section["source_start_index"] = section["paragraphs"][0]["source_index"]
            section["source_end_index"] = section["paragraphs"][-1]["source_index"]
        else:
            section["source_start_index"] = section["heading_source_index"]
            section["source_end_index"] = section["heading_source_index"]
        section["paragraph_count"] = len(section["paragraphs"])


def segment_paragraphs(paragraphs: list[dict[str, Any]]) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    counters = {"frontmatter": 0, "chapter": 0, "backmatter": 0}
    current_section: dict[str, Any] | None = None
    has_seen_chapter = False
    inside_toc = False

    index = 0
    while index < len(paragraphs):
        paragraph = paragraphs[index]
        text = str(paragraph.get("text", ""))
        stripped = text.strip()

        if not stripped:
            index += 1
            continue

        if _is_divider(stripped):
            if inside_toc:
                inside_toc = False
                current_section = None
            index += 1
            continue

        normalized = _normalize_heading(stripped)
        chapter_match = CHAPTER_RE.match(stripped) if "\t" not in stripped else None

        if inside_toc:
            if current_section is None:
                raise ValueError("table of contents state requires an active section")
            _append_paragraph(current_section, int(paragraph["index"]), stripped)
            index += 1
            continue

        if normalized in FRONTMATTER_TITLES or normalized in BACKMATTER_TITLES or chapter_match:
            title = stripped
            section_type = "frontmatter"
            consume_subtitle = False
            slug_source = stripped

            if chapter_match:
                has_seen_chapter = True
                section_type = "chapter"
                title_suffix = chapter_match.group(2)

                if title_suffix:
                    title = stripped
                    slug_source = title_suffix
                else:
                    next_index = index + 1
                    while next_index < len(paragraphs):
                        next_text = str(paragraphs[next_index].get("text", "")).strip()
                        if not next_text or _is_divider(next_text):
                            next_index += 1
                            continue
                        if _is_heading_candidate(next_text):
                            break
                        if len(next_text) <= 120:
                            title = f"{stripped.rstrip('.')} — {next_text}"
                            slug_source = next_text
                            consume_subtitle = True
                        break

            elif normalized in BACKMATTER_TITLES:
                section_type = "backmatter"
            elif has_seen_chapter:
                section_type = "backmatter"

            current_section = _start_section(
                sections,
                counters,
                section_type,
                title,
                slug_source,
                int(paragraph["index"]),
            )
            inside_toc = normalized in {"sumário", "sumario"}

            if consume_subtitle:
                index = next_index + 1
            else:
                index += 1
            continue

        if current_section is None:
            current_section = _start_section(
                sections,
                counters,
                "frontmatter" if not has_seen_chapter else "backmatter",
                "Opening" if not has_seen_chapter else "Untitled Section",
                "Opening" if not has_seen_chapter else "Untitled Section",
                None,
            )

        _append_paragraph(current_section, int(paragraph["index"]), stripped)
        index += 1

    _finalize_sections(sections)

    return {
        "section_count": len(sections),
        "chapter_count": sum(1 for section in sections if section["type"] == "chapter"),
        "sections": sections,
    }


def segment_extracted_manuscript(extracted_dir: Path, output_dir: Path) -> dict[str, Any]:
    paragraphs_path = extracted_dir / "paragraphs.json"
    paragraphs = json.loads(paragraphs_path.read_text(encoding="utf-8"))

    segmented = segment_paragraphs(paragraphs)
    output_dir.mkdir(parents=True, exist_ok=True)

    for existing_file in output_dir.glob("*.json"):
        existing_file.unlink()

    index_payload = {
        "section_count": segmented["section_count"],
        "chapter_count": segmented["chapter_count"],
        "sections": [
            {
                "id": section["id"],
                "type": section["type"],
                "order": section["order"],
                "title": section["title"],
                "heading_source_index": section["heading_source_index"],
                "source_start_index": section["source_start_index"],
                "source_end_index": section["source_end_index"],
                "paragraph_count": section["paragraph_count"],
                "file": f"{section['id']}.json",
            }
            for section in segmented["sections"]
        ],
    }

    write_json(output_dir / "index.json", index_payload)

    for section in segmented["sections"]:
        write_json(output_dir / f"{section['id']}.json", section)

    return {
        "section_count": segmented["section_count"],
        "chapter_count": segmented["chapter_count"],
        "output_dir": str(output_dir),
    }
