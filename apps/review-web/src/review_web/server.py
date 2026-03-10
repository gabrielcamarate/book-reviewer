from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from review_web.dashboard import build_dashboard_state, render_dashboard_html

DashboardLoader = Callable[[], dict[str, object]]


def _build_loader(
    *,
    chunks_dir: Path,
    consolidated_dir: Path,
    reports_dir: Path,
    reviews_ptbr_dir: Path,
    reviews_es_dir: Path,
    deliverables_dir: Path,
) -> DashboardLoader:
    def _load() -> dict[str, object]:
        return build_dashboard_state(
            chunks_dir=chunks_dir,
            consolidated_dir=consolidated_dir,
            reports_dir=reports_dir,
            reviews_ptbr_dir=reviews_ptbr_dir,
            reviews_es_dir=reviews_es_dir,
            deliverables_dir=deliverables_dir,
        )

    return _load


class DashboardHandler(BaseHTTPRequestHandler):
    dashboard_loader: DashboardLoader | None = None

    def do_GET(self) -> None:  # noqa: N802
        if self.dashboard_loader is None:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "dashboard loader not configured")
            return

        state = self.dashboard_loader()
        if self.path == "/":
            payload = render_dashboard_html(state).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/api/dashboard":
            payload = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def build_handler(dashboard_loader: DashboardLoader) -> type[DashboardHandler]:
    class ConfiguredDashboardHandler(DashboardHandler):
        pass

    ConfiguredDashboardHandler.dashboard_loader = staticmethod(dashboard_loader)
    return ConfiguredDashboardHandler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local-first editorial review web dashboard."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind.")
    parser.add_argument("--chunks-dir", type=Path, default=Path("manuscript/chunks"))
    parser.add_argument("--consolidated-dir", type=Path, default=Path("manuscript/consolidated"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--reviews-ptbr-dir", type=Path, default=Path("reviews/ptbr"))
    parser.add_argument("--reviews-es-dir", type=Path, default=Path("reviews/es"))
    parser.add_argument("--deliverables-dir", type=Path, default=Path("deliverables"))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    handler = build_handler(
        _build_loader(
        chunks_dir=args.chunks_dir,
        consolidated_dir=args.consolidated_dir,
        reports_dir=args.reports_dir,
        reviews_ptbr_dir=args.reviews_ptbr_dir,
        reviews_es_dir=args.reviews_es_dir,
        deliverables_dir=args.deliverables_dir,
        )
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        json.dumps(
            {
                "host": args.host,
                "port": args.port,
                "url": f"http://{args.host}:{args.port}/",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
