#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8766}"
FRONTEND_PORT="${FRONTEND_PORT:-4173}"
DATA_ROOT="${REVIEW_ROOT:-$ROOT_DIR}"
cleanup() {
  for pid in "${BACKEND_PID:-}" "${FRONTEND_PID:-}"; do
    if [[ -n "$pid" ]]; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cd "$ROOT_DIR"
python3 - "$BACKEND_PORT" "$FRONTEND_PORT" <<'CHECK'
import socket, sys
for value in sys.argv[1:]:
    port = int(value)
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(('127.0.0.1', port))
        except OSError: sys.exit(f'Porta {port} ocupada. Defina BACKEND_PORT e FRONTEND_PORT ou encerre sua execução anterior.')
CHECK
if [[ ! -x "$ROOT_DIR/frontend/node_modules/.bin/vite" ]]; then
  echo 'Instale as dependências: pnpm --dir frontend install --frozen-lockfile' >&2
  exit 1
fi
export REVIEW_API_PORT="$BACKEND_PORT"
"$ROOT_DIR/scripts/workspace-python.sh" -m revisor.server --root "$DATA_ROOT" --port "$BACKEND_PORT" --model "${REVIEW_MODEL:-gpt-6.1-sol}" &
BACKEND_PID=$!
"$ROOT_DIR/frontend/node_modules/.bin/vite" "$ROOT_DIR/frontend" --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort &
FRONTEND_PID=$!
wait -n "$BACKEND_PID" "$FRONTEND_PID"
