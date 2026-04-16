from __future__ import annotations

from pathlib import Path
from typing import Any

from editorial_core.copyedit import Runner, run_copyedit_pass
from editorial_core.job_log import append_job_log
from editorial_core.queue import build_review_queue


def run_copyedit_batch(
    *,
    chunks_dir: Path,
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
    queue_state = build_review_queue(
        chunks_dir=chunks_dir,
        reviews_ptbr_dir=reviews_dir,
        reviews_es_dir=Path("reviews/es") if reviews_dir == Path("reviews/ptbr") else reviews_dir.parent / "es",
    )
    selected_chunk_ids = [
        item["chunk_id"]
        for item in queue_state["queue_items"]
        if item["queue_status"] == "pending_copyedit"
    ]
    if max_chunks is not None:
        selected_chunk_ids = selected_chunk_ids[:max_chunks]

    processed: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    stopped_early = False

    for chunk_id in selected_chunk_ids:
        try:
            summary = run_copyedit_pass(
                chunks_dir=chunks_dir,
                reviews_dir=reviews_dir,
                style_guide_path=style_guide_path,
                glossary_path=glossary_path,
                decisions_path=decisions_path,
                runner=runner,
                model=model,
                chunk_id=chunk_id,
            )
        except Exception as error:
            failure = {
                "chunk_id": chunk_id,
                "error": str(error),
            }
            failures.append(failure)
            append_job_log(
                jobs_dir=jobs_dir,
                job_type="copyedit",
                status="failed",
                target_id=chunk_id,
                details={
                    **failure,
                    "mode": "batch",
                },
            )
            if stop_on_error:
                stopped_early = True
                break
            continue

        processed.append(summary)
        append_job_log(
            jobs_dir=jobs_dir,
            job_type="copyedit",
            status="succeeded",
            target_id=chunk_id,
            details={
                **summary,
                "mode": "batch",
            },
        )

    batch_summary = {
        "selected_chunk_ids": selected_chunk_ids,
        "processed_count": len(processed),
        "failed_count": len(failures),
        "processed": processed,
        "failures": failures,
        "stopped_early": stopped_early,
        "model": model,
    }
    append_job_log(
        jobs_dir=jobs_dir,
        job_type="copyedit-batch",
        status="failed" if failures else "succeeded",
        target_id="queue",
        details=batch_summary,
    )
    return batch_summary
