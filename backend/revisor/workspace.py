"""Independent book projects, durable proposals and resumable background work."""
from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from threading import RLock, Thread

from revisor import book_prompts
from revisor.book_pipeline import run_automatic
from revisor.book_response import EditorialIssues, apply_paragraphs
from revisor.book_terms import canonical_glossary, contains_target, source_terms
from revisor.docx.editable import MAX_ARCHIVE, edit_document, inspect_document, splice_sections
from revisor.docx.reader import parse_xml, extract_docx_metadata
from revisor.provider import DEFAULT_MODEL, InvalidModelResponse, codex_runner


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


class BookWorkspace:
    def __init__(self, root: Path, *, runner=codex_runner, model=DEFAULT_MODEL):
        self.root = root.resolve() / '.books'
        self.root.mkdir(parents=True, exist_ok=True)
        self.runner, self.model = runner, model
        self.lock = RLock()
        self.thread = None
        self.active_job = None
        self.file_lock = (self.root / 'workspace.lock').open('a')
        try:
            fcntl.flock(self.file_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.file_lock.close()
            raise ValueError('Já existe outro processo usando esta pasta de livros.') from error
        for file in self.root.glob('*/job.json'):
            job = read_json(file)
            if job['status'] in {'running', 'stopping'}:
                job['status'] = 'interrupted'; job['message'] = 'Execução interrompida. Retome a partir do progresso salvo.'
                save_json(file, job)

    def close(self):
        with self.lock:
            if self.active_job:
                self.active_job['stop_requested'] = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=310)
        if not self.file_lock.closed:
            self.file_lock.close()

    def _folder(self, pid):
        if not isinstance(pid, str) or len(pid) != 32 or any(c not in '0123456789abcdef' for c in pid):
            raise ValueError('Trabalho inválido.')
        folder = self.root / pid
        if not (folder / 'project.json').is_file():
            raise ValueError('Trabalho não encontrado.')
        return folder

    def _load(self, pid):
        folder = self._folder(pid)
        return folder, read_json(folder / 'project.json'), read_json(folder / 'state.json')

    def _idle(self):
        if self.active_job:
            raise ValueError('Há uma operação em andamento. Pare após o trecho atual antes de alterar o trabalho.')

    def import_book(self, source: Path, *, destination: Path | None = None, name: str | None = None):
        with self.lock:
            self._idle()
            if name is not None and not isinstance(name,str): raise ValueError('O nome do trabalho deve ser um texto.')
            doc = inspect_document(source)
            if doc['paragraph_count'] == 0:
                raise ValueError('O Word não contém texto para revisar.')
            dest_doc = inspect_document(destination) if destination else None
            pid = uuid.uuid4().hex
            with tempfile.TemporaryDirectory(dir=self.root) as temp:
                folder = Path(temp)
                shutil.copy2(source, folder / 'source.docx')
                if destination: shutil.copy2(destination, folder / 'destination.docx')
                project = {'id':pid, 'name':(name or source.stem)[:200], 'filename':source.name,
                           'author':extract_docx_metadata(source).get('core',{}).get('creator'),
                           'created_at':time.time(), 'document':doc, 'destination':dest_doc,
                           'destination_filename':destination.name if destination else None,
                           'settings':{'scope':'sections' if destination else 'whole', 'section_ids':[], 'instructions':'', 'glossary':{}},
                           'model':self.model, 'reasoning_effort':'low', 'locale':'es-419'}
                state = {'chunks':self._chunks(project), 'terms':{}, 'audit':[], 'revision':0}
                save_json(folder / 'project.json', project); save_json(folder / 'state.json', state)
                folder.rename(self.root / pid)
            return {'id':pid, 'name':project['name']}

    def _selected(self, project):
        settings, doc = project['settings'], project['document']
        if settings['scope'] == 'whole':
            return [p for p in doc['paragraphs'] if p['text'].strip()]
        selected = {pid for section in doc['sections'] if section['key'] in settings['section_ids'] for pid in section['paragraph_ids']}
        return [p for p in doc['paragraphs'] if p['id'] in selected]

    def _chunks(self, project):
        doc = project['document']; paragraphs = self._selected(project)
        section_for = {pid:section['title'] for section in doc['sections'] for pid in section['paragraph_ids']}
        chunks = []; current = []; size = 0; title = None
        for paragraph in paragraphs:
            section = section_for.get(paragraph['id'], 'Notas e cabeçalhos')
            if current and (size + len(paragraph['text']) > 4000 or len(current) >= 8 or section != title):
                chunks.append({'id':f'chunk-{len(chunks)+1:05}', 'paragraph_ids':current, 'title':title, 'status':'pending'})
                current = []; size = 0
            current.append(paragraph['id']); size += len(paragraph['text']); title = section
        if current: chunks.append({'id':f'chunk-{len(chunks)+1:05}', 'paragraph_ids':current, 'title':title, 'status':'pending'})
        return chunks

    def configure(self, pid, data):
        with self.lock:
            self._idle(); folder, project, state = self._load(pid)
            if any(c['status'] != 'pending' for c in state['chunks']):
                raise ValueError('O trabalho já começou. Importe uma nova cópia para mudar o escopo ou as regras.')
            settings = copy.deepcopy(project['settings'])
            for key in ('scope','section_ids','instructions','glossary'):
                if key in data: settings[key] = data[key]
            if settings['scope'] not in {'whole','sections'}:
                raise ValueError('Escolha livro inteiro ou seções.')
            known = {s['key'] for s in project['document']['sections']}
            if not isinstance(settings['section_ids'], list) or not set(settings['section_ids']).issubset(known):
                raise ValueError('Selecione seções existentes no corpo do documento.')
            if settings['scope'] == 'sections' and not settings['section_ids']:
                raise ValueError('Selecione pelo menos uma seção.')
            if project['destination'] and settings['scope'] != 'sections':
                raise ValueError('Para inserir em um Word espanhol, selecione apenas as seções a substituir.')
            if project['destination']:
                targets = {s['key'] for s in project['destination']['sections']}
                if not set(settings['section_ids']).issubset(targets):
                    raise ValueError('O destino não contém todas as seções selecionadas.')
            if not isinstance(settings['instructions'], str) or len(settings['instructions']) > 12000:
                raise ValueError('As instruções editoriais devem ter até 12.000 caracteres.')
            glossary = settings['glossary']
            if not isinstance(glossary, dict) or len(glossary) > 1000 or any(not isinstance(k,str) or not isinstance(v,str) or not k.strip() or not v.strip() for k,v in glossary.items()):
                raise ValueError('O glossário deve relacionar termos em português a termos em espanhol.')
            project['settings'] = settings; state['chunks'] = self._chunks(project)
            save_json(folder / 'project.json', project); save_json(folder / 'state.json', state)
            return self.detail(pid)

    def list_projects(self):
        with self.lock:
            projects = []
            for path in self.root.glob('*/project.json'):
                project = read_json(path); state = read_json(path.parent / 'state.json')
                projects.append({'id':project['id'], 'name':project['name'], 'created_at':project['created_at'],
                                 'scope':project['settings']['scope'], 'progress':self._progress(project,state)})
            return sorted(projects, key=lambda p:p['created_at'], reverse=True)

    @staticmethod
    def _glossary(project,state):
        return canonical_glossary(state['terms'],state.get('glossary_override',project['settings']['glossary']))

    def _progress(self, project, state):
        chunks = state['chunks']; total = sum(len(c['paragraph_ids']) for c in chunks)
        drafted = sum(len(c['paragraph_ids']) for c in chunks if c['status'] in {'ready','approved'})
        approved = sum(len(c['paragraph_ids']) for c in chunks if c['status'] == 'approved')
        translated = sum(len(c['paragraph_ids']) for c in chunks if c.get('translations'))
        checked = sum(len(c['paragraph_ids']) for c in chunks if self._es_checked(project,state,c))
        return {'draft_paragraphs':drafted, 'draft_percent':round(100*drafted/total) if total else 0, 'checked_paragraphs':checked, 'checked_percent':round(100*checked/total) if total else 0, 'total_paragraphs':total, 'approved_paragraphs':approved, 'translated_paragraphs':translated,
                'total_chunks':len(chunks), 'ready_chunks':sum(c['status']=='ready' for c in chunks),
                'pending_chunks':sum(c['status'] in {'pending','rejected'} for c in chunks),
                'review_percent':round(100*approved/total) if total else 0,
                'translation_percent':round(100*translated/total) if total else 0}

    def detail(self, pid, chunk_id=None):
        with self.lock:
            folder, project, state = self._load(pid)
            selected = {p['id']:p for p in project['document']['paragraphs']}
            current = next((c for c in state['chunks'] if c['id']==chunk_id), None) if chunk_id else None
            if current is None:
                current = next((c for c in state['chunks'] if c['status'] != 'approved'), None)
            if current is None and state['chunks']: current = state['chunks'][-1]
            enriched = None
            if current:
                enriched = copy.deepcopy(current)
                enriched['spanish_checked']=self._es_checked(project,state,current)
                enriched['paragraphs'] = [selected[i] for i in current['paragraph_ids']]
                enriched['original_text'] = '\n\n'.join(p['text'] for p in enriched['paragraphs'])
                enriched['revised_text'] = '\n\n'.join(current.get('revised',{}).get(str(p['id']),p['text']) for p in enriched['paragraphs'])
                enriched['spanish_text'] = '\n\n'.join(current.get('translations',{}).get(str(p['id']),'') for p in enriched['paragraphs'])
            job_path = folder / 'job.json'
            job=read_json(job_path) if job_path.exists() else None
            if job:
                job['elapsed_seconds']=max(0,int(job.get('finished_at',time.time())-job.get('started_at',time.time())))
                if not job.get('problems') and job.get('failed_chunk'):
                    job['problems']=[{'chunk_id':job['failed_chunk'],'phase':job.get('phase',''),'message':job['message']}]
                for problem in job.get('problems',[]):
                    match=next(((i,c) for i,c in enumerate(state['chunks'],1) if c['id']==problem['chunk_id']),None)
                    if match: problem.update(index=match[0],title=match[1]['title'])
            automatic_result=state.get('automatic_result') if (state.get('automatic_result',{}).get('revision') == state['revision'] and all(c['status']=='approved' and self._es_checked(project,state,c) for c in state['chunks']) and not self._warnings(project,state)) else None
            if automatic_result:
                automatic_result=automatic_result | {'files':{language:artifact | {'filename':self._download_filename(project,language)} for language,artifact in automatic_result['files'].items()}}
            return {'id':pid, 'name':project['name'], 'filename':project['filename'], 'author':project.get('author'),
                    'destination_filename':project['destination_filename'], 'settings':project['settings'],
                    'sections':project['document']['sections'], 'model':self.model, 'reasoning_effort':'low', 'locale':'es-419',
                    'progress':self._progress(project,state), 'current':enriched,
                    'editorial_notes':self._editorial_notes(project,state),
                    'chunks':[{'id':c['id'], 'title':c['title'], 'status':c['status'], 'translated':bool(c.get('translations')), 'corrections':len(c.get('edits') or [])} for c in state['chunks']],
                    'job':job,
                    'automatic_result':automatic_result,
                    'glossary':self._glossary(project,state),
                    'consistency_warnings':self._warnings(project,state), 'revision':state['revision']}

    def _chunk_input(self, project, state, chunk):
        paragraphs = project['document']['paragraphs']; by_id = {p['id']:p for p in paragraphs}
        chosen = [dict(by_id[i]) for i in chunk['paragraph_ids']]
        if chunk['status'] == 'approved':
            chosen = [p | {'text':chunk['revised'][str(p['id'])]} for p in chosen]
        first = next(i for i,p in enumerate(paragraphs) if p['id'] == chunk['paragraph_ids'][0])
        last = next(i for i,p in enumerate(paragraphs) if p['id'] == chunk['paragraph_ids'][-1])
        settings = project['settings'] | {'glossary':self._glossary(project,state)}
        dest_context = ''
        if project['destination']:
            # Bounded, source-grounded context from existing Spanish near the selected sections.
            dest = project['destination']; keys = set(project['settings']['section_ids'])
            starts = [s['start'] for s in dest['sections'] if s['key'] in keys]
            if starts:
                nearby = [p['text'] for p in dest['paragraphs'] if isinstance(p['id'],int) and min(starts)-25 <= p['id'] <= max(starts)+5]
                dest_context = '\n'.join(nearby)[-12000:]
        return chosen, {'previous':[p['text'] for p in paragraphs[max(0,first-2):first]],
                        'following':[p['text'] for p in paragraphs[last+1:last+3]], 'title':chunk['title'],
                        'settings':settings, 'feedback':chunk.get('feedback',''), 'destination_context':dest_context}

    @staticmethod
    def _digest(value):
        return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

    def _request_token(self, project, state, chunk):
        # Other chunks can finish concurrently. Protect this input and user configuration.
        return self._digest([project, state.get('glossary_override'), chunk])

    def _es_signature(self, project, state, chunk):
        return self._digest([chunk.get('revised'),chunk.get('translations'),self._glossary(project,state)])

    def _es_checked(self, project, state, chunk):
        receipt=chunk.get('checks',{}).get('es',{})
        return (bool(chunk.get('translations')) and receipt.get('signature')==self._es_signature(project,state,chunk)
                and receipt.get('issues')==[] and receipt.get('prompt_version')==book_prompts.VERSION)

    def _operate(self, pid, chunk_id, task, *, glossary=None, validation_feedback='', paragraph_output=False):
        if task not in {'review','translate'}: raise ValueError('Operação editorial inválida.')
        with self.lock:
            folder, project, state = self._load(pid)
            chunk = next((c for c in state['chunks'] if c['id']==chunk_id), None)
            if chunk is None: raise ValueError('Trecho não encontrado.')
            if task == 'review' and chunk['status'] == 'approved': raise ValueError('Este trecho já está aprovado.')
            if task == 'translate' and chunk['status'] != 'approved': raise ValueError('Aprove a revisão antes de traduzir.')
            paragraphs, context = self._chunk_input(project,state,chunk)
            if glossary is not None: context['settings']['glossary']=glossary
            prompt = book_prompts.prompt(task, paragraphs, **context, validation_feedback=validation_feedback, paragraph_output=paragraph_output)
            expected_token = self._request_token(project,state,chunk)
        # Do not hold the read lock while a model is running: polling remains responsive.
        response = self.runner(prompt=prompt, schema=book_prompts.schema(task,paragraph_output=paragraph_output), model=self.model)
        if not isinstance(response,dict): raise InvalidModelResponse('A IA devolveu uma resposta inválida. Gere novamente.')
        with self.lock:
            folder, project, state = self._load(pid)
            chunk = next(c for c in state['chunks'] if c['id']==chunk_id)
            if self._request_token(project,state,chunk) != expected_token: raise ValueError('O trabalho mudou durante a geração. Atualize a tela.')
            by_id = {str(p['id']):p['text'] for p in paragraphs}
            if task == 'review':
                revised, changes = apply_paragraphs(by_id,response) if paragraph_output else self._apply_edits(by_id,response)
                if paragraph_output: chunk['paragraph_proposals']=response['paragraphs']
                chunk.update(status='ready', edits=changes, revised=revised, proposal_id=uuid.uuid4().hex)
                chunk.pop('feedback',None); chunk.pop('checks',None)
            else:
                translated = response.get('translations'); terms = response.get('terms',[])
                if not isinstance(translated,list): raise InvalidModelResponse('O modelo devolveu uma tradução inválida.')
                actual = [str(t.get('paragraph_id','')) for t in translated if isinstance(t,dict)]
                if actual != list(by_id) or any(not isinstance(t.get('text'),str) or not t['text'].strip() for t in translated):
                    raise InvalidModelResponse('A tradução não cobre exatamente todos os parágrafos. O trecho não foi salvo.')
                chunk['translations'] = {str(t['paragraph_id']):t['text'] for t in translated}
                chunk.get('checks',{}).pop('es',None)
                for eid,text in chunk['translations'].items(): self._validate_model_breaks(by_id[eid],text)
                if not isinstance(terms,list): raise InvalidModelResponse('Glossário devolvido inválido.')
                known = self._glossary(project,state)
                for term in terms:
                    if not isinstance(term,dict): raise InvalidModelResponse('Glossário devolvido inválido.')
                    source, target = term.get('source',''), term.get('target','')
                    if isinstance(source,str) and isinstance(target,str) and source.strip() and target.strip() and source.casefold() not in {s.casefold() for s in known}:
                        if any(source in text for text in by_id.values()) and any(target in text for text in chunk['translations'].values()):
                            state['terms'][source] = target
            chunk.setdefault('provenance',{})[task] = {'model':self.model, 'reasoning_effort':'low', 'prompt_version':book_prompts.VERSION,
                                   'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(), 'at':time.time()}
            state['revision'] += 1
            state['audit'].append({'action':task, 'chunk':chunk_id, 'at':time.time()})
            save_json(folder / 'state.json',state)

    @classmethod
    def _apply_edits(cls, by_id, response):
        edits = response.get('edits')
        if not isinstance(edits,list): raise InvalidModelResponse('O modelo devolveu uma revisão inválida.')
        revised = dict(by_id); changes = []
        for edit in edits:
            if not isinstance(edit,dict): raise InvalidModelResponse('Correção inválida.')
            eid = str(edit.get('paragraph_id','')); original = edit.get('original'); replacement = edit.get('replacement')
            if eid not in revised or not isinstance(original,str) or not original or not isinstance(replacement,str):
                raise InvalidModelResponse('A correção não identifica um trecho único do original. Gere uma nova proposta.')
            if not isinstance(edit.get('reason'),str) or not edit['reason'].strip():
                raise InvalidModelResponse('A correção precisa de uma justificativa em texto.')
            if not isinstance(edit.get('category'),str) or not edit['category'].strip():
                raise InvalidModelResponse('A correção precisa de uma categoria em texto.')
            positions=[m.start() for m in re.finditer(re.escape(original),by_id[eid])]
            occurrence=edit.get('occurrence',0 if len(positions)==1 else None)
            if type(occurrence) is not int or not 0 <= occurrence < len(positions):
                raise InvalidModelResponse('A correção não identifica a ocorrência no texto original. Gere uma nova proposta.')
            edit = dict(edit) | {'occurrence':occurrence,'start':positions[occurrence]}
            changes.append(edit)
        for eid,text in by_id.items():
            ordered=sorted((e for e in changes if str(e['paragraph_id'])==eid),key=lambda e:e['start'])
            for i,e in enumerate(ordered):
                if i and e['start'] < ordered[i-1]['start']+len(ordered[i-1]['original']):
                    raise InvalidModelResponse('A proposta contém correções sobrepostas. Gere uma nova revisão.')
            for e in reversed(ordered):
                text=text[:e['start']]+e['replacement']+text[e['start']+len(e['original']):]
            if not text.strip(): raise InvalidModelResponse(f'A correção não pode apagar um parágrafo inteiro (parágrafo {eid}).')
            cls._validate_model_breaks(by_id[eid],text)
            revised[eid]=text
        return revised, changes

    def _check(self, pid, chunk_id, language, *, validation_feedback=''):
        task='check_pt' if language=='pt' else 'check_es'
        with self.lock:
            _, project, state = self._load(pid)
            chunk=next(c for c in state['chunks'] if c['id']==chunk_id)
            if language=='pt' and chunk['status']!='ready': raise ValueError('Gere a proposta antes da validação automática.')
            if language=='es' and (chunk['status']!='approved' or not chunk.get('translations')):
                raise ValueError('Gere a tradução antes da revisão bilíngue.')
            paragraphs, context=self._chunk_input(project,state,chunk)
            draft=copy.deepcopy(chunk['revised' if language=='pt' else 'translations'])
            if language=='es':
                term_feedback=[w['message'] for w in self._warnings(project,state,chunk_id=chunk_id)]
                if term_feedback:
                    context['consistency_feedback']='\n'.join(term_feedback)
            prompt=book_prompts.prompt(task,paragraphs,**context,draft=draft,validation_feedback=validation_feedback,paragraph_output=True)
            expected_token=self._request_token(project,state,chunk)
        response=self.runner(prompt=prompt,schema=book_prompts.schema(task,paragraph_output=True),model=self.model)
        if not isinstance(response,dict) or not isinstance(response.get('issues'),list) or any(not isinstance(i,str) or not i.strip() for i in response['issues']):
            raise InvalidModelResponse('A validação editorial devolveu uma resposta inválida.')
        notes=response.get('notes',[])
        if not isinstance(notes,list) or any(not isinstance(n,str) or not n.strip() for n in notes):
            raise InvalidModelResponse('As observações editoriais precisam ser uma lista de textos.')
        with self.lock:
            folder, project, state=self._load(pid)
            chunk=next(c for c in state['chunks'] if c['id']==chunk_id)
            if self._request_token(project,state,chunk)!=expected_token:
                raise ValueError('O trecho mudou durante a validação. Atualize e retome.')
            changed, edits=apply_paragraphs(draft,response)
            receipt={'issues':response['issues'],'notes':notes,'paragraphs':response['paragraphs'],'model':self.model,'prompt_version':book_prompts.VERSION,
                     'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'at':time.time()}
            if not response['issues']:
                receipt['edits']=edits
                if language=='pt':
                    final=[]
                    for p in paragraphs:
                        eid=str(p['id'])
                        reasons=[e['reason'] for e in chunk.get('edits',[]) if str(e['paragraph_id'])==eid]
                        checked=next(p for p in response['paragraphs'] if p['paragraph_id']==eid)
                        if checked['text']!=draft[eid]: reasons.append(checked['reason'])
                        final.append({'paragraph_id':eid,'text':changed[eid],
                                      'reason':'; '.join(dict.fromkeys(reasons)) or 'Revisão editorial.',
                                      'category':checked['category'] or 'revisão'})
                    _,chunk['edits']=apply_paragraphs({str(p['id']):p['text'] for p in paragraphs},{'paragraphs':final})
                    chunk['revised']=changed; chunk['status']='approved'; chunk['approval_mode']='automatic'; chunk['approved_at']=time.time()
                    receipt['signature']=self._digest(changed)
                    state['audit'].append({'action':'auto-approve','chunk':chunk_id,'proposal_id':chunk['proposal_id'],
                                           'before':draft,'edits':edits,'at':time.time()})
                else:
                    chunk['translations']=changed
                    receipt['signature']=self._es_signature(project,state,chunk)
                    state['audit'].append({'action':'check-es-applied','chunk':chunk_id,'before':draft,'edits':edits,'at':time.time()})
            chunk.setdefault('checks',{})[language]=receipt
            state['audit'].append({'action':task,'chunk':chunk_id,'issues':response['issues'],'at':time.time()})
            state['revision']+=1; save_json(folder/'state.json',state)
        if response['issues']:
            raise EditorialIssues('Validação com pendências. '+ '; '.join(i[:200] for i in response['issues'][:3]))

    @staticmethod
    def _note_id(chunk_id,language,message):
        # Stable while the receipt that produced the note stays valid.
        return hashlib.sha256(f'{chunk_id}\0{language}\0{message}'.encode()).hexdigest()[:16]

    def _editorial_notes(self,project,state):
        notes=[]; read=set(state.get('notes_read',[]))
        for index,chunk in enumerate(state['chunks'],1):
            for language,receipt in chunk.get('checks',{}).items():
                current=(chunk['status']=='approved' and receipt.get('signature')==self._digest(chunk.get('revised'))) if language=='pt' else self._es_checked(project,state,chunk)
                if current:
                    for message in receipt.get('notes',[]):
                        note_id=self._note_id(chunk['id'],language,message)
                        notes.append({'id':note_id,'chunk_id':chunk['id'],'index':index,'title':chunk['title'],'language':language,'message':message,'read':note_id in read})
        return notes

    def mark_notes(self,pid,ids,read):
        """Record that the author read (or wants to reread) notes; text, revision and delivery stay as they are."""
        if not isinstance(ids,list) or not ids or any(not isinstance(i,str) for i in ids) or not isinstance(read,bool):
            raise ValueError('Escolha as observações e se foram lidas.')
        with self.lock:
            folder, project, state = self._load(pid)
            known={n['id'] for n in self._editorial_notes(project,state)}
            if not set(ids)<=known: raise ValueError('Essa observação não existe mais. Atualize a tela.')
            current=set(state.get('notes_read',[]))
            state['notes_read']=sorted(current|set(ids) if read else current-set(ids))
            state['audit'].append({'action':'notes-read','ids':ids,'read':read,'at':time.time()})
            save_json(folder/'state.json',state)

    def _deliver_automatic(self,pid):
        with self.lock:
            folder, project, state=self._load(pid)
            if any(c['status']!='approved' or not self._es_checked(project,state,c) for c in state['chunks']):
                raise ValueError('A revisão bilíngue precisa cobrir todo o escopo antes da entrega.')
            if self._warnings(project,state):
                raise ValueError('Há alertas de variante regional ou glossário. Confira os trechos e retome antes da entrega automática.')
            files={language:self._export(pid,language) for language in ('pt-BR','es')}
            state['automatic_result']={'revision':state['revision'],'files':files,'completed_at':time.time(),
                                       'mode':'automatic','locale':'es-419'}
            notes=self._editorial_notes(project,state)
            if notes:
                notes_path=folder/'deliverables'/'observacoes-editoriais.json'
                save_json(notes_path,{'revision':state['revision'],'notes':notes})
                state['automatic_result']['notes_path']=str(notes_path)
            state['audit'].append({'action':'automatic-delivery','at':time.time(),'revision':state['revision']})
            save_json(folder/'state.json',state)

    def review_chunk(self, pid, chunk_id):
        with self.lock: self._idle()
        self._operate(pid,chunk_id,'review')

    def approve(self, pid, chunk_id, proposal_id, *, revised=None):
        with self.lock:
            self._idle(); folder, project, state = self._load(pid)
            chunk = next((c for c in state['chunks'] if c['id']==chunk_id),None)
            if not chunk or chunk['status'] != 'ready' or chunk.get('proposal_id') != proposal_id:
                raise ValueError('A proposta mudou. Atualize a tela antes de aprovar.')
            if revised is not None:
                if not isinstance(revised,dict) or set(revised) != set(chunk['revised']) or any(not isinstance(v,str) or not v.strip() for v in revised.values()):
                    raise ValueError('O ajuste deve manter todos os parágrafos do trecho.')
                source={str(p['id']):p['text'] for p in project['document']['paragraphs']}
                for eid,text in revised.items(): self._validate_breaks(source[eid],text)
                chunk['revised'] = revised
            chunk['status'] = 'approved'; chunk['approval_mode']='automatic'; chunk['approved_at'] = time.time(); state['revision'] += 1
            state['audit'].append({'action':'approve','chunk':chunk_id,'proposal_id':proposal_id,'at':time.time()})
            save_json(folder / 'state.json',state)

    def approve_all(self, pid, *, expected_revision=None):
        with self.lock:
            self._idle(); folder, project, state = self._load(pid)
            if expected_revision is not None and state['revision'] != expected_revision:
                raise ValueError('As propostas mudaram. Confira a revisão antes de aprovar.')
            for chunk in state['chunks']:
                if chunk['status']=='ready':
                    chunk['status']='approved'; chunk['approval_mode']='automatic'; chunk['approved_at']=time.time()
            state['revision'] += 1
            state['audit'].append({'action':'approve-all','at':time.time()})
            save_json(folder / 'state.json',state)

    def reject(self, pid, chunk_id, proposal_id, reason):
        with self.lock:
            self._idle(); folder, project, state = self._load(pid)
            chunk = next((c for c in state['chunks'] if c['id']==chunk_id),None)
            if not chunk or chunk['status']!='ready' or chunk.get('proposal_id')!=proposal_id:
                raise ValueError('A proposta mudou. Atualize a tela.')
            if not isinstance(reason,str) or not reason.strip(): raise ValueError('Informe um motivo para recusar.')
            state['audit'].append({'action':'reject','chunk':chunk_id,'proposal':copy.deepcopy(chunk),'reason':reason,'at':time.time()})
            chunk.update(status='rejected', feedback=reason.strip()); state['revision']+=1
            save_json(folder/'state.json',state)

    def reopen(self, pid, chunk_id):
        with self.lock:
            self._idle(); folder, project, state = self._load(pid)
            chunk = next((c for c in state['chunks'] if c['id']==chunk_id),None)
            if not chunk or chunk['status']!='approved': raise ValueError('Selecione um trecho aprovado.')
            state['audit'].append({'action':'reopen','chunk':chunk_id,'previous':copy.deepcopy(chunk),'at':time.time()})
            chunk['status']='ready'; chunk['proposal_id']=uuid.uuid4().hex; chunk.pop('translations',None)
            state['revision']+=1; save_json(folder/'state.json',state)

    def _targets(self, state, task):
        if not state['chunks']: raise ValueError('Selecione o escopo e salve antes de iniciar.')
        if task=='automatic': return [c['id'] for c in state['chunks']]
        if task=='review': return [c['id'] for c in state['chunks'] if c['status'] in {'pending','rejected'}]
        if task!='translate': raise ValueError('Operação de lote inválida.')
        if any(c['status']!='approved' for c in state['chunks']):
            raise ValueError('Aprove toda a revisão do escopo escolhido antes de traduzir.')
        return [c['id'] for c in state['chunks'] if not c.get('translations')]

    def run_sync(self, pid, task, *, limit=None):
        if task not in {'review','translate'}: raise ValueError('Use start para o processamento completo.')
        _, _, state = self._load(pid)
        targets = self._targets(state,task)
        if limit is not None: targets = targets[:limit]
        for chunk in targets: self._operate(pid,chunk,task)
        return {'processed':len(targets)}

    def save_job(self,pid,job):
        save_json(self._folder(pid)/'job.json',job)

    def record_response_retry(self, pid, chunk_id, phase, reason):
        with self.lock:
            folder, _, state = self._load(pid)
            state['audit'].append({'action':'response-retry','chunk':chunk_id,'phase':phase,'attempt':2,
                                   'reason':reason,'model':self.model,'prompt_version':book_prompts.VERSION,'at':time.time()})
            state['revision'] += 1
            save_json(folder/'state.json',state)

    def record_problem(self, pid, problem):
        with self.lock:
            folder, _, state=self._load(pid)
            state['audit'].append({'action':'processing-problem', **problem, 'at':time.time()})
            state['revision']+=1
            save_json(folder/'state.json',state)

    def start(self, pid, task, *, limit=None, chunk_id=None):
        if limit is not None and (type(limit) is not int or not 1 <= limit <= 100000):
            raise ValueError('O limite deve ser um inteiro positivo.')
        with self.lock:
            self._idle(); folder, _, state = self._load(pid)
            targets = self._targets(state,task)
            if task=='automatic' and (limit is not None or chunk_id is not None):
                raise ValueError('O processamento automático usa todo o escopo selecionado; limite de lote pertence ao modo manual.')
            if chunk_id:
                if chunk_id not in targets: raise ValueError('Este trecho não está disponível para a operação.')
                targets = [chunk_id]
            if limit is not None: targets = targets[:limit]
            job = {'id':uuid.uuid4().hex, 'project_id':pid, 'task':task, 'status':'running', 'total':len(targets),
                   'processed':0, 'started_at':time.time(), 'stop_requested':False, 'message':'Preparando…'}
            self.active_job = job
            save_json(folder/'job.json',job)
            self.thread = Thread(target=self._run_job,args=(pid,targets,job),daemon=True)
            self.thread.start()
            return copy.deepcopy(job)

    def _run_job(self, pid, targets, job):
        folder = self._folder(pid)
        try:
            if job['task']=='automatic':
                run_automatic(self,pid,job)
                return
            for chunk_id in targets:
                with self.lock:
                    if job['stop_requested']: break
                    job['current_chunk']=chunk_id; job['message']=f'Trecho {job["processed"]+1} de {job["total"]}'
                    save_json(folder/'job.json',job)
                self._operate(pid,chunk_id,job['task'])
                with self.lock:
                    job['processed']+=1; save_json(folder/'job.json',job)
            job['status']='paused' if job['stop_requested'] else 'completed'
            job['message']='Progresso salvo. Você pode retomar.' if job['stop_requested'] else 'Lote concluído.'
        except Exception as error:
            job['status']='failed'
            job['message']=str(error) if isinstance(error,ValueError) else 'A IA não concluiu este trecho. Confira o Codex e retome; o progresso foi salvo.'
        finally:
            with self.lock:
                job['finished_at']=time.time(); save_json(folder/'job.json',job); self.active_job=None

    def stop(self, pid):
        with self.lock:
            if not self.active_job or self.active_job['project_id'] != pid: raise ValueError('Não há lote ativo neste trabalho.')
            self.active_job['stop_requested']=True; self.active_job['status']='stopping'
            self.active_job['message']='Parando após concluir as operações em andamento…'
            save_json(self._folder(pid)/'job.json',self.active_job)

    def _warnings(self, project, state, *, chunk_id=None):
        warnings = []
        for chunk in state['chunks']:
            if chunk_id is not None and chunk['id']!=chunk_id: continue
            for text in chunk.get('translations',{}).values():
                if re.search(r'\b(vosotros|vosotras|vuestro|vuestra)\b',text,re.I):
                    warnings.append({'chunk_id':chunk['id'],'message':'Confira o uso de formas próprias do espanhol da Espanha.'}); break
            missing=set()
            for pid,pt in chunk.get('revised',{}).items():
                es=chunk.get('translations',{}).get(pid,'')
                if not es: continue
                for term,expected in source_terms(pt,self._glossary(project,state)):
                    if not contains_target(es,expected): missing.add((term,expected))
            for term,expected in sorted(missing):
                warnings.append({'chunk_id':chunk['id'],'message':f'Confira a tradução do termo “{term}”: esperado “{expected}”.'})
        return warnings

    def update_glossary(self,pid,glossary,expected_revision):
        with self.lock:
            self._idle(); folder, project, state = self._load(pid)
            if state['revision']!=expected_revision: raise ValueError('O glossário mudou. Atualize a tela antes de salvar.')
            if not isinstance(glossary,dict) or len(glossary)>1000 or any(not isinstance(k,str) or not isinstance(v,str) or not k.strip() or not v.strip() for k,v in glossary.items()):
                raise ValueError('Relacione os termos em português a termos não vazios em espanhol.')
            before=self._glossary(project,state)
            changed={k for k in set(before)|set(glossary) if before.get(k)!=glossary.get(k)}
            invalidated=0
            for chunk in state['chunks']:
                pt='\n'.join(chunk.get('revised',{}).values()).casefold()
                if chunk.get('translations') and any(term.casefold() in pt for term in changed):
                    chunk.pop('translations'); invalidated+=1
            state['audit'].append({'action':'glossary','previous':before,'new':glossary,'invalidated_chunks':invalidated,'at':time.time()})
            state['terms']={}; state['glossary_override']=glossary; state['revision']+=1
            save_json(folder/'state.json',state)
            return {'ok':True,'invalidated_chunks':invalidated}

    def save_translation(self, pid, chunk_id, translations, expected_revision):
        with self.lock:
            self._idle(); folder, project, state = self._load(pid)
            if state['revision'] != expected_revision: raise ValueError('A tradução mudou. Atualize a tela antes de salvar.')
            chunk = next((c for c in state['chunks'] if c['id']==chunk_id),None)
            if not chunk or not chunk.get('translations'): raise ValueError('Gere a tradução do trecho antes de ajustar.')
            if not isinstance(translations,dict) or set(translations)!=set(chunk['translations']) or any(not isinstance(t,str) or not t.strip() for t in translations.values()):
                raise ValueError('O ajuste deve manter todos os parágrafos traduzidos.')
            for eid,text in translations.items(): self._validate_breaks(chunk['revised'][eid],text)
            state['audit'].append({'action':'edit-translation','chunk':chunk_id,'previous':chunk['translations'],'at':time.time()})
            chunk['translations']=translations; state['revision']+=1
            save_json(folder/'state.json',state)

    @staticmethod
    def _validate_breaks(original,changed):
        if re.findall(r'[\n\t]',original)!=re.findall(r'[\n\t]',changed):
            raise ValueError('Mantenha as quebras internas e tabulações de cada parágrafo. Gere novamente ou ajuste o texto.')

    @classmethod
    def _validate_model_breaks(cls, original, changed):
        try:
            cls._validate_breaks(original,changed)
        except ValueError as error:
            raise InvalidModelResponse(str(error)) from error

    @staticmethod
    def _validate_word(output):
        with zipfile.ZipFile(output) as archive:
            if sum(i.file_size for i in archive.infolist()) > MAX_ARCHIVE:
                raise ValueError('O Word gerado excede o limite descompactado de 256 MB.')
            if archive.testzip() is not None: raise ValueError('O Word gerado contém um membro inválido.')
            for name in archive.namelist():
                if name.endswith(('.xml','.rels')): parse_xml(archive.read(name))

    def export(self, pid, language):
        with self.lock:
            self._idle()
            return self._export(pid,language)

    @staticmethod
    def _download_filename(project, language):
        original=project['destination_filename'] if language=='es' and project['destination_filename'] else project['filename']
        return f'{Path(original).stem} REVISADO.docx'

    def download_filename(self, pid, language):
        if language not in {'pt-BR','es'}: raise ValueError('Idioma inválido.')
        with self.lock:
            _,project,_=self._load(pid)
            return self._download_filename(project,language)

    def _export(self, pid, language):
        with self.lock:
            folder, project, state = self._load(pid)
            if language not in {'pt-BR','es'}: raise ValueError('Idioma inválido.')
            if any(c['status']!='approved' for c in state['chunks']): raise ValueError('Aprove toda a revisão antes de exportar a versão final.')
            if language=='es' and any(not c.get('translations') for c in state['chunks']): raise ValueError('Traduza todos os trechos antes de exportar o espanhol.')
            values = {p['id']:c['translations' if language=='es' else 'revised'][str(p['id'])]
                      for c in state['chunks'] for p in project['document']['paragraphs'] if p['id'] in c['paragraph_ids']}
            output = folder / 'deliverables' / ('livro-revisado-ptbr.docx' if language=='pt-BR' else 'livro-espanhol-latinoamericano.docx')
            settings = project['settings']
            sections = [s for s in project['document']['sections'] if s['key'] in settings['section_ids']]
            if language=='es' and project['destination']:
                splice_sections(folder/'source.docx',folder/'destination.docx',output,sections,values)
            else:
                only = {pid for s in sections for pid in range(s['start'],s['end']+1)} if language=='es' and settings['scope']=='sections' else None
                edit_document(folder/'source.docx',output,values,only_ids=only,language='es-MX' if language=='es' else None)
            self._validate_word(output)
            manifest = {'project':pid,'language':language,'source_sha256':project['document']['sha256'],
                        'destination_sha256':project['destination']['sha256'] if project['destination'] else None,
                        'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(), 'revision':state['revision'],
                        'paragraph_count':len(values),'model':self.model,'reasoning_effort':'low',
                        'locale':'es-419','warnings':self._warnings(project,state),'at':time.time(),
                        'checked_paragraphs':self._progress(project,state)['checked_paragraphs']}

            save_json(output.with_suffix('.manifest.json'),manifest)
            return {'path':str(output),'filename':self._download_filename(project,language),'paragraph_count':len(values),
                    'download_url':f'/downloads/books/{pid}/{language}'}

    def download_path(self, pid, language):
        if language not in {'pt-BR','es'}: raise ValueError('Idioma inválido.')
        folder, project, state = self._load(pid)
        name = 'livro-revisado-ptbr.docx' if language=='pt-BR' else 'livro-espanhol-latinoamericano.docx'
        output = folder/'deliverables'/name
        manifest = output.with_suffix('.manifest.json')
        if not output.is_file() or not manifest.is_file(): raise ValueError('Gere o Word antes de baixar.')
        if read_json(manifest)['revision'] != state['revision']: raise ValueError('O livro mudou. Gere novamente o Word para baixar a versão atual.')
        return output
