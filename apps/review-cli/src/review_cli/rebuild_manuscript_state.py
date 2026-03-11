from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.manuscript_rebuild import rebuild_manuscript_state


DEFAULT_CUTOFF_EXCERPT = "Todo cuidado é pouco, tratando-se do Sistema Terra estabelecido"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rebuild canonical manuscript state after segmentation normalization."
    )
    parser.add_argument("--extracted-dir", type=Path, default=Path("manuscript/extracted"))
    parser.add_argument("--chapters-dir", type=Path, default=Path("manuscript/chapters"))
    parser.add_argument("--chunks-dir", type=Path, default=Path("manuscript/chunks"))
    parser.add_argument("--consolidated-dir", type=Path, default=Path("manuscript/consolidated"))
    parser.add_argument("--reviews-ptbr-dir", type=Path, default=Path("reviews/ptbr"))
    parser.add_argument("--reviews-es-dir", type=Path, default=Path("reviews/es"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--cutoff-excerpt", default=DEFAULT_CUTOFF_EXCERPT)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = rebuild_manuscript_state(
        extracted_dir=args.extracted_dir,
        chapters_dir=args.chapters_dir,
        chunks_dir=args.chunks_dir,
        consolidated_dir=args.consolidated_dir,
        reviews_ptbr_dir=args.reviews_ptbr_dir,
        reviews_es_dir=args.reviews_es_dir,
        reports_dir=args.reports_dir,
        cutoff_excerpt=args.cutoff_excerpt,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
