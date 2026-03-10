from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from editorial_core.copyedit import run_copyedit_pass


def _codex_runner(prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        schema_path = temp_path / "copyedit-schema.json"
        output_path = temp_path / "copyedit-output.json"
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
        description="Run the pt-BR copyedit pass for the next pending chunk."
    )
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=Path("manuscript/chunks"),
        help="Directory containing chunk artifacts.",
    )
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        default=Path("reviews/ptbr"),
        help="Directory where copyedit review outputs will be written.",
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
        "--chunk-id",
        default=None,
        help="Optional chunk identifier. Defaults to the next chunk without a persisted copyedit output.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5-codex",
        help="Codex model identifier used for the copyedit pass.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    summary = run_copyedit_pass(
        chunks_dir=args.chunks_dir,
        reviews_dir=args.reviews_dir,
        style_guide_path=args.style_guide,
        glossary_path=args.glossary,
        runner=_codex_runner,
        model=args.model,
        chunk_id=args.chunk_id,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
