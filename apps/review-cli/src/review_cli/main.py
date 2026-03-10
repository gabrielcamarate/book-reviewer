from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.import_docx import import_docx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import a .docx manuscript into reproducible extracted artifacts."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("livro.docx"),
        help="Path to the source .docx manuscript.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("manuscript/extracted"),
        help="Directory where extracted artifacts will be written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = import_docx(args.input, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
