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


def _locate_entry(lines: list[str], entry_title: str) -> tuple[int, int]:
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
        raise ValueError(f"registry entry not found: {entry_title}")
    return entry_start, entry_end


def curate_character_entry(
    *,
    characters_path: Path,
    entry_title: str,
    preferred_form: str,
    aliases_text: str,
) -> dict[str, Any]:
    lines = characters_path.read_text(encoding="utf-8").splitlines()
    aliases = _parse_alias_values(aliases_text)
    entry_start, entry_end = _locate_entry(lines, entry_title)

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
        raise ValueError(f"character entry is missing curatable fields: {entry_title}")

    characters_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "entry_title": entry_title,
        "preferred_form": preferred_form.strip(),
        "aliases": aliases,
        "characters_path": str(characters_path),
    }


def curate_world_rule_entry(
    *,
    world_rules_path: Path,
    entry_title: str,
    preferred_form: str,
    aliases_text: str,
    expanded_form: str | None = None,
) -> dict[str, Any]:
    lines = world_rules_path.read_text(encoding="utf-8").splitlines()
    aliases = _parse_alias_values(aliases_text)
    entry_start, entry_end = _locate_entry(lines, entry_title)

    preferred_line_found = False
    aliases_line_found = False
    expanded_line_found = False
    for index in range(entry_start + 1, entry_end):
        if lines[index].startswith("- Preferred form:"):
            lines[index] = f"- Preferred form: `{preferred_form.strip()}`"
            preferred_line_found = True
        elif lines[index].startswith("- Expanded form:"):
            lines[index] = f"- Expanded form: `{(expanded_form or '').strip()}`"
            expanded_line_found = True
        elif lines[index].startswith("- Observed aliases or variants:"):
            lines[index] = f"- Observed aliases or variants: {_format_alias_values(aliases)}"
            aliases_line_found = True

    if not preferred_line_found or not aliases_line_found:
        raise ValueError(f"world rule entry is missing curatable fields: {entry_title}")

    world_rules_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "entry_title": entry_title,
        "preferred_form": preferred_form.strip(),
        "aliases": aliases,
        "expanded_form": expanded_form.strip() if expanded_line_found and expanded_form is not None else None,
        "world_rules_path": str(world_rules_path),
    }
