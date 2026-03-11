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

## TASK-020 — Approve and apply selected `copyedit` suggestions from the web interface

Status: IN_PROGRESS

Description:

Allow the operator to approve all or part of a review and apply it to consolidated state.

Acceptance Criteria:

- selected suggestions can be approved from the web layer
- approval file is persisted
- consolidated manuscript state is updated only through existing backend logic

Dependencies:

- requires `TASK-019`

---

## TASK-021 — Surface consolidated paragraph state and audit trail in the web interface

Status: TODO

Description:

Expose what changed in consolidated manuscript state after approvals.

Acceptance Criteria:

- consolidated paragraph text is visible
- source text remains inspectable
- applied review metadata is shown for changed paragraphs

Dependencies:

- requires `TASK-020`

---

## TASK-022 — Trigger and browse consistency findings by type in the web interface

Status: TODO

Description:

Turn the consistency report into an actionable operator view.

Acceptance Criteria:

- consistency report can be regenerated from the web layer
- findings are grouped and browsable by type
- finding details link back to affected paragraphs or sections when possible

Dependencies:

- requires `TASK-021`

---

## TASK-023 — Trigger Spanish translation for stable chunks from the web interface

Status: TODO

Description:

Expose the `translation-es` pass to the operator for already stabilized `pt-BR` chunks.

Acceptance Criteria:

- translation can be triggered for eligible chunks
- translated output is persisted in `reviews/es/`
- ineligible chunks are clearly blocked in the UI

Dependencies:

- requires `TASK-020` and `TASK-022`

---

## TASK-024 — Compare `pt-BR` and Spanish chunk outputs side by side

Status: TODO

Description:

Provide a bilingual inspection view for translated chunks.

Acceptance Criteria:

- `pt-BR` and `es` chunk texts are shown side by side
- paragraph alignment is preserved
- operator can inspect translation rationale and confidence

Dependencies:

- requires `TASK-023`

---

## TASK-025 — Trigger `pt-BR` and Spanish export from the web interface

Status: TODO

Description:

Expose deliverable generation through the operator workflow.

Acceptance Criteria:

- export actions are available from the web interface
- generated `.docx` deliverables are persisted under `deliverables/`
- interface reflects the latest deliverables

Dependencies:

- requires `TASK-023`

---

## TASK-026 — Add repository-backed editorial decisions management

Status: TODO

Description:

Create a persisted workflow for editorial decisions that need to survive beyond a single chunk.

Acceptance Criteria:

- `editorial/DECISIONS.md` is surfaced and updated through explicit workflow
- decisions are linked to chunk or section context when relevant
- future review passes can consume these decisions

Dependencies:

- requires `TASK-021`

---

## TASK-027 — Add characters registry generation and inspection

Status: TODO

Description:

Generate and inspect a persistent characters registry from the approved and consolidated corpus.

Acceptance Criteria:

- `editorial/CHARACTERS.md` is generated or updated
- web interface can inspect the registry
- proper names and aliases remain traceable

Dependencies:

- requires `TASK-026`

---

## TASK-028 — Add world rules registry generation and inspection

Status: TODO

Description:

Persist and inspect the cosmological and philosophical rules of the manuscript.

Acceptance Criteria:

- `editorial/WORLD_RULES.md` is generated or updated
- web interface can inspect the registry
- future reviews can consume these rules

Dependencies:

- requires `TASK-026`

---

## TASK-029 — Add operator search across chapters, chunks, glossary, and decisions

Status: TODO

Description:

Provide a local search workflow for navigating manuscript state and editorial memory.

Acceptance Criteria:

- operator can search chunk text and identifiers
- search can surface glossary and decision references
- results link back into the web workflow

Dependencies:

- requires `TASK-027` and `TASK-028`

---

## TASK-030 — Add review queue controls and resumable operator workflow

Status: TODO

Description:

Turn the chunk flow into an explicit operational queue with progress awareness.

Acceptance Criteria:

- queue can show next recommended chunk
- queue reflects review progress by status
- operator can resume work without losing context

Dependencies:

- requires `TASK-020` and `TASK-029`

---

## TASK-031 — Add job logging for long-running review and export actions

Status: TODO

Description:

Persist operational logs for expensive or slow actions.

Acceptance Criteria:

- long-running actions generate structured logs
- web interface can display recent job outcomes
- failures are visible without reading terminal output

Dependencies:

- requires `TASK-025` and `TASK-030`

---

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
