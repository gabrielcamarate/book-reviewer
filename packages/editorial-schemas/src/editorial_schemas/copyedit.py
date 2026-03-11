from __future__ import annotations


COPYEDIT_SCHEMA_NAME = "copyedit-output"
COPYEDIT_SCHEMA_VERSION = "2026-03-10.1"


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
