from __future__ import annotations
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from revisor.service import ReviewService, StaleReview


def fixture(root: Path) -> None:
    def save(name, data):
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False))
    section = dict(id='chapter-1', type='chapter', order=1, title='Capítulo 1: Teste',
                   heading_source_index=0, source_start_index=1, source_end_index=1,
                   paragraph_count=1, review_status='pending_review', file='chapter-1.json')
    paragraph = dict(id='p1', source_index=1, text='As estrela brilha.', review_status='pending_review')
    save('manuscript/chapters/index.json', dict(section_count=1, chapter_count=1, sections=[section]))
    save('manuscript/chapters/chapter-1.json', {**section, 'paragraphs': [paragraph]})
    chunk = dict(id='chunk-1', section_id='chapter-1', section_title=section['title'], chunk_order=1,
                 review_status='pending_review', paragraph_ids=['p1'], source_start_index=1,
                 source_end_index=1, paragraph_count=1, base_text=paragraph['text'],
                 previous_context=[], next_context=[], file='chunk-1.json')
    save('manuscript/chunks/index.json', dict(chunk_count=1, chunks=[chunk]))
    save('manuscript/chunks/chunk-1.json', chunk)
    (root / 'editorial').mkdir()
    for name in ['STYLE_GUIDE','GLOSSARY','DECISIONS']:
        (root / f'editorial/{name}.md').write_text('# Referência de teste\n')
    with zipfile.ZipFile(root / 'livro.docx', 'w') as z:
        z.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p/><w:sectPr/></w:body></w:document>')


def fake_runner(*, prompt, schema, model):
    if 'suggestions' in schema.get('properties', {}):
        return {'suggestions': [dict(original='As estrela brilha.', suggested='As estrelas brilham.',
                                    change_type='agreement', reason='Concordância nominal e verbal.', confidence=0.99)]}
    return {'translations': [dict(paragraph_id='p1', translated_text='Las estrellas brillan.',
                                 rationale='Tradução alinhada.', confidence=0.99)]}


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)
        self.service = ReviewService(self.root, runner=fake_runner, model='fixture')

    def test_review_accept_translate_export_preserves_source(self):
        source = (self.root / 'manuscript/chapters/chapter-1.json').read_bytes()
        self.service.perform('review', {'chunk_id': 'chunk-1'})
        state = self.service.state()
        self.assertEqual(state['revised_text'], 'As estrelas brilham.')
        self.assertEqual(state['spanish_text'], 'Las estrellas brillan.')
        self.assertTrue(state['review_available'])
        self.assertEqual(state['summary']['total_chunks'], 1)
        self.service.perform('accept', {'chunk_id': 'chunk-1'})
        self.assertFalse(self.service.state()['has_actionable_chunk'])
        self.service.perform('translate', {})
        for language in ['pt-BR', 'es']:
            result = self.service.perform('export', {'language': language})
            self.assertTrue(Path(result['output_path']).exists())
        self.assertEqual(source, (self.root / 'manuscript/chapters/chapter-1.json').read_bytes())

    def test_rejection_persists_feedback_and_removes_proposal(self):
        self.service.perform('review', {'chunk_id': 'chunk-1'})
        self.service.perform('reject', {'chunk_id': 'chunk-1', 'reason': 'Manter esta construção.'})
        self.assertEqual(self.service.state()['rejection_reason'], 'Manter esta construção.')
        self.assertFalse(self.service.state()['spanish_available'])
        self.assertFalse((self.root / 'manuscript/consolidated/chapter-1.json').exists())

    def test_stale_screen_cannot_approve_different_chunk(self):
        with self.assertRaises(StaleReview):
            self.service.perform('accept', {'chunk_id': 'outro'})

    def test_clean_review_can_be_approved_without_changes(self):
        self.service.runner = lambda **kwargs: {'suggestions': []} if 'suggestions' in kwargs['schema']['properties'] else fake_runner(**kwargs)
        self.service.perform('review', {'chunk_id': 'chunk-1'})
        self.assertTrue(self.service.state()['review_available'])
        self.service.perform('accept', {'chunk_id': 'chunk-1'})
        self.assertFalse(self.service.state()['has_actionable_chunk'])
        self.assertEqual(self.service.perform('translate', {})['processed_count'], 1)
        self.service.perform('rollback', {})
        self.assertTrue(self.service.state()['has_actionable_chunk'])
        self.assertFalse((self.root / 'reviews/es/chunk-1.translation-es.json').exists())

    def test_spanish_export_blocks_missing_translation(self):
        with self.assertRaises(ValueError):
            self.service.perform('export', {'language': 'es'})

    def test_whole_chunk_approval_includes_paragraphs_without_corrections(self):
        chapter_path = self.root / 'manuscript/chapters/chapter-1.json'
        chapter = json.loads(chapter_path.read_text())
        chapter['paragraphs'].append(dict(id='p2', source_index=2, text='O céu está limpo.', review_status='pending_review'))
        chapter_path.write_text(json.dumps(chapter))
        chunk_path = self.root / 'manuscript/chunks/chunk-1.json'
        chunk = json.loads(chunk_path.read_text())
        chunk.update(paragraph_ids=['p1', 'p2'], base_text='As estrela brilha.\n\nO céu está limpo.')
        chunk_path.write_text(json.dumps(chunk))
        def runner(**kwargs):
            result = fake_runner(**kwargs)
            if 'translations' in result:
                result['translations'].append(dict(paragraph_id='p2', translated_text='El cielo está despejado.', rationale='Tradução.', confidence=0.99))
            return result
        self.service.runner = runner
        self.service.perform('review', {'chunk_id': 'chunk-1'})
        expected = self.service.state()['revised_text']
        self.service.perform('accept', {'chunk_id': 'chunk-1'})
        approved = json.loads((self.root / 'manuscript/consolidated/chapter-1.json').read_text())
        self.assertEqual('\n\n'.join(p['text'] for p in approved['paragraphs']), expected)
        self.assertTrue(all(p['review_status'] == 'approved' for p in approved['paragraphs']))
        self.assertEqual(self.service.perform('translate', {})['processed_count'], 1)
        self.service.perform('rollback', {})
        restored = json.loads((self.root / 'manuscript/consolidated/chapter-1.json').read_text())
        self.assertTrue(all(p['review_status'] == 'pending_review' for p in restored['paragraphs']))

    def test_conflicting_suggestions_have_same_preview_and_approved_text(self):
        def runner(**kwargs):
            result = fake_runner(**kwargs)
            if 'suggestions' in result:
                result['suggestions'].append(dict(original='As estrela brilha.', suggested='As estrelas brilham!', change_type='punctuation', reason='Pontuação.', confidence=0.99))
            else:
                self.assertIn('As estrelas brilham.', kwargs['prompt'])
                self.assertNotIn('As estrelas brilham!', kwargs['prompt'])
            return result
        self.service.runner = runner
        self.service.perform('review', {'chunk_id': 'chunk-1'})
        self.assertEqual(self.service.state()['revised_text'], 'As estrelas brilham.')
        self.service.perform('accept', {'chunk_id': 'chunk-1'})
        approved = json.loads((self.root / 'manuscript/consolidated/chapter-1.json').read_text())
        self.assertEqual(approved['paragraphs'][0]['text'], 'As estrelas brilham.')
