from __future__ import annotations

import json
from typing import Any


def build_copyedit_prompt(
    *,
    chunk_payload: dict[str, Any],
    style_guide_text: str,
    glossary_text: str,
) -> str:
    prompt_payload = {
        "task": "copyedit-ptbr",
        "rules": [
            "Preserve the author's voice and literalness.",
            "Apply conservative copyedit only: spelling, grammar, punctuation, agreement, and syntax.",
            "Do not rewrite the whole chunk.",
            "Return only actionable suggestions grounded in the provided chunk.",
            "Use the provided style guide and glossary as persistent editorial memory.",
        ],
        "chunk": {
            "id": chunk_payload["id"],
            "section_title": chunk_payload["section_title"],
            "paragraph_ids": chunk_payload["paragraph_ids"],
            "base_text": chunk_payload["base_text"],
            "previous_context": chunk_payload["previous_context"],
            "next_context": chunk_payload["next_context"],
        },
        "style_guide": style_guide_text,
        "glossary": glossary_text,
    }

    return (
        "You are reviewing a literary manuscript chunk in pt-BR.\n"
        "Produce a conservative copyedit proposal with structured suggestions only.\n\n"
        "Review context:\n"
        f"{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}\n"
    )
