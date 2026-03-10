from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx_adapter.reader import write_json


def _context_slice(
    paragraphs: list[dict[str, Any]],
    start_index: int,
    end_index: int,
) -> list[dict[str, Any]]:
    return [
        {
            "paragraph_id": paragraph["id"],
            "source_index": paragraph["source_index"],
            "review_status": paragraph.get("review_status"),
            "text": paragraph["text"],
        }
        for paragraph in paragraphs[start_index:end_index]
    ]


def _build_chunk_payload(
    section_payload: dict[str, Any],
    chunk_order: int,
    paragraphs: list[dict[str, Any]],
    start_index: int,
    end_index: int,
    context_paragraphs: int,
) -> dict[str, Any]:
    chunk_paragraphs = paragraphs[start_index:end_index]
    chunk_id = f"{section_payload['id']}-chunk-{chunk_order:04d}"

    return {
        "id": chunk_id,
        "section_id": section_payload["id"],
        "section_type": section_payload["type"],
        "section_title": section_payload["title"],
        "chunk_order": chunk_order,
        "review_status": "pending_review",
        "paragraph_ids": [paragraph["id"] for paragraph in chunk_paragraphs],
        "source_start_index": chunk_paragraphs[0]["source_index"],
        "source_end_index": chunk_paragraphs[-1]["source_index"],
        "paragraph_count": len(chunk_paragraphs),
        "base_text": "\n\n".join(paragraph["text"] for paragraph in chunk_paragraphs),
        "previous_context": _context_slice(
            paragraphs,
            max(0, start_index - context_paragraphs),
            start_index,
        ),
        "next_context": _context_slice(
            paragraphs,
            end_index,
            min(len(paragraphs), end_index + context_paragraphs),
        ),
    }


def _chunk_section(
    section_payload: dict[str, Any],
    target_characters: int,
    max_paragraphs: int,
    context_paragraphs: int,
) -> list[dict[str, Any]]:
    paragraphs = section_payload.get("paragraphs", [])
    chunks: list[dict[str, Any]] = []
    index = 0
    chunk_order = 1

    while index < len(paragraphs):
        paragraph = paragraphs[index]
        if paragraph.get("review_status") != "pending_review":
            index += 1
            continue

        start_index = index
        end_index = index
        accumulated_characters = 0

        while end_index < len(paragraphs):
            candidate = paragraphs[end_index]
            if candidate.get("review_status") != "pending_review":
                break

            candidate_size = len(candidate["text"])
            would_exceed_characters = (
                accumulated_characters > 0
                and accumulated_characters + candidate_size > target_characters
            )
            would_exceed_paragraphs = end_index - start_index >= max_paragraphs

            if would_exceed_characters or would_exceed_paragraphs:
                break

            accumulated_characters += candidate_size
            end_index += 1

        chunks.append(
            _build_chunk_payload(
                section_payload=section_payload,
                chunk_order=chunk_order,
                paragraphs=paragraphs,
                start_index=start_index,
                end_index=end_index,
                context_paragraphs=context_paragraphs,
            )
        )
        chunk_order += 1
        index = end_index

    return chunks


def build_review_chunks(
    chapters_dir: Path,
    output_dir: Path,
    target_characters: int = 1400,
    max_paragraphs: int = 4,
    context_paragraphs: int = 2,
) -> dict[str, Any]:
    index_payload = json.loads((chapters_dir / "index.json").read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for existing_file in output_dir.glob("*.json"):
        existing_file.unlink()

    chunks: list[dict[str, Any]] = []

    for section_entry in index_payload["sections"]:
        section_payload = json.loads((chapters_dir / section_entry["file"]).read_text(encoding="utf-8"))
        chunks.extend(
            _chunk_section(
                section_payload=section_payload,
                target_characters=target_characters,
                max_paragraphs=max_paragraphs,
                context_paragraphs=context_paragraphs,
            )
        )

    if not chunks:
        raise ValueError("no pending review paragraphs found to build chunks")

    index_output = {
        "chunk_count": len(chunks),
        "chunks": [
            {
                "id": chunk["id"],
                "section_id": chunk["section_id"],
                "section_title": chunk["section_title"],
                "chunk_order": chunk["chunk_order"],
                "review_status": chunk["review_status"],
                "paragraph_count": chunk["paragraph_count"],
                "source_start_index": chunk["source_start_index"],
                "source_end_index": chunk["source_end_index"],
                "file": f"{chunk['id']}.json",
            }
            for chunk in chunks
        ],
    }

    write_json(output_dir / "index.json", index_output)

    for chunk in chunks:
        write_json(output_dir / f"{chunk['id']}.json", chunk)

    return {
        "chunk_count": len(chunks),
        "output_dir": str(output_dir),
        "source_section_count": len({chunk["section_id"] for chunk in chunks}),
    }
