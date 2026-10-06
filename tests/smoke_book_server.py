"""Isolated UI fixture. No real manuscript and no model calls."""
import argparse
import json
import time
from pathlib import Path
from revisor.server import create_server
from revisor.service import ReviewService
from revisor.workspace import BookWorkspace
from test_book_api import runner
from test_book_workflows import fixture

parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True); parser.add_argument('--port',type=int,default=8787)
parser.add_argument('--overlap',choices=['once','always'],help='Inject rejected overlapping edits in the synthetic review.')
parser.add_argument('--erase',choices=['once','always'],help='Inject a rejected paragraph deletion in the synthetic review.')
parser.add_argument('--note',action='store_true',help='Preserved source uncertainty in the synthetic check.')
parser.add_argument('--delay',type=float,default=0,help='Synthetic seconds per operation.')
args=parser.parse_args(); args.root.mkdir(parents=True,exist_ok=True)
fixture(args.root/'Livro de teste.docx'); fixture(args.root/'Livro em espanhol.docx',True)
def smoke_runner(**kwargs):
    data=json.loads(kwargs['prompt'].split('INPUT_JSON\n')[1])
    time.sleep(args.delay)
    if data.get('response_format')=='paragraphs':
        result=runner(**kwargs)
        if args.note and data['task']=='check_pt' and any('estavam' in p['text'] for p in data['paragraphs']):
            result['notes']=['Termo fictício do original preservado para decisão da autora.']
        if data['task']=='review' and not (args.root/'recover').exists() and any('estavam' in p['text'] for p in data['paragraphs']):
            if args.erase and (args.erase=='always' or not data.get('validation_feedback')): result['paragraphs'][0]['text']=''
            elif args.overlap and (args.overlap=='always' or not data.get('validation_feedback')): result['paragraphs'].append(dict(result['paragraphs'][0]))
        return result
    if args.erase and data['task']=='review' and (args.erase=='always' or not data.get('validation_feedback')):
        p=next((p for p in data['paragraphs'] if 'estavam' in p['text']),None)
        if p:
            return {'edits':[{'paragraph_id':p['id'],'original':p['text'],'replacement':'','occurrence':0,
                             'reason':'Fixture.','category':'teste'}]}
    if args.overlap and data['task']=='review' and (args.overlap=='always' or not data.get('validation_feedback')):
        p=next((p for p in data['paragraphs'] if 'estavam' in p['text']),None)
        if p:
            edit={'paragraph_id':p['id'],'original':'estavam','replacement':'estava','occurrence':0,
                  'reason':'Concordância.','category':'gramática'}
            return {'edits':[edit,edit]}
    return runner(**kwargs)

workspace=BookWorkspace(args.root,runner=smoke_runner)
with create_server(ReviewService(args.root),workspace=workspace,port=args.port) as server:
    print(f'Fixture pronta em http://127.0.0.1:{server.server_port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
