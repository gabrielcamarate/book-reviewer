from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.review_rollback import rollback_last_review_approval


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rollback the latest active approval when it is still safe to revert."
    )
    parser.add_argument("--reviews-dir", type=Path, default=Path("reviews/ptbr"))
    parser.add_argument("--chapters-dir", type=Path, default=Path("manuscript/chapters"))
    parser.add_argument("--consolidated-dir", type=Path, default=Path("manuscript/consolidated"))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    summary = rollback_last_review_approval(
        reviews_dir=args.reviews_dir,
        chapters_dir=args.chapters_dir,
        consolidated_dir=args.consolidated_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
