# Execução e distribuição local

Este aplicativo é local. O antigo preview remoto Docker foi removido junto com a interface avançada; não há deploy nem acesso público habilitado.

Desenvolvimento: `./scripts/dev.sh` inicia API na porta 8766 e Vite na porta 4173. O proxy recebe a porta por ambiente. `Ctrl+C` encerra ambos.

Interface compilada: `pnpm --dir frontend build`, depois `./scripts/workspace-python.sh -m revisor.server`. Esse único processo serve a API e o React em http://127.0.0.1:8766.

Docker Compose permanece apenas como ambiente isolado de desenvolvimento/testes através de `scripts/jail.sh`. Não contém o login do Codex nem faz revisão real de manuscrito por si só.

O GitHub Actions verifica Python 3.11, estado editorial local quando presente, testes unitários e HTTP, lint/build do frontend e Bandit. CI não mede qualidade editorial nem publica o aplicativo.
