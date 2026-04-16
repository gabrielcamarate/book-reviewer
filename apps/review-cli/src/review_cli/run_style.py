from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.codex_runner import run_codex_with_schema
from editorial_core.style import run_style_pass


def _codex_runner(prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
    return run_codex_with_schema(
        prompt=prompt,
        schema=schema,
        model=model,
        schema_filename="style-schema.json",
        output_filename="style-output.json",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the pt-BR style pass for the next stable chunk."
    )
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=Path("manuscript/chunks"),
        help="Directory containing chunk artifacts.",
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory containing source chapter state.",
    )
    parser.add_argument(
        "--consolidated-dir",
        type=Path,
        default=Path("manuscript/consolidated"),
        help="Directory containing consolidated pt-BR state.",
    )
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        default=Path("reviews/ptbr"),
        help="Directory where style review outputs will be written.",
    )
    parser.add_argument(
        "--style-guide",
        type=Path,
        default=Path("editorial/STYLE_GUIDE.md"),
        help="Path to the persisted style guide.",
    )
    parser.add_argument(
        "--glossary",
        type=Path,
        default=Path("editorial/GLOSSARY.md"),
        help="Path to the persisted glossary.",
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=Path("editorial/DECISIONS.md"),
        help="Path to the persisted editorial decisions log.",
    )
    parser.add_argument(
        "--chunk-id",
        default=None,
        help="Optional chunk identifier. Defaults to the next stable chunk without a style output.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.4",
        help="Codex model identifier used for the style pass.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = run_style_pass(
        chunks_dir=args.chunks_dir,
        chapters_dir=args.chapters_dir,
        consolidated_dir=args.consolidated_dir,
        reviews_dir=args.reviews_dir,
        style_guide_path=args.style_guide,
        glossary_path=args.glossary,
        decisions_path=args.decisions,
        runner=_codex_runner,
        model=args.model,
        chunk_id=args.chunk_id,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
