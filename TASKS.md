# TASKS.md — Agent Task Board

This file defines the active backlog for the editorial review project.

If `AGENTS.md` defines how to work and `ARCHITECTURE.md` defines structural boundaries, this file defines what to work on next.

---

# How Agents Must Use This File

- Read `AGENTS.md`, `ARCHITECTURE.md`, and `TASKS.md` before starting substantial work
- Read `TASKS-HISTORY.md` when past completed work may affect the current task
- Work in task order unless explicitly instructed otherwise
- Do not build future-phase functionality without a clear need
- Update task status as work progresses
- Keep tasks small and verifiable
- When a task is completed, move it from `TASKS.md` to `TASKS-HISTORY.md`
- `TASKS.md` must contain only active and future tasks
- `TASKS-HISTORY.md` is the source of truth for completed tasks

Task status legend:

- `TODO` → not started
- `IN_PROGRESS` → currently being implemented
- `DONE` → completed, locally verified, and moved to `TASKS-HISTORY.md`
- `BLOCKED` → waiting for clarification or dependency

---

# Current Objective

Turn the current manuscript into an operational editorial review project with persistent memory, following a staged model: isolation and governance first, foundation second, testing third, core backend fourth, interface later.

---

# Current Sprint

Sprint: `Editorial Operations Web`

Goal:

- turn the backend pipeline into a usable editorial workstation
- enable chunk-by-chunk review through the local web interface
- preserve the repository as the source of truth for every action

---

# Tasks

## TASK-046 — Add snapshot backups before deliverable export

Status: TODO

Description:

Protect deliverable generation with reproducible snapshots of the current repository-backed editorial state.

Acceptance Criteria:

- export flow can persist a snapshot manifest before writing deliverables
- snapshot scope is documented clearly
- snapshot generation does not mutate editorial source state unexpectedly

Dependencies:

- requires `TASK-013` and `TASK-025`

---

## TASK-047 — Implement rollback for the last applied review approval

Status: TODO

Description:

Allow recovery from the most recent mistaken approval without manually editing consolidated artifacts.

Acceptance Criteria:

- rollback targets the last applied approval deterministically
- consolidated state and audit metadata remain consistent after rollback
- operator workflow documents when rollback is safe

Dependencies:

- requires `TASK-010` and `TASK-031`

---

## TASK-048 — Add glossary curation and alias editing through the web interface

Status: TODO

Description:

Allow the operator to maintain the glossary as repository-backed state from the workstation.

Acceptance Criteria:

- glossary entries and aliases can be edited through controlled forms
- resulting changes preserve deterministic file structure
- glossary updates become available to later review passes

Dependencies:

- requires `TASK-007` and `TASK-014`

---

## TASK-049 — Add manual curation for characters and world rules

Status: TODO

Description:

Allow the operator to refine generated character and world-rule registries without bypassing the repository as source of truth.

Acceptance Criteria:

- characters and world rules can be edited intentionally
- changes are persisted in deterministic files
- web views expose current manual curation status

Dependencies:

- requires `TASK-027`, `TASK-028`, and `TASK-014`

---

## TASK-050 — Add cross-chapter entity consistency analysis

Status: TODO

Description:

Expand consistency checking so entities, aliases, and concepts are validated across the whole book, not only chunk-local findings.

Acceptance Criteria:

- report groups cross-chapter issues by entity or concept
- glossary, characters, and world rules are consumed together
- findings link back to affected chunks or chapters

Dependencies:

- requires `TASK-011`, `TASK-027`, `TASK-028`, and `TASK-029`

---

## TASK-051 — Add Spanish consistency validation

Status: TODO

Description:

Validate that the Spanish output remains coherent with the established literary register and glossary.

Acceptance Criteria:

- Spanish consistency report is generated separately from `pt-BR`
- glossary-sensitive terms are checked in Spanish outputs
- findings remain auditable and non-destructive

Dependencies:

- requires `TASK-012` and `TASK-050`

---

## TASK-052 — Generate deliverable manifests and checksums

Status: TODO

Description:

Add reproducible manifests for exported deliverables so handoff and verification become explicit.

Acceptance Criteria:

- each export can emit a manifest with metadata and checksums
- manifest differentiates `pt-BR` and Spanish deliverables
- manifests are kept alongside deliverables or reports

Dependencies:

- requires `TASK-013`

---

## TASK-053 — Add preview healthcheck and operational diagnostics endpoint

Status: TODO

Description:

Expose a lightweight operational endpoint for preview environments that reports health without leaking editorial data.

Acceptance Criteria:

- health endpoint is explicit and minimal
- endpoint reflects repository validation status safely
- preview workflow documents how to use it

Dependencies:

- requires `TASK-032` and `TASK-033`

---

## TASK-054 — Add preview access control for non-local environments

Status: TODO

Description:

Protect preview deployments that are exposed beyond localhost.

Acceptance Criteria:

- preview access-control strategy is implemented or explicitly scripted
- default local workflow remains simple
- remote preview no longer assumes open access on the exposed port

Dependencies:

- requires `TASK-032` and `TASK-053`

---

## TASK-055 — Prepare adapter fixtures for future bot-channel contract testing

Status: TODO

Description:

Create stable fixtures and contract examples so future WhatsApp or bot adapters can be validated against existing backend expectations.

Acceptance Criteria:

- fixtures cover queue, chunk summary, job summary, and export readiness contracts
- fixtures do not introduce any bot-specific business logic
- future adapter work can start from deterministic examples

Dependencies:

- requires `TASK-034` and `TASK-037`

# Notes for Agents

- the current manuscript is the only available source of truth
- there is no pre-review versus post-review diff for the already revised section
- the already reviewed corpus must be treated as the primary editorial reference
- completed tasks belong in `TASKS-HISTORY.md`, not in this file
- interface work belongs after backend/core stabilization, not before
