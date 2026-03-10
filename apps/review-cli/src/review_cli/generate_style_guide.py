from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.style_guide import generate_style_guide


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the initial STYLE_GUIDE.md from the approved reference corpus."
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory containing segmented chapter artifacts.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("editorial/STYLE_GUIDE.md"),
        help="Path where the generated style guide will be written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = generate_style_guide(args.chapters_dir, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
