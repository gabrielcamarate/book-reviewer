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

Turn the current manuscript into an operational editorial review project with persistent memory, starting from `.docx` ingestion, text segmentation, and style learning from the already approved section.

---

# Current Sprint

Sprint: `Editorial Pipeline Foundation`

Goal:

- move from a single `.docx` file to a reproducible workflow
- persist editorial context outside the chat
- prepare pending `pt-BR` review work

---

# Tasks

## TASK-004 — Segment the manuscript into chapters and paragraphs

Status: TODO

Description:

Convert the raw extraction into a structured representation with chapters, paragraphs, and canonical order.

Acceptance Criteria:

- chapters are identifiable
- paragraphs are preserved in order
- stable identifiers exist per block

---

## TASK-005 — Mark the approved versus pending boundary

Status: TODO

Description:

Persist the operational point where approved review ends and pending review begins.

Acceptance Criteria:

- the cutoff excerpt is located in structured manuscript state
- chunks before the cutoff are marked as `approved_reference`
- chunks from the cutoff onward are marked as `pending_review`

---

## TASK-006 — Generate initial `STYLE_GUIDE.md` from the approved corpus

Status: TODO

Description:

Analyze the already revised section and consolidate observable rules about style, literalness, and acceptable intervention level.

Acceptance Criteria:

- `editorial/STYLE_GUIDE.md` created
- decisions written in operational language
- clear distinction between confirmed rule and editorial hypothesis

---

## TASK-007 — Generate initial `GLOSSARY.md`

Status: TODO

Description:

Extract proper names, recurring concepts, philosophical formulas, acronyms, and preferred spellings.

Acceptance Criteria:

- `editorial/GLOSSARY.md` created
- terms normalized
- relevant aliases or variants recorded

---

## TASK-008 — Implement operational chunking for review

Status: TODO

Description:

Define and generate stable chunks for local review with side context.

Acceptance Criteria:

- chunks persisted to disk
- size compatible with high-quality review
- previous and next context included

---

## TASK-009 — Implement the `copyedit` pass in `pt-BR`

Status: TODO

Description:

Create the first automated conservative review flow for pending chunks.

Acceptance Criteria:

- structured chunk input
- structured output with suggestion and reason
- no irreversible automatic manuscript mutation

---

## TASK-010 — Implement review approval and application

Status: TODO

Description:

Allow approved suggestions to be consolidated into manuscript state.

Acceptance Criteria:

- approved review is recorded
- consolidated text is updated
- audit trail is preserved

---

## TASK-011 — Implement global consistency checking

Status: TODO

Description:

Create a pass that detects terminological, naming, and conceptual inconsistencies in the consolidated manuscript.

Acceptance Criteria:

- report written to `reports/`
- inconsistencies grouped by type
- no silent automatic mutation

---

## TASK-012 — Implement the literary Spanish translation pipeline

Status: TODO

Description:

Generate an equivalent Spanish version from the consolidated `pt-BR` text.

Acceptance Criteria:

- depends on reviewed `pt-BR`
- respects glossary and style
- produces persisted outputs per chapter or chunk

---

## TASK-013 — Implement final export

Status: TODO

Description:

Rebuild the reviewed work into a final delivery format.

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
