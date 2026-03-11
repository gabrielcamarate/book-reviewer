#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8765}"
FRONTEND_PORT="${FRONTEND_PORT:-4173}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

cd "$ROOT_DIR"

python3 "$ROOT_DIR/scripts/dev_backend_watch.py" --port "$BACKEND_PORT" &
BACKEND_PID=$!

cd "$ROOT_DIR/frontend"
exec pnpm dev --host 127.0.0.1 --port "$FRONTEND_PORT"
