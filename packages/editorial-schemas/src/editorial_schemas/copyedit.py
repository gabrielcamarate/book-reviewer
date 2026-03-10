from __future__ import annotations


def copyedit_output_schema() -> dict[str, object]:
    suggestion_schema: dict[str, object] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "original",
            "suggested",
            "change_type",
            "reason",
            "confidence",
        ],
        "properties": {
            "original": {"type": "string"},
            "suggested": {"type": "string"},
            "change_type": {"type": "string"},
            "reason": {"type": "string"},
            "confidence": {"type": "number"},
        },
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["suggestions"],
        "properties": {
            "suggestions": {
                "type": "array",
                "items": suggestion_schema,
            }
        },
    }
