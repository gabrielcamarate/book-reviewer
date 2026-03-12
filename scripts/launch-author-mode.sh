#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_URL="${APP_URL:-http://127.0.0.1:4173/}"
OPEN_DELAY_SECONDS="${OPEN_DELAY_SECONDS:-3}"

prepare_node_environment() {
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  if [[ -s "$NVM_DIR/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    . "$NVM_DIR/nvm.sh"
    nvm use --silent default >/dev/null 2>&1 || true
  fi

  if [[ -d "$HOME/.local/share/pnpm" ]]; then
    export PNPM_HOME="$HOME/.local/share/pnpm"
    case ":$PATH:" in
      *":$PNPM_HOME:"*) ;;
      *) export PATH="$PNPM_HOME:$PATH" ;;
    esac
  fi

  if ! command -v node >/dev/null 2>&1; then
    printf 'Node.js nao encontrado no ambiente do WSL. Verifique a instalacao antes de iniciar o revisor.\n'
    exit 1
  fi

  if ! command -v pnpm >/dev/null 2>&1; then
    printf 'pnpm nao encontrado no ambiente do WSL. Verifique a instalacao antes de iniciar o revisor.\n'
    exit 1
  fi
}

open_browser() {
  local url="$1"

  if command -v explorer.exe >/dev/null 2>&1; then
    explorer.exe "$url" >/dev/null 2>&1 &
    return 0
  fi

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
    return 0
  fi

  if command -v google-chrome >/dev/null 2>&1; then
    google-chrome "$url" >/dev/null 2>&1 &
    return 0
  fi

  if command -v chromium >/dev/null 2>&1; then
    chromium "$url" >/dev/null 2>&1 &
    return 0
  fi

  printf 'Nao foi possivel abrir o navegador automaticamente. Abra manualmente: %s\n' "$url"
  return 1
}

cleanup() {
  if [[ -n "${DEV_PID:-}" ]] && kill -0 "$DEV_PID" >/dev/null 2>&1; then
    kill "$DEV_PID" >/dev/null 2>&1 || true
    wait "$DEV_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

cd "$ROOT_DIR"
prepare_node_environment

printf 'Iniciando o Revisor Livro...\n'
printf 'Pasta do projeto: %s\n' "$ROOT_DIR"
printf 'URL da aplicacao: %s\n' "$APP_URL"

"$ROOT_DIR/scripts/dev.sh" &
DEV_PID=$!

sleep "$OPEN_DELAY_SECONDS"
open_browser "$APP_URL" || true

wait "$DEV_PID"
