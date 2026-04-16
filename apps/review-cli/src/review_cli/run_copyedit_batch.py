from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.codex_runner import run_codex_with_schema
from editorial_core.copyedit_batch import run_copyedit_batch


def _codex_runner(prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
    return run_codex_with_schema(
        prompt=prompt,
        schema=schema,
        model=model,
        schema_filename="copyedit-schema.json",
        output_filename="copyedit-output.json",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the pt-BR copyedit pass for multiple queued chunks."
    )
    parser.add_argument("--chunks-dir", type=Path, default=Path("manuscript/chunks"))
    parser.add_argument("--reviews-dir", type=Path, default=Path("reviews/ptbr"))
    parser.add_argument("--jobs-dir", type=Path, default=Path("reports/jobs"))
    parser.add_argument("--style-guide", type=Path, default=Path("editorial/STYLE_GUIDE.md"))
    parser.add_argument("--glossary", type=Path, default=Path("editorial/GLOSSARY.md"))
    parser.add_argument("--decisions", type=Path, default=Path("editorial/DECISIONS.md"))
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--max-chunks", type=int, default=None)
    parser.add_argument("--continue-on-error", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = run_copyedit_batch(
        chunks_dir=args.chunks_dir,
        reviews_dir=args.reviews_dir,
        jobs_dir=args.jobs_dir,
        style_guide_path=args.style_guide,
        glossary_path=args.glossary,
        decisions_path=args.decisions,
        runner=_codex_runner,
        model=args.model,
        max_chunks=args.max_chunks,
        stop_on_error=not args.continue_on_error,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
