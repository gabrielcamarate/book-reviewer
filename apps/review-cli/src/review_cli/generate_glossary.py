from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.glossary import generate_glossary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate editorial/GLOSSARY.md from the approved manuscript corpus."
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory containing chapter artifacts with review status metadata.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("editorial/GLOSSARY.md"),
        help="Markdown file path for the generated glossary.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = generate_glossary(args.chapters_dir, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
