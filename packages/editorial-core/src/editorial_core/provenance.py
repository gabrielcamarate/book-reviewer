from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_llm_provenance(
    *,
    model: str,
    prompt_template_id: str,
    prompt_version: str,
    prompt_text: str,
    schema_name: str,
    schema_version: str,
    schema: dict[str, Any],
    context_inputs: dict[str, str],
) -> dict[str, Any]:
    return {
        "model": {
            "name": model,
        },
        "prompt": {
            "template_id": prompt_template_id,
            "version": prompt_version,
            "sha256": sha256_text(prompt_text),
        },
        "schema": {
            "name": schema_name,
            "version": schema_version,
            "sha256": sha256_text(json.dumps(schema, ensure_ascii=False, sort_keys=True)),
        },
        "context_inputs": {
            name: {
                "sha256": sha256_text(text),
                "character_count": len(text),
            }
            for name, text in context_inputs.items()
        },
    }
