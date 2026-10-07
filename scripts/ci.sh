#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python3 -m compileall -q backend tests
./scripts/test.sh
node --test frontend/src/lib/*.test.ts
pnpm --dir frontend lint
pnpm --dir frontend build
