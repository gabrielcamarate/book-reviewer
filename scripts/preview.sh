#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ -z "${PREVIEW_TOKEN:-}" ]]; then
  echo "PREVIEW_TOKEN is required for preview environments bound beyond localhost." >&2
  exit 1
fi

docker compose \
  -f docker-compose.yml \
  -f docker-compose.preview.yml \
  up --build review-web
