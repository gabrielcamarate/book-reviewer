"""Use cases shared by HTTP and CLI. The repository is the only state store."""
from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any, Callable

from revisor.core.copyedit import run_copyedit_pass
from revisor.core.copyedit_batch import run_copyedit_batch
from revisor.core.export_docx import export_manuscript_docx
from revisor.core.review_application import apply_review_approval
from revisor.core.review_rejection import reject_review_proposal
from revisor.core.review_rollback import rollback_last_review_approval
from revisor.core.translation_batch import run_translation_es_batch
from revisor.core.translation_es import run_translation_es_preview_pass
from revisor.provider import DEFAULT_MODEL, codex_runner
from revisor.state import build_simple_home_state


class StaleReview(ValueError):
    """The displayed chunk no longer matches the repository queue."""


class ReviewService:
    def __init__(self, root: Path, *, runner: Callable[..., dict] = codex_runner,
                 model: str = DEFAULT_MODEL) -> None:
        self.root = root.resolve()
        self.runner = runner
        self.model = model
        self.lock = RLock()

    def _state(self) -> dict[str, Any]:
        return build_simple_home_state(
            chunks_dir=self.root / 'manuscript/chunks',
            reviews_ptbr_dir=self.root / 'reviews/ptbr', reviews_es_dir=self.root / 'reviews/es',
        )

    def state(self) -> dict[str, Any]:
        with self.lock:
            return self._state()

    def perform(self, action: str, data: dict[str, Any]) -> dict[str, Any]:
        limit = data.get('max_chunks')
        if limit is not None and (type(limit) is not int or limit <= 0):
            raise ValueError('max_chunks deve ser um inteiro positivo.')
        with self.lock:
            paths = dict(chunks_dir=self.root / 'manuscript/chunks',
                         chapters_dir=self.root / 'manuscript/chapters',
                         consolidated_dir=self.root / 'manuscript/consolidated')
            context = dict(style_guide_path=self.root / 'editorial/STYLE_GUIDE.md',
                           glossary_path=self.root / 'editorial/GLOSSARY.md',
                           decisions_path=self.root / 'editorial/DECISIONS.md',
                           runner=self.runner, model=self.model)
            ptbr, es = self.root / 'reviews/ptbr', self.root / 'reviews/es'
            if action in {'review', 'accept', 'reject'}:
                chunk_id = data.get('chunk_id')
                current = self._state().get('chunk', {}).get('id')
                if not isinstance(chunk_id, str) or chunk_id != current:
                    raise StaleReview('O trecho mudou. Atualize a tela antes de continuar.')
                if action == 'review':
                    review = run_copyedit_pass(chunks_dir=paths['chunks_dir'], reviews_dir=ptbr,
                                               chunk_id=chunk_id, **context)
                    preview = run_translation_es_preview_pass(chunks_dir=paths["chunks_dir"], reviews_ptbr_dir=ptbr,
                                                              reviews_dir=es, chunk_id=chunk_id, **context)
                    return {'review': review, 'translation_preview': preview}
                if action == 'accept':
                    return apply_review_approval(review_path=ptbr / f'{chunk_id}.copyedit.json', **paths)
                reason = data.get('reason', '')
                if not isinstance(reason, str) or not reason.strip():
                    raise ValueError('Informe um motivo para recusar a revisão.')
                return reject_review_proposal(chunk_id=chunk_id, reviews_ptbr_dir=ptbr,
                                              reviews_es_dir=es, reason=reason.strip())
            if action == 'review-batch':
                return run_copyedit_batch(chunks_dir=paths['chunks_dir'], reviews_dir=ptbr,
                                          jobs_dir=self.root / 'reports/jobs', **context,
                                          max_chunks=data.get('max_chunks'))
            if action == 'translate':
                return run_translation_es_batch(**paths, reviews_dir=es, **context,
                                                jobs_dir=self.root / 'reports/jobs',
                                                max_chunks=data.get('max_chunks'))
            if action == 'export':
                language = data.get('language', 'pt-BR')
                if language not in {'pt-BR', 'es'}:
                    raise ValueError('Idioma de exportação inválido.')
                slug = 'ptbr' if language == 'pt-BR' else 'es'
                return export_manuscript_docx(
                    template_path=self.root / 'livro.docx', chapters_dir=paths['chapters_dir'],
                    consolidated_dir=paths['consolidated_dir'], translations_dir=es,
                    output_path=self.root / f'deliverables/{slug}/livro-{slug}.docx', language=language,
                )
            if action == 'rollback':
                result = rollback_last_review_approval(reviews_dir=ptbr, chapters_dir=paths["chapters_dir"],
                                                       consolidated_dir=paths['consolidated_dir'])
                for suffix in ['translation-es.json', 'translation-es.preview.json']:
                    (es / f"{result['chunk_id']}.{suffix}").unlink(missing_ok=True)
                return result
            raise ValueError('Ação desconhecida.')
