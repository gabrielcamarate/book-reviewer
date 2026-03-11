from __future__ import annotations

import json
from typing import Any

TRANSLATION_ES_PROMPT_TEMPLATE_ID = "translation-es"
TRANSLATION_ES_PROMPT_VERSION = "2026-03-10.1"


def build_translation_es_prompt(
    *,
    chunk_payload: dict[str, Any],
    source_paragraphs: list[dict[str, Any]],
    style_guide_text: str,
    glossary_text: str,
    decisions_text: str,
) -> str:
    prompt_payload = {
        "task": TRANSLATION_ES_PROMPT_TEMPLATE_ID,
        "rules": [
            "Translate from pt-BR into literary Spanish with conservative intervention.",
            "Preserve meaning, tone, cadence, and authorial literalness whenever possible.",
            "Respect glossary terms, proper names, cosmological concepts, and deliberate repetitions.",
            "Keep paragraph alignment by returning one translated paragraph per source paragraph.",
            "Do not summarize, explain, or rewrite beyond what is required for an equivalent literary Spanish rendering.",
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
        "You are translating a literary manuscript chunk from pt-BR into Spanish.\n"
        "Produce a structured, paragraph-aligned translation only.\n\n"
        "Translation context:\n"
        f"{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}\n"
    )
