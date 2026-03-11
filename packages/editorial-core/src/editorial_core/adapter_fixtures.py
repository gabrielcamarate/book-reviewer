from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from editorial_core.job_log import read_recent_job_logs
from editorial_core.queue import build_review_queue


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_chunk_summary(
    *,
    chunks_dir: Path,
    consolidated_dir: Path,
) -> dict[str, Any]:
    chunk_index = _read_json(chunks_dir / "index.json")
    chunk_entry = chunk_index["chunks"][0]
    chunk_payload = _read_json(chunks_dir / chunk_entry["file"])
    section_payload = _read_json(consolidated_dir / f"{chunk_payload['section_id']}.json")
    target_paragraph_ids = set(chunk_payload.get("paragraph_ids", []))
    paragraph_summaries = [
        {
            "paragraph_id": paragraph["id"],
            "review_status": paragraph.get("review_status", "unknown"),
        }
        for paragraph in section_payload.get("paragraphs", [])
        if paragraph.get("id") in target_paragraph_ids
    ]
    return {
        "chunk_id": chunk_payload["id"],
        "section_id": chunk_payload["section_id"],
        "section_title": chunk_payload.get("section_title", ""),
        "paragraph_count": len(chunk_payload.get("paragraph_ids", [])),
        "review_status": chunk_entry.get("review_status", "unknown"),
        "paragraph_summaries": paragraph_summaries,
    }


def _compute_export_readiness(
    *,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, dict[str, Any]]:
    chapter_index = _read_json(chapters_dir / "index.json")
    translation_map: dict[str, str] = {}
    if reviews_es_dir.exists():
        for translation_path in sorted(reviews_es_dir.glob("*.translation-es.json")):
            payload = _read_json(translation_path)
            for entry in payload.get("translations", []):
                translation_map[entry["paragraph_id"]] = entry["translated_text"]

    required_paragraph_ids: list[str] = []
    for section in chapter_index.get("sections", []):
        section_path = consolidated_dir / section["file"]
        if not section_path.exists():
            continue
        section_payload = _read_json(section_path)
        required_paragraph_ids.extend(
            paragraph["id"] for paragraph in section_payload.get("paragraphs", [])
        )

    missing_translation_ids = [
        paragraph_id for paragraph_id in required_paragraph_ids if paragraph_id not in translation_map
    ]
    return {
        "pt-BR": {
            "eligible": True,
            "reason": "O export em pt-BR está disponível.",
        },
        "es": {
            "eligible": not missing_translation_ids,
            "reason": (
                "O export em espanhol está disponível."
                if not missing_translation_ids
                else f"Faltam traduções para {len(missing_translation_ids)} parágrafo(s)."
            ),
        },
    }


def generate_adapter_contract_fixtures(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    jobs_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    queue_fixture = build_review_queue(
        chunks_dir=chunks_dir,
        reviews_ptbr_dir=reviews_ptbr_dir,
        reviews_es_dir=reviews_es_dir,
    )
    chunk_fixture = _build_chunk_summary(
        chunks_dir=chunks_dir,
        consolidated_dir=consolidated_dir,
    )
    recent_jobs = read_recent_job_logs(jobs_dir=jobs_dir, limit=1)
    job_fixture = recent_jobs[0] if recent_jobs else {
        "job_type": "none",
        "status": "unknown",
        "target_id": "",
        "details": {},
    }
    export_fixture = _compute_export_readiness(
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_es_dir=reviews_es_dir,
    )

    fixtures = {
        "queue-summary.json": queue_fixture,
        "chunk-summary.json": chunk_fixture,
        "job-summary.json": job_fixture,
        "export-readiness.json": export_fixture,
    }
    for filename, payload in fixtures.items():
        _write_json(output_dir / filename, payload)

    return {
        "output_dir": str(output_dir),
        "fixture_count": len(fixtures),
        "files": sorted(fixtures.keys()),
    }
