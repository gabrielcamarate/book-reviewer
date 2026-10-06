"""Isolated browser fixture. No real manuscript or model calls."""
import argparse
import tempfile
from pathlib import Path
from revisor.server import create_server
from revisor.service import ReviewService
from test_service import fixture, fake_runner

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8777)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='revisor-smoke-') as directory:
        root = Path(directory)
        fixture(root)
        print(f'Fixture: {root}', flush=True)
        with create_server(ReviewService(root, runner=fake_runner, model='fixture'), port=args.port) as server:
            try: server.serve_forever()
            except KeyboardInterrupt: pass
