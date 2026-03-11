from __future__ import annotations

import json
from typing import Any

STYLE_PROMPT_TEMPLATE_ID = "style-ptbr"
STYLE_PROMPT_VERSION = "2026-03-10.1"


def build_style_prompt(
    *,
    chunk_payload: dict[str, Any],
    source_paragraphs: list[dict[str, Any]],
    style_guide_text: str,
    glossary_text: str,
    decisions_text: str,
) -> str:
    prompt_payload = {
        "task": STYLE_PROMPT_TEMPLATE_ID,
        "rules": [
            "Refine fluency, cadence, and clarity while preserving the author's voice and literalness.",
            "Do not perform broad rewriting or change the philosophical intent of the manuscript.",
            "Return only structured, conservative style suggestions grounded in the provided stable pt-BR text.",
            "Respect glossary terms, editorial decisions, deliberate repetitions, and the manuscript's elevated register.",
        ],
        "chunk": {
            "id": chunk_payload["id"],
            "section_title": chunk_payload["section_title"],
            "paragraph_ids": chunk_payload["paragraph_ids"],
            "source_paragraphs": source_paragraphs,
            "previous_context": chunk_payload["previous_context"],
            "next_context": chunk_payload["next_context"],
        },
        "style_guide": style_guide_text,
        "glossary": glossary_text,
        "editorial_decisions": decisions_text,
    }

    return (
        "You are refining a literary manuscript chunk in pt-BR.\n"
        "Produce a conservative style proposal with structured suggestions only.\n\n"
        "Review context:\n"
        f"{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}\n"
    )
