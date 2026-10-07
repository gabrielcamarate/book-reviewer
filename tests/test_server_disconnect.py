import io
import json
import socket
import struct
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock
from urllib.request import urlopen

from revisor.server import Handler, create_server


class DisconnectedClientTest(unittest.TestCase):
    def handler(self):
        handler = object.__new__(Handler)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.close_connection = False
        return handler

    def test_disconnection_while_writing_headers_or_body_closes_only_request(self):
        for phase in ('end_headers', 'write'):
            for error in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                with self.subTest(phase=phase, error=error):
                    handler = self.handler()
                    operation = handler.end_headers if phase == 'end_headers' else handler.wfile.write
                    operation.side_effect = error('client disconnected')
                    handler.json(200, {'projects': []})
                    self.assertTrue(handler.close_connection)

    def test_unrelated_write_failure_is_not_silenced(self):
        handler = self.handler()
        handler.wfile.write.side_effect = OSError('unrelated failure')
        with self.assertRaisesRegex(OSError, 'unrelated failure'):
            handler.json(200, {'projects': []})

    def test_post_success_does_not_send_a_second_error_response_after_disconnect(self):
        handler = self.handler()
        handler.path = '/api/books/p1/stop'
        handler.headers = Mock()
        handler.headers.get_content_type.return_value = 'application/json'
        handler.headers.get.return_value = '2'
        handler.rfile = io.BytesIO(b'{}')
        handler.local_request = Mock(return_value=True)
        handler.workspace = Mock()
        handler.wfile.write.side_effect = BrokenPipeError('client disconnected')
        handler.do_POST()
        handler.workspace.stop.assert_called_once_with('p1')
        handler.send_response.assert_called_once_with(200)
        self.assertTrue(handler.close_connection)

    def test_real_reset_does_not_report_server_error_and_next_request_succeeds(self):
        with tempfile.TemporaryDirectory() as temp:
            server = create_server(Path(temp), port=0)
            entered = threading.Event(); release = threading.Event(); finished = threading.Event()
            errors = []
            server.handle_error = lambda *_args: errors.append('request exception')
            original_handler = server.RequestHandlerClass
            def tracked_handler(*args, **kwargs):
                try:
                    original_handler(*args, **kwargs)
                finally:
                    finished.set()
            server.RequestHandlerClass = tracked_handler
            def delayed_list():
                entered.set()
                if not release.wait(2):
                    raise TimeoutError('fixture timeout')
                return []
            server.workspace.list_projects = delayed_list
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                with socket.create_connection(server.server_address, timeout=2) as client:
                    client.sendall(b'GET /api/books HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n')
                    self.assertTrue(entered.wait(1))
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                release.set()
                self.assertTrue(finished.wait(2))
                self.assertEqual(errors, [])
                with urlopen(f'http://127.0.0.1:{server.server_port}/api/books', timeout=2) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response)['projects'], [])
                self.assertEqual(errors, [])
            finally:
                release.set(); server.shutdown(); server.server_close(); thread.join()


class InstallableAppTest(unittest.TestCase):
    def test_manifest_is_served_as_a_web_app_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            dist = Path(temp) / 'dist'; (dist / 'assets').mkdir(parents=True)
            (dist / 'index.html').write_text('<!doctype html>')
            (dist / 'manifest.webmanifest').write_text('{"name":"Revisor"}')
            server = create_server(Path(temp), port=0, frontend_dist=dist)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/manifest.webmanifest', timeout=3) as response:
                    self.assertEqual(response.headers['Content-Type'], 'application/manifest+json')
                    self.assertEqual(json.loads(response.read())['name'], 'Revisor')
            finally:
                server.shutdown(); server.server_close(); thread.join()
