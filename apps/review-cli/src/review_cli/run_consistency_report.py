from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.consistency_report import generate_consistency_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a grouped pt-BR consistency report from the consolidated manuscript."
    )
    parser.add_argument(
        "--consolidated-dir",
        type=Path,
        default=Path("manuscript/consolidated"),
        help="Directory containing consolidated manuscript state.",
    )
    parser.add_argument(
        "--glossary",
        type=Path,
        default=Path("editorial/GLOSSARY.md"),
        help="Path to the persisted glossary.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("reports"),
        help="Directory where consistency reports are written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = generate_consistency_report(
        consolidated_dir=args.consolidated_dir,
        glossary_path=args.glossary,
        reports_dir=args.reports_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
