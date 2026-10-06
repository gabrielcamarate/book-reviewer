"""Bounded phases that preserve independent results and expose actionable problems."""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from revisor.book_response import EditorialIssues
from revisor.provider import InvalidModelResponse

WORKERS = 4


def _phase(workspace, pid, job, phase, targets, operation):
    with workspace.lock:
        job.update(phase=phase, phase_processed=0, phase_attempted=0, phase_total=len(targets), message='Processamento em andamento.')
        workspace.save_job(pid,job)
    failure=None
    remaining=iter(targets)

    def attempt(chunk):
        try:
            operation(chunk)
        except InvalidModelResponse as error:
            with workspace.lock:
                if job['stop_requested'] or failure is not None: return False
                workspace.record_response_retry(pid,chunk,phase,str(error))
                job['response_retries']=job.get('response_retries',0)+1
                job['message']='Corrigindo uma resposta incompleta. Os demais trechos continuam.'
                workspace.save_job(pid,job)
            try:
                operation(chunk,validation_feedback=str(error))
            except InvalidModelResponse as repeated:
                raise EditorialIssues(f'A resposta continuou inválida após duas tentativas: {repeated} Nenhuma alteração inválida foi aplicada.') from repeated
        return True

    with ThreadPoolExecutor(max_workers=WORKERS,thread_name_prefix='book') as pool:
        pending={}
        def submit_one():
            with workspace.lock:
                if job['stop_requested'] or failure is not None: return
                chunk=next(remaining,None)
                if chunk is not None: pending[pool.submit(attempt,chunk)]=chunk
        for _ in range(WORKERS): submit_one()
        while pending:
            done,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in done:
                chunk=pending.pop(future)
                try:
                    if not future.result(): continue
                    with workspace.lock:
                        job['phase_processed']+=1
                        if phase=='Revisão do espanhol': job['processed']+=1
                except EditorialIssues as error:
                    # Do not starve the rest of the queue over one editorial response.
                    with workspace.lock:
                        problem={'chunk_id':chunk,'phase':phase,'message':str(error)}
                        job['problems'].append(problem)
                        workspace.record_problem(pid,problem)
                        job['message']='Há trechos para conferir. O restante continua sendo processado.'
                except Exception as error:
                    if failure is None:
                        failure=error
                        with workspace.lock: job['failed_chunk']=chunk
                finally:
                    with workspace.lock:
                        job['phase_attempted']+=1
                        workspace.save_job(pid,job)
            for _ in done: submit_one()
    if failure is not None: raise failure
    return not job['stop_requested']


def _attention(job):
    job.update(status='needs_attention',message='O trabalho válido foi salvo. Confira os trechos abaixo ou tente novamente; a entrega aguarda a resolução das pendências.')


def run_automatic(workspace, pid, job):
    job['problems']=[]
    stages=(('Revisão do português','review'),('Validação das correções','check_pt'),
            ('Tradução para espanhol','translate'),('Revisão do espanhol','check_es'))
    for label,task in stages:
        with workspace.lock:
            _,project,state=workspace._load(pid)
            if task=='check_pt': targets=[c['id'] for c in state['chunks'] if c['status']=='ready']
            elif task=='check_es':
                warnings={w['chunk_id'] for w in workspace._warnings(project,state)}
                targets=[c['id'] for c in state['chunks'] if c.get('translations') and (not workspace._es_checked(project,state,c) or c['id'] in warnings)]
                job['processed']=sum(workspace._es_checked(project,state,c) and c['id'] not in targets for c in state['chunks'])
            else: targets=workspace._targets(state,task)
            glossary=workspace._glossary(project,state)
        if task in {'check_pt','check_es'}:
            operation=lambda chunk,validation_feedback='',task=task: workspace._check(pid,chunk,'pt' if task=='check_pt' else 'es',validation_feedback=validation_feedback)
        else:
            operation=lambda chunk,validation_feedback='',task=task,glossary=glossary: workspace._operate(pid,chunk,task,glossary=glossary,validation_feedback=validation_feedback,paragraph_output=task=='review')
        if not _phase(workspace,pid,job,label,targets,operation):
            job.update(status='paused',message='Progresso salvo. Continue de onde parou.')
            return
        if task=='check_pt':
            with workspace.lock:
                _,_,state=workspace._load(pid)
                if any(c['status']!='approved' for c in state['chunks']):
                    _attention(job)
                    return  # No Spanish generation before the entire PT scope is stable.
    with workspace.lock:
        if job['stop_requested']:
            job.update(status='paused',message='Progresso salvo. Continue para preparar os arquivos.')
            return
        _,project,state=workspace._load(pid)
        for warning in workspace._warnings(project,state):
            job['problems'].append(warning | {'phase':'Consistência do espanhol'})
        if job['problems']:
            _attention(job)
            return
        job.update(phase='Preparação dos arquivos',message='Validando os arquivos Word…')
        workspace.save_job(pid,job)
        workspace._deliver_automatic(pid)
        job.update(status='completed',processed=job['total'],message='Português e espanhol revisados. Os arquivos Word estão disponíveis.')
