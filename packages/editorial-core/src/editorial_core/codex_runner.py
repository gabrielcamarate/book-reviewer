from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def run_codex_with_schema(
    *,
    prompt: str,
    schema: dict[str, object],
    model: str,
    schema_filename: str,
    output_filename: str,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        schema_path = temp_path / schema_filename
        output_path = temp_path / output_filename
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
