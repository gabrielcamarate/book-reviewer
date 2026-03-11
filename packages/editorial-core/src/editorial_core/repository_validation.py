from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REQUIRED_PATHS = (
    "editorial/STYLE_GUIDE.md",
    "editorial/GLOSSARY.md",
    "editorial/DECISIONS.md",
    "manuscript/chunks/index.json",
    "manuscript/chapters/index.json",
    "manuscript/consolidated/index.json",
)


def _validate_json_file(path: Path) -> str | None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return f"{path.as_posix()} is not valid JSON: {error}"
    return None


def validate_repository_state(*, root_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    for relative_path in _REQUIRED_PATHS:
        path = root_dir / relative_path
        if not path.exists():
            errors.append(f"missing required artifact: {relative_path}")
            continue
        if path.suffix == ".json":
            json_error = _validate_json_file(path)
            if json_error is not None:
                errors.append(json_error)

    return {
        "ok": not errors,
        "error_count": len(errors),
        "errors": errors,
    }
