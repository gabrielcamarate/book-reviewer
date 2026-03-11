from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_NON_CHARACTER_KEYWORDS = {
    "fazenda",
    "ilha",
    "igreja",
    "grupo",
    "escola",
    "conselho",
    "presídio",
    "sistema",
    "energia",
    "poder",
    "governador",
    "gerente",
}


def _parse_backtick_values(raw_value: str) -> list[str]:
    if "none confirmed" in raw_value.lower():
        return []
    matches = re.findall(r"`([^`]+)`", raw_value)
    if matches:
        return [match.strip() for match in matches if match.strip()]
    return [raw_value.split(":", 1)[1].strip()] if ":" in raw_value else [raw_value.strip()]


def _parse_glossary_proper_names(glossary_text: str) -> list[dict[str, Any]]:
    in_proper_names = False
    current: dict[str, Any] | None = None
    entries: list[dict[str, Any]] = []

    for line in glossary_text.splitlines():
        if line.startswith("## "):
            if in_proper_names and current is not None:
                entries.append(current)
                current = None
            in_proper_names = line.strip() == "## Proper Names"
            continue
        if not in_proper_names:
            continue
        if line.startswith("### "):
            if current is not None:
                entries.append(current)
            current = {"title": line.removeprefix("### ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("- Preferred form: "):
            current["preferred_form"] = _parse_backtick_values(line)[0]
        elif line.startswith("- Observed aliases or variants: "):
            current["aliases"] = _parse_backtick_values(line)
        elif line.startswith("- Evidence: "):
            current["evidence"] = _parse_backtick_values(line)

    if in_proper_names and current is not None:
        entries.append(current)
    return entries


def _is_character_candidate(entry: dict[str, Any]) -> bool:
    preferred_form = str(entry.get("preferred_form") or entry.get("title") or "").strip()
    if not preferred_form:
        return False
    lowered = preferred_form.lower()
    if any(keyword in lowered for keyword in _NON_CHARACTER_KEYWORDS):
        return False
    if preferred_form.isupper():
        return False
    return " " in preferred_form


def _render_characters_registry(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Characters Registry",
        "",
        "## Scope",
        f"- Character entries: `{len(entries)}`",
        "",
    ]
    for entry in entries:
        aliases = entry.get("aliases", [])
        evidence = entry.get("evidence", [])
        alias_line = (
            ", ".join(f"`{alias}`" for alias in aliases)
            if aliases
            else "none confirmed"
        )
        evidence_line = ", ".join(f"`{item}`" for item in evidence) if evidence else "none confirmed"
        lines.extend(
            [
                f"### {entry['title']}",
                f"- Preferred form: `{entry['preferred_form']}`",
                f"- Observed aliases or variants: {alias_line}",
                f"- Evidence: {evidence_line}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def generate_characters_registry(
    *,
    glossary_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    glossary_text = glossary_path.read_text(encoding="utf-8")
    entries = [
        {
            "title": str(entry.get("title", "")).strip(),
            "preferred_form": str(entry.get("preferred_form") or entry.get("title") or "").strip(),
            "aliases": list(entry.get("aliases", [])),
            "evidence": list(entry.get("evidence", [])),
        }
        for entry in _parse_glossary_proper_names(glossary_text)
        if _is_character_candidate(entry)
    ]
    entries.sort(key=lambda item: item["title"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_characters_registry(entries), encoding="utf-8")
    return {
        "character_count": len(entries),
        "output_path": str(output_path),
    }


def read_characters_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            if current is not None:
                entries.append(current)
            current = {"title": line.removeprefix("### ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("- Preferred form: "):
            values = _parse_backtick_values(line)
            current["preferred_form"] = values[0] if values else current["title"]
        elif line.startswith("- Observed aliases or variants: "):
            current["aliases"] = _parse_backtick_values(line)
        elif line.startswith("- Evidence: "):
            current["evidence"] = _parse_backtick_values(line)

    if current is not None:
        entries.append(current)
    return entries
