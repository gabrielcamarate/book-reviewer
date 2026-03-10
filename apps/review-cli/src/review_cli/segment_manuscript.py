from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.segment_manuscript import segment_extracted_manuscript


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Segment extracted manuscript paragraphs into canonical chapter files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("manuscript/extracted"),
        help="Directory containing extracted manuscript artifacts.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory where segmented chapter artifacts will be written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = segment_extracted_manuscript(args.input_dir, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
