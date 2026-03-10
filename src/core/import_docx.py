from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.adapters.docx_reader import (
    extract_docx_metadata,
    extract_docx_paragraphs,
    write_json,
)


def import_docx(input_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = extract_docx_metadata(input_path)
    paragraphs = extract_docx_paragraphs(input_path)

    non_empty_paragraphs = [paragraph for paragraph in paragraphs if not paragraph["is_empty"]]

    summary = {
        "source_file": input_path.name,
        "output_dir": str(output_dir),
        "paragraph_count": len(paragraphs),
        "non_empty_paragraph_count": len(non_empty_paragraphs),
        "first_non_empty_excerpt": (
            non_empty_paragraphs[0]["text"][:160] if non_empty_paragraphs else None
        ),
    }

    write_json(output_dir / "metadata.json", metadata)
    write_json(output_dir / "paragraphs.json", paragraphs)
    write_json(output_dir / "summary.json", summary)

    text_output = "\n\n".join(paragraph["text"] for paragraph in paragraphs if paragraph["text"])
    (output_dir / "document.txt").write_text(text_output + "\n", encoding="utf-8")

    with (output_dir / "paragraphs.jsonl").open("w", encoding="utf-8") as handle:
        for paragraph in paragraphs:
            handle.write(json.dumps(paragraph, ensure_ascii=False) + "\n")

    return summary
