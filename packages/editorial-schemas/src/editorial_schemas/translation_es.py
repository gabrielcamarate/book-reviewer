from __future__ import annotations


def translation_es_output_schema() -> dict[str, object]:
    translation_schema: dict[str, object] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "paragraph_id",
            "translated_text",
            "rationale",
            "confidence",
        ],
        "properties": {
            "paragraph_id": {"type": "string"},
            "translated_text": {"type": "string"},
            "rationale": {"type": "string"},
            "confidence": {"type": "number"},
        },
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["translations"],
        "properties": {
            "translations": {
                "type": "array",
                "items": translation_schema,
            }
        },
    }
