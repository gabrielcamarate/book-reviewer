from __future__ import annotations

from pathlib import Path
from typing import Any


def _parse_alias_values(raw_value: str) -> list[str]:
    cleaned = raw_value.strip()
    if not cleaned or cleaned == "none confirmed":
        return []
    aliases: list[str] = []
    for part in cleaned.split(","):
        alias = part.strip().strip("`").strip()
        if alias and alias not in aliases:
            aliases.append(alias)
    return aliases


def _format_alias_values(aliases: list[str]) -> str:
    if not aliases:
        return "none confirmed"
    return ", ".join(f"`{alias}`" for alias in aliases)


def parse_glossary_entries(glossary_path: Path) -> list[dict[str, Any]]:
    lines = glossary_path.read_text(encoding="utf-8").splitlines()
    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] | None = None
    current_entry: dict[str, Any] | None = None

    for line in lines:
        if line.startswith("## "):
            current_section = {"title": line.removeprefix("## ").strip(), "entries": []}
            sections.append(current_section)
            current_entry = None
            continue
        if line.startswith("### "):
            if current_section is None:
                continue
            current_entry = {
                "title": line.removeprefix("### ").strip(),
                "preferred_form": "",
                "aliases": [],
                "expanded_form": None,
                "evidence": "",
            }
            current_section["entries"].append(current_entry)
            continue
        if current_entry is None or not line.startswith("- "):
            continue

        label, _, raw_value = line[2:].partition(":")
        value = raw_value.strip()
        normalized_label = label.strip().casefold()
        if normalized_label == "preferred form":
            current_entry["preferred_form"] = value.strip("`")
        elif normalized_label == "observed aliases or variants":
            current_entry["aliases"] = _parse_alias_values(value)
        elif normalized_label == "expanded form":
            current_entry["expanded_form"] = value.strip("`")
        elif normalized_label == "evidence":
            current_entry["evidence"] = value

    return sections


def curate_glossary_entry(
    *,
    glossary_path: Path,
    entry_title: str,
    preferred_form: str,
    aliases_text: str,
) -> dict[str, Any]:
    lines = glossary_path.read_text(encoding="utf-8").splitlines()
    aliases = _parse_alias_values(aliases_text)

    entry_start: int | None = None
    entry_end: int | None = None
    for index, line in enumerate(lines):
        if line == f"### {entry_title}":
            entry_start = index
            entry_end = len(lines)
            for next_index in range(index + 1, len(lines)):
                if lines[next_index].startswith(("### ", "## ")):
                    entry_end = next_index
                    break
            break

    if entry_start is None or entry_end is None:
        raise ValueError(f"glossary entry not found: {entry_title}")

    preferred_line_found = False
    aliases_line_found = False
    for index in range(entry_start + 1, entry_end):
        if lines[index].startswith("- Preferred form:"):
            lines[index] = f"- Preferred form: `{preferred_form.strip()}`"
            preferred_line_found = True
        elif lines[index].startswith("- Observed aliases or variants:"):
            lines[index] = f"- Observed aliases or variants: {_format_alias_values(aliases)}"
            aliases_line_found = True

    if not preferred_line_found or not aliases_line_found:
        raise ValueError(f"glossary entry is missing curatable fields: {entry_title}")

    glossary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "entry_title": entry_title,
        "preferred_form": preferred_form.strip(),
        "aliases": aliases,
        "glossary_path": str(glossary_path),
    }

