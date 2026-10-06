"""Local HTTP transport: JSON API and the single built React interface."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import tempfile
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs

from revisor.core.repository_validation import validate_repository_state
from revisor.service import ReviewService, StaleReview
from revisor.workspace import BookWorkspace
from revisor.provider import DEFAULT_MODEL

LOCAL_HOSTS = {'127.0.0.1', 'localhost', '::1'}
ACTIONS = {
    '/api/simple-home/review': 'review', '/api/simple-home/accept': 'accept',
    '/api/simple-home/reject': 'reject', '/api/translate': 'translate',
    '/api/export': 'export', '/api/rollback': 'rollback',
}


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, service: ReviewService, workspace: BookWorkspace, frontend_dist: Path, **kwargs):
        self.service = service
        self.workspace = workspace
        self.frontend_dist = frontend_dist.resolve()
        super().__init__(*args, **kwargs)

    def log_message(self, *_args):
        pass  # Do not log manuscript content or request bodies.

    def send_bytes(self, status: int, payload: bytes, content_type: str, **headers):
        try:
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cache-Control', 'no-store')
            for name, value in headers.items():
                self.send_header(name.replace('_', '-'), value)
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Fetch cancellation/navigation can close the socket before the response.
            # The action may already have succeeded; do not send a second response.
            self.close_connection = True

    def json(self, status: int, data):
        self.send_bytes(status, json.dumps(data, ensure_ascii=False).encode(), 'application/json; charset=utf-8')

    def local_request(self) -> bool:
        host = urlsplit('//' + self.headers.get('Host', '')).hostname
        origin = self.headers.get('Origin')
        if host not in LOCAL_HOSTS or (origin and urlsplit(origin).hostname not in LOCAL_HOSTS):
            self.json(403, {'error': 'A interface está disponível apenas no computador local.'})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        path = unquote(urlsplit(self.path).path)
        if path == '/api/books':
            with self.workspace.lock:
                active_id = self.workspace.active_job['project_id'] if self.workspace.active_job else None
            self.json(200, {'projects':self.workspace.list_projects(), 'legacy_available':(self.service.root/'manuscript/chunks/index.json').is_file(),
                            'model':self.workspace.model, 'reasoning_effort':'low',
                            'active_project_id':active_id})
            return
        if path.startswith('/api/books/'):
            try:
                chunk = parse_qs(urlsplit(self.path).query).get('chunk',[None])[0]
                self.json(200,self.workspace.detail(path.split('/')[-1],chunk))
            except ValueError as error:
                self.json(400,{'error':str(error)})
            return
        if path.startswith('/downloads/books/'):
            try:
                _, _, _, pid, language = path.split('/')
                file = self.workspace.download_path(pid,language)
                self.send_bytes(200,file.read_bytes(),'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                Content_Disposition=f'attachment; filename="{file.name}"')
            except ValueError as error:
                self.json(400,{'error':str(error)})
            return
        if path == '/api/simple-home':
            try:
                self.json(200, self.service.state())
            except (OSError, ValueError):
                self.json(500, {'error': 'Não foi possível ler o estado editorial. Execute o comando check.'})
            return
        if path == '/healthz':
            self.json(200, {'ready': True})
            return
        downloads = {'/downloads/ptbr': 'deliverables/ptbr/livro-ptbr.docx',
                     '/downloads/es': 'deliverables/es/livro-es.docx'}
        if path in downloads:
            file = self.service.root / downloads[path]
            if not file.is_file():
                self.json(404, {'error': 'Gere o arquivo antes de baixá-lo.'})
                return
            self.send_bytes(200, file.read_bytes(),
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            Content_Disposition=f'attachment; filename="{file.name}"')
            return
        dist = self.frontend_dist
        file = (dist / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
        if path != '/' and not path.startswith('/assets/'):
            self.json(404, {'error': 'Rota não encontrada.'})
        elif not file.is_relative_to(dist) or not file.is_file():
            self.json(503 if path == '/' else 404, {'error': 'Interface não compilada. Execute pnpm build em frontend/ ou use scripts/dev.sh.'})
        else:
            self.send_bytes(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or 'application/octet-stream')

    def do_POST(self):
        if not self.local_request():
            return
        action = ACTIONS.get(urlsplit(self.path).path)
        book_action = urlsplit(self.path).path.startswith('/api/books/')
        if action is None and not book_action:
            self.json(404, {'error': 'Rota não encontrada.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            maximum = 96 * 1024 * 1024 if self.path == '/api/books/import' else 1024 * 1024
            if not 0 <= length <= maximum or self.headers.get_content_type() != 'application/json':
                raise ValueError('Envie um objeto JSON válido.')
            data = json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(data, dict):
                raise ValueError('Envie um objeto JSON válido.')
            result = self.book_action(data) if book_action else self.service.perform(action, data)
            if action == 'export':
                result['download_url'] = '/downloads/ptbr' if data.get('language', 'pt-BR') == 'pt-BR' else '/downloads/es'
            self.json(200, result)
        except StaleReview as error:
            self.json(409, {'error': str(error)})
        except (ValueError, FileNotFoundError) as error:
            self.json(400, {'error': str(error)})
        except (RuntimeError, TimeoutError):
            self.json(502, {'error': 'O modelo não concluiu a operação. O progresso já salvo foi preservado.'})
        except Exception:
            self.json(500, {'error': 'A operação falhou. Confira o estado antes de repetir.'})

    def book_action(self, data):
        path = urlsplit(self.path).path
        if path == '/api/books/import':
            with tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)
                def upload(key):
                    payload = data.get(key)
                    if payload is None: return None
                    if not isinstance(payload,dict) or not isinstance(payload.get('name'),str) or not isinstance(payload.get('data'),str):
                        raise ValueError('Selecione um arquivo Word válido.')
                    name = Path(payload['name']).name
                    if not name.lower().endswith('.docx'): raise ValueError('Selecione um arquivo .docx.')
                    try: content = base64.b64decode(payload['data'],validate=True)
                    except ValueError as error: raise ValueError('O upload do Word está inválido.') from error
                    if len(content) > 32*1024*1024: raise ValueError('Cada Word deve ter até 32 MB.')
                    target = folder / key / name; target.parent.mkdir(); target.write_bytes(content)
                    return target
                source = upload('source'); destination = upload('destination')
                if source is None: raise ValueError('Selecione o manuscrito em português.')
                result = self.workspace.import_book(source,destination=destination,name=data.get('name'))
                if destination:
                    detail = self.workspace.detail(result['id'])
                    keys = [s['key'] for s in detail['sections'] if s['key'] in {'epilogo','posfacio'}]
                    if keys: self.workspace.configure(result['id'],{'scope':'sections','section_ids':keys})
                return result
        pieces = path.strip('/').split('/')
        if len(pieces)!=4: raise ValueError('Operação de livro inválida.')
        _, _, pid, operation = pieces
        if operation=='configure': return self.workspace.configure(pid,data)
        if operation=='start': return self.workspace.start(pid,data.get('task'),limit=data.get('limit'),chunk_id=data.get('chunk_id'))
        if operation=='stop': self.workspace.stop(pid)
        elif operation=='approve': self.workspace.approve(pid,data.get('chunk_id'),data.get('proposal_id'),revised=data.get('revised'))
        elif operation=='approve-all': self.workspace.approve_all(pid,expected_revision=data.get('revision'))
        elif operation=='reject': self.workspace.reject(pid,data.get('chunk_id'),data.get('proposal_id'),data.get('reason'))
        elif operation=='reopen': self.workspace.reopen(pid,data.get('chunk_id'))
        elif operation=='export': return self.workspace.export(pid,data.get('language'))
        elif operation=='save-translation': self.workspace.save_translation(pid,data.get('chunk_id'),data.get('translations'),data.get('revision'))
        elif operation=='glossary': return self.workspace.update_glossary(pid,data.get('glossary'),data.get('revision'))
        else: raise ValueError('Operação de livro desconhecida.')
        return {'ok':True}


class LocalServer(ThreadingHTTPServer):
    def server_close(self):
        super().server_close()
        self.workspace.close()


def create_server(service: ReviewService, *, host='127.0.0.1', port=8766, frontend_dist: Path | None = None, workspace=None):
    if host not in {'127.0.0.1', 'localhost'}:
        raise ValueError('Use 127.0.0.1 ou localhost. Exposição remota não faz parte deste aplicativo local.')
    dist = frontend_dist if frontend_dist is not None else Path(__file__).resolve().parents[2] / 'frontend/dist'
    workspace = workspace or BookWorkspace(service.root,runner=service.runner,model=service.model)
    try:
        server = LocalServer((host, port), partial(Handler, service=service, workspace=workspace, frontend_dist=dist))
    except Exception:
        workspace.close()
        raise
    server.workspace = workspace
    server.daemon_threads = True
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description='API local do revisor e tradutor.')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--model', default=DEFAULT_MODEL)
    args = parser.parse_args()
    validation = validate_repository_state(root_dir=args.root)
    if (args.root/'manuscript').is_dir() and not validation['ok']:
        parser.error('; '.join(validation['errors']))
    try:
        with create_server(ReviewService(args.root, model=args.model), port=args.port) as server:
            print(f'Revisor: http://127.0.0.1:{server.server_port}/', flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
