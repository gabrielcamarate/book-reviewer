#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "[ci] compileall"
python3 -m compileall apps packages tests

echo "[ci] unit tests"
./scripts/test.sh
