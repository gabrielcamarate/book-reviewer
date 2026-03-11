from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.adapter_fixtures import generate_adapter_contract_fixtures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate deterministic adapter contract fixtures for future bot-channel integrations."
    )
    parser.add_argument("--chunks-dir", type=Path, default=Path("manuscript/chunks"))
    parser.add_argument("--chapters-dir", type=Path, default=Path("manuscript/chapters"))
    parser.add_argument("--consolidated-dir", type=Path, default=Path("manuscript/consolidated"))
    parser.add_argument("--reviews-ptbr-dir", type=Path, default=Path("reviews/ptbr"))
    parser.add_argument("--reviews-es-dir", type=Path, default=Path("reviews/es"))
    parser.add_argument("--jobs-dir", type=Path, default=Path("reports/jobs"))
    parser.add_argument("--output-dir", type=Path, default=Path("fixtures/bot-contracts"))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    summary = generate_adapter_contract_fixtures(
        chunks_dir=args.chunks_dir,
        chapters_dir=args.chapters_dir,
        consolidated_dir=args.consolidated_dir,
        reviews_ptbr_dir=args.reviews_ptbr_dir,
        reviews_es_dir=args.reviews_es_dir,
        jobs_dir=args.jobs_dir,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
