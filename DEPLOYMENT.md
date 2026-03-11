# Deployment Baseline

This document defines the current deployment baseline for the editorial review project.

## Current State

The project is still local-first.

That means:

- backend/core is the source of truth
- the first operator interface is the local web dashboard
- production deployment is not enabled yet

## Chosen Preview Target

The first preview deployment target is:

- self-hosted Docker Compose preview on a Linux machine or VM

Reasoning:

- the web interface depends on repository-backed state under `manuscript/`, `editorial/`, `reviews/`, `reports/`, and `deliverables/`
- a branch checkout must remain the source of truth for preview data
- the preview path must not introduce a hidden remote database or parallel state store

This means preview runs against a checked-out branch of the repository itself.

## Current Runnable Interfaces

- CLI:
  - `./scripts/workspace-python.sh -m review_cli.main --help`
- Local web dashboard:
  - `./scripts/workspace-python.sh -m review_web.server`

## CI Baseline

The repository CI baseline must run:

- Python bytecode compilation checks
- repository state validation for the web workflow
- unit tests
- security scanning with `bandit`

## Security Baseline

Current runtime dependencies are standard-library-first and intentionally minimal.

Security scanning currently focuses on:

- static Python security scanning through `bandit`
- keeping third-party runtime dependencies close to zero unless justified

Runtime safety currently also depends on:

- fail-fast validation of required repository artifacts before the web server starts
- blocking default startup when persisted manuscript/editorial state is missing or malformed
- keeping any validation bypass restricted to explicit diagnostic usage only

## Deployment Path

The current deployment path is intentionally staged:

1. local-first web validation
2. repository CI passing on every branch and pull request
3. use self-hosted Docker Compose as the preview target
4. run preview against a checked-out branch with repository-backed state
5. add production deployment

## Preview Workflow

Preview artifacts:

- `docker-compose.preview.yml`
- `scripts/preview.sh`

Local preview:

```bash
docker compose -f docker-compose.yml -f docker-compose.preview.yml config
./scripts/preview.sh
```

Then open:

```text
http://127.0.0.1:8765/
```

Remote preview on a Linux machine or VM:

1. clone the repository on the target machine
2. checkout the branch to preview
3. ensure manuscript and editorial state files are present in the checkout
4. run `docker compose -f docker-compose.yml -f docker-compose.preview.yml up --build review-web`
5. expose port `8765` only through the intended preview ingress or tunnel

## State Rules for Preview

Preview must not bypass repository-backed state.

That means:

- no hidden database for manuscript or review state
- no deployment that omits the tracked editorial artifacts
- no preview target that diverges from the checked-out branch contents
- generated files in preview remain artifacts of that checkout, not of an external service

## Future Interface Expansion

The current operator interface is web.

Future channels may include:

- WhatsApp
- other bot-style interfaces

These future channels must reuse the same backend/core contracts and persisted repository state.
