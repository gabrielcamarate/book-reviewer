from __future__ import annotations

import json
# Fixed CLI with argument list; no shell or executable from input.
import subprocess  # nosec B404
import tempfile
from pathlib import Path

DEFAULT_MODEL = 'gpt-6.1-sol'
REASONING_EFFORT = 'low'


class InvalidModelResponse(ValueError):
    """Rejected model output; state conflicts and provider failures use other errors."""


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
            "-m", DEFAULT_MODEL if model == 'codex-default' else model,
            "-c", 'model_reasoning_effort="low"',
            "--skip-git-repo-check",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        # Fixed executable and separate arguments; prompt goes through stdin.
        completed = subprocess.run(  # nosec B603
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
            cwd=temp_path,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "codex exec failed with exit code "
                f"{completed.returncode}. Confira a autenticação e a disponibilidade do modelo."
            )
        try:
            return json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise InvalidModelResponse('O modelo devolveu JSON inválido. Gere uma nova resposta.') from error


def codex_runner(*, prompt: str, schema: dict[str, object], model: str) -> dict[str, object]:
    return run_codex_with_schema(prompt=prompt, schema=schema, model=model,
                                schema_filename="schema.json", output_filename="response.json")
