from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def _initial_document() -> str:
    return "# Editorial Decisions\n\n"


def read_editorial_decisions(decisions_path: Path) -> list[dict[str, str]]:
    if not decisions_path.exists():
        return []

    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in decisions_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current is not None:
                entries.append(current)
            current = {"title": line.removeprefix("## ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("- Timestamp: "):
            current["timestamp"] = line.removeprefix("- Timestamp: ").strip()
        elif line.startswith("- Scope: "):
            current["scope"] = line.removeprefix("- Scope: ").strip()
        elif line.startswith("- Rationale: "):
            current["rationale"] = line.removeprefix("- Rationale: ").strip()

    if current is not None:
        entries.append(current)
    return entries


def append_editorial_decision(
    *,
    decisions_path: Path,
    title: str,
    rationale: str,
    scope: str,
) -> dict[str, Any]:
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    if not decisions_path.exists():
        decisions_path.write_text(_initial_document(), encoding="utf-8")

    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = (
        f"## {title.strip()}\n"
        f"- Timestamp: {timestamp}\n"
        f"- Scope: {scope.strip()}\n"
        f"- Rationale: {rationale.strip()}\n\n"
    )
    with decisions_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)

    entries = read_editorial_decisions(decisions_path)
    return {
        "decision_count": len(entries),
        "path": str(decisions_path),
        "last_title": title.strip(),
    }
