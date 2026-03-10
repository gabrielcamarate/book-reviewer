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

Sprint: `Isolation, Foundation, and TDD Alignment`

Goal:

- align the repository with the staged development roadmap
- finish backend-first project setup before new core features
- establish AI jail, monorepo foundation, and TDD enforcement

---

# Tasks

## TASK-003C — Establish testing foundation and enforce TDD

Status: TODO

Description:

Create the testing baseline and make test-first development mandatory for upcoming feature work.

Acceptance Criteria:

- testing toolchain selected and configured
- first executable test command available
- governance documents explicitly enforce `test -> feature`

---

## TASK-004 — Segment the manuscript into chapters and paragraphs

Status: TODO

Description:

Convert the raw extraction into a structured representation with chapters, paragraphs, and canonical order.

Dependencies:

- requires `TASK-003A`, `TASK-003B`, and `TASK-003C`

Acceptance Criteria:

- chapters are identifiable
- paragraphs are preserved in order
- stable identifiers exist per block

---

## TASK-005 — Mark the approved versus pending boundary

Status: TODO

Description:

Persist the operational point where approved review ends and pending review begins.

Dependencies:

- requires `TASK-004`

Acceptance Criteria:

- the cutoff excerpt is located in structured manuscript state
- chunks before the cutoff are marked as `approved_reference`
- chunks from the cutoff onward are marked as `pending_review`

---

## TASK-006 — Generate initial `STYLE_GUIDE.md` from the approved corpus

Status: TODO

Description:

Analyze the already revised section and consolidate observable rules about style, literalness, and acceptable intervention level.

Dependencies:

- requires `TASK-005`

Acceptance Criteria:

- `editorial/STYLE_GUIDE.md` created
- decisions written in operational language
- clear distinction between confirmed rule and editorial hypothesis

---

## TASK-007 — Generate initial `GLOSSARY.md`

Status: TODO

Description:

Extract proper names, recurring concepts, philosophical formulas, acronyms, and preferred spellings.

Dependencies:

- requires `TASK-005`

Acceptance Criteria:

- `editorial/GLOSSARY.md` created
- terms normalized
- relevant aliases or variants recorded

---

## TASK-008 — Implement operational chunking for review

Status: TODO

Description:

Define and generate stable chunks for local review with side context.

Dependencies:

- requires `TASK-004`

Acceptance Criteria:

- chunks persisted to disk
- size compatible with high-quality review
- previous and next context included

---

## TASK-009 — Implement the `copyedit` pass in `pt-BR`

Status: TODO

Description:

Create the first automated conservative review flow for pending chunks.

Dependencies:

- requires `TASK-003C`, `TASK-006`, `TASK-007`, and `TASK-008`

Acceptance Criteria:

- structured chunk input
- structured output with suggestion and reason
- no irreversible automatic manuscript mutation

---

## TASK-010 — Implement review approval and application

Status: TODO

Description:

Allow approved suggestions to be consolidated into manuscript state.

Dependencies:

- requires `TASK-009`

Acceptance Criteria:

- approved review is recorded
- consolidated text is updated
- audit trail is preserved

---

## TASK-011 — Implement global consistency checking

Status: TODO

Description:

Create a pass that detects terminological, naming, and conceptual inconsistencies in the consolidated manuscript.

Dependencies:

- requires `TASK-010`

Acceptance Criteria:

- report written to `reports/`
- inconsistencies grouped by type
- no silent automatic mutation

---

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
