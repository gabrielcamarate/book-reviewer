from __future__ import annotations

import html
import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_chunk_index(chunks_dir: Path) -> dict[str, Any]:
    index_path = chunks_dir / "index.json"
    if not index_path.exists():
        return {"chunk_count": 0, "chunks": []}
    return _read_json(index_path)


def _load_consolidated_index(consolidated_dir: Path) -> dict[str, Any]:
    index_path = consolidated_dir / "index.json"
    if not index_path.exists():
        return {"section_count": 0, "chapter_count": 0, "sections": []}
    return _read_json(index_path)


def _load_chunk_summary(chunks_dir: Path) -> tuple[int, list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    payload = _load_chunk_index(chunks_dir)
    chunks = payload.get("chunks", [])
    pending_count = sum(1 for chunk in chunks if chunk.get("review_status") == "pending_review")
    chunks_by_section: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        chunks_by_section.setdefault(chunk["section_id"], []).append(
            {
                "id": chunk["id"],
                "section_id": chunk["section_id"],
                "section_title": chunk.get("section_title", "Untitled Section"),
                "review_status": chunk.get("review_status", "unknown"),
                "file": chunk.get("file"),
            }
        )

    return pending_count, [
        {
            "id": chunk["id"],
            "section_id": chunk["section_id"],
            "section_title": chunk.get("section_title", "Untitled Section"),
            "review_status": chunk.get("review_status", "unknown"),
        }
        for chunk in chunks[:10]
    ], chunks_by_section


def _load_consistency_report(reports_dir: Path) -> dict[str, Any]:
    report_path = reports_dir / "ptbr-consistency-report.json"
    if not report_path.exists():
        return {
            "finding_count": 0,
            "finding_types": [],
        }

    payload = _read_json(report_path)
    findings_by_type = payload.get("findings_by_type", {})
    finding_types = [
        {
            "type": finding_type,
            "count": len(findings),
        }
        for finding_type, findings in findings_by_type.items()
    ]
    finding_types.sort(key=lambda item: item["count"], reverse=True)
    return {
        "finding_count": int(payload.get("finding_count", 0)),
        "finding_types": finding_types,
    }


def _count_review_files(directory: Path, suffix: str) -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob(suffix)))


def _collect_deliverables(deliverables_dir: Path) -> list[dict[str, str]]:
    if not deliverables_dir.exists():
        return []

    deliverables: list[dict[str, str]] = []
    for path in sorted(deliverables_dir.rglob("*")):
        if not path.is_file():
            continue
        deliverables.append(
            {
                "path": str(path.relative_to(deliverables_dir.parent)),
                "name": path.name,
            }
        )
    return deliverables


def _build_chapter_summary(
    *,
    consolidated_dir: Path,
    chunks_by_section: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    consolidated_index = _load_consolidated_index(consolidated_dir)
    chapters: list[dict[str, Any]] = []
    for section in consolidated_index.get("sections", []):
        if not str(section.get("id", "")).startswith("chapter-"):
            continue
        chapters.append(
            {
                "id": section["id"],
                "title": section.get("title", "Untitled Chapter"),
                "review_status": section.get("review_status", "unknown"),
                "chunk_count": len(chunks_by_section.get(section["id"], [])),
            }
        )
    return chapters


def _render_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f5f0e8;
        --panel: #fffaf3;
        --ink: #1f1b16;
        --muted: #6d6254;
        --accent: #9a3412;
        --border: #d8ccb9;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        background:
          radial-gradient(circle at top, rgba(154, 52, 18, 0.08), transparent 30%),
          linear-gradient(180deg, #f7f1e8 0%, var(--bg) 100%);
        color: var(--ink);
      }}
      main {{
        max-width: 1120px;
        margin: 0 auto;
        padding: 40px 20px 56px;
      }}
      h1, h2, h3 {{ margin: 0 0 12px; }}
      p, .muted {{ color: var(--muted); }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin: 24px 0 32px;
      }}
      .card, section, article {{
        background: rgba(255, 250, 243, 0.92);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 10px 30px rgba(71, 48, 24, 0.06);
      }}
      .card strong {{
        display: block;
        font-size: 2rem;
        color: var(--accent);
      }}
      .layout {{
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 18px;
      }}
      .two-col {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
      }}
      ul {{
        margin: 0;
        padding-left: 18px;
      }}
      li {{
        margin: 0 0 10px;
      }}
      code, a.chunk-link {{
        background: #f1e7da;
        border-radius: 6px;
        padding: 2px 6px;
      }}
      a {{
        color: var(--accent);
        text-decoration: none;
      }}
      .diff-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }}
      .diff-panel {{
        background: #f8efe3;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px;
      }}
      .diff-added {{
        background: #d7f5dc;
        border-radius: 4px;
        padding: 0 2px;
      }}
      .diff-removed {{
        background: #fde2dc;
        border-radius: 4px;
        padding: 0 2px;
      }}
      pre {{
        white-space: pre-wrap;
        font-family: Georgia, "Times New Roman", serif;
        line-height: 1.55;
        margin: 0;
      }}
      nav {{
        margin-bottom: 18px;
      }}
      @media (max-width: 800px) {{
        .layout, .two-col {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
  </head>
  <body>
    <main>{body}</main>
  </body>
</html>
"""


def build_dashboard_state(
    *,
    chunks_dir: Path,
    consolidated_dir: Path,
    reports_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    deliverables_dir: Path,
) -> dict[str, Any]:
    pending_chunk_count, recent_chunks, chunks_by_section = _load_chunk_summary(chunks_dir)
    consolidated_index = _load_consolidated_index(consolidated_dir)
    consistency_report = _load_consistency_report(reports_dir)
    deliverables = _collect_deliverables(deliverables_dir)
    chapters = _build_chapter_summary(
        consolidated_dir=consolidated_dir,
        chunks_by_section=chunks_by_section,
    )

    return {
        "summary": {
            "pending_chunk_count": pending_chunk_count,
            "section_count": int(consolidated_index.get("section_count", 0)),
            "copyedit_review_count": _count_review_files(reviews_ptbr_dir, "*.copyedit.json"),
            "translation_review_count": _count_review_files(reviews_es_dir, "*.translation-es.json"),
            "deliverable_count": len(deliverables),
        },
        "consistency_report": consistency_report,
        "recent_chunks": recent_chunks,
        "chapters": chapters,
        "deliverables": deliverables,
    }


def build_chapter_detail_state(
    *,
    chapter_id: str,
    chunks_dir: Path,
    consolidated_dir: Path,
) -> dict[str, Any]:
    _, _, chunks_by_section = _load_chunk_summary(chunks_dir)
    consolidated_index = _load_consolidated_index(consolidated_dir)
    chapter = next(
        (section for section in consolidated_index.get("sections", []) if section.get("id") == chapter_id),
        None,
    )
    if chapter is None:
        raise ValueError(f"chapter not found: {chapter_id}")

    return {
        "chapter": {
            "id": chapter["id"],
            "title": chapter.get("title", "Untitled Chapter"),
            "review_status": chapter.get("review_status", "unknown"),
        },
        "chunks": chunks_by_section.get(chapter_id, []),
    }


def build_chunk_detail_state(
    *,
    chunk_id: str,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, Any]:
    index_payload = _load_chunk_index(chunks_dir)
    chunk_entry = next(
        (chunk for chunk in index_payload.get("chunks", []) if chunk.get("id") == chunk_id),
        None,
    )
    if chunk_entry is None:
        raise ValueError(f"chunk not found: {chunk_id}")

    chunk_payload = _read_json(chunks_dir / chunk_entry["file"])
    copyedit_path = reviews_ptbr_dir / f"{chunk_id}.copyedit.json"
    approval_path = reviews_ptbr_dir / f"{chunk_id}.approval.json"
    translation_path = reviews_es_dir / f"{chunk_id}.translation-es.json"

    return {
        "chunk": chunk_payload,
        "copyedit_review": _read_json(copyedit_path) if copyedit_path.exists() else None,
        "approval": _read_json(approval_path) if approval_path.exists() else None,
        "translation_review": _read_json(translation_path) if translation_path.exists() else None,
    }


def render_dashboard_html(state: dict[str, Any]) -> str:
    summary = state["summary"]
    consistency_report = state["consistency_report"]
    recent_chunks = state["recent_chunks"]
    chapters = state["chapters"]
    deliverables = state["deliverables"]

    chapter_items = "".join(
        (
            "<li>"
            f"<a href=\"/chapters/{html.escape(chapter['id'])}\"><strong>{html.escape(chapter['title'])}</strong></a> "
            f"<code>{html.escape(chapter['review_status'])}</code> "
            f"<span class=\"muted\">{chapter['chunk_count']} chunks</span>"
            "</li>"
        )
        for chapter in chapters
    ) or "<li>No chapters available.</li>"

    chunk_items = "".join(
        (
            "<li>"
            f"<a class=\"chunk-link\" href=\"/chunks/{html.escape(chunk['id'])}\">{html.escape(chunk['id'])}</a> "
            f"<span>{html.escape(chunk['section_title'])}</span> "
            f"<code>{html.escape(chunk['review_status'])}</code>"
            "</li>"
        )
        for chunk in recent_chunks
    ) or "<li>No chunks available.</li>"

    finding_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['type'])}</strong>: {item['count']}"
            "</li>"
        )
        for item in consistency_report["finding_types"]
    ) or "<li>No consistency report available.</li>"

    deliverable_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['name'])}</strong> "
            f"<code>{html.escape(item['path'])}</code>"
            "</li>"
        )
        for item in deliverables
    ) or "<li>No deliverables generated yet.</li>"

    body = f"""
      <header>
        <h1>Editorial Review Dashboard</h1>
        <p>Local-first web interface over the persisted editorial review backend.</p>
      </header>
      <div class="grid">
        <div class="card"><span>Pending Review Chunks</span><strong>{summary['pending_chunk_count']}</strong></div>
        <div class="card"><span>Sections in Consolidated State</span><strong>{summary['section_count']}</strong></div>
        <div class="card"><span>pt-BR Review Files</span><strong>{summary['copyedit_review_count']}</strong></div>
        <div class="card"><span>Spanish Translation Files</span><strong>{summary['translation_review_count']}</strong></div>
        <div class="card"><span>Generated Deliverables</span><strong>{summary['deliverable_count']}</strong></div>
        <div class="card"><span>Consistency Findings</span><strong>{consistency_report['finding_count']}</strong></div>
      </div>
      <div class="layout">
        <section>
          <h2>Chapter Navigation</h2>
          <ul>{chapter_items}</ul>
        </section>
        <section>
          <h2>Consistency Report</h2>
          <ul>{finding_items}</ul>
        </section>
      </div>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Recent Chunks</h2>
          <ul>{chunk_items}</ul>
        </section>
        <section>
          <h2>Deliverables</h2>
          <ul>{deliverable_items}</ul>
        </section>
      </div>
    """
    return _render_page("Editorial Review Dashboard", body)


def render_chapter_detail_html(state: dict[str, Any]) -> str:
    chapter = state["chapter"]
    chunks = state["chunks"]
    chunk_items = "".join(
        (
            "<li>"
            f"<a class=\"chunk-link\" href=\"/chunks/{html.escape(chunk['id'])}\">{html.escape(chunk['id'])}</a> "
            f"<code>{html.escape(chunk['review_status'])}</code>"
            "</li>"
        )
        for chunk in chunks
    ) or "<li>No chunks available for this chapter.</li>"

    body = f"""
      <nav><a href=\"/\">← Dashboard</a></nav>
      <section>
        <h1>{html.escape(chapter['title'])}</h1>
        <p><strong>Chapter Navigation</strong> for <code>{html.escape(chapter['id'])}</code></p>
        <p class=\"muted\">Review status: <code>{html.escape(chapter['review_status'])}</code></p>
      </section>
      <section style=\"margin-top: 18px;\">
        <h2>Chunks</h2>
        <ul>{chunk_items}</ul>
      </section>
    """
    return _render_page(chapter["title"], body)


def _render_inline_diff(original: str, suggested: str) -> tuple[str, str]:
    matcher = SequenceMatcher(a=original, b=suggested)
    original_parts: list[str] = []
    suggested_parts: list[str] = []

    for opcode, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        original_text = html.escape(original[a_start:a_end])
        suggested_text = html.escape(suggested[b_start:b_end])

        if opcode == "equal":
            original_parts.append(original_text)
            suggested_parts.append(suggested_text)
        elif opcode == "delete":
            original_parts.append(f"<span class=\"diff-removed\">{original_text}</span>")
        elif opcode == "insert":
            suggested_parts.append(f"<span class=\"diff-added\">{suggested_text}</span>")
        elif opcode == "replace":
            original_parts.append(f"<span class=\"diff-removed\">{original_text}</span>")
            suggested_parts.append(f"<span class=\"diff-added\">{suggested_text}</span>")

    return "".join(original_parts), "".join(suggested_parts)


def render_chunk_detail_html(state: dict[str, Any]) -> str:
    chunk = state["chunk"]
    copyedit_review = state.get("copyedit_review")
    approval = state.get("approval")
    translation_review = state.get("translation_review")
    previous_context = "".join(
        f"<li><pre>{html.escape(item.get('text', ''))}</pre></li>"
        for item in chunk.get("previous_context", [])
    ) or "<li>No previous context.</li>"
    next_context = "".join(
        f"<li><pre>{html.escape(item.get('text', ''))}</pre></li>"
        for item in chunk.get("next_context", [])
    ) or "<li>No next context.</li>"
    copyedit_items = "".join(
        (
            "<li>"
            f"<label><input type=\"checkbox\" name=\"approve_index\" value=\"{item['index']}\" checked> "
            f"<strong>{item['change_type']}</strong>"
            "</label>"
            "<div class=\"diff-grid\" style=\"margin-top: 8px;\">"
            "<div class=\"diff-panel\">"
            "<strong>Original</strong><br>"
            f"{item['original_html']}"
            "</div>"
            "<div class=\"diff-panel\">"
            "<strong>Suggested</strong><br>"
            f"{item['suggested_html']}"
            "</div>"
            "</div>"
            f"<div class=\"muted\" style=\"margin-top: 8px;\">{item['reason']}</div>"
            f"<div class=\"muted\">Confidence: <code>{item['confidence']}</code></div>"
            "</li>"
        )
        for item in [
            {
                "index": index,
                "change_type": html.escape(suggestion.get("change_type", "change")),
                "reason": html.escape(suggestion.get("reason", "")),
                "confidence": html.escape(str(suggestion.get("confidence", "unknown"))),
                "original_html": _render_inline_diff(
                    suggestion.get("original", ""),
                    suggestion.get("suggested", ""),
                )[0],
                "suggested_html": _render_inline_diff(
                    suggestion.get("original", ""),
                    suggestion.get("suggested", ""),
                )[1],
            }
            for index, suggestion in enumerate((copyedit_review or {}).get("suggestions", []))
        ]
    ) or "<li>No persisted copyedit review.</li>"
    approval_summary = (
        f"<p class=\"muted\">Approved changes: <code>{approval.get('applied_change_count', 0)}</code></p>"
        if approval is not None
        else "<p class=\"muted\">No persisted approval record.</p>"
    )
    translation_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item.get('paragraph_id', ''))}</strong><br>"
            f"<span>{html.escape(item.get('translated_text', ''))}</span><br>"
            f"<span class=\"muted\">{html.escape(item.get('rationale', ''))}</span>"
            "</li>"
        )
        for item in (translation_review or {}).get("translations", [])
    ) or "<li>No persisted Spanish translation.</li>"

    body = f"""
      <nav>
        <a href=\"/\">← Dashboard</a>
        &nbsp;·&nbsp;
        <a href=\"/chapters/{html.escape(chunk['section_id'])}\">Back to chapter</a>
      </nav>
      <section>
        <h1>Chunk Detail</h1>
        <p><strong>{html.escape(chunk['id'])}</strong></p>
        <p class=\"muted\">{html.escape(chunk.get('section_title', 'Untitled Section'))}</p>
        <p class=\"muted\">Status: <code>{html.escape(chunk.get('review_status', 'unknown'))}</code></p>
      </section>
      <article style=\"margin-top: 18px;\">
        <h2>Chunk Text</h2>
        <form method=\"post\" action=\"/chunks/{html.escape(chunk['id'])}/copyedit\" style=\"margin: 0 0 12px;\">
          <button type=\"submit\">Run Copyedit</button>
        </form>
        <pre>{html.escape(chunk.get('base_text', ''))}</pre>
      </article>
      <div class=\"two-col\" style=\"margin-top: 18px;\">
        <section>
          <h3>Previous Context</h3>
          <ul>{previous_context}</ul>
        </section>
        <section>
          <h3>Next Context</h3>
          <ul>{next_context}</ul>
        </section>
      </div>
      <div class=\"two-col\" style=\"margin-top: 18px;\">
        <section>
          <h3>Suggestion Review</h3>
          <form method=\"post\" action=\"/chunks/{html.escape(chunk['id'])}/approve-copyedit\">
            <ul>{copyedit_items}</ul>
            <button type=\"submit\">Approve Selected Changes</button>
          </form>
          {approval_summary}
        </section>
        <section>
          <h3>Persisted Spanish Translation</h3>
          <ul>{translation_items}</ul>
        </section>
      </div>
    """
    return _render_page(chunk["id"], body)
