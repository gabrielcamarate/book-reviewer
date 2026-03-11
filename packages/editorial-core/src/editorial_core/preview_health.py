from __future__ import annotations

from pathlib import Path
from typing import Any

from editorial_core.repository_doctor import run_repository_doctor


def build_preview_health_payload(*, root_dir: Path) -> dict[str, Any]:
    diagnostics = run_repository_doctor(root_dir=root_dir)
    return {
        "status": "ok" if diagnostics["ok"] else "degraded",
        "repository_ok": diagnostics["ok"],
        "blocking_count": diagnostics["blocking_count"],
        "advisory_count": diagnostics["advisory_count"],
        "diagnostics_path": "/diagnostics",
    }


def build_preview_diagnostics_payload(*, root_dir: Path) -> dict[str, Any]:
    return run_repository_doctor(root_dir=root_dir)
