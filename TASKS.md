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

Sprint: `Core Editorial Memory Bootstrap`

Goal:

- derive persistent editorial memory from the approved corpus
- consolidate style and glossary artifacts before automated review
- prepare stable chunking for the first `pt-BR` copyedit pass

---

# Tasks

## TASK-012 — Implement the literary Spanish translation pipeline

Status: TODO

Description:

Generate an equivalent Spanish version from the consolidated `pt-BR` text.

Dependencies:

- requires `TASK-010` and `TASK-011`

Acceptance Criteria:

- depends on reviewed `pt-BR`
- respects glossary and style
- produces persisted outputs per chapter or chunk

---

## TASK-013 — Implement final export

Status: TODO

Description:

Rebuild the reviewed work into a final delivery format.

Dependencies:

- requires `TASK-010`

Acceptance Criteria:

- `pt-BR` export available
- foundation ready for Spanish export
- output is reproducible

---

## TASK-014 — Build output interface

Status: TODO

Description:

Build the first output interface only after backend/core flow is stable.

Acceptance Criteria:

- interface type explicitly chosen
- interface consumes stable backend/core outputs
- no business logic is moved into the interface layer

Dependencies:

- requires `TASK-010` and, preferably, `TASK-011`

---

## TASK-015 — Prepare CI/CD and deployment baseline

Status: TODO

Description:

Create the delivery pipeline and production readiness workflow.

Acceptance Criteria:

- CI/CD script or workflow defined
- code validation and test automation included
- security or vulnerability scanning included
- deployment path documented

Dependencies:

- requires stable backend/core workflow and test foundation

Acceptance Criteria:

- `pt-BR` export available
- foundation ready for Spanish export
- output is reproducible

---

# Notes for Agents

- the current manuscript is the only available source of truth
- there is no pre-review versus post-review diff for the already revised section
- the already reviewed corpus must be treated as the primary editorial reference
- completed tasks belong in `TASKS-HISTORY.md`, not in this file
- interface work belongs after backend/core stabilization, not before
