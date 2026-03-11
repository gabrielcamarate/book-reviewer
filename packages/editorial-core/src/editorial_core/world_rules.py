from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _parse_backtick_values(raw_value: str) -> list[str]:
    if "none confirmed" in raw_value.lower():
        return []
    matches = re.findall(r"`([^`]+)`", raw_value)
    if matches:
        return [match.strip() for match in matches if match.strip()]
    return [raw_value.split(":", 1)[1].strip()] if ":" in raw_value else [raw_value.strip()]


def _parse_glossary_sections(glossary_text: str) -> dict[str, list[dict[str, Any]]]:
    sections = {
        "Organizations and Acronyms": [],
        "Concepts and Formulas": [],
    }
    active_section: str | None = None
    current: dict[str, Any] | None = None

    for line in glossary_text.splitlines():
        if line.startswith("## "):
            if active_section in sections and current is not None:
                sections[active_section].append(current)
                current = None
            title = line.removeprefix("## ").strip()
            active_section = title if title in sections else None
            continue
        if active_section is None:
            continue
        if line.startswith("### "):
            if current is not None:
                sections[active_section].append(current)
            current = {"title": line.removeprefix("### ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("- Preferred form: "):
            values = _parse_backtick_values(line)
            current["preferred_form"] = values[0] if values else current["title"]
        elif line.startswith("- Expanded form: "):
            values = _parse_backtick_values(line)
            current["expanded_form"] = values[0] if values else ""
        elif line.startswith("- Observed aliases or variants: "):
            current["aliases"] = _parse_backtick_values(line)
        elif line.startswith("- Evidence: "):
            current["evidence"] = _parse_backtick_values(line)

    if active_section in sections and current is not None:
        sections[active_section].append(current)
    return sections


def _render_section(
    title: str,
    entries: list[dict[str, Any]],
    *,
    include_expanded_form: bool,
) -> list[str]:
    lines = [f"## {title}", ""]
    for entry in entries:
        alias_line = (
            ", ".join(f"`{alias}`" for alias in entry.get("aliases", []))
            if entry.get("aliases")
            else "none confirmed"
        )
        evidence_line = (
            ", ".join(f"`{item}`" for item in entry.get("evidence", []))
            if entry.get("evidence")
            else "none confirmed"
        )
        lines.extend(
            [
                f"### {entry['title']}",
                f"- Preferred form: `{entry['preferred_form']}`",
            ]
        )
        if include_expanded_form:
            lines.append(f"- Expanded form: `{entry.get('expanded_form', '')}`")
        lines.extend(
            [
                f"- Observed aliases or variants: {alias_line}",
                f"- Evidence: {evidence_line}",
                "",
            ]
        )
    return lines


def generate_world_rules_registry(
    *,
    glossary_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    sections = _parse_glossary_sections(glossary_path.read_text(encoding="utf-8"))
    organizations = sections["Organizations and Acronyms"]
    concepts = sections["Concepts and Formulas"]
    lines = [
        "# World Rules Registry",
        "",
        "## Scope",
        f"- Organizations and acronyms: `{len(organizations)}`",
        f"- Concepts and formulas: `{len(concepts)}`",
        "",
    ]
    lines.extend(_render_section("Organizations and Acronyms", organizations, include_expanded_form=True))
    lines.extend(_render_section("Concepts and Formulas", concepts, include_expanded_form=False))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {
        "organization_count": len(organizations),
        "concept_count": len(concepts),
        "output_path": str(output_path),
    }


def read_world_rules_registry(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {"organizations": [], "concepts": []}

    sections = {"organizations": [], "concepts": []}
    active_key: str | None = None
    current: dict[str, Any] | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if active_key and current is not None:
                sections[active_key].append(current)
                current = None
            title = line.removeprefix("## ").strip()
            active_key = {
                "Organizations and Acronyms": "organizations",
                "Concepts and Formulas": "concepts",
            }.get(title)
            continue
        if active_key is None:
            continue
        if line.startswith("### "):
            if current is not None:
                sections[active_key].append(current)
            current = {"title": line.removeprefix("### ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("- Preferred form: "):
            values = _parse_backtick_values(line)
            current["preferred_form"] = values[0] if values else current["title"]
        elif line.startswith("- Expanded form: "):
            values = _parse_backtick_values(line)
            current["expanded_form"] = values[0] if values else ""
        elif line.startswith("- Observed aliases or variants: "):
            current["aliases"] = _parse_backtick_values(line)
        elif line.startswith("- Evidence: "):
            current["evidence"] = _parse_backtick_values(line)

    if active_key and current is not None:
        sections[active_key].append(current)
    return sections
