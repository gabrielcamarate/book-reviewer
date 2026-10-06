from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _slugify_target_id(target_id: str) -> str:
    return "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in target_id)


def append_job_log(
    *,
    jobs_dir: Path,
    job_type: str,
    status: str,
    target_id: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    jobs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="microseconds")
    filename = (
        f"{timestamp.replace(':', '-')}-{job_type}-{status}-{_slugify_target_id(target_id)}.json"
    )
    payload = {
        "timestamp": timestamp,
        "job_type": job_type,
        "status": status,
        "target_id": target_id,
        "details": details,
    }
    path = jobs_dir / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def read_recent_job_logs(*, jobs_dir: Path, limit: int = 10) -> list[dict[str, Any]]:
    if not jobs_dir.exists():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted(jobs_dir.glob("*.json"), reverse=True)[:limit]:
        entries.append(json.loads(path.read_text(encoding="utf-8")))
    return entries
