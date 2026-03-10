#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec "$ROOT_DIR/scripts/workspace-python.sh" -m unittest discover -s "$ROOT_DIR/tests" -p "test_*.py" -v
