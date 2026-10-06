import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from revisor.server import create_server
from revisor.service import ReviewService
from test_service import fixture, fake_runner


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)
        self.static = Path(self.temp.name) / 'app-dist'
        self.static.mkdir()
        (self.static / 'index.html').write_text('<title>Revisor</title>')
        self.server = create_server(ReviewService(self.root, runner=fake_runner), port=0, frontend_dist=self.static)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, data=None, headers=None):
        headers = {'Content-Type': 'application/json', **(headers or {})}
        req = Request(self.url + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            with urlopen(req) as response:
                return response.status, response.read(), response.headers
        except HTTPError as response:
            with response:
                return response.code, response.read(), response.headers

    def test_react_is_only_page_and_legacy_routes_are_gone(self):
        self.assertEqual(self.request('/')[1], b'<title>Revisor</title>')
        self.assertFalse((self.root / 'frontend').exists())
        for path in ['/advanced', '/queue', '/glossary', '/characters', '/api/dashboard', '/../../livro.docx']:
            self.assertEqual(self.request(path)[0], 404)

    def test_http_review_accept_and_download(self):
        state = json.loads(self.request('/api/simple-home')[1])
        self.assertEqual(state['chunk']['id'], 'chunk-1')
        for action in ['review', 'accept']:
            self.assertEqual(self.request('/api/simple-home/' + action, {'chunk_id': 'chunk-1'})[0], 200)
        self.assertEqual(self.request('/api/translate', {})[0], 200)
        payload = json.loads(self.request('/api/export', {'language': 'es'})[1])
        status, body, headers = self.request(payload['download_url'])
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b'PK'))
        self.assertIn('attachment', headers['Content-Disposition'])

    def test_errors_are_json_and_old_screen_is_rejected(self):
        status, body, _ = self.request('/api/simple-home/accept', {'chunk_id': 'old'})
        self.assertEqual(status, 409)
        self.assertIn('error', json.loads(body))
        self.assertEqual(self.request('/api/simple-home/reject', {'chunk_id': 'chunk-1', 'reason': ''})[0], 400)
        self.assertEqual(self.request('/api/simple-home/review', [], {})[0], 400)
        for limit in [0, -1, '1', True]:
            self.assertEqual(self.request('/api/translate', {'max_chunks': limit})[0], 400)

    def test_mutations_reject_external_origin_and_host(self):
        self.assertEqual(self.request('/api/simple-home/review', {'chunk_id': 'chunk-1'}, {'Origin': 'https://evil.example'})[0], 403)
        self.assertEqual(self.request('/api/simple-home', headers={'Host': 'evil.example'})[0], 403)
