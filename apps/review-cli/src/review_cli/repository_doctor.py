from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.repository_doctor import run_repository_doctor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run repository diagnostics and separate blocking from advisory workflow findings."
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=Path.cwd(),
        help="Repository root to inspect.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    summary = run_repository_doctor(root_dir=args.root_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
