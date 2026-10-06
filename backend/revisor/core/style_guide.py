from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

LONG_PARAGRAPH_THRESHOLD = 200
VERY_LONG_PARAGRAPH_THRESHOLD = 400
ALL_CAPS_RE = re.compile(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}\b")
NON_PROSE_FRONTMATTER_TITLES = {
    "opening",
    "sumário",
    "sumario",
    "créditos",
    "creditos",
}


def _normalize_title(text: str) -> str:
    return " ".join(text.split()).strip().casefold()


def _should_include_section(section_payload: dict[str, Any]) -> bool:
    if section_payload["type"] != "frontmatter":
        return True
    return _normalize_title(section_payload["title"]) not in NON_PROSE_FRONTMATTER_TITLES


def _load_approved_reference(chapters_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    index_path = chapters_dir / "index.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))

    approved_paragraphs: list[dict[str, Any]] = []
    approved_sections: dict[str, dict[str, Any]] = {}

    for section_entry in index_payload["sections"]:
        section_path = chapters_dir / section_entry["file"]
        section_payload = json.loads(section_path.read_text(encoding="utf-8"))
        if not _should_include_section(section_payload):
            continue

        approved_in_section = [
            paragraph
            for paragraph in section_payload.get("paragraphs", [])
            if paragraph.get("review_status") == "approved_reference"
        ]

        if not approved_in_section:
            continue

        approved_sections[section_payload["id"]] = {
            "id": section_payload["id"],
            "type": section_payload["type"],
            "title": section_payload["title"],
        }

        for paragraph in approved_in_section:
            approved_paragraphs.append(
                {
                    "section_id": section_payload["id"],
                    "section_type": section_payload["type"],
                    "section_title": section_payload["title"],
                    "paragraph_id": paragraph["id"],
                    "source_index": paragraph["source_index"],
                    "text": paragraph["text"],
                }
            )

    if not approved_paragraphs:
        raise ValueError("no approved reference paragraphs found in chapter artifacts")

    return approved_paragraphs, {
        "section_count": len(approved_sections),
        "sections": list(approved_sections.values()),
    }


def _sample_ids(items: list[dict[str, Any]], limit: int = 3) -> str:
    return ", ".join(f"`{item['paragraph_id']}`" for item in items[:limit])


def _analyze_approved_reference(approved_paragraphs: list[dict[str, Any]]) -> dict[str, Any]:
    texts = [paragraph["text"] for paragraph in approved_paragraphs]
    joined_text = "\n".join(texts)
    lengths = [len(text) for text in texts]

    dialogue_examples = [item for item in approved_paragraphs if "▬" in item["text"]]
    ellipsis_examples = [item for item in approved_paragraphs if "..." in item["text"]]
    dash_examples = [
        item
        for item in approved_paragraphs
        if "—" in item["text"] or "―" in item["text"]
    ]
    quoted_examples = [
        item
        for item in approved_paragraphs
        if any(marker in item["text"] for marker in ('"', "“", "”"))
    ]
    long_examples = [item for item in approved_paragraphs if len(item["text"]) >= LONG_PARAGRAPH_THRESHOLD]
    acronym_counts = Counter(ALL_CAPS_RE.findall(joined_text))
    section_type_counts = Counter(item["section_type"] for item in approved_paragraphs)

    return {
        "approved_paragraph_count": len(approved_paragraphs),
        "average_length": round(statistics.mean(lengths), 1),
        "median_length": round(statistics.median(lengths), 1),
        "max_length": max(lengths),
        "paragraphs_over_200": len(long_examples),
        "paragraphs_over_400": sum(
            len(item["text"]) >= VERY_LONG_PARAGRAPH_THRESHOLD for item in approved_paragraphs
        ),
        "dialogue_examples": dialogue_examples,
        "ellipsis_examples": ellipsis_examples,
        "dash_examples": dash_examples,
        "quoted_examples": quoted_examples,
        "long_examples": long_examples,
        "acronym_counts": acronym_counts,
        "section_type_counts": section_type_counts,
    }


def _build_confirmed_rules(analysis: dict[str, Any]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []

    if analysis["dialogue_examples"]:
        rules.append(
            {
                "title": "Preserve dialogue turns marked with `▬`.",
                "evidence": (
                    f"Observed in `{len(analysis['dialogue_examples'])}` approved paragraphs, "
                    f"including {_sample_ids(analysis['dialogue_examples'])}."
                ),
                "operation": (
                    "Do not normalize this marker into quotation marks or simple leading hyphens during copyedit."
                ),
            }
        )

    if analysis["ellipsis_examples"]:
        rules.append(
            {
                "title": "Preserve ellipsis chains `...`.",
                "evidence": (
                    f"Observed in `{len(analysis['ellipsis_examples'])}` approved paragraphs, "
                    f"including {_sample_ids(analysis['ellipsis_examples'])}."
                ),
                "operation": (
                    "Keep ellipsis when they signal cadence, conceptual accumulation, hesitation, or formulaic repetition."
                ),
            }
        )

    if analysis["dash_examples"]:
        rules.append(
            {
                "title": "Preserve em dash and horizontal bar insertions.",
                "evidence": (
                    f"Observed in `{len(analysis['dash_examples'])}` approved paragraphs, "
                    f"including {_sample_ids(analysis['dash_examples'])}."
                ),
                "operation": (
                    "Treat `—` and `―` as meaningful structural punctuation used for apposition, attribution beats, and conceptual emphasis."
                ),
            }
        )

    if analysis["acronym_counts"]:
        top_acronyms = ", ".join(
            f"`{token}` ({count})" for token, count in analysis["acronym_counts"].most_common(5)
        )
        rules.append(
            {
                "title": "Preserve uppercase acronyms and institutional short forms.",
                "evidence": f"Recurring approved tokens include {top_acronyms}.",
                "operation": (
                    "Do not silently recase acronym-like terms; confirm glossary intent before normalizing capitalization."
                ),
            }
        )

    if analysis["paragraphs_over_200"]:
        rules.append(
            {
                "title": "Preserve long periodic prose when grammar remains sound.",
                "evidence": (
                    f"Median approved paragraph length is `{analysis['median_length']}` characters, "
                    f"with `{analysis['paragraphs_over_200']}` paragraphs at or above `{LONG_PARAGRAPH_THRESHOLD}` characters."
                ),
                "operation": (
                    "Prefer conservative punctuation and agreement fixes over sentence splitting or structural compression."
                ),
            }
        )

    return rules


def _build_observed_patterns(analysis: dict[str, Any], section_summary: dict[str, Any]) -> list[str]:
    section_type_counts = ", ".join(
        f"`{section_type}`: {count}"
        for section_type, count in sorted(analysis["section_type_counts"].items())
    )
    patterns = [
        (
            f"Approved reference currently spans `{section_summary['section_count']}` sections and "
            f"`{analysis['approved_paragraph_count']}` paragraphs across {section_type_counts}."
        ),
        (
            "The corpus alternates dense exposition with marked dialogue and attribution beats, so copyedit must preserve rhythm rather than flatten paragraph texture."
        ),
    ]

    if analysis["quoted_examples"]:
        patterns.append(
            "Direct quotation appears alongside dash-led dialogue, which indicates mixed speech presentation rather than a single dialogue convention."
        )

    if analysis["acronym_counts"]:
        patterns.append(
            "Institutional and cosmological terms are frequently encoded as uppercase abbreviations, often close to expanded forms."
        )

    return patterns


def _build_editorial_hypotheses(analysis: dict[str, Any], section_summary: dict[str, Any]) -> list[str]:
    hypotheses = [
        (
            "Single-word or split-word frontmatter lines may be layout artifacts from the `.docx` source and should be validated before normalization."
        ),
        (
            "Some apparent punctuation or agreement irregularities may be deliberate rhetorical cadence and should only be changed when the error is unambiguous."
        ),
        (
            "Capitalization, acronym spacing, and repeated philosophical formulas may encode world-building rather than inconsistency, so future normalization should wait for `GLOSSARY.md`."
        ),
    ]

    if any(section["type"] == "frontmatter" for section in section_summary["sections"]) and any(
        section["type"] == "chapter" for section in section_summary["sections"]
    ):
        hypotheses.append(
            "Frontmatter tone may be slightly more essayistic than chapter narrative, so chapter-level evidence should win if future style signals conflict."
        )
    else:
        hypotheses.append(
            "Current approved reference is still partial, so later approved chapters may refine the intervention threshold."
        )

    if analysis["paragraphs_over_400"]:
        hypotheses.append(
            "Very long approved paragraphs suggest the author tolerates sustained syntactic accumulation; sentence splitting should remain exceptional."
        )

    return hypotheses


def _render_style_guide(
    section_summary: dict[str, Any],
    analysis: dict[str, Any],
    confirmed_rules: list[dict[str, str]],
    observed_patterns: list[str],
    editorial_hypotheses: list[str],
) -> str:
    scope_sections = ", ".join(
        f"`{section['id']}` ({section['title']})" for section in section_summary["sections"]
    )

    lines = [
        "# Style Guide",
        "",
        "Initial deterministic style guide derived from the approved reference corpus persisted in `manuscript/chapters`.",
        "",
        "## Corpus Scope",
        f"- Approved reference sections: `{section_summary['section_count']}`",
        f"- Approved reference paragraphs: `{analysis['approved_paragraph_count']}`",
        f"- Average paragraph length: `{analysis['average_length']}` characters",
        f"- Median paragraph length: `{analysis['median_length']}` characters",
        f"- Paragraphs with `{LONG_PARAGRAPH_THRESHOLD}+` characters: `{analysis['paragraphs_over_200']}`",
        f"- Paragraphs with `{VERY_LONG_PARAGRAPH_THRESHOLD}+` characters: `{analysis['paragraphs_over_400']}`",
        f"- Corpus sections: {scope_sections}",
        "",
        "## Confirmed Rules",
    ]

    for index, rule in enumerate(confirmed_rules, start=1):
        lines.extend(
            [
                f"### {index}. {rule['title']}",
                f"- Evidence: {rule['evidence']}",
                f"- Operational rule: {rule['operation']}",
                "",
            ]
        )

    lines.append("## Observed Patterns")
    for pattern in observed_patterns:
        lines.append(f"- {pattern}")
    lines.append("")

    lines.append("## Editorial Hypotheses")
    for hypothesis in editorial_hypotheses:
        lines.append(f"- {hypothesis}")
    lines.append("")

    return "\n".join(lines)


def generate_style_guide(chapters_dir: Path, output_path: Path) -> dict[str, Any]:
    approved_paragraphs, section_summary = _load_approved_reference(chapters_dir)
    analysis = _analyze_approved_reference(approved_paragraphs)
    confirmed_rules = _build_confirmed_rules(analysis)
    observed_patterns = _build_observed_patterns(analysis, section_summary)
    editorial_hypotheses = _build_editorial_hypotheses(analysis, section_summary)
    guide_text = _render_style_guide(
        section_summary=section_summary,
        analysis=analysis,
        confirmed_rules=confirmed_rules,
        observed_patterns=observed_patterns,
        editorial_hypotheses=editorial_hypotheses,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(guide_text, encoding="utf-8")

    return {
        "output_path": str(output_path),
        "approved_section_count": section_summary["section_count"],
        "approved_paragraph_count": analysis["approved_paragraph_count"],
        "confirmed_rule_count": len(confirmed_rules),
        "observed_pattern_count": len(observed_patterns),
        "hypothesis_count": len(editorial_hypotheses),
    }
