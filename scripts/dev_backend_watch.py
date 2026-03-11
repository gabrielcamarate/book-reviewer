#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
WATCH_DIRS = (
    ROOT_DIR / "apps" / "review-cli" / "src",
    ROOT_DIR / "apps" / "review-web" / "src",
    ROOT_DIR / "packages" / "docx-adapter" / "src",
    ROOT_DIR / "packages" / "editorial-core" / "src",
    ROOT_DIR / "packages" / "editorial-prompts" / "src",
    ROOT_DIR / "packages" / "editorial-schemas" / "src",
)


def _collect_state() -> dict[str, int]:
    state: dict[str, int] = {}
    for directory in WATCH_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            state[str(path)] = stat.st_mtime_ns
    return state


def _start_server(port: int) -> subprocess.Popen[bytes]:
    command = [
        str(ROOT_DIR / "scripts" / "workspace-python.sh"),
        "-m",
        "review_web.server",
        "--port",
        str(port),
    ]
    return subprocess.Popen(command, cwd=ROOT_DIR)


def _stop_server(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run review_web.server and restart it when Python files change.",
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--interval", type=float, default=0.8)
    args = parser.parse_args()

    server_process = _start_server(args.port)
    watched_state = _collect_state()
    shutting_down = False

    def _handle_signal(signum: int, _frame: object) -> None:
        nonlocal shutting_down
        shutting_down = True
        _stop_server(server_process)
        sys.exit(128 + signum)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print(
        f"[dev-backend] watching Python sources and serving on http://127.0.0.1:{args.port}/",
        flush=True,
    )

    while not shutting_down:
        time.sleep(args.interval)
        current_state = _collect_state()

        if current_state != watched_state:
            print("[dev-backend] change detected, restarting backend...", flush=True)
            _stop_server(server_process)
            server_process = _start_server(args.port)
            watched_state = current_state
            continue

        if server_process.poll() is not None:
            print("[dev-backend] backend exited, restarting...", flush=True)
            server_process = _start_server(args.port)
            watched_state = current_state

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
