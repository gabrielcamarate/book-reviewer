from __future__ import annotations


COPYEDIT_SCHEMA_NAME = "copyedit-output"
COPYEDIT_SCHEMA_VERSION = "2026-03-11.1"


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
            "change_type": {
                "type": "string",
                "enum": [
                    "spelling",
                    "ortografia",
                    "grammar",
                    "gramática",
                    "punctuation",
                    "pontuação",
                    "agreement",
                    "concordância",
                    "syntax",
                    "sintaxe",
                    "capitalization",
                    "capitalização",
                    "quotation",
                    "citação",
                    "aspas",
                    "diacritics",
                    "acentuação",
                ],
            },
            "reason": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0.8, "maximum": 1.0},
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
