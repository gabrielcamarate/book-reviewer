from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.review_boundary import apply_review_boundary


DEFAULT_CUTOFF_EXCERPT = "Todo cuidado é pouco, tratando-se do Sistema Terra estabelecido"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mark the approved versus pending review boundary in chapter artifacts."
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory containing segmented chapter artifacts.",
    )
    parser.add_argument(
        "--cutoff-excerpt",
        default=DEFAULT_CUTOFF_EXCERPT,
        help="Excerpt that marks the first pending-review paragraph.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = apply_review_boundary(args.chapters_dir, args.cutoff_excerpt)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
