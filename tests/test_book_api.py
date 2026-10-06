import base64
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from revisor.server import create_server
from revisor.service import ReviewService
from revisor.workspace import BookWorkspace, read_json, save_json
from test_book_workflows import fixture


def runner(**kwargs):
    data=json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
    if data.get('response_format')=='paragraphs':
        result={'paragraphs':[{'paragraph_id':p['id'],
                'text':p.get('draft',p['text']).replace('estavam','estava') if data['task']=='review' else p['draft'],
                'reason':'Concordância com o sujeito singular.','category':'concordância'} for p in data['paragraphs']]}
        if data['task']!='review': result['issues']=[]
        return result
    if data['task'] in {'check_pt','check_es'}: return {'edits':[], 'issues':[]}
    if data['task']=='review':
        return {'edits':[{'paragraph_id':p['id'],'original':'estavam','occurrence':0,'replacement':'estava','reason':'Concordância com o sujeito singular.','category':'concordância'} for p in data['paragraphs'] if 'estavam' in p['text']]}
    return {'translations':[{'paragraph_id':p['id'],'text':'ES '+p['text']} for p in data['paragraphs']], 'terms':[]}


class BookApiTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.source=self.root/'pt.docx'; fixture(self.source)
        self.dest=self.root/'es.docx'; fixture(self.dest,True)
        self.workspace=BookWorkspace(self.root,runner=runner)
        self.server=create_server(ReviewService(self.root),port=0,workspace=self.workspace)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.temp.cleanup()

    def request(self,path,data=None):
        req=Request(self.url+path, data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=3) as response: return response.status,response.read()
        except HTTPError as response:
            with response: return response.code,response.read()

    def json(self,path,data=None):
        status,body=self.request(path,data); self.assertEqual(status,200,body); return json.loads(body)

    def wait_job(self,pid):
        end=time.monotonic()+3
        while time.monotonic()<end:
            detail=self.json('/api/books/'+pid)
            if detail['job']['status'] not in {'running','stopping'}: return detail
            time.sleep(.01)
        self.fail('Background job did not complete')

    def test_upload_background_review_approve_translate_and_both_downloads(self):
        payload=lambda p:{'name':p.name,'data':base64.b64encode(p.read_bytes()).decode()}
        pid=self.json('/api/books/import',{'source':payload(self.source),'destination':payload(self.dest)})['id']
        detail=self.json('/api/books/'+pid)
        self.assertEqual(detail['settings']['scope'],'sections')
        self.assertEqual(detail['settings']['section_ids'],['epilogo','posfacio'])
        self.assertEqual(detail['model'],'gpt-6.1-sol')
        self.json(f'/api/books/{pid}/start',{'task':'review'})
        detail=self.wait_job(pid); self.assertEqual(detail['job']['status'],'completed')
        self.json(f'/api/books/{pid}/approve-all',{'revision':detail['revision']})
        self.json(f'/api/books/{pid}/start',{'task':'translate'})
        detail=self.wait_job(pid); self.assertEqual(detail['job']['status'],'completed')
        for language in ['pt-BR','es']:
            result=self.json(f'/api/books/{pid}/export',{'language':language})
            status,body=self.request(result['download_url']); self.assertEqual(status,200); self.assertTrue(body.startswith(b'PK'))
        chunk=detail['current']['id']
        self.json(f'/api/books/{pid}/reopen',{'chunk_id':chunk})
        self.assertEqual(self.request(result['download_url'])[0],400)

    def test_automatic_api_delivers_both_words_without_approval_requests(self):
        pid=self.workspace.import_book(self.source)['id']
        self.json(f'/api/books/{pid}/start',{'task':'automatic'})
        detail=self.wait_job(pid)
        self.assertEqual(detail['job']['status'],'completed')
        self.assertEqual(detail['progress']['checked_percent'],100)
        for artifact in detail['automatic_result']['files'].values():
            status,body=self.request(artifact['download_url'])
            self.assertEqual(status,200); self.assertTrue(body.startswith(b'PK'))

    def test_automatic_api_recovers_retired_response_format_and_records_retry(self):
        calls = []
        def recover(**kwargs):
            data = json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1]); calls.append(data)
            if data['task'] == 'review' and not data.get('validation_feedback'):
                p = data['paragraphs'][0]
                edit = {'paragraph_id':p['id'],'original':p['text'],'replacement':p['text'],
                        'occurrence':0,'reason':'Fixture.','category':'teste'}
                return {'edits':[edit,edit]}
            return runner(**kwargs)
        self.workspace.runner = recover
        pid = self.workspace.import_book(self.source)['id']
        self.json(f'/api/books/{pid}/start', {'task':'automatic'})
        detail = self.wait_job(pid)
        self.assertEqual(detail['job']['status'], 'completed', detail['job']['message'])
        self.assertEqual(detail['job']['response_retries'], 4)
        self.assertEqual(sum(d['task']=='review' for d in calls), 8)
        for artifact in detail['automatic_result']['files'].values():
            self.assertEqual(self.request(artifact['download_url'])[0], 200)

    def test_invalid_upload_ids_and_limits_do_not_create_jobs(self):
        self.assertEqual(self.request('/api/books/import',{'source':{'name':'pt.docx','data':'invalid@@'}})[0],400)
        self.assertEqual(self.json('/api/books')['projects'],[])
        pid=self.workspace.import_book(self.source)['id']
        for limit in [-1,True,'10',0]: self.assertEqual(self.request(f'/api/books/{pid}/start',{'task':'review','limit':limit})[0],400)
        self.assertEqual(self.request('/api/books/../../etc/passwd')[0],400)


class JobReliabilityTest(unittest.TestCase):
    def test_cancel_saves_current_chunk_resume_skips_it_and_lock_prevents_second_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'pt.docx'; fixture(source)
            entered=threading.Event(); release=threading.Event(); calls=[]
            def slow(**kwargs):
                calls.append(kwargs); entered.set(); release.wait(3); return runner(**kwargs)
            ws=BookWorkspace(root,runner=slow)
            try:
                with self.assertRaises(ValueError): BookWorkspace(root)
                pid=ws.import_book(source)['id']; ws.start(pid,'review'); self.assertTrue(entered.wait(1))
                self.assertEqual(ws.detail(pid)['job']['processed'],0)
                with self.assertRaises(ValueError): ws.configure(pid,{'scope':'whole'})
                ws.stop(pid); release.set(); ws.thread.join(2)
                self.assertEqual(ws.detail(pid)['job']['status'],'paused')
                self.assertEqual(ws.detail(pid)['progress']['ready_chunks'],1)
                ws.runner=runner; ws.start(pid,'review'); ws.thread.join(2)
                self.assertEqual(ws.detail(pid)['job']['status'],'completed')
                self.assertEqual(ws.detail(pid)['progress']['pending_chunks'],0)
            finally: release.set(); ws.close()

    def test_restart_marks_live_job_interrupted_and_preserves_book_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'pt.docx'; fixture(source)
            ws=BookWorkspace(root,runner=runner); pid=ws.import_book(source)['id']; ws.run_sync(pid,'review',limit=1)
            folder=ws._folder(pid); state_before=read_json(folder/'state.json')
            save_json(folder/'job.json',{'id':'old','status':'running','task':'review','processed':1,'total':3})
            ws.close(); ws=BookWorkspace(root,runner=runner)
            try:
                self.assertEqual(ws.detail(pid)['job']['status'],'interrupted')
                self.assertEqual(read_json(folder/'state.json'),state_before)
                ws.run_sync(pid,'review'); self.assertEqual(ws.detail(pid)['progress']['pending_chunks'],0)
            finally: ws.close()
