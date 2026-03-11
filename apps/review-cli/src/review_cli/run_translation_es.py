from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from editorial_core.translation_es import run_translation_es_pass


def _codex_runner(prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        schema_path = temp_path / "translation-es-schema.json"
        output_path = temp_path / "translation-es-output.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

        command = [
            "codex",
            "exec",
            "-m",
            model,
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "codex exec failed with exit code "
                f"{completed.returncode}: {completed.stderr.strip() or completed.stdout.strip()}"
            )
        return json.loads(output_path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the literary Spanish translation pass for the next stable pt-BR chunk."
    )
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=Path("manuscript/chunks"),
        help="Directory containing chunk artifacts.",
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=Path("manuscript/chapters"),
        help="Directory containing source chapter state.",
    )
    parser.add_argument(
        "--consolidated-dir",
        type=Path,
        default=Path("manuscript/consolidated"),
        help="Directory containing consolidated pt-BR state.",
    )
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        default=Path("reviews/es"),
        help="Directory where Spanish translation outputs will be written.",
    )
    parser.add_argument(
        "--style-guide",
        type=Path,
        default=Path("editorial/STYLE_GUIDE.md"),
        help="Path to the persisted style guide.",
    )
    parser.add_argument(
        "--glossary",
        type=Path,
        default=Path("editorial/GLOSSARY.md"),
        help="Path to the persisted glossary.",
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=Path("editorial/DECISIONS.md"),
        help="Path to the persisted editorial decisions log.",
    )
    parser.add_argument(
        "--chunk-id",
        default=None,
        help="Optional chunk identifier. Defaults to the next stable chunk without a Spanish translation output.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5-codex",
        help="Codex model identifier used for the translation pass.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = run_translation_es_pass(
        chunks_dir=args.chunks_dir,
        chapters_dir=args.chapters_dir,
        consolidated_dir=args.consolidated_dir,
        reviews_dir=args.reviews_dir,
        style_guide_path=args.style_guide,
        glossary_path=args.glossary,
        decisions_path=args.decisions,
        runner=_codex_runner,
        model=args.model,
        chunk_id=args.chunk_id,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
