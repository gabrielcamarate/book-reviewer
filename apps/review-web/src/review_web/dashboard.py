from __future__ import annotations

import html
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from editorial_core.characters import read_characters_registry
from editorial_core.decisions import read_editorial_decisions
from editorial_core.job_log import read_recent_job_logs
from editorial_core.queue import build_review_queue
from editorial_core.search import search_repository_state
from editorial_core.translation_es import STABLE_REVIEW_STATUSES
from editorial_core.world_rules import read_world_rules_registry


CHAPTER_TITLE_RE = re.compile(
    r"^Cap[ií]tulo\s+([IVXLCDM]+|\d+)(?::\s*(.+?))?\.?$",
    re.IGNORECASE,
)

ROMAN_VALUES = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


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


def _load_chapter_index(chapters_dir: Path) -> dict[str, Any]:
    index_path = chapters_dir / "index.json"
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
        "findings_by_type": findings_by_type,
    }


def _load_decisions(decisions_path: Path) -> list[dict[str, str]]:
    return list(reversed(read_editorial_decisions(decisions_path)))


def _load_characters(characters_path: Path) -> list[dict[str, Any]]:
    return read_characters_registry(characters_path)


def _load_world_rules(world_rules_path: Path) -> dict[str, list[dict[str, Any]]]:
    return read_world_rules_registry(world_rules_path)


def _load_recent_jobs(jobs_dir: Path) -> list[dict[str, Any]]:
    return read_recent_job_logs(jobs_dir=jobs_dir)


def _build_paragraph_chunk_map(chunks_dir: Path) -> dict[str, str]:
    payload = _load_chunk_index(chunks_dir)
    paragraph_map: dict[str, str] = {}
    for chunk in payload.get("chunks", []):
        chunk_file = chunk.get("file")
        if not chunk_file:
            continue
        chunk_path = chunks_dir / chunk_file
        if not chunk_path.exists():
            continue
        chunk_payload = _read_json(chunk_path)
        for paragraph_id in chunk_payload.get("paragraph_ids", []):
            paragraph_map[paragraph_id] = chunk_payload["id"]
    return paragraph_map


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


def _parse_chapter_number(raw_value: str) -> int | None:
    stripped = raw_value.strip()
    if not stripped:
        return None
    if stripped.isdigit():
        return int(stripped)

    total = 0
    previous_value = 0
    for character in reversed(stripped.upper()):
        value = ROMAN_VALUES.get(character)
        if value is None:
            return None
        if value < previous_value:
            total -= value
        else:
            total += value
            previous_value = value
    return total if total > 0 else None


def _extract_declared_chapter_number(title: str) -> int | None:
    match = CHAPTER_TITLE_RE.match(title.strip())
    if match is None:
        return None
    return _parse_chapter_number(match.group(1))


def _compute_missing_chapter_numbers(chapters: list[dict[str, Any]]) -> list[int]:
    declared_numbers = sorted(
        {
            int(chapter["declared_chapter_number"])
            for chapter in chapters
            if chapter.get("declared_chapter_number") is not None and not chapter.get("missing")
        }
    )
    if not declared_numbers:
        return []

    missing_numbers: list[int] = []
    previous_number = 0
    for chapter_number in declared_numbers:
        if chapter_number > previous_number + 1:
            missing_numbers.extend(range(previous_number + 1, chapter_number))
        previous_number = chapter_number
    return missing_numbers


def compute_export_readiness(
    *,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, dict[str, Any]]:
    chapter_index = _read_json(chapters_dir / "index.json")
    translation_map: dict[str, str] = {}
    if reviews_es_dir.exists():
        for translation_path in sorted(reviews_es_dir.glob("*.translation-es.json")):
            payload = _read_json(translation_path)
            for entry in payload.get("translations", []):
                translation_map[entry["paragraph_id"]] = entry["translated_text"]

    required_paragraph_ids: list[str] = []
    for section in chapter_index.get("sections", []):
        section_path = consolidated_dir / section["file"]
        if section_path.exists():
            section_payload = _read_json(section_path)
        else:
            section_payload = _read_json(chapters_dir / section["file"])
        required_paragraph_ids.extend(
            paragraph["id"]
            for paragraph in section_payload.get("paragraphs", [])
        )

    missing_translation_ids = [
        paragraph_id for paragraph_id in required_paragraph_ids if paragraph_id not in translation_map
    ]

    return {
        "pt-BR": {
            "eligible": True,
            "reason": "O export em pt-BR está disponível.",
        },
        "es": {
            "eligible": not missing_translation_ids,
            "reason": (
                "O export em espanhol está disponível."
                if not missing_translation_ids
                else f"Faltam traduções para {len(missing_translation_ids)} parágrafo(s)."
            ),
        },
    }


def _build_chapter_summary(
    *,
    chapters_dir: Path,
    consolidated_dir: Path,
    chunks_by_section: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    chapter_index = _load_chapter_index(chapters_dir)
    consolidated_index = _load_consolidated_index(consolidated_dir)
    chapters_by_id: dict[str, dict[str, Any]] = {}
    for section in chapter_index.get("sections", []):
        if not str(section.get("id", "")).startswith("chapter-"):
            continue
        chapter_id = section["id"]
        chapters_by_id[chapter_id] = {
            "id": chapter_id,
            "title": section.get("title", "Capítulo sem título"),
            "review_status": section.get("review_status", "unknown"),
            "chunk_count": len(chunks_by_section.get(chapter_id, [])),
            "declared_chapter_number": section.get("declared_chapter_number")
            or _extract_declared_chapter_number(section.get("title", "")),
            "missing": False,
        }
    for section in consolidated_index.get("sections", []):
        if not str(section.get("id", "")).startswith("chapter-"):
            continue
        chapter_id = section["id"]
        existing = chapters_by_id.get(chapter_id, {})
        chapters_by_id[chapter_id] = {
            "id": chapter_id,
            "title": section.get("title", "Capítulo sem título"),
            "review_status": section.get("review_status", "unknown"),
            "chunk_count": len(chunks_by_section.get(chapter_id, [])),
            "declared_chapter_number": section.get("declared_chapter_number")
            or existing.get("declared_chapter_number")
            or _extract_declared_chapter_number(section.get("title", "")),
            "missing": False,
        }

    for section_id, chunks in chunks_by_section.items():
        if not section_id.startswith("chapter-") or section_id in chapters_by_id:
            continue
        first_chunk = chunks[0]
        chapters_by_id[section_id] = {
            "id": section_id,
            "title": first_chunk.get("section_title", "Capítulo sem título"),
            "review_status": "unknown",
            "chunk_count": len(chunks),
            "declared_chapter_number": _extract_declared_chapter_number(
                first_chunk.get("section_title", "")
            ),
            "missing": False,
        }

    ordered_chapters = sorted(
        chapters_by_id.values(),
        key=lambda chapter: (
            chapter.get("declared_chapter_number") is None,
            chapter.get("declared_chapter_number") or 0,
            chapter["id"],
        ),
    )

    missing_numbers = chapter_index.get("missing_chapter_numbers")
    if not isinstance(missing_numbers, list):
        missing_numbers = _compute_missing_chapter_numbers(ordered_chapters)
    missing_number_set = {int(number) for number in missing_numbers}

    chapters_with_gaps: list[dict[str, Any]] = []
    previous_number = 0
    for chapter in ordered_chapters:
        declared_number = chapter.get("declared_chapter_number")
        if declared_number is not None:
            for missing_number in range(previous_number + 1, int(declared_number)):
                if missing_number not in missing_number_set:
                    continue
                chapters_with_gaps.append(
                    {
                        "id": f"missing-chapter-{missing_number:04d}",
                        "title": f"Capítulo {missing_number} — ausente no manuscrito segmentado",
                        "review_status": "missing_in_manuscript",
                        "chunk_count": 0,
                        "declared_chapter_number": missing_number,
                        "missing": True,
                    }
                )
            previous_number = int(declared_number)
        chapters_with_gaps.append(chapter)

    return chapters_with_gaps


def _render_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
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
    chapters_dir: Path,
    chunks_dir: Path,
    consolidated_dir: Path,
    reports_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    deliverables_dir: Path,
    decisions_path: Path,
    jobs_dir: Path,
) -> dict[str, Any]:
    pending_chunk_count, recent_chunks, chunks_by_section = _load_chunk_summary(chunks_dir)
    consolidated_index = _load_consolidated_index(consolidated_dir)
    consistency_report = _load_consistency_report(reports_dir)
    deliverables = _collect_deliverables(deliverables_dir)
    chapters = _build_chapter_summary(
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        chunks_by_section=chunks_by_section,
    )
    decisions = _load_decisions(decisions_path)
    recent_jobs = _load_recent_jobs(jobs_dir)
    export_readiness = compute_export_readiness(
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_es_dir=reviews_es_dir,
    )

    return {
        "summary": {
            "pending_chunk_count": pending_chunk_count,
            "section_count": int(consolidated_index.get("section_count", 0)),
            "copyedit_review_count": _count_review_files(reviews_ptbr_dir, "*.copyedit.json"),
            "translation_review_count": _count_review_files(reviews_es_dir, "*.translation-es.json"),
            "deliverable_count": len(deliverables),
            "decision_count": len(decisions),
            "job_count": len(recent_jobs),
        },
        "consistency_report": consistency_report,
        "recent_chunks": recent_chunks,
        "chapters": chapters,
        "deliverables": deliverables,
        "recent_decisions": decisions[:5],
        "recent_jobs": recent_jobs,
        "export_readiness": export_readiness,
    }


def build_decisions_state(*, decisions_path: Path) -> dict[str, Any]:
    decisions = _load_decisions(decisions_path)
    return {
        "decision_count": len(decisions),
        "decisions": decisions,
    }


def build_characters_state(*, characters_path: Path) -> dict[str, Any]:
    characters = _load_characters(characters_path)
    return {
        "character_count": len(characters),
        "characters": characters,
    }


def build_world_rules_state(*, world_rules_path: Path) -> dict[str, Any]:
    registry = _load_world_rules(world_rules_path)
    organizations = registry["organizations"]
    concepts = registry["concepts"]
    return {
        "organization_count": len(organizations),
        "concept_count": len(concepts),
        "organizations": organizations,
        "concepts": concepts,
    }


def build_search_state(
    *,
    query: str,
    chunks_dir: Path,
    consolidated_dir: Path,
    glossary_path: Path,
    decisions_path: Path,
) -> dict[str, Any]:
    return search_repository_state(
        query=query,
        chunks_dir=chunks_dir,
        consolidated_dir=consolidated_dir,
        glossary_path=glossary_path,
        decisions_path=decisions_path,
    )


def build_queue_state(
    *,
    chunks_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
) -> dict[str, Any]:
    return build_review_queue(
        chunks_dir=chunks_dir,
        reviews_ptbr_dir=reviews_ptbr_dir,
        reviews_es_dir=reviews_es_dir,
    )


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
        fallback_chunks = chunks_by_section.get(chapter_id)
        if not fallback_chunks:
            raise ValueError(f"chapter not found: {chapter_id}")
        chapter = {
            "id": chapter_id,
            "title": fallback_chunks[0].get("section_title", "Capítulo sem título"),
            "review_status": "unknown",
        }

    return {
        "chapter": {
            "id": chapter["id"],
            "title": chapter.get("title", "Untitled Chapter"),
            "review_status": chapter.get("review_status", "unknown"),
        },
        "chunks": chunks_by_section.get(chapter_id, []),
    }


def build_consistency_detail_state(
    *,
    finding_type: str,
    reports_dir: Path,
    chunks_dir: Path,
) -> dict[str, Any]:
    report = _load_consistency_report(reports_dir)
    findings = report.get("findings_by_type", {}).get(finding_type)
    if findings is None:
        raise ValueError(f"consistency finding type not found: {finding_type}")

    paragraph_chunk_map = _build_paragraph_chunk_map(chunks_dir)
    enriched_findings: list[dict[str, Any]] = []
    for finding in findings:
        paragraph_id = finding.get("paragraph_id")
        resolved_chunk_id = paragraph_chunk_map.get(paragraph_id) if paragraph_id else None
        enriched_findings.append(
            {
                **finding,
                "resolved_chunk_id": resolved_chunk_id,
            }
        )

    return {
        "finding_type": finding_type,
        "finding_count": len(enriched_findings),
        "findings": enriched_findings,
    }


def build_chunk_detail_state(
    *,
    chunk_id: str,
    chunks_dir: Path,
    consolidated_dir: Path,
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
    style_path = reviews_ptbr_dir / f"{chunk_id}.style.json"
    style_approval_path = reviews_ptbr_dir / f"{chunk_id}.style.approval.json"
    translation_path = reviews_es_dir / f"{chunk_id}.translation-es.json"
    consolidated_path = consolidated_dir / f"{chunk_payload['section_id']}.json"
    consolidated_payload = _read_json(consolidated_path) if consolidated_path.exists() else None
    consolidated_paragraphs: list[dict[str, Any]] = []
    translation_eligibility = {
        "eligible": False,
        "reason": "O chunk ainda não está pronto para tradução ao espanhol.",
    }
    if consolidated_payload is not None:
        target_paragraph_ids = set(chunk_payload.get("paragraph_ids", []))
        consolidated_paragraphs = [
            paragraph
            for paragraph in consolidated_payload.get("paragraphs", [])
            if paragraph.get("id") in target_paragraph_ids
        ]
        if translation_path.exists():
            translation_eligibility = {
                "eligible": False,
                "reason": "Já existe tradução em espanhol para este chunk.",
            }
        elif consolidated_paragraphs and all(
            paragraph.get("review_status") in STABLE_REVIEW_STATUSES
            for paragraph in consolidated_paragraphs
        ):
            translation_eligibility = {
                "eligible": True,
                "reason": "O chunk está estável e pronto para tradução ao espanhol.",
            }
        else:
            translation_eligibility = {
                "eligible": False,
                "reason": "O chunk precisa de aprovação estável em pt-BR antes da tradução ao espanhol.",
            }
    translation_comparison: list[dict[str, Any]] = []
    translation_map = {
        item.get("paragraph_id"): item
        for item in ( _read_json(translation_path).get("translations", []) if translation_path.exists() else [] )
    }
    for paragraph in consolidated_paragraphs:
        translation = translation_map.get(paragraph.get("id"))
        if translation is None:
            continue
        translation_comparison.append(
            {
                "paragraph_id": paragraph.get("id"),
                "ptbr_text": paragraph.get("text", ""),
                "translated_text": translation.get("translated_text", ""),
                "rationale": translation.get("rationale", ""),
                "confidence": translation.get("confidence", ""),
            }
        )

    return {
        "chunk": chunk_payload,
        "copyedit_review": _read_json(copyedit_path) if copyedit_path.exists() else None,
        "approval": _read_json(approval_path) if approval_path.exists() else None,
        "style_review": _read_json(style_path) if style_path.exists() else None,
        "style_approval": _read_json(style_approval_path) if style_approval_path.exists() else None,
        "translation_review": _read_json(translation_path) if translation_path.exists() else None,
        "consolidated_paragraphs": consolidated_paragraphs,
        "translation_eligibility": translation_eligibility,
        "translation_comparison": translation_comparison,
    }


def render_dashboard_html(state: dict[str, Any]) -> str:
    summary = state["summary"]
    consistency_report = state["consistency_report"]
    recent_chunks = state["recent_chunks"]
    chapters = state["chapters"]
    deliverables = state["deliverables"]
    recent_decisions = state["recent_decisions"]
    recent_jobs = state.get("recent_jobs", [])
    export_readiness = state["export_readiness"]

    chapter_items = "".join(
        (
            "<li>"
            + (
                f"<strong>{html.escape(chapter['title'])}</strong> "
                if chapter.get("missing")
                else f"<a href=\"/chapters/{html.escape(chapter['id'])}\"><strong>{html.escape(chapter['title'])}</strong></a> "
            )
            + f"<code>{html.escape(chapter['review_status'])}</code> "
            + (
                "<span class=\"muted\">sem conteúdo segmentado</span>"
                if chapter.get("missing")
                else f"<span class=\"muted\">{chapter['chunk_count']} chunks</span>"
            )
            + "</li>"
        )
        for chapter in chapters
    ) or "<li>Nenhum capítulo disponível.</li>"

    chunk_items = "".join(
        (
            "<li>"
            f"<a class=\"chunk-link\" href=\"/chunks/{html.escape(chunk['id'])}\">{html.escape(chunk['id'])}</a> "
            f"<span>{html.escape(chunk['section_title'])}</span> "
            f"<code>{html.escape(chunk['review_status'])}</code>"
            "</li>"
        )
        for chunk in recent_chunks
    ) or "<li>Nenhum chunk disponível.</li>"

    finding_items = "".join(
        (
            "<li>"
            f"<a href=\"/consistency/{html.escape(item['type'])}\"><strong>{html.escape(item['type'])}</strong></a>: {item['count']}"
            "</li>"
        )
        for item in consistency_report["finding_types"]
    ) or "<li>Nenhum relatório de consistência disponível.</li>"

    deliverable_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['name'])}</strong> "
            f"<code>{html.escape(item['path'])}</code>"
            "</li>"
        )
        for item in deliverables
    ) or "<li>Nenhum entregável gerado ainda.</li>"
    decision_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['title'])}</strong> "
            f"<code>{html.escape(item.get('scope', 'global'))}</code>"
            f"<div class=\"muted\">{html.escape(item.get('rationale', ''))}</div>"
            "</li>"
        )
        for item in recent_decisions
    ) or "<li>Nenhuma decisão editorial registrada.</li>"
    job_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item.get('job_type', 'job'))}</strong> "
            f"<code>{html.escape(item.get('status', 'unknown'))}</code> "
            f"<span class=\"muted\">{html.escape(item.get('target_id', ''))}</span>"
            "</li>"
        )
        for item in recent_jobs
    ) or "<li>Nenhum job recente registrado.</li>"

    body = f"""
      <header>
        <h1>Painel de Revisão Editorial</h1>
        <p>Interface web local sobre o backend persistido de revisão editorial.</p>
        <form method="get" action="/search" style="margin-top: 18px;">
          <label>Buscar no projeto<br><input type="text" name="q" placeholder="Sistema Terra, Joseph Harrison..." style="width: min(520px, 100%);"></label>
          <button type="submit">Buscar</button>
        </form>
        <p style="margin-top: 12px;"><a href="/queue">Abrir fila de revisão</a></p>
        <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px;">
          <form method="post" action="/exports/pt-BR/run" style="margin: 0;">
            <button type="submit">Gerar Export pt-BR</button>
          </form>
          {
            f'<form method="post" action="/exports/es/run" style="margin: 0;"><button type="submit">Gerar Export Espanhol</button></form>'
            if export_readiness["es"]["eligible"]
            else f'<p class="muted" style="margin: 0;">Export espanhol indisponível: {html.escape(export_readiness["es"]["reason"])}</p>'
          }
        </div>
      </header>
      <div class="grid">
        <div class="card"><span>Chunks Pendentes de Revisão</span><strong>{summary['pending_chunk_count']}</strong></div>
        <div class="card"><span>Seções no Estado Consolidado</span><strong>{summary['section_count']}</strong></div>
        <div class="card"><span>Arquivos de Revisão pt-BR</span><strong>{summary['copyedit_review_count']}</strong></div>
        <div class="card"><span>Arquivos de Tradução Espanhola</span><strong>{summary['translation_review_count']}</strong></div>
        <div class="card"><span>Entregáveis Gerados</span><strong>{summary['deliverable_count']}</strong></div>
        <div class="card"><span>Achados de Consistência</span><strong>{consistency_report['finding_count']}</strong></div>
        <div class="card"><span>Decisões Editoriais</span><strong>{summary.get('decision_count', len(recent_decisions))}</strong></div>
        <div class="card"><span>Jobs Recentes</span><strong>{summary.get('job_count', len(recent_jobs))}</strong></div>
      </div>
      <div class="layout">
        <section>
          <h2>Navegação por Capítulo</h2>
          <ul>{chapter_items}</ul>
        </section>
        <section>
          <h2>Relatório de Consistência</h2>
          <form method=\"post\" action=\"/consistency/run\" style=\"margin: 0 0 12px;\">
            <button type=\"submit\">Regenerar Relatório de Consistência</button>
          </form>
          <ul>{finding_items}</ul>
        </section>
      </div>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Chunks Recentes</h2>
          <ul>{chunk_items}</ul>
        </section>
        <section>
          <h2>Entregáveis</h2>
          <ul>{deliverable_items}</ul>
        </section>
      </div>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Decisões Editoriais</h2>
          <p><a href="/decisions">Abrir registro completo de decisões</a></p>
          <ul>{decision_items}</ul>
        </section>
        <section>
          <h2>Registrar Nova Decisão</h2>
          <form method="post" action="/decisions">
            <p><label>Título<br><input type="text" name="title" required style="width: 100%;"></label></p>
            <p><label>Escopo<br><input type="text" name="scope" placeholder="chapter-0001... ou global" style="width: 100%;"></label></p>
            <p><label>Justificativa<br><textarea name="rationale" required style="width: 100%; min-height: 120px;"></textarea></label></p>
            <button type="submit">Salvar Decisão Editorial</button>
          </form>
        </section>
      </div>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Registro de Personagens</h2>
          <p><a href="/characters">Abrir registro de personagens</a></p>
        </section>
        <section>
          <h2>Atualizar Registro</h2>
          <form method="post" action="/characters/run">
            <button type="submit">Gerar Registro de Personagens</button>
          </form>
        </section>
      </div>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Regras do Mundo</h2>
          <p><a href="/world-rules">Abrir registro de regras do mundo</a></p>
        </section>
        <section>
          <h2>Atualizar Registro</h2>
          <form method="post" action="/world-rules/run">
            <button type="submit">Gerar Registro de Regras do Mundo</button>
          </form>
        </section>
      </div>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Jobs Recentes</h2>
          <ul>{job_items}</ul>
        </section>
      </div>
    """
    return _render_page("Painel de Revisão Editorial", body)


def render_decisions_html(state: dict[str, Any]) -> str:
    decision_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['title'])}</strong><br>"
            f"<span class=\"muted\">{html.escape(item.get('timestamp', ''))}</span><br>"
            + (
                f"<a class=\"chunk-link\" href=\"/chunks/{html.escape(item['scope'])}\">{html.escape(item['scope'])}</a><br>"
                if item.get("scope", "").startswith("chapter-") and "-chunk-" in item.get("scope", "")
                else f"<code>{html.escape(item.get('scope', 'global'))}</code><br>"
            )
            + f"<span>{html.escape(item.get('rationale', ''))}</span>"
            "</li>"
        )
        for item in state["decisions"]
    ) or "<li>Nenhuma decisão editorial registrada.</li>"

    body = f"""
      <nav><a href=\"/\">← Painel</a></nav>
      <section>
        <h1>Decisões Editoriais</h1>
        <p class=\"muted\">Total de decisões registradas: <code>{state['decision_count']}</code></p>
      </section>
      <section style=\"margin-top: 18px;\">
        <ul>{decision_items}</ul>
      </section>
    """
    return _render_page("Decisões Editoriais", body)


def render_characters_html(state: dict[str, Any]) -> str:
    character_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['title'])}</strong><br>"
            f"<code>{html.escape(item.get('preferred_form', item['title']))}</code><br>"
            + (
                f"<span class=\"muted\">Aliases: {html.escape(', '.join(item.get('aliases', [])))}</span><br>"
                if item.get("aliases")
                else "<span class=\"muted\">Aliases: none confirmed</span><br>"
            )
            + f"<span class=\"muted\">Evidence: {html.escape(', '.join(item.get('evidence', [])))}</span>"
            "</li>"
        )
        for item in state["characters"]
    ) or "<li>Nenhum personagem registrado.</li>"

    body = f"""
      <nav><a href=\"/\">← Painel</a></nav>
      <section>
        <h1>Registro de Personagens</h1>
        <p class=\"muted\">Total de personagens registrados: <code>{state['character_count']}</code></p>
      </section>
      <section style=\"margin-top: 18px;\">
        <ul>{character_items}</ul>
      </section>
    """
    return _render_page("Registro de Personagens", body)


def render_world_rules_html(state: dict[str, Any]) -> str:
    organization_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['title'])}</strong><br>"
            f"<span>{html.escape(item.get('expanded_form', ''))}</span><br>"
            + (
                f"<span class=\"muted\">Aliases: {html.escape(', '.join(item.get('aliases', [])))}</span><br>"
                if item.get("aliases")
                else "<span class=\"muted\">Aliases: none confirmed</span><br>"
            )
            + f"<span class=\"muted\">Evidence: {html.escape(', '.join(item.get('evidence', [])))}</span>"
            "</li>"
        )
        for item in state["organizations"]
    ) or "<li>Nenhuma organização registrada.</li>"

    concept_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['title'])}</strong><br>"
            f"<code>{html.escape(item.get('preferred_form', item['title']))}</code><br>"
            + (
                f"<span class=\"muted\">Aliases: {html.escape(', '.join(item.get('aliases', [])))}</span><br>"
                if item.get("aliases")
                else "<span class=\"muted\">Aliases: none confirmed</span><br>"
            )
            + f"<span class=\"muted\">Evidence: {html.escape(', '.join(item.get('evidence', [])))}</span>"
            "</li>"
        )
        for item in state["concepts"]
    ) or "<li>Nenhum conceito registrado.</li>"

    body = f"""
      <nav><a href=\"/\">← Painel</a></nav>
      <section>
        <h1>Registro de Regras do Mundo</h1>
        <p class=\"muted\">Organizações: <code>{state['organization_count']}</code> · Conceitos: <code>{state['concept_count']}</code></p>
      </section>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Organizações e Acrônimos</h2>
          <ul>{organization_items}</ul>
        </section>
        <section>
          <h2>Conceitos e Fórmulas</h2>
          <ul>{concept_items}</ul>
        </section>
      </div>
    """
    return _render_page("Registro de Regras do Mundo", body)


def render_search_html(state: dict[str, Any]) -> str:
    chapter_items = "".join(
        (
            "<li>"
            f"<a href=\"{html.escape(item['link'])}\"><strong>{html.escape(item['title'])}</strong></a>"
            "</li>"
        )
        for item in state["chapter_matches"]
    ) or "<li>Nenhum capítulo correspondente.</li>"

    chunk_items = "".join(
        (
            "<li>"
            f"<a class=\"chunk-link\" href=\"{html.escape(item['link'])}\">{html.escape(item['chunk_id'])}</a><br>"
            f"<span class=\"muted\">{html.escape(item['section_title'])}</span><br>"
            f"<span>{html.escape(item['excerpt'])}</span>"
            "</li>"
        )
        for item in state["chunk_matches"]
    ) or "<li>Nenhum chunk correspondente.</li>"

    glossary_items = "".join(
        (
            "<li>"
            f"<a href=\"{html.escape(item['link'])}\"><strong>{html.escape(item['title'])}</strong></a><br>"
            f"<span>{html.escape(item['excerpt'])}</span>"
            "</li>"
        )
        for item in state["glossary_matches"]
    ) or "<li>Nenhum termo correspondente no glossário.</li>"

    decision_items = "".join(
        (
            "<li>"
            f"<a href=\"{html.escape(item['link'])}\"><strong>{html.escape(item['title'])}</strong></a><br>"
            f"<code>{html.escape(item.get('scope', 'global'))}</code><br>"
            f"<span>{html.escape(item.get('rationale', ''))}</span>"
            "</li>"
        )
        for item in state["decision_matches"]
    ) or "<li>Nenhuma decisão correspondente.</li>"

    body = f"""
      <nav><a href=\"/\">← Painel</a></nav>
      <section>
        <h1>Resultados da Busca</h1>
        <p class=\"muted\">Consulta: <code>{html.escape(state['query'])}</code> · Resultados: <code>{state['result_count']}</code></p>
      </section>
      <div class="layout" style="margin-top: 18px;">
        <section>
          <h2>Capítulos</h2>
          <ul>{chapter_items}</ul>
        </section>
        <section>
          <h2>Chunks</h2>
          <ul>{chunk_items}</ul>
        </section>
      </div>
      <div class="layout" style="margin-top: 18px;">
        <section id="glossary-results">
          <h2>Glossário</h2>
          <ul>{glossary_items}</ul>
        </section>
        <section>
          <h2>Decisões Editoriais</h2>
          <ul>{decision_items}</ul>
        </section>
      </div>
    """
    return _render_page("Resultados da Busca", body)


def render_queue_html(state: dict[str, Any]) -> str:
    summary = state["summary"]
    next_recommended = state["next_recommended"]
    queue_items = "".join(
        (
            "<li>"
            f"<a class=\"chunk-link\" href=\"{html.escape(item['link'])}\">{html.escape(item['chunk_id'])}</a> "
            f"<code>{html.escape(item['queue_status'])}</code> "
            f"<span class=\"muted\">{html.escape(item['section_title'])}</span>"
            "</li>"
        )
        for item in state["queue_items"]
    ) or "<li>Nenhum chunk disponível na fila.</li>"

    resume_block = (
        f"<p><a class=\"chunk-link\" href=\"{html.escape(next_recommended['link'])}\">Retomar Próximo Chunk</a></p>"
        f"<p class=\"muted\">Próximo recomendado: <code>{html.escape(next_recommended['chunk_id'])}</code> · <code>{html.escape(next_recommended['queue_status'])}</code></p>"
        if next_recommended is not None
        else "<p class=\"muted\">Nenhum chunk pendente para retomada.</p>"
    )

    body = f"""
      <nav><a href=\"/\">← Painel</a></nav>
      <section>
        <h1>Fila de Revisão</h1>
        {resume_block}
      </section>
      <div class="grid">
        <div class="card"><span>Total de Chunks</span><strong>{summary['total_chunks']}</strong></div>
        <div class="card"><span>Pendentes de Copyedit</span><strong>{summary['pending_copyedit_count']}</strong></div>
        <div class="card"><span>Aguardando Aprovação</span><strong>{summary['awaiting_approval_count']}</strong></div>
        <div class="card"><span>Aprovados</span><strong>{summary['approved_count']}</strong></div>
        <div class="card"><span>Traduzidos</span><strong>{summary['translated_count']}</strong></div>
        <div class="card"><span>Referência Aprovada</span><strong>{summary['reference_count']}</strong></div>
      </div>
      <section>
        <h2>Ordem Operacional</h2>
        <ul>{queue_items}</ul>
      </section>
    """
    return _render_page("Fila de Revisão", body)


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
    ) or "<li>Nenhum chunk disponível para este capítulo.</li>"

    body = f"""
      <nav><a href=\"/\">← Painel</a></nav>
      <section>
        <h1>{html.escape(chapter['title'])}</h1>
        <p><strong>Navegação por Capítulo</strong> para <code>{html.escape(chapter['id'])}</code></p>
        <p class=\"muted\">Status de revisão: <code>{html.escape(chapter['review_status'])}</code></p>
      </section>
      <section style=\"margin-top: 18px;\">
        <h2>Chunks</h2>
        <ul>{chunk_items}</ul>
      </section>
    """
    return _render_page(chapter["title"], body)


def render_consistency_detail_html(state: dict[str, Any]) -> str:
    finding_items = "".join(
        (
            "<li>"
            f"<pre>{html.escape(json.dumps(finding, ensure_ascii=False, indent=2))}</pre>"
            + (
                f"<p><a class=\"chunk-link\" href=\"/chunks/{html.escape(finding['resolved_chunk_id'])}\">Abrir chunk relacionado</a></p>"
                if finding.get("resolved_chunk_id")
                else ""
            )
            + "</li>"
        )
        for finding in state["findings"]
    ) or "<li>Nenhum achado para este tipo.</li>"

    body = f"""
      <nav><a href=\"/\">← Painel</a></nav>
      <section>
        <h1>Achados de Consistência</h1>
        <p><strong>{html.escape(state['finding_type'])}</strong></p>
        <p class=\"muted\">Achados: <code>{state['finding_count']}</code></p>
      </section>
      <section style=\"margin-top: 18px;\">
        <ul>{finding_items}</ul>
      </section>
    """
    return _render_page(f"Consistência · {state['finding_type']}", body)


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
    style_review = state.get("style_review")
    style_approval = state.get("style_approval")
    translation_review = state.get("translation_review")
    consolidated_paragraphs = state.get("consolidated_paragraphs", [])
    translation_comparison = state.get("translation_comparison", [])
    translation_eligibility = state.get(
        "translation_eligibility",
        {"eligible": False, "reason": "O chunk ainda não está pronto para tradução ao espanhol."},
    )
    previous_context = "".join(
        f"<li><pre>{html.escape(item.get('text', ''))}</pre></li>"
        for item in chunk.get("previous_context", [])
    ) or "<li>Nenhum contexto anterior.</li>"
    next_context = "".join(
        f"<li><pre>{html.escape(item.get('text', ''))}</pre></li>"
        for item in chunk.get("next_context", [])
    ) or "<li>Nenhum contexto seguinte.</li>"
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
            "<strong>Sugerido</strong><br>"
            f"{item['suggested_html']}"
            "</div>"
            "</div>"
            f"<div class=\"muted\" style=\"margin-top: 8px;\">{item['reason']}</div>"
            f"<div class=\"muted\">Confiança: <code>{item['confidence']}</code></div>"
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
    ) or "<li>Nenhuma revisão de copyedit persistida.</li>"
    approval_summary = (
        f"<p class=\"muted\">Alterações aprovadas: <code>{approval.get('applied_change_count', 0)}</code></p>"
        if approval is not None
        else "<p class=\"muted\">Nenhum registro persistido de aprovação.</p>"
    )
    style_items = "".join(
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
            "<strong>Sugerido</strong><br>"
            f"{item['suggested_html']}"
            "</div>"
            "</div>"
            f"<div class=\"muted\" style=\"margin-top: 8px;\">{item['reason']}</div>"
            f"<div class=\"muted\">Confiança: <code>{item['confidence']}</code></div>"
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
            for index, suggestion in enumerate((style_review or {}).get("suggestions", []))
        ]
    ) or "<li>Nenhuma revisão de style persistida.</li>"
    style_approval_summary = (
        f"<p class=\"muted\">Alterações de style aprovadas: <code>{style_approval.get('applied_change_count', 0)}</code></p>"
        if style_approval is not None
        else "<p class=\"muted\">Nenhum registro persistido de aprovação de style.</p>"
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
    ) or "<li>Nenhuma tradução espanhola persistida.</li>"
    if translation_eligibility["eligible"]:
        translation_controls = (
            f"<form method=\"post\" action=\"/chunks/{html.escape(chunk['id'])}/translation-es\" style=\"margin: 0 0 12px;\">"
            "<button type=\"submit\">Executar Tradução para Espanhol</button>"
            "</form>"
        )
    else:
        translation_controls = (
            f"<p class=\"muted\">Tradução indisponível: {html.escape(translation_eligibility['reason'])}</p>"
        )
    consolidated_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(paragraph.get('id', ''))}</strong>"
            f"<div class=\"muted\">Status: <code>{html.escape(paragraph.get('review_status', 'unknown'))}</code></div>"
            "<div style=\"margin-top: 8px;\"><strong>Texto Atual</strong><pre>"
            f"{html.escape(paragraph.get('text', ''))}"
            "</pre></div>"
            "<div style=\"margin-top: 8px;\"><strong>Texto-Fonte</strong><pre>"
            f"{html.escape(paragraph.get('source_text', ''))}"
            "</pre></div>"
            "<div style=\"margin-top: 8px;\"><strong>Metadados da Revisão Aplicada</strong>"
            f"{_render_applied_review_metadata(paragraph.get('applied_reviews', []))}"
            "</div>"
            "</li>"
        )
        for paragraph in consolidated_paragraphs
    ) or "<li>Ainda não há estado consolidado para este chunk.</li>"
    translation_comparison_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item.get('paragraph_id', ''))}</strong>"
            "<div class=\"diff-grid\" style=\"margin-top: 8px;\">"
            "<div class=\"diff-panel\">"
            "<strong>pt-BR</strong><br>"
            f"{html.escape(item.get('ptbr_text', ''))}"
            "</div>"
            "<div class=\"diff-panel\">"
            "<strong>Español</strong><br>"
            f"{html.escape(item.get('translated_text', ''))}"
            "</div>"
            "</div>"
            f"<div class=\"muted\" style=\"margin-top: 8px;\">{html.escape(str(item.get('rationale', '')))}</div>"
            f"<div class=\"muted\">Confiança: <code>{html.escape(str(item.get('confidence', '')))}</code></div>"
            "</li>"
        )
        for item in translation_comparison
    ) or "<li>Ainda não há comparação alinhada entre pt-BR e espanhol para este chunk.</li>"

    body = f"""
      <nav>
        <a href=\"/\">← Painel</a>
        &nbsp;·&nbsp;
        <a href=\"/chapters/{html.escape(chunk['section_id'])}\">Voltar ao capítulo</a>
      </nav>
      <section>
        <h1>Detalhe do Chunk</h1>
        <p><strong>{html.escape(chunk['id'])}</strong></p>
        <p class=\"muted\">{html.escape(chunk.get('section_title', 'Seção sem título'))}</p>
        <p class=\"muted\">Status: <code>{html.escape(chunk.get('review_status', 'unknown'))}</code></p>
      </section>
      <article style=\"margin-top: 18px;\">
        <h2>Texto do Chunk</h2>
        <form method=\"post\" action=\"/chunks/{html.escape(chunk['id'])}/copyedit\" style=\"margin: 0 0 12px;\">
          <button type=\"submit\">Executar Copyedit</button>
        </form>
        <form method=\"post\" action=\"/chunks/{html.escape(chunk['id'])}/style\" style=\"margin: 0 0 12px;\">
          <button type=\"submit\">Executar Style</button>
        </form>
        <pre>{html.escape(chunk.get('base_text', ''))}</pre>
      </article>
      <div class=\"two-col\" style=\"margin-top: 18px;\">
        <section>
          <h3>Contexto Anterior</h3>
          <ul>{previous_context}</ul>
        </section>
        <section>
          <h3>Contexto Seguinte</h3>
          <ul>{next_context}</ul>
        </section>
      </div>
      <div class=\"two-col\" style=\"margin-top: 18px;\">
        <section>
          <h3>Revisão de Sugestões</h3>
          <form method=\"post\" action=\"/chunks/{html.escape(chunk['id'])}/approve-copyedit\">
            <ul>{copyedit_items}</ul>
            <button type=\"submit\">Aprovar Alterações Selecionadas</button>
          </form>
          {approval_summary}
        </section>
        <section>
          <h3>Refino de Estilo</h3>
          <form method=\"post\" action=\"/chunks/{html.escape(chunk['id'])}/approve-style\">
            <ul>{style_items}</ul>
            <button type=\"submit\">Aprovar Refino de Estilo Selecionado</button>
          </form>
          {style_approval_summary}
        </section>
      </div>
      <div class=\"two-col\" style=\"margin-top: 18px;\">
        <section>
          <h3>Tradução Espanhola Persistida</h3>
          {translation_controls}
          <ul>{translation_items}</ul>
        </section>
        <section>
          <h3>Estado Consolidado dos Parágrafos</h3>
          <ul>{consolidated_items}</ul>
        </section>
      </div>
      <section style=\"margin-top: 18px;\">
        <h3>Comparação pt-BR e Espanhol</h3>
        <ul>{translation_comparison_items}</ul>
      </section>
    """
    return _render_page(chunk["id"], body)


def _render_applied_review_metadata(applied_reviews: list[dict[str, Any]]) -> str:
    if not applied_reviews:
        return "<p class=\"muted\">Nenhuma revisão aplicada registrada.</p>"

    items = "".join(
        (
            "<li>"
            f"<code>{html.escape(review.get('approval_file', ''))}</code> "
            f"<span>{html.escape(review.get('change_type', ''))}</span> "
            f"<span class=\"muted\">{html.escape(review.get('reason', ''))}</span>"
            "</li>"
        )
        for review in applied_reviews
    )
    return f"<ul>{items}</ul>"
