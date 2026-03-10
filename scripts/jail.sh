#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for the AI jail workflow" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required for the AI jail workflow" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exec docker compose run --rm workspace
fi

exec docker compose run --rm workspace "$@"
