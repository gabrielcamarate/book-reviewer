from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_core.export_docx import export_manuscript_docx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the current manuscript state to a reproducible .docx deliverable."
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("livro.docx"),
        help="Source .docx template used to preserve the base document package.",
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory containing segmented chapter and section state.",
    )
    parser.add_argument(
        "--consolidated-dir",
        type=Path,
        default=Path("manuscript/consolidated"),
        help="Directory containing current consolidated pt-BR state.",
    )
    parser.add_argument(
        "--translations-dir",
        type=Path,
        default=Path("reviews/es"),
        help="Directory containing persisted Spanish translation outputs.",
    )
    parser.add_argument(
        "--language",
        choices=("pt-BR", "es"),
        default="pt-BR",
        help="Deliverable language.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output .docx path.",
    )
    return parser


def _default_output_path(language: str) -> Path:
    language_slug = "ptbr" if language == "pt-BR" else "es"
    return Path("deliverables") / language_slug / f"exilados-da-terra.{language_slug}.docx"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_path = args.output or _default_output_path(args.language)

    summary = export_manuscript_docx(
        template_path=args.template,
        chapters_dir=args.chapters_dir,
        consolidated_dir=args.consolidated_dir,
        translations_dir=args.translations_dir,
        output_path=output_path,
        language=args.language,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
