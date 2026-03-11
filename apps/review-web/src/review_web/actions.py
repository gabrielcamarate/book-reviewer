from __future__ import annotations

from pathlib import Path

from editorial_core.copyedit import Runner, run_copyedit_pass
from editorial_core.review_application import apply_review_approval


def trigger_copyedit(
    *,
    chunk_id: str,
    chunks_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    runner: Runner,
    model: str = "gpt-5-codex",
) -> dict[str, object]:
    return run_copyedit_pass(
        chunks_dir=chunks_dir,
        reviews_dir=reviews_dir,
        style_guide_path=style_guide_path,
        glossary_path=glossary_path,
        runner=runner,
        model=model,
        chunk_id=chunk_id,
    )


def trigger_review_approval(
    *,
    chunk_id: str,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    approved_suggestion_indexes: list[int] | None = None,
) -> dict[str, object]:
    return apply_review_approval(
        review_path=reviews_dir / f"{chunk_id}.copyedit.json",
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        approved_suggestion_indexes=approved_suggestion_indexes,
    )
