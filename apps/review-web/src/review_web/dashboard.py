from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_chunk_summary(chunks_dir: Path) -> tuple[int, list[dict[str, Any]]]:
    index_path = chunks_dir / "index.json"
    if not index_path.exists():
        return 0, []

    payload = _read_json(index_path)
    chunks = payload.get("chunks", [])
    pending_count = sum(1 for chunk in chunks if chunk.get("review_status") == "pending_review")
    return pending_count, [
        {
            "id": chunk["id"],
            "section_title": chunk.get("section_title", "Untitled Section"),
            "review_status": chunk.get("review_status", "unknown"),
        }
        for chunk in chunks[:10]
    ]


def _load_consolidated_summary(consolidated_dir: Path) -> int:
    index_path = consolidated_dir / "index.json"
    if not index_path.exists():
        return 0
    payload = _read_json(index_path)
    return int(payload.get("section_count", 0))


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


def build_dashboard_state(
    *,
    chunks_dir: Path,
    consolidated_dir: Path,
    reports_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    deliverables_dir: Path,
) -> dict[str, Any]:
    pending_chunk_count, recent_chunks = _load_chunk_summary(chunks_dir)
    section_count = _load_consolidated_summary(consolidated_dir)
    consistency_report = _load_consistency_report(reports_dir)
    deliverables = _collect_deliverables(deliverables_dir)

    return {
        "summary": {
            "pending_chunk_count": pending_chunk_count,
            "section_count": section_count,
            "copyedit_review_count": _count_review_files(reviews_ptbr_dir, "*.copyedit.json"),
            "translation_review_count": _count_review_files(reviews_es_dir, "*.translation-es.json"),
            "deliverable_count": len(deliverables),
        },
        "consistency_report": consistency_report,
        "recent_chunks": recent_chunks,
        "deliverables": deliverables,
    }


def render_dashboard_html(state: dict[str, Any]) -> str:
    summary = state["summary"]
    consistency_report = state["consistency_report"]
    recent_chunks = state["recent_chunks"]
    deliverables = state["deliverables"]

    chunk_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(chunk['id'])}</strong> "
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

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Editorial Review Dashboard</title>
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
      h1, h2 {{ margin: 0 0 12px; }}
      p {{ color: var(--muted); }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin: 24px 0 32px;
      }}
      .card, section {{
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
      ul {{
        margin: 0;
        padding-left: 18px;
      }}
      li {{
        margin: 0 0 10px;
      }}
      code {{
        background: #f1e7da;
        border-radius: 6px;
        padding: 2px 6px;
      }}
      @media (max-width: 800px) {{
        .layout {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
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
          <h2>Recent Chunks</h2>
          <ul>{chunk_items}</ul>
        </section>
        <section>
          <h2>Consistency Report</h2>
          <ul>{finding_items}</ul>
        </section>
      </div>
      <section style="margin-top: 18px;">
        <h2>Deliverables</h2>
        <ul>{deliverable_items}</ul>
      </section>
    </main>
  </body>
</html>
"""
