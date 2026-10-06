#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python3 -m compileall -q backend tests
if [[ -f "$ROOT_DIR/manuscript/chunks/index.json" ]]; then
  ./scripts/workspace-python.sh -m revisor.cli check
else
  echo 'Sem acervo editorial local; testes usam documentos fictícios.'
fi
./scripts/test.sh
pnpm --dir frontend lint
pnpm --dir frontend build
