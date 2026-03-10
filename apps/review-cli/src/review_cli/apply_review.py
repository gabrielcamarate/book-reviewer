from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.review_application import apply_review_approval


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Approve and apply a persisted review into consolidated manuscript state."
    )
    parser.add_argument(
        "--review-file",
        type=Path,
        required=True,
        help="Path to the persisted review proposal file.",
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
        help="Directory containing source chapter artifacts.",
    )
    parser.add_argument(
        "--consolidated-dir",
        type=Path,
        default=Path("manuscript/consolidated"),
        help="Directory where consolidated manuscript state will be written.",
    )
    parser.add_argument(
        "--approve-index",
        type=int,
        action="append",
        dest="approve_indexes",
        help="Suggestion index to approve. Repeat to approve specific suggestions. Defaults to all suggestions.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = apply_review_approval(
        review_path=args.review_file,
        chunks_dir=args.chunks_dir,
        chapters_dir=args.chapters_dir,
        consolidated_dir=args.consolidated_dir,
        approved_suggestion_indexes=args.approve_indexes,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
