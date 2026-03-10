# Deployment Baseline

This document defines the current deployment baseline for the editorial review project.

## Current State

The project is still local-first.

That means:

- backend/core is the source of truth
- the first operator interface is the local web dashboard
- production deployment is not enabled yet

## Current Runnable Interfaces

- CLI:
  - `./scripts/workspace-python.sh -m review_cli.main --help`
- Local web dashboard:
  - `./scripts/workspace-python.sh -m review_web.server`

## CI Baseline

The repository CI baseline must run:

- Python bytecode compilation checks
- unit tests
- security scanning with `bandit`

## Security Baseline

Current runtime dependencies are standard-library-first and intentionally minimal.

Security scanning currently focuses on:

- static Python security scanning through `bandit`
- keeping third-party runtime dependencies close to zero unless justified

## Deployment Path

The current deployment path is intentionally staged:

1. local-first web validation
2. repository CI passing on every branch and pull request
3. choose hosting target for the web interface
4. add preview deployment
5. add production deployment

## Future Interface Expansion

The current operator interface is web.

Future channels may include:

- WhatsApp
- other bot-style interfaces

These future channels must reuse the same backend/core contracts and persisted repository state.
