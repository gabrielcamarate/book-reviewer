from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.chunking import build_review_chunks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate stable pending-review chunks with side context."
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory containing chapter artifacts with review metadata.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("manuscript/chunks"),
        help="Directory where chunk artifacts will be written.",
    )
    parser.add_argument(
        "--target-characters",
        type=int,
        default=1400,
        help="Target maximum characters per chunk before opening a new chunk.",
    )
    parser.add_argument(
        "--max-paragraphs",
        type=int,
        default=4,
        help="Maximum number of pending paragraphs per chunk.",
    )
    parser.add_argument(
        "--context-paragraphs",
        type=int,
        default=2,
        help="Number of neighboring paragraphs to include on each side as context.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = build_review_chunks(
        chapters_dir=args.chapters_dir,
        output_dir=args.output_dir,
        target_characters=args.target_characters,
        max_paragraphs=args.max_paragraphs,
        context_paragraphs=args.context_paragraphs,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
