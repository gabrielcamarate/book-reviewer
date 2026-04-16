from __future__ import annotations

from pathlib import Path
from typing import Any

from editorial_core.job_log import append_job_log
from editorial_core.translation_es import Runner, list_translation_es_candidates, run_translation_es_pass


def run_translation_es_batch(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    jobs_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    runner: Runner,
    model: str = "gpt-5.4",
    max_chunks: int | None = None,
    stop_on_error: bool = True,
) -> dict[str, Any]:
    candidates = list_translation_es_candidates(
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_dir=reviews_dir,
    )
    selected_chunk_ids = candidates["eligible_chunk_ids"]
    if max_chunks is not None:
        selected_chunk_ids = selected_chunk_ids[:max_chunks]

    processed: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    stopped_early = False

    for chunk_id in selected_chunk_ids:
        try:
            summary = run_translation_es_pass(
                chunks_dir=chunks_dir,
                chapters_dir=chapters_dir,
                consolidated_dir=consolidated_dir,
                reviews_dir=reviews_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=runner,
                model=model,
                chunk_id=chunk_id,
            )
        except Exception as error:
            failure = {"chunk_id": chunk_id, "error": str(error)}
            failures.append(failure)
            append_job_log(
                jobs_dir=jobs_dir,
                job_type="translation-es",
                status="failed",
                target_id=chunk_id,
                details={**failure, "mode": "batch"},
            )
            if stop_on_error:
                stopped_early = True
                break
            continue

        processed.append(summary)
        append_job_log(
            jobs_dir=jobs_dir,
            job_type="translation-es",
            status="succeeded",
            target_id=chunk_id,
            details={**summary, "mode": "batch"},
        )

    batch_summary = {
        "selected_chunk_ids": selected_chunk_ids,
        "processed_count": len(processed),
        "failed_count": len(failures),
        "skipped_count": len(candidates["skipped"]),
        "processed": processed,
        "failures": failures,
        "skipped": candidates["skipped"],
        "stopped_early": stopped_early,
        "model": model,
    }
    append_job_log(
        jobs_dir=jobs_dir,
        job_type="translation-es-batch",
        status="failed" if failures else "succeeded",
        target_id="queue",
        details=batch_summary,
    )
    return batch_summary
