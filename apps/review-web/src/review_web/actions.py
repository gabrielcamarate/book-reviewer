from __future__ import annotations

from pathlib import Path

from editorial_core.characters import generate_characters_registry
from editorial_core.consistency_report import generate_consistency_report
from editorial_core.copyedit import Runner, run_copyedit_pass
from editorial_core.decisions import append_editorial_decision
from editorial_core.deliverable_readiness import generate_deliverable_readiness_report
from editorial_core.export_docx import export_manuscript_docx
from editorial_core.glossary_curation import curate_glossary_entry
from editorial_core.registry_curation import curate_character_entry, curate_world_rule_entry
from editorial_core.review_rollback import rollback_last_review_approval
from editorial_core.review_application import apply_review_approval
from editorial_core.style import run_style_pass
from editorial_core.translation_es import run_translation_es_pass
from editorial_core.world_rules import generate_world_rules_registry


def trigger_copyedit(
    *,
    chunk_id: str,
    chunks_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    runner: Runner,
    model: str = "gpt-5-codex",
) -> dict[str, object]:
    return run_copyedit_pass(
        chunks_dir=chunks_dir,
        reviews_dir=reviews_dir,
        style_guide_path=style_guide_path,
        glossary_path=glossary_path,
        decisions_path=decisions_path,
        runner=runner,
        model=model,
        chunk_id=chunk_id,
    )


def trigger_review_approval(
    *,
    chunk_id: str,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    approved_suggestion_indexes: list[int] | None = None,
) -> dict[str, object]:
    return apply_review_approval(
        review_path=reviews_dir / f"{chunk_id}.copyedit.json",
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        approved_suggestion_indexes=approved_suggestion_indexes,
    )


def trigger_style(
    *,
    chunk_id: str,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    runner: Runner,
    model: str = "gpt-5-codex",
) -> dict[str, object]:
    return run_style_pass(
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_dir=reviews_dir,
        style_guide_path=style_guide_path,
        glossary_path=glossary_path,
        decisions_path=decisions_path,
        runner=runner,
        model=model,
        chunk_id=chunk_id,
    )


def trigger_style_approval(
    *,
    chunk_id: str,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    approved_suggestion_indexes: list[int] | None = None,
) -> dict[str, object]:
    return apply_review_approval(
        review_path=reviews_dir / f"{chunk_id}.style.json",
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        approved_suggestion_indexes=approved_suggestion_indexes,
    )


def trigger_consistency_report(
    *,
    consolidated_dir: Path,
    glossary_path: Path,
    reports_dir: Path,
) -> dict[str, object]:
    return generate_consistency_report(
        consolidated_dir=consolidated_dir,
        glossary_path=glossary_path,
        reports_dir=reports_dir,
    )


def trigger_deliverable_readiness_report(
    *,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    reports_dir: Path,
) -> dict[str, object]:
    return generate_deliverable_readiness_report(
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_ptbr_dir=reviews_ptbr_dir,
        reviews_es_dir=reviews_es_dir,
        reports_dir=reports_dir,
    )


def trigger_translation_es(
    *,
    chunk_id: str,
    chunks_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    reviews_dir: Path,
    style_guide_path: Path,
    glossary_path: Path,
    decisions_path: Path,
    runner: Runner,
    model: str = "gpt-5-codex",
) -> dict[str, object]:
    return run_translation_es_pass(
        chunks_dir=chunks_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        reviews_dir=reviews_dir,
        style_guide_path=style_guide_path,
        glossary_path=glossary_path,
        decisions_path=decisions_path,
        runner=runner,
        model=model,
        chunk_id=chunk_id,
    )


def trigger_append_decision(
    *,
    decisions_path: Path,
    title: str,
    rationale: str,
    scope: str,
) -> dict[str, object]:
    return append_editorial_decision(
        decisions_path=decisions_path,
        title=title,
        rationale=rationale,
        scope=scope,
    )


def trigger_generate_characters(
    *,
    glossary_path: Path,
    characters_path: Path,
) -> dict[str, object]:
    return generate_characters_registry(
        glossary_path=glossary_path,
        output_path=characters_path,
    )


def trigger_generate_world_rules(
    *,
    glossary_path: Path,
    world_rules_path: Path,
) -> dict[str, object]:
    return generate_world_rules_registry(
        glossary_path=glossary_path,
        output_path=world_rules_path,
    )


def trigger_export_docx(
    *,
    template_path: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
    translations_dir: Path,
    deliverables_dir: Path,
    language: str,
) -> dict[str, object]:
    language_slug = "ptbr" if language == "pt-BR" else "es"
    output_path = deliverables_dir / language_slug / f"exilados-da-terra.{language_slug}.docx"
    return export_manuscript_docx(
        template_path=template_path,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
        translations_dir=translations_dir,
        output_path=output_path,
        language=language,
    )


def trigger_rollback_last_approval(
    *,
    reviews_dir: Path,
    chapters_dir: Path,
    consolidated_dir: Path,
) -> dict[str, object]:
    return rollback_last_review_approval(
        reviews_dir=reviews_dir,
        chapters_dir=chapters_dir,
        consolidated_dir=consolidated_dir,
    )


def trigger_curate_glossary_entry(
    *,
    glossary_path: Path,
    entry_title: str,
    preferred_form: str,
    aliases_text: str,
) -> dict[str, object]:
    return curate_glossary_entry(
        glossary_path=glossary_path,
        entry_title=entry_title,
        preferred_form=preferred_form,
        aliases_text=aliases_text,
    )


def trigger_curate_character_entry(
    *,
    characters_path: Path,
    entry_title: str,
    preferred_form: str,
    aliases_text: str,
) -> dict[str, object]:
    return curate_character_entry(
        characters_path=characters_path,
        entry_title=entry_title,
        preferred_form=preferred_form,
        aliases_text=aliases_text,
    )


def trigger_curate_world_rule_entry(
    *,
    world_rules_path: Path,
    entry_title: str,
    preferred_form: str,
    aliases_text: str,
    expanded_form: str | None = None,
) -> dict[str, object]:
    return curate_world_rule_entry(
        world_rules_path=world_rules_path,
        entry_title=entry_title,
        preferred_form=preferred_form,
        aliases_text=aliases_text,
        expanded_form=expanded_form,
    )
