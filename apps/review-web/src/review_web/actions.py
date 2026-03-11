from __future__ import annotations

from pathlib import Path

from editorial_core.copyedit import Runner, run_copyedit_pass


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
