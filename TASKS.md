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

## TASK-032 — Add preview deployment path for the local web interface

Status: TODO

Description:

Define and implement the first preview deployment path for the web interface.

Acceptance Criteria:

- preview deployment target explicitly chosen
- deployment steps are scripted or documented
- preview path does not bypass repository-backed state rules

Dependencies:

- requires `TASK-015`

---

## TASK-033 — Harden security and repository validation for the web workflow

Status: TODO

Description:

Expand safety checks now that the project exposes an operator interface.

Acceptance Criteria:

- validation covers the web app as part of CI
- repository state assumptions are checked more explicitly
- unsafe runtime paths are documented or blocked

Dependencies:

- requires `TASK-015` and `TASK-032`

---

## TASK-034 — Define WhatsApp integration boundary over the existing backend

Status: TODO

Description:

Prepare the future bot channel without implementing it prematurely.

Acceptance Criteria:

- WhatsApp scope is documented
- required backend contracts are explicit
- no WhatsApp-specific business logic leaks into current web flow

Dependencies:

- requires `TASK-023` and `TASK-031`

---

## TASK-035 — Create the first end-to-end editorial runbook

Status: TODO

Description:

Document the exact operator sequence to review, approve, translate, and export the manuscript.

Acceptance Criteria:

- runbook covers `pt-BR` review flow
- runbook covers Spanish translation flow
- runbook covers web, CLI fallback, and deliverable generation

Dependencies:

- requires `TASK-025`, `TASK-030`, and `TASK-031`

# Notes for Agents

- the current manuscript is the only available source of truth
- there is no pre-review versus post-review diff for the already revised section
- the already reviewed corpus must be treated as the primary editorial reference
- completed tasks belong in `TASKS-HISTORY.md`, not in this file
- interface work belongs after backend/core stabilization, not before
