from __future__ import annotations

import json
from pathlib import Path

from docx_adapter.reader import write_json


def _copyedit_review_path(reviews_ptbr_dir: Path, chunk_id: str) -> Path:
    return reviews_ptbr_dir / f"{chunk_id}.copyedit.json"


def _rejection_path(reviews_ptbr_dir: Path, chunk_id: str) -> Path:
    return reviews_ptbr_dir / f"{chunk_id}.rejection.json"


def _translation_preview_path(reviews_es_dir: Path, chunk_id: str) -> Path:
    return reviews_es_dir / f"{chunk_id}.translation-es.preview.json"


def reject_review_proposal(
    *,
    chunk_id: str,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    reason: str,
) -> dict[str, object]:
    trimmed_reason = reason.strip()
    if not trimmed_reason:
        raise ValueError("rejection reason is required")

    review_path = _copyedit_review_path(reviews_ptbr_dir, chunk_id)
    if not review_path.exists():
        raise FileNotFoundError(f"copyedit review not found for chunk: {chunk_id}")

    translation_preview_path = _translation_preview_path(reviews_es_dir, chunk_id)
    rejection_path = _rejection_path(reviews_ptbr_dir, chunk_id)

    review_path.unlink()
    removed_translation_preview = False
    if translation_preview_path.exists():
        translation_preview_path.unlink()
        removed_translation_preview = True

    write_json(
        rejection_path,
        {
            "chunk_id": chunk_id,
            "status": "rejected",
            "reason": trimmed_reason,
        },
    )

    return {
        "chunk_id": chunk_id,
        "status": "rejected",
        "reason": trimmed_reason,
        "removed_copyedit_review": True,
        "removed_translation_preview": removed_translation_preview,
        "rejection_path": str(rejection_path),
    }

