#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PYTHONPATH="$ROOT_DIR/apps/review-cli/src:$ROOT_DIR/apps/review-web/src:$ROOT_DIR/packages/docx-adapter/src:$ROOT_DIR/packages/editorial-core/src:$ROOT_DIR/packages/editorial-prompts/src:$ROOT_DIR/packages/editorial-schemas/src${PYTHONPATH:+:$PYTHONPATH}"

exec python3 "$@"
