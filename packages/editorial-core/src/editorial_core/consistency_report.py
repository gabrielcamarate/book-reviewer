from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from editorial_core.characters import read_characters_registry
from editorial_core.world_rules import read_world_rules_registry
from docx_adapter.reader import write_json

ENTRY_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_inline_code_values(line: str) -> list[str]:
    return re.findall(r"`([^`]+)`", line)


def _parse_glossary(glossary_path: Path) -> list[dict[str, Any]]:
    lines = glossary_path.read_text(encoding="utf-8").splitlines()
    entries: list[dict[str, Any]] = []
    current_section: str | None = None
    current_entry: dict[str, Any] | None = None

    for line in lines:
        section_match = SECTION_HEADING_RE.match(line)
        if section_match:
            current_section = section_match.group(1)
            continue

        entry_match = ENTRY_HEADING_RE.match(line)
        if entry_match:
            if current_entry is not None:
                entries.append(current_entry)
            current_entry = {
                "section": current_section,
                "title": entry_match.group(1),
                "preferred_form": entry_match.group(1),
                "aliases": [],
            }
            continue

        if current_entry is None:
            continue

        if line.startswith("- Preferred form:"):
            values = _parse_inline_code_values(line)
            if values:
                current_entry["preferred_form"] = values[0]
        elif line.startswith("- Expanded form:"):
            values = _parse_inline_code_values(line)
            if values:
                current_entry["expanded_form"] = values[0]
        elif line.startswith("- Observed aliases or variants:"):
            aliases = _parse_inline_code_values(line)
            current_entry["aliases"] = [alias for alias in aliases if alias != "none confirmed"]

    if current_entry is not None:
        entries.append(current_entry)

    return entries


def _load_consolidated_paragraphs(consolidated_dir: Path) -> list[dict[str, Any]]:
    index_path = consolidated_dir / "index.json"
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    index_payload = _read_json(index_path)
    paragraphs: list[dict[str, Any]] = []
    for section_entry in index_payload["sections"]:
        section_path = consolidated_dir / section_entry["file"]
        if not section_path.exists():
            continue
        section_payload = _read_json(section_path)
        for paragraph in section_payload.get("paragraphs", []):
            paragraphs.append(
                {
                    "section_id": section_payload["id"],
                    "section_title": section_payload["title"],
                    "paragraph_id": paragraph["id"],
                    "text": paragraph["text"],
                }
            )
    return paragraphs


def _find_alias_usage(
    glossary_entries: list[dict[str, Any]],
    paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for entry in glossary_entries:
        preferred_form = entry.get("preferred_form", entry["title"])
        for alias in entry.get("aliases", []):
            if alias == preferred_form:
                continue
            for paragraph in paragraphs:
                if alias in paragraph["text"]:
                    findings.append(
                        {
                            "section_id": paragraph["section_id"],
                            "paragraph_id": paragraph["paragraph_id"],
                            "entry_title": entry["title"],
                            "preferred_form": preferred_form,
                            "observed_variant": alias,
                        }
                    )
    return findings


def _find_quote_anomalies(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for paragraph in paragraphs:
        opening_quotes = paragraph["text"].count("“")
        closing_quotes = paragraph["text"].count("”")
        if opening_quotes != closing_quotes:
            findings.append(
                {
                    "section_id": paragraph["section_id"],
                    "paragraph_id": paragraph["paragraph_id"],
                    "opening_quotes": opening_quotes,
                    "closing_quotes": closing_quotes,
                }
            )
    return findings


def _find_spacing_anomalies(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for paragraph in paragraphs:
        double_space_count = paragraph["text"].count("  ")
        if double_space_count:
            findings.append(
                {
                    "section_id": paragraph["section_id"],
                    "paragraph_id": paragraph["paragraph_id"],
                    "issue": "double_space",
                    "occurrences": double_space_count,
                }
            )
    return findings


def _find_similar_proper_names(glossary_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proper_names = [
        entry["preferred_form"]
        for entry in glossary_entries
        if entry.get("section") == "Proper Names"
    ]
    findings: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for index, left in enumerate(proper_names):
        for right in proper_names[index + 1 :]:
            ratio = SequenceMatcher(a=left, b=right).ratio()
            if ratio < 0.82:
                continue
            pair = tuple(sorted((left, right)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            findings.append(
                {
                    "left": left,
                    "right": right,
                    "similarity": round(ratio, 3),
                }
            )

    return findings


def _build_registry_groups(
    *,
    glossary_entries: list[dict[str, Any]],
    character_entries: list[dict[str, Any]],
    world_rule_entries: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}

    def ingest(entry: dict[str, Any], source: str) -> None:
        title = str(entry.get("title", "")).strip()
        preferred_form = str(entry.get("preferred_form") or title).strip()
        if not title or not preferred_form:
            return
        key = title.casefold()
        group = groups.setdefault(
            key,
            {
                "entry_title": title,
                "preferred_form": preferred_form,
                "aliases": [],
                "registry_sources": [],
            },
        )
        if source not in group["registry_sources"]:
            group["registry_sources"].append(source)
        for alias in entry.get("aliases", []):
            normalized_alias = str(alias).strip()
            if normalized_alias and normalized_alias not in group["aliases"]:
                group["aliases"].append(normalized_alias)

    for entry in glossary_entries:
        ingest(entry, "glossary")
    for entry in character_entries:
        ingest(entry, "characters")
    for entry in world_rule_entries.get("organizations", []):
        ingest(entry, "world_rules")
    for entry in world_rule_entries.get("concepts", []):
        ingest(entry, "world_rules")

    return list(groups.values())


def _find_cross_chapter_entity_variants(
    registry_groups: list[dict[str, Any]],
    paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for group in registry_groups:
        observed_forms: list[str] = []
        paragraph_ids: list[str] = []
        chapter_ids: list[str] = []
        search_forms = [group["preferred_form"], *group.get("aliases", [])]

        for paragraph in paragraphs:
            text = paragraph["text"]
            matched_form: str | None = None
            for search_form in search_forms:
                if search_form and search_form in text:
                    matched_form = search_form
                    break
            if matched_form is None:
                continue
            if matched_form not in observed_forms:
                observed_forms.append(matched_form)
            if paragraph["paragraph_id"] not in paragraph_ids:
                paragraph_ids.append(paragraph["paragraph_id"])
            if paragraph["section_id"] not in chapter_ids:
                chapter_ids.append(paragraph["section_id"])

        if len(chapter_ids) < 2 or len(observed_forms) < 2:
            continue

        findings.append(
            {
                "entry_title": group["entry_title"],
                "preferred_form": group["preferred_form"],
                "registry_sources": sorted(group["registry_sources"]),
                "chapter_ids": sorted(chapter_ids),
                "paragraph_ids": paragraph_ids,
                "observed_forms": observed_forms,
            }
        )

    return findings


def generate_consistency_report(
    *,
    consolidated_dir: Path,
    glossary_path: Path,
    characters_path: Path,
    world_rules_path: Path,
    reports_dir: Path,
) -> dict[str, Any]:
    paragraphs = _load_consolidated_paragraphs(consolidated_dir)
    glossary_entries = _parse_glossary(glossary_path)
    character_entries = read_characters_registry(characters_path)
    world_rule_entries = read_world_rules_registry(world_rules_path)
    registry_groups = _build_registry_groups(
        glossary_entries=glossary_entries,
        character_entries=character_entries,
        world_rule_entries=world_rule_entries,
    )

    findings_by_type = {
        "alias_usage": _find_alias_usage(glossary_entries, paragraphs),
        "quote_anomalies": _find_quote_anomalies(paragraphs),
        "spacing_anomalies": _find_spacing_anomalies(paragraphs),
        "similar_proper_names": _find_similar_proper_names(glossary_entries),
        "cross_chapter_entity_variants": _find_cross_chapter_entity_variants(registry_groups, paragraphs),
    }

    report_payload = {
        "scope": {
            "section_count": len({paragraph["section_id"] for paragraph in paragraphs}),
            "paragraph_count": len(paragraphs),
            "glossary_entry_count": len(glossary_entries),
            "character_entry_count": len(character_entries),
            "world_rule_entry_count": len(world_rule_entries.get("organizations", []))
            + len(world_rule_entries.get("concepts", [])),
        },
        "finding_count": sum(len(findings) for findings in findings_by_type.values()),
        "findings_by_type": findings_by_type,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "ptbr-consistency-report.json"
    write_json(report_path, report_payload)

    return {
        "report_path": str(report_path),
        "finding_count": report_payload["finding_count"],
        "section_count": report_payload["scope"]["section_count"],
        "paragraph_count": report_payload["scope"]["paragraph_count"],
    }
