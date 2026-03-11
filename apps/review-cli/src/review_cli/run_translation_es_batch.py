from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from editorial_core.translation_batch import run_translation_es_batch


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
        description="Run the literary Spanish translation pass for multiple eligible chunks."
    )
    parser.add_argument("--chunks-dir", type=Path, default=Path("manuscript/chunks"))
    parser.add_argument("--chapters-dir", type=Path, default=Path("manuscript/chapters"))
    parser.add_argument("--consolidated-dir", type=Path, default=Path("manuscript/consolidated"))
    parser.add_argument("--reviews-dir", type=Path, default=Path("reviews/es"))
    parser.add_argument("--jobs-dir", type=Path, default=Path("reports/jobs"))
    parser.add_argument("--style-guide", type=Path, default=Path("editorial/STYLE_GUIDE.md"))
    parser.add_argument("--glossary", type=Path, default=Path("editorial/GLOSSARY.md"))
    parser.add_argument("--decisions", type=Path, default=Path("editorial/DECISIONS.md"))
    parser.add_argument("--model", default="gpt-5-codex")
    parser.add_argument("--max-chunks", type=int, default=None)
    parser.add_argument("--continue-on-error", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = run_translation_es_batch(
        chunks_dir=args.chunks_dir,
        chapters_dir=args.chapters_dir,
        consolidated_dir=args.consolidated_dir,
        reviews_dir=args.reviews_dir,
        jobs_dir=args.jobs_dir,
        style_guide_path=args.style_guide,
        glossary_path=args.glossary,
        decisions_path=args.decisions,
        runner=_codex_runner,
        model=args.model,
        max_chunks=args.max_chunks,
        stop_on_error=not args.continue_on_error,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
