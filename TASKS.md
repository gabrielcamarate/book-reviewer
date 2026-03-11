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
