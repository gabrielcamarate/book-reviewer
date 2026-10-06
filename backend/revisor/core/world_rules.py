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
