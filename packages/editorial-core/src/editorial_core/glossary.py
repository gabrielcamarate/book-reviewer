from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ALL_CAPS_RE = re.compile(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}\b")
CAPITALIZED_WORD_RE = r"(?:[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç][\wÀ-ÿ]*|eXilados)"
CONNECTOR_RE = r"(?:da|de|do|dos|das)"
ACRONYM_EXPANSION_RE = re.compile(
    rf"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{{2,}})\s*[—―-]\s*({CAPITALIZED_WORD_RE}(?:\s+(?:{CONNECTOR_RE}\s+)?{CAPITALIZED_WORD_RE}){{1,11}})"
)
TITLE_PHRASE_RE = re.compile(
    rf"\b({CAPITALIZED_WORD_RE}(?:\s+(?:{CONNECTOR_RE}\s+)?{CAPITALIZED_WORD_RE}){{1,4}})\b"
)

NON_PROSE_FRONTMATTER_TITLES = {
    "opening",
    "sumário",
    "sumario",
    "créditos",
    "creditos",
}
PROPER_NAME_BLACKLIST = {
    "Capítulo",
    "Prefácio",
    "Introdução",
    "Prólogo",
    "Epílogo",
    "O Escritor",
    "Soberana Energia Universal",
    "Supremo Poder Anônimo",
    "Sistema Terra",
    "Independência Mundial dos Servos de Deus",
}
PROPER_NAME_LEAD_BLACKLIST = {
    "Afirma",
    "Atesta",
    "Brada",
    "Descaracteriza",
    "Diretor",
    "Executiva",
    "Esta",
    "Fala",
    "Funcionário",
    "Codificação",
    "Conselho",
    "Conselhos",
    "Controladoria",
    "Escola",
    "Estados",
    "Presídio",
    "Sistema",
    "Soberana",
    "Supremo",
}
CONCEPT_HEADWORDS = {
    "Sistema",
    "Energia",
    "Poder",
    "Lei",
    "Consciência",
    "Terra",
    "Universo",
    "Universais",
    "Universal",
    "Guerreiros",
    "Casa",
    "Fonte",
    "Amor",
}
FORMULA_SEGMENTS = [
    "a minha raça humana é universal",
    "o meu sexo é o amor",
    "a minha religião é a consciência",
    "todos os gêneros são iguais",
]


def _normalize_title(text: str) -> str:
    return " ".join(text.split()).strip().casefold()


def _clean_phrase(text: str) -> str:
    return " ".join(text.strip().strip(".,;:!?\"“”").split())


def _should_include_section(section_payload: dict[str, Any]) -> bool:
    if section_payload["type"] != "frontmatter":
        return True
    return _normalize_title(section_payload["title"]) not in NON_PROSE_FRONTMATTER_TITLES


def _load_approved_reference(chapters_dir: Path) -> list[dict[str, Any]]:
    index_payload = json.loads((chapters_dir / "index.json").read_text(encoding="utf-8"))
    approved_paragraphs: list[dict[str, Any]] = []

    for section_entry in index_payload["sections"]:
        section_payload = json.loads(
            (chapters_dir / section_entry["file"]).read_text(encoding="utf-8")
        )
        if not _should_include_section(section_payload):
            continue

        for paragraph in section_payload.get("paragraphs", []):
            if paragraph.get("review_status") != "approved_reference":
                continue
            approved_paragraphs.append(
                {
                    "section_id": section_payload["id"],
                    "section_title": section_payload["title"],
                    "paragraph_id": paragraph["id"],
                    "text": paragraph["text"],
                }
            )

    if not approved_paragraphs:
        raise ValueError("no approved reference paragraphs available to generate GLOSSARY.md")

    return approved_paragraphs


def _append_evidence(entry: dict[str, Any], paragraph_id: str) -> None:
    if paragraph_id not in entry["evidence_ids"]:
        entry["evidence_ids"].append(paragraph_id)


def _extract_acronym_entries(approved_paragraphs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}

    for paragraph in approved_paragraphs:
        for acronym, raw_expansion in ACRONYM_EXPANSION_RE.findall(paragraph["text"]):
            expansion = _clean_phrase(raw_expansion.split(",")[0])
            if len(expansion.split()) < 3:
                continue

            entry = entries.setdefault(
                acronym,
                {
                    "term": acronym,
                    "preferred_form": acronym,
                    "expanded_form": expansion,
                    "aliases": set(),
                    "evidence_ids": [],
                },
            )
            entry["aliases"].add(expansion)
            _append_evidence(entry, paragraph["paragraph_id"])

    return entries


def _extract_proper_name_entries(approved_paragraphs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: Counter[str] = Counter()
    evidence: dict[str, list[str]] = {}

    for paragraph in approved_paragraphs:
        for raw_phrase in TITLE_PHRASE_RE.findall(paragraph["text"]):
            phrase = _clean_phrase(raw_phrase)
            tokens = phrase.split()
            if phrase in PROPER_NAME_BLACKLIST:
                continue
            if tokens[0] in PROPER_NAME_LEAD_BLACKLIST:
                continue
            if len([token for token in tokens if token[0].isupper()]) < 2:
                continue
            if tokens[0] in CONCEPT_HEADWORDS:
                continue
            if phrase.isupper():
                continue

            counts[phrase] += 1
            evidence.setdefault(phrase, [])
            if paragraph["paragraph_id"] not in evidence[phrase]:
                evidence[phrase].append(paragraph["paragraph_id"])

    return {
        term: {
            "term": term,
            "preferred_form": term,
            "aliases": set(),
            "evidence_ids": evidence[term][:5],
        }
        for term, count in counts.items()
        if count >= 1
    }


def _extract_concept_entries(
    approved_paragraphs: list[dict[str, Any]],
    acronym_entries: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    counts: Counter[str] = Counter()
    evidence: dict[str, list[str]] = {}

    for paragraph in approved_paragraphs:
        for raw_phrase in TITLE_PHRASE_RE.findall(paragraph["text"]):
            phrase = _clean_phrase(raw_phrase)
            tokens = phrase.split()
            if phrase in PROPER_NAME_BLACKLIST:
                counts[phrase] += 1
            elif tokens[0] in CONCEPT_HEADWORDS:
                counts[phrase] += 1
            else:
                continue

            evidence.setdefault(phrase, [])
            if paragraph["paragraph_id"] not in evidence[phrase]:
                evidence[phrase].append(paragraph["paragraph_id"])

    entries: dict[str, dict[str, Any]] = {}
    for term, count in counts.items():
        if count < 2 and term not in PROPER_NAME_BLACKLIST:
            continue
        entries[term] = {
            "term": term,
            "preferred_form": term,
            "aliases": set(),
            "evidence_ids": evidence[term][:5],
        }

    for acronym, entry in acronym_entries.items():
        expanded_form = entry["expanded_form"]
        if expanded_form in entries:
            entries[expanded_form]["aliases"].add(acronym)

    return entries


def _extract_formula_entry(approved_paragraphs: list[dict[str, Any]]) -> dict[str, Any] | None:
    found_segments: list[str] = []
    evidence_ids: list[str] = []

    for paragraph in approved_paragraphs:
        lowered = paragraph["text"].casefold()
        matched = [segment for segment in FORMULA_SEGMENTS if segment in lowered]
        if matched:
            for segment in matched:
                if segment not in found_segments:
                    found_segments.append(segment)
            if paragraph["paragraph_id"] not in evidence_ids:
                evidence_ids.append(paragraph["paragraph_id"])

    if not found_segments:
        return None

    preferred_form = "... ".join(segment.rstrip(".") for segment in FORMULA_SEGMENTS if segment in found_segments)
    return {
        "term": "Philosophical Formula",
        "preferred_form": preferred_form + ".",
        "aliases": set(found_segments),
        "evidence_ids": evidence_ids[:5],
    }


def _format_aliases(aliases: set[str]) -> str:
    if not aliases:
        return "none confirmed"
    return ", ".join(f"`{alias}`" for alias in sorted(aliases))


def _render_entry(title: str, lines: list[str]) -> list[str]:
    return [f"### {title}", *lines, ""]


def _render_glossary(
    approved_paragraphs: list[dict[str, Any]],
    acronym_entries: dict[str, dict[str, Any]],
    proper_name_entries: dict[str, dict[str, Any]],
    concept_entries: dict[str, dict[str, Any]],
    formula_entry: dict[str, Any] | None,
) -> str:
    lines = [
        "# Glossary",
        "",
        "Initial deterministic glossary derived from the `approved_reference` corpus.",
        "",
        "## Scope",
        f"- Approved reference paragraphs: `{len(approved_paragraphs)}`",
        f"- Approved reference sections: `{len({paragraph['section_id'] for paragraph in approved_paragraphs})}`",
        "",
        "## Organizations and Acronyms",
        "",
    ]

    if acronym_entries:
        for term in sorted(acronym_entries):
            entry = acronym_entries[term]
            lines.extend(
                _render_entry(
                    term,
                    [
                        f"- Preferred form: `{entry['preferred_form']}`",
                        f"- Expanded form: `{entry['expanded_form']}`",
                        f"- Observed aliases or variants: {_format_aliases(entry['aliases'])}",
                        f"- Evidence: {', '.join(f'`{item}`' for item in entry['evidence_ids'])}",
                    ],
                )
            )
    else:
        lines.extend(["No acronym entries detected.", ""])

    lines.extend(["## Proper Names", ""])

    if proper_name_entries:
        for term in sorted(proper_name_entries):
            entry = proper_name_entries[term]
            lines.extend(
                _render_entry(
                    term,
                    [
                        f"- Preferred form: `{entry['preferred_form']}`",
                        f"- Observed aliases or variants: {_format_aliases(entry['aliases'])}",
                        f"- Evidence: {', '.join(f'`{item}`' for item in entry['evidence_ids'])}",
                    ],
                )
            )
    else:
        lines.extend(["No proper-name entries detected.", ""])

    lines.extend(["## Concepts and Formulas", ""])

    for term in sorted(concept_entries):
        entry = concept_entries[term]
        lines.extend(
            _render_entry(
                term,
                [
                    f"- Preferred form: `{entry['preferred_form']}`",
                    f"- Observed aliases or variants: {_format_aliases(entry['aliases'])}",
                    f"- Evidence: {', '.join(f'`{item}`' for item in entry['evidence_ids'])}",
                ],
            )
        )

    if formula_entry is not None:
        lines.extend(
            _render_entry(
                formula_entry["term"],
                [
                    f"- Preferred form: `{formula_entry['preferred_form']}`",
                    f"- Observed aliases or variants: {_format_aliases(formula_entry['aliases'])}",
                    f"- Evidence: {', '.join(f'`{item}`' for item in formula_entry['evidence_ids'])}",
                ],
            )
        )

    return "\n".join(lines).rstrip() + "\n"


def generate_glossary(chapters_dir: Path, output_path: Path) -> dict[str, Any]:
    approved_paragraphs = _load_approved_reference(chapters_dir)
    acronym_entries = _extract_acronym_entries(approved_paragraphs)
    proper_name_entries = _extract_proper_name_entries(approved_paragraphs)
    concept_entries = _extract_concept_entries(approved_paragraphs, acronym_entries)
    formula_entry = _extract_formula_entry(approved_paragraphs)

    glossary_text = _render_glossary(
        approved_paragraphs,
        acronym_entries,
        proper_name_entries,
        concept_entries,
        formula_entry,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(glossary_text, encoding="utf-8")

    entry_count = (
        len(acronym_entries)
        + len(proper_name_entries)
        + len(concept_entries)
        + (1 if formula_entry is not None else 0)
    )

    return {
        "approved_paragraph_count": len(approved_paragraphs),
        "approved_section_count": len({paragraph["section_id"] for paragraph in approved_paragraphs}),
        "entry_count": entry_count,
        "output_path": str(output_path),
    }
