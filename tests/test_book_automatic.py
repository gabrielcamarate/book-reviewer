"""Software regressions with a controlled runner; no literary quality claims."""
import json
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

from revisor.docx.editable import inspect_document
from revisor.workspace import BookWorkspace, read_json
from test_book_api import runner as manual_runner
from test_book_workflows import fixture


def automatic_runner(**kwargs):
    data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
    if data['task'] in {'check_pt', 'check_es'}:
        return {'paragraphs':[{'paragraph_id':p['id'],
                'text':p['draft'].replace('vosotros','ustedes') if data['task']=='check_es' else p['draft'],
                'reason':'Variante latino-americana.','category':'variante'} for p in data['paragraphs']], 'issues':[]}
    result = manual_runner(**kwargs)
    if data['task'] == 'translate':
        for p in result['translations']:
            p['text'] = p['text'].replace('Texto final.', 'vosotros llegaron.')
    return result


class AutomaticBookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root/'pt.docx'; fixture(self.source)
        self.destination = self.root/'es.docx'; fixture(self.destination, True)
        self.calls = []
        def record(**kwargs):
            self.calls.append(json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])['task'])
            return automatic_runner(**kwargs)
        self.ws = BookWorkspace(self.root, runner=record)
        self.pid = self.ws.import_book(self.source)['id']

    def tearDown(self):
        self.ws.close(); self.temp.cleanup()

    def run_job(self):
        self.ws.start(self.pid, 'automatic'); self.ws.thread.join(5)
        self.assertFalse(self.ws.thread.is_alive())
        return self.ws.detail(self.pid)

    def test_complete_automatic_workflow_checks_both_languages_and_exports_copies(self):
        original = self.source.read_bytes()
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'completed')
        self.assertEqual(detail['progress']['review_percent'], 100)
        self.assertEqual(detail['progress']['checked_percent'], 100)
        self.assertTrue(detail['automatic_result'])
        state = read_json(self.ws._folder(self.pid)/'state.json')
        self.assertEqual(sum(a['action']=='auto-approve' for a in state['audit']), len(state['chunks']))
        self.assertNotIn('approve-all', [a['action'] for a in state['audit']])
        self.assertEqual(set(self.calls), {'review', 'check_pt', 'translate', 'check_es'})
        self.assertEqual(detail['consistency_warnings'], [])
        for language, artifact in detail['automatic_result']['files'].items():
            self.assertTrue(Path(artifact['path']).is_file())
            self.assertEqual(self.ws.download_path(self.pid, language), Path(artifact['path']))
        es = inspect_document(Path(detail['automatic_result']['files']['es']['path']))
        self.assertTrue(any('ustedes llegaron' in p['text'] for p in es['paragraphs']))
        self.assertEqual(self.source.read_bytes(), original)
        before = len(self.calls)
        self.assertTrue(self.run_job()['automatic_result'])
        self.assertEqual(len(self.calls), before)

    def test_manual_mode_does_not_autoapprove_or_run_quality_passes(self):
        self.ws.run_sync(self.pid, 'review')
        detail = self.ws.detail(self.pid)
        self.assertGreater(detail['progress']['ready_chunks'], 0)
        self.assertEqual(detail['progress']['approved_paragraphs'], 0)
        self.assertIsNone(detail['automatic_result'])
        self.assertEqual(set(self.calls), {'review'})

    @staticmethod
    def overlapping_response(data):
        paragraph = next(p for p in data['paragraphs'] if 'estavam' in p.get('draft', p['text']))
        edits = [{'paragraph_id': paragraph['id'], 'original': original, 'replacement': 'estava',
                  'occurrence': 0, 'reason': 'Concordância.', 'category': 'gramática'}
                 for original in ('estavam', 'Ela estavam')]
        return {'edits': edits, **({'issues': []} if data['task'] != 'review' else {})}

    @staticmethod
    def duplicate_response(data):
        result={'paragraphs':[{'paragraph_id':p['id'],'text':p.get('draft',p['text']),
                             'reason':'Fixture.','category':'teste'} for p in data['paragraphs']]}
        result['paragraphs'].append(dict(result['paragraphs'][0]))
        if data['task']!='review': result['issues']=[]
        return result

    def test_automatic_duplicate_paragraph_retries_only_invalid_chunk_with_feedback_and_audit(self):
        seen = []
        def recover(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); seen.append(data)
            if data['task'] == 'review' and any('estavam' in p['text'] for p in data['paragraphs']):
                if not data.get('validation_feedback'): return self.duplicate_response(data)
            return automatic_runner(**kwargs)
        self.ws.runner = recover
        original = self.source.read_bytes()
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'completed', detail['job']['message'])
        reviews = [d for d in seen if d['task'] == 'review']
        retried = [d for d in reviews if d.get('validation_feedback')]
        self.assertEqual(len(retried), 1)
        self.assertIn('uma vez cada', retried[0]['validation_feedback'])
        self.assertEqual(len(reviews), 5)  # Four chunks, only one additional request.
        state = read_json(self.ws._folder(self.pid)/'state.json')
        retries = [a for a in state['audit'] if a['action'] == 'response-retry']
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0]['attempt'], 2)
        self.assertEqual(self.source.read_bytes(), original)

    def test_repeated_invalid_response_becomes_attention_and_resume_keeps_saved_work(self):
        seen = []
        def invalid(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); seen.append(data)
            if data['task'] == 'review' and any('estavam' in p['text'] for p in data['paragraphs']):
                return self.duplicate_response(data)
            return automatic_runner(**kwargs)
        self.ws.runner = invalid
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'needs_attention')
        self.assertEqual(sum(any('estavam' in p['text'] for p in d['paragraphs']) for d in seen), 2)
        self.assertEqual(detail['job']['problems'][0]['chunk_id'], 'chunk-00003')
        self.assertEqual(detail['job']['problems'][0]['chunk_id'],'chunk-00003')
        self.assertIsNone(detail['automatic_result'])
        state = read_json(self.ws._folder(self.pid)/'state.json')
        self.assertEqual(state['chunks'][2]['status'], 'pending')
        self.assertNotIn('revised', state['chunks'][2])
        saved = {c['id']: c['proposal_id'] for c in state['chunks'] if c['status'] == 'ready'}
        self.ws.runner = automatic_runner
        self.assertTrue(self.run_job()['automatic_result'])
        resumed = read_json(self.ws._folder(self.pid)/'state.json')
        self.assertTrue(all(c['proposal_id'] == saved[c['id']] for c in resumed['chunks'] if c['id'] in saved))

    def test_both_quality_checks_recover_duplicate_paragraphs_before_approval_or_delivery(self):
        for task in ('check_pt', 'check_es'):
            with self.subTest(task=task):
                self.pid = self.ws.import_book(self.source)['id']
                seen = []
                def recover(**kwargs):
                    data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); seen.append(data)
                    if data['task'] == task and not data.get('validation_feedback'):
                        p = data['paragraphs'][0]
                        edit = {'paragraph_id': p['id'], 'original': p['draft'], 'replacement': p['draft'],
                                'occurrence': 0, 'reason': 'Fixture.', 'category': 'teste'}
                        return self.duplicate_response(data)
                    return automatic_runner(**kwargs)
                self.ws.runner = recover
                detail = self.run_job()
                self.assertEqual(detail['job']['status'], 'completed', detail['job']['message'])
                checks = [d for d in seen if d['task'] == task]
                self.assertEqual(len(checks), 8)
                self.assertEqual(sum(bool(d.get('validation_feedback')) for d in checks), 4)

    def test_manual_invalid_response_is_not_retried(self):
        seen = []
        def invalid(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); seen.append(data)
            return self.overlapping_response(data)
        self.ws.runner = invalid
        with self.assertRaisesRegex(ValueError, 'sobrepostas'):
            self.ws._operate(self.pid, 'chunk-00003', 'review')
        self.assertEqual(len(seen), 1)
        self.assertEqual(self.ws.detail(self.pid)['progress']['approved_paragraphs'], 0)

    def test_empty_paragraph_response_recovers_in_review_and_both_checks(self):
        for task in ('review', 'check_pt', 'check_es'):
            with self.subTest(task=task):
                self.pid = self.ws.import_book(self.source)['id']; seen = []
                def recover(**kwargs):
                    data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); seen.append(data)
                    if data['task'] == task and not data.get('validation_feedback'):
                        p = data['paragraphs'][0]; text = p.get('draft', p['text'])
                        result=automatic_runner(**kwargs); result['paragraphs'][0]['text']=''
                        return result
                    return automatic_runner(**kwargs)
                self.ws.runner = recover
                detail = self.run_job()
                self.assertEqual(detail['job']['status'], 'completed', detail['job']['message'])
                attempts = [d for d in seen if d['task'] == task]
                self.assertEqual(len(attempts), 8)
                self.assertTrue(all('apagar um parágrafo' in d['validation_feedback'] for d in attempts if d.get('validation_feedback')))
                state = read_json(self.ws._folder(self.pid)/'state.json')
                self.assertTrue(all(text.strip() for c in state['chunks'] for text in c['revised'].values()))
                self.assertTrue(all(text.strip() for c in state['chunks'] for text in c['translations'].values()))

    def test_invalid_model_shapes_ids_breaks_and_translation_coverage_recover_once(self):
        def paragraph_result(data):
            return {'paragraphs':[{'paragraph_id':p['id'],'text':p['text'],'reason':'Fixture.','category':'teste'} for p in data['paragraphs']]}
        def bad_breaks(data):
            result=paragraph_result(data); result['paragraphs'][0]['text']+='\n'; return result
        def bad_id(data):
            result=paragraph_result(data); result['paragraphs'][0]['paragraph_id']='unknown'; return result
        cases = [('review',lambda data:None), ('review',lambda data:{'paragraphs':[None]}),
                 ('review',bad_id), ('review',bad_breaks),
                 ('translate',lambda data:{'translations':[],'terms':[]}),
                 ('translate',lambda data:{'translations':[{'paragraph_id':p['id'],'text':'ES '+p['text']} for p in data['paragraphs']], 'terms':None}),
                 ('check_pt',lambda data:{'paragraphs':[],'issues':None})]
        for i,(task,bad_response) in enumerate(cases):
            with self.subTest(case=i,task=task):
                self.pid = self.ws.import_book(self.source)['id']; attempts = []
                def recover(**kwargs):
                    data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
                    if data['task'] == task:
                        attempts.append(data)
                        if not data.get('validation_feedback'): return bad_response(data)
                    return automatic_runner(**kwargs)
                self.ws.runner = recover
                detail = self.run_job()
                self.assertEqual(detail['job']['status'], 'completed', detail['job']['message'])
                self.assertEqual(len(attempts), 8)
                self.assertEqual(detail['job']['response_retries'], 4)

    def test_persistent_erase_response_is_blocked_twice_with_chunk_and_reason(self):
        seen = []
        def erase(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); seen.append(data)
            if data['task'] == 'review' and any('estavam' in p['text'] for p in data['paragraphs']):
                p = next(p for p in data['paragraphs'] if 'estavam' in p['text'])
                result=automatic_runner(**kwargs); next(item for item in result['paragraphs'] if item['paragraph_id']==p['id'])['text']=''
                return result
            return automatic_runner(**kwargs)
        self.ws.runner = erase
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'needs_attention')
        self.assertEqual(sum(any('estavam' in p['text'] for p in d['paragraphs']) for d in seen), 2)
        self.assertEqual(detail['job']['problems'][0]['chunk_id'],'chunk-00003')
        self.assertIn('apagar um parágrafo', detail['job']['problems'][0]['message'])
        self.assertIsNone(detail['automatic_result'])
        state = read_json(self.ws._folder(self.pid)/'state.json')
        self.assertEqual(state['chunks'][2]['status'], 'pending')
        self.assertNotIn('revised', state['chunks'][2])
        self.assertFalse((self.ws._folder(self.pid)/'deliverables').exists())

    def test_stop_during_invalid_response_prevents_retry_and_keeps_pending_chunk(self):
        def stop_invalid(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            if data['task'] == 'review' and any('estavam' in p['text'] for p in data['paragraphs']):
                self.ws.stop(self.pid)
                self.calls.append('invalid')
                return self.duplicate_response(data)
            return automatic_runner(**kwargs)
        self.ws.runner = stop_invalid
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'paused')
        self.assertEqual(self.calls.count('invalid'), 1)
        self.assertIsNone(detail['automatic_result'])
        state = read_json(self.ws._folder(self.pid)/'state.json')
        self.assertEqual(state['chunks'][2]['status'], 'pending')
        self.ws.runner = automatic_runner
        self.assertTrue(self.run_job()['automatic_result'])

    def test_transport_and_state_errors_are_not_retried(self):
        from unittest.mock import patch
        for error in (RuntimeError('provider unavailable'), ValueError('O trabalho mudou durante a geração.')):
            with self.subTest(error=type(error).__name__):
                seen = []
                def fail(pid, chunk_id, task, **kwargs):
                    seen.append(chunk_id)
                    raise error
                with patch.object(self.ws, '_operate', side_effect=fail):
                    detail = self.run_job()
                self.assertEqual(detail['job']['status'], 'failed')
                self.assertEqual(len(seen), len(set(seen)))
                state = read_json(self.ws._folder(self.pid)/'state.json')
                self.assertFalse(any(a['action'] == 'response-retry' for a in state['audit']))

    def test_unresolved_pt_issue_blocks_approval_and_resume_keeps_completed_review(self):
        def blocked(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            self.calls.append(data['task'])
            if data['task']=='check_pt':
                result=automatic_runner(**kwargs); result['issues']=['Conferir alteração de sentido.']; return result
            return automatic_runner(**kwargs)
        self.ws.runner = blocked
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'needs_attention')
        self.assertEqual(detail['progress']['approved_paragraphs'], 0)
        self.assertIsNone(detail['automatic_result'])
        count = self.calls.count('review')
        self.assertEqual(self.calls.count('check_pt'), 4)  # Editorial issues never trigger output retries.
        self.ws.runner = automatic_runner
        self.assertTrue(self.run_job()['automatic_result'])
        self.assertEqual(self.calls.count('review'), count)

    def test_unresolved_es_issue_blocks_final_word_and_resume_does_not_retranslate(self):
        def blocked(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); self.calls.append(data['task'])
            if data['task']=='check_es':
                result=automatic_runner(**kwargs); result['issues']=['Tradução omitiu uma informação.']; return result
            return automatic_runner(**kwargs)
        self.ws.runner = blocked
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'needs_attention')
        self.assertIsNone(detail['automatic_result'])
        self.assertFalse((self.ws._folder(self.pid)/'deliverables').exists())
        count = self.calls.count('translate')
        self.ws.runner = automatic_runner
        self.assertTrue(self.run_job()['automatic_result'])
        self.assertEqual(self.calls.count('translate'), count)

    def test_missing_translation_paragraph_never_finishes_automatic_job(self):
        def incomplete(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            result = automatic_runner(**kwargs)
            if data['task']=='translate': result['translations'].pop()
            return result
        self.ws.runner = incomplete
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'needs_attention')
        self.assertEqual(detail['progress']['translated_paragraphs'], 0)
        self.assertIsNone(detail['automatic_result'])

    def test_four_inflight_reviews_stop_drain_and_resume_without_repeating_saved_chunks(self):
        entered = threading.Event(); release = threading.Event(); guard = threading.Lock()
        counts = {'active': 0, 'peak': 0, 'calls': 0}
        def slow(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            if data['task']=='review':
                with guard:
                    counts['active']+=1; counts['calls']+=1; counts['peak']=max(counts['peak'],counts['active'])
                    if counts['active']==4: entered.set()
                try:
                    if not release.wait(3): raise TimeoutError('fixture wait')
                    return automatic_runner(**kwargs)
                finally:
                    with guard: counts['active']-=1
            return automatic_runner(**kwargs)
        self.ws.runner = slow
        try:
            self.ws.start(self.pid, 'automatic')
            self.assertTrue(entered.wait(2))
            self.ws.stop(self.pid); release.set(); self.ws.thread.join(4)
            detail = self.ws.detail(self.pid)
            self.assertEqual(detail['job']['status'], 'paused')
            self.assertEqual(counts['peak'], 4)
            self.assertEqual(detail['progress']['pending_chunks'], 0)
            self.assertEqual(detail['progress']['approved_paragraphs'], 0)
            self.assertTrue(self.run_job()['automatic_result'])
            self.assertEqual(counts['calls'], 4)
        finally: release.set()

    def test_manual_translation_edit_invalidates_automatic_result_and_requires_new_check(self):
        detail = self.run_job(); self.assertTrue(detail['automatic_result'])
        chunk = detail['current']
        changed = dict(chunk['translations']); key = next(iter(changed)); changed[key] += ' Ajuste.'
        self.ws.save_translation(self.pid, chunk['id'], changed, detail['revision'])
        self.assertIsNone(self.ws.detail(self.pid)['automatic_result'])
        before = self.calls.count('check_es')
        self.assertTrue(self.run_job()['automatic_result'])
        self.assertEqual(self.calls.count('check_es'), before+1)

    def test_section_destination_is_preserved_in_automatic_mode(self):
        self.pid = self.ws.import_book(self.source, destination=self.destination)['id']
        self.ws.configure(self.pid, {'scope':'sections', 'section_ids':['epilogo','posfacio']})
        original = self.destination.read_bytes()
        detail = self.run_job(); self.assertTrue(detail['automatic_result'])
        es = inspect_document(Path(detail['automatic_result']['files']['es']['path']))
        self.assertEqual([p['text'] for p in es['paragraphs']][:2], ['Capítulo 1', 'Texto español intacto.'])
        self.assertEqual(self.destination.read_bytes(), original)

    def test_checker_cannot_erase_a_whole_paragraph(self):
        def erase(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            if data['task']=='check_pt':
                p = data['paragraphs'][0]
                result=automatic_runner(**kwargs); result['paragraphs'][0]['text']=''
                return result
            return automatic_runner(**kwargs)
        self.ws.runner = erase
        detail = self.run_job()
        self.assertEqual(detail['job']['status'], 'needs_attention')
        self.assertEqual(detail['progress']['approved_paragraphs'], 0)
        self.assertIsNone(detail['automatic_result'])

    def test_final_region_warning_blocks_delivery_even_if_model_reported_no_issues(self):
        def ignore_region(**kwargs):
            data=json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            if data['task']=='check_es':
                result=automatic_runner(**kwargs)
                for item,p in zip(result['paragraphs'],data['paragraphs']): item['text']=p['draft']
                return result
            return automatic_runner(**kwargs)
        self.ws.runner=ignore_region
        detail=self.run_job()
        self.assertEqual(detail['job']['status'],'needs_attention')
        self.assertGreater(len(detail['consistency_warnings']),0)
        self.assertIsNone(detail['automatic_result'])
        self.assertFalse((self.ws._folder(self.pid)/'deliverables').exists())

    def test_translation_review_uses_final_shared_glossary_after_parallel_generation(self):
        glossaries={'translate':[], 'check_es':[]}
        def terms(**kwargs):
            data=json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            if data['task'] in glossaries: glossaries[data['task']].append(data['glossary'])
            result=automatic_runner(**kwargs)
            if data['task']=='translate' and any('preservado' in p['text'] for p in data['paragraphs']):
                result['terms']=[{'source':'preservado','target':'preservado'}]
            return result
        self.ws.runner=terms
        detail=self.run_job(); self.assertTrue(detail['automatic_result'])
        self.assertTrue(all(g=={} for g in glossaries['translate']))
        self.assertTrue(all(g=={'preservado':'preservado'} for g in glossaries['check_es']))

    def test_untrusted_extra_xml_blocks_word_delivery(self):
        with zipfile.ZipFile(self.source,'a') as archive:
            archive.writestr('customXml/item1.xml',b'<!DOCTYPE x [<!ENTITY boom "blocked">]><x>&boom;</x>')
        self.pid=self.ws.import_book(self.source)['id']
        detail=self.run_job()
        self.assertEqual(detail['job']['status'],'failed')
        self.assertIsNone(detail['automatic_result'])
        with self.assertRaises(ValueError): self.ws.download_path(self.pid,'pt-BR')


    def test_new_check_contract_invalidates_old_automatic_completion(self):
        from unittest.mock import patch
        from revisor import book_prompts
        self.assertTrue(self.run_job()['automatic_result'])
        with patch.object(book_prompts,'VERSION','new-check-contract'):
            self.assertIsNone(self.ws.detail(self.pid)['automatic_result'])
            before=self.calls.count('check_es')
            self.assertTrue(self.run_job()['automatic_result'])
            self.assertEqual(self.calls.count('check_es'),before+4)


class DetailCostTests(unittest.TestCase):
    """Opening a book recomputes nothing per paragraph that can be computed once."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root/'pt.docx'; fixture(self.source)
        self.ws = BookWorkspace(self.root, runner=automatic_runner)
        self.pid = self.ws.import_book(self.source)['id']
        self.ws.configure(self.pid, {'glossary': {'Texto': 'Texto', 'Epílogo': 'Epílogo', 'planos terráqueos': 'planos terrícolas'}})
        self.ws.start(self.pid, 'automatic'); self.ws.thread.join(5)

    def tearDown(self):
        self.ws.close(); self.temp.cleanup()

    def test_detail_checks_consistency_once_with_one_glossary(self):
        expected = self.ws.detail(self.pid)['consistency_warnings']
        calls = {'warnings': 0, 'glossary': 0}
        warnings, glossary = self.ws._warnings, self.ws._glossary
        def count_warnings(*args, **kwargs):
            calls['warnings'] += 1
            before = calls['glossary']
            result = warnings(*args, **kwargs)
            self.assertEqual(calls['glossary'] - before, 1)
            return result
        def count_glossary(*args):
            calls['glossary'] += 1
            return glossary(*args)
        self.ws._warnings, self.ws._glossary = count_warnings, count_glossary
        self.assertEqual(self.ws.detail(self.pid)['consistency_warnings'], expected)
        self.assertEqual(calls['warnings'], 1)

    def test_term_patterns_are_built_once_per_glossary(self):
        from revisor import book_terms
        glossary = {'planos terráqueos': 'planos terrícolas', 'grama': 'césped'}
        book_terms.term_patterns.cache_clear()
        for text in ['Os planos terráqueos.', 'A grama.', 'Nada aqui.'] * 50:
            book_terms.source_terms(text, glossary)
        self.assertEqual(book_terms.term_patterns.cache_info().misses, 1)


class AuthorPortugueseEditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root/'pt.docx'; fixture(self.source)
        self.calls = []
        def record(**kwargs):
            self.calls.append(json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])['task'])
            return automatic_runner(**kwargs)
        self.ws = BookWorkspace(self.root, runner=record)
        self.pid = self.ws.import_book(self.source)['id']
        self.ws.start(self.pid, 'automatic'); self.ws.thread.join(5)

    def tearDown(self):
        self.ws.close(); self.temp.cleanup()

    def chunk_with_change(self):
        detail = self.ws.detail(self.pid)
        for item in detail['chunks']:
            current = self.ws.detail(self.pid, item['id'])['current']
            if current['edits']: return detail, current
        self.fail('fixture has no corrected chunk')

    def test_author_edit_keeps_approval_and_only_retranslates_that_chunk(self):
        detail, chunk = self.chunk_with_change()
        changed = chunk['edits'][0]['paragraph_id']
        revised = dict(chunk['revised']); revised[changed] = revised[changed] + ' Acréscimo da autora.'
        self.ws.edit_portuguese(self.pid, chunk['id'], revised, detail['revision'])
        after = self.ws.detail(self.pid, chunk['id'])
        current = after['current']
        self.assertEqual(current['status'], 'approved')
        self.assertEqual(current['revised'][changed], revised[changed])
        self.assertNotIn('translations', current)
        self.assertIsNone(after['automatic_result'])
        self.assertGreater(after['revision'], detail['revision'])
        mine = [e for e in current['edits'] if e['paragraph_id'] == changed]
        self.assertTrue(mine and all(e['reason'] == 'Ajustado por você.' for e in mine))
        others = [e for e in chunk['edits'] if e['paragraph_id'] != changed]
        self.assertEqual([e for e in current['edits'] if e['paragraph_id'] != changed], others)
        translated = [c['id'] for c in after['chunks'] if c['translated']]
        self.assertEqual(len(translated), len(after['chunks']) - 1)
        state = read_json(self.ws._folder(self.pid)/'state.json')
        self.assertEqual(state['audit'][-1]['action'], 'edit-portuguese')
        self.calls.clear()
        self.ws.start(self.pid, 'automatic'); self.ws.thread.join(5)
        final = self.ws.detail(self.pid)
        self.assertTrue(final['automatic_result'])
        self.assertNotIn('review', self.calls)
        self.assertNotIn('check_pt', self.calls)
        self.assertEqual(self.calls.count('translate'), 1)

    def test_invalid_author_edits_change_nothing(self):
        detail, chunk = self.chunk_with_change()
        revision, revised = detail['revision'], chunk['revised']
        first = next(iter(revised))
        cases = [
            (revised, revision),
            ({**revised, first: '  '}, revision),
            ({k: v for k, v in list(revised.items())[1:]}, revision),
            ({**revised, first: revised[first] + ' x'}, revision - 1),
        ]
        for value, expected in cases:
            with self.subTest(value=value, expected=expected), self.assertRaises(ValueError):
                self.ws.edit_portuguese(self.pid, chunk['id'], value, expected)
        self.assertEqual(self.ws.detail(self.pid)['revision'], revision)


class EditorialNotesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root/'pt.docx'; fixture(self.source)
        def noting(**kwargs):
            result = automatic_runner(**kwargs)
            if json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])['task'] == 'check_pt':
                result['notes'] = ['Ambiguidade fictícia preservada.', 'Segunda dúvida fictícia.']
            return result
        self.ws = BookWorkspace(self.root, runner=noting)
        self.pid = self.ws.import_book(self.source)['id']
        self.ws.start(self.pid, 'automatic'); self.ws.thread.join(5)

    def tearDown(self):
        self.ws.close(); self.temp.cleanup()

    def test_notes_are_marked_read_without_touching_the_delivery(self):
        detail = self.ws.detail(self.pid)
        notes = detail['editorial_notes']
        self.assertGreater(len(notes), 2)
        self.assertEqual(len({n['id'] for n in notes}), len(notes))
        self.assertFalse(any(n['read'] for n in notes))
        revision, result = detail['revision'], detail['automatic_result']
        self.assertTrue(result)
        self.ws.mark_notes(self.pid, [notes[0]['id']], True)
        after = self.ws.detail(self.pid)
        self.assertEqual([n['read'] for n in after['editorial_notes']], [True] + [False] * (len(notes) - 1))
        self.assertEqual((after['revision'], after['automatic_result']), (revision, result))
        self.ws.mark_notes(self.pid, [n['id'] for n in notes], True)
        self.ws.mark_notes(self.pid, [notes[1]['id']], False)
        final = self.ws.detail(self.pid)['editorial_notes']
        self.assertEqual(sum(not n['read'] for n in final), 1)
        self.assertFalse(final[1]['read'])
        state = read_json(self.ws._folder(self.pid)/'state.json')
        self.assertEqual(sum(a['action'] == 'notes-read' for a in state['audit']), 3)

    def test_unknown_or_invalid_note_ids_change_nothing(self):
        for ids in (['nao-existe'], 'texto', [], [1]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.ws.mark_notes(self.pid, ids, True)
        with self.assertRaises(ValueError):
            self.ws.mark_notes(self.pid, [self.ws.detail(self.pid)['editorial_notes'][0]['id']], 'sim')
        self.assertFalse(any(n['read'] for n in self.ws.detail(self.pid)['editorial_notes']))


class ResetAndRemoveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root/'pt.docx'; fixture(self.source)
        self.ws = BookWorkspace(self.root, runner=automatic_runner)
        self.pid = self.ws.import_book(self.source)['id']
        self.ws.start(self.pid, 'automatic'); self.ws.thread.join(5)

    def tearDown(self):
        self.ws.close(); self.temp.cleanup()

    def test_reset_starts_over_keeps_settings_and_archives_the_previous_work(self):
        self.ws.set_spellings(self.pid, added=['eXtra'], removed=[])
        self.assertTrue(self.ws.detail(self.pid)['automatic_result'])
        self.ws.reset(self.pid)
        detail = self.ws.detail(self.pid)
        self.assertTrue(all(c['status'] == 'pending' and not c['translated'] for c in detail['chunks']))
        self.assertIsNone(detail['automatic_result']); self.assertIsNone(detail['job'])
        self.assertEqual(detail['spellings']['added'], ['eXtra'])
        archived = list((self.ws._folder(self.pid)/'history').glob('state-*.json'))
        self.assertEqual(len(archived), 1)
        self.assertTrue(read_json(archived[0])['automatic_result'])
        self.ws.configure(self.pid, {'scope': 'sections', 'section_ids': ['epilogo']})  # Settings unlock again.
        self.assertEqual(read_json(self.ws._folder(self.pid)/'state.json')['audit'][0]['action'], 'reset')

    def test_remove_hides_the_book_but_keeps_its_files_recoverable(self):
        other = self.ws.import_book(self.source, name='Outro')['id']
        folder = self.ws._folder(self.pid)
        self.ws.remove(self.pid)
        self.assertEqual([p['id'] for p in self.ws.list_projects()], [other])
        self.assertFalse(folder.exists())
        kept = list((self.ws.root/'.removidos').glob(f'{self.pid}-*/project.json'))
        self.assertEqual(len(kept), 1)
        with self.assertRaises(ValueError): self.ws.detail(self.pid)

    def test_a_running_book_cannot_be_reset_or_removed(self):
        import threading
        gate, release = threading.Event(), threading.Event()
        def slow(**kwargs):
            gate.set(); release.wait(5); return automatic_runner(**kwargs)
        self.ws.reset(self.pid)
        self.ws.runner = slow
        self.ws.start(self.pid, 'automatic'); self.assertTrue(gate.wait(5))
        try:
            for operation in (self.ws.reset, self.ws.remove):
                with self.subTest(operation=operation.__name__), self.assertRaises(ValueError):
                    operation(self.pid)
        finally:
            release.set(); self.ws.stop(self.pid); self.ws.thread.join(10)


class ChangedOnlyWorkflowTests(unittest.TestCase):
    def test_automatic_book_completes_when_the_model_returns_only_changed_paragraphs(self):
        def changed_only(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
            if data['task'] == 'translate': return automatic_runner(**kwargs)
            key = 'draft' if data['task'] != 'review' else 'text'
            changed, unchanged = [], []
            for p in data['paragraphs']:
                text = p.get(key, p['text'])
                fixed = text.replace('estavam', 'estava') if data['task'] == 'review' else text.replace('vosotros', 'ustedes')
                if fixed != text: changed.append({'paragraph_id': p['id'], 'text': fixed, 'reason': 'Correção.', 'category': 'gramática'})
                else: unchanged.append(p['id'])
            result = {'paragraphs': changed, 'unchanged': unchanged}
            if data['task'] != 'review': result |= {'issues': [], 'notes': []}
            return result
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'pt.docx'; fixture(source)
            ws = BookWorkspace(root, runner=changed_only)
            try:
                pid = ws.import_book(source)['id']
                ws.start(pid, 'automatic'); ws.thread.join(5)
                detail = ws.detail(pid)
                self.assertEqual(detail['job']['status'], 'completed')
                self.assertTrue(detail['automatic_result'])
                texts = [t for c in read_json(ws._folder(pid)/'state.json')['chunks'] for t in c['revised'].values()]
                self.assertIn('Ela estava aqui. ― Olá!', texts)
            finally:
                ws.close()

    def test_new_books_are_split_into_chunks_of_up_to_32_paragraphs(self):
        from test_book_spellings import book
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'longo.docx'
            book(source, [('Capítulo 1', 'Heading1')] + [(f'Parágrafo {i} do capítulo.', '') for i in range(70)] + [('Capítulo 2', 'Heading1'), ('Fim.', '')])
            ws = BookWorkspace(root, runner=automatic_runner)
            try:
                pid = ws.import_book(source)['id']
                sizes = [len(c['paragraph_ids']) for c in read_json(ws._folder(pid)/'state.json')['chunks']]
                self.assertEqual(sizes, [32, 32, 7, 2])
            finally:
                ws.close()
