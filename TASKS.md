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

Sprint: `Simple Operator Mode`

Goal:

- turn the current web layer into a simple operator flow for the author's real use case
- keep the advanced workstation available on a separate route for technical operation
- validate each UI step with the user before moving to the next one

Frontend implementation rules for this sprint:

- any frontend task must use the installed frontend skills documented in `AGENTS.md`
- use `frontend-design` for visual direction and layout work
- use `vercel-react-best-practices` for React architecture and performance decisions once the dedicated frontend app starts
- use `tailwind-design-system` for Tailwind-based tokens, patterns, and component structure
- use `shadcn` when working with `shadcn/ui` components or project setup
- use `web-design-guidelines` for UI review and compliance passes
- use `find-skills` if a missing frontend workflow or tool needs to be evaluated before custom implementation

User-authorized parallel track:

- begin the dedicated `frontend/` foundation now
- keep the current server-rendered interface operational while the new frontend is being built
- migrate by parity, not by rewrite-in-place

---

# Tasks

## TASK-061C — Establish the frontend design system baseline

Status: IN_PROGRESS

Description:

Set up the first design-system layer for the new frontend using the installed frontend skills.

Acceptance Criteria:

- the frontend has a baseline visual system
- Tailwind and component conventions are in place
- `shadcn/ui` setup is prepared if used
- the baseline is appropriate for the author-facing simple review workflow

Dependencies:

- requires `TASK-061B`

Implementation note:

- Tailwind v4 baseline is already in progress inside `frontend/`
- `shadcn/ui` initialization is still pending because local `npx shadcn@latest` currently fails with a transient cache rename error and should be retried in a clean step

---

## TASK-061D — Expose the first backend-to-frontend local contract

Status: IN_PROGRESS

Description:

Connect the new frontend shell to a minimal backend-fed contract without moving editorial logic into the frontend.

Acceptance Criteria:

- the frontend can load one simple review screen from backend-fed data
- no editorial write path bypasses the backend
- localhost integration path is demonstrated
- the current server-rendered flow remains available during transition

Implementation note:

- a minimal `/api/simple-home` contract is now in progress together with `./scripts/dev.sh` for one-terminal local development
- current real write path scope is limited to `review` and `accept`; `reject` persistence remains part of `TASK-056D`

Dependencies:

- requires `TASK-061B`

---

## TASK-061E — Normalize repository structure to the target backend/frontend layout

Status: TODO

Description:

Move the current Python workspace into a dedicated `backend/` root only after the new frontend track is stable enough to justify the structural migration.

Acceptance Criteria:

- current Python apps and packages live under `backend/`
- repository scripts and docs are updated to the new backend root
- frontend and backend local startup flow remains clear
- the migration does not lose any repository-backed editorial state

Dependencies:

- requires `TASK-061D`

## TASK-056C — Build the simple `pt-BR` review home

Status: IN_PROGRESS

Description:

Create the simplified home screen focused on one `pt-BR` chunk at a time for the author's workflow.

Acceptance Criteria:

- home route shows only the essential `pt-BR` review information
- top block shows orientation data such as current chapter, remaining chapters, current chunk position, and remaining chunks
- center area shows `Original` and `Revisado`
- bottom area shows only the primary actions for the current chunk
- layout is readable for a non-technical, older operator

Dependencies:

- requires `TASK-056A` and `TASK-056B`

Implementation note:

- before considering this task complete, the real editorial state must be normalized so the home reflects only human-approved manuscript progress and not development-generated approvals
- while the current server-rendered web layer remains active, frontend refinements must still follow the installed frontend skillset where applicable

---

## TASK-056D — Define and implement `Recusar` with explicit feedback

Status: TODO

Description:

Make rejection a traceable editorial action instead of an implicit non-approval.

Acceptance Criteria:

- `Recusar` does not apply any change to consolidated state
- operator can provide a short reason for rejection
- rejection is persisted as repository-backed state
- workflow can later regenerate the same chunk review with the rejection feedback as explicit context

Dependencies:

- requires `TASK-056A` and `TASK-056C`

---

## TASK-056E — Build the simple Spanish review route

Status: TODO

Description:

Expose a second simple route for Spanish review that operates only on `pt-BR`-approved material.

Acceptance Criteria:

- `/review/es` reuses the same simple visual structure as `pt-BR`
- left side shows consolidated `pt-BR`
- right side shows suggested Spanish text
- route only surfaces eligible chunks
- navigation clearly separates `Revisar PT-BR` from `Revisar Espanhol`

Dependencies:

- requires `TASK-056A`, `TASK-056C`, and `TASK-012`

---

## TASK-056F — Simplify export entry points for the author workflow

Status: TODO

Description:

Make export understandable from the simple mode without exposing technical internals.

Acceptance Criteria:

- simple flow explains what the export will contain in `pt-BR`
- simple flow explains why Spanish export may still be blocked
- export actions remain backed by the existing repository state
- human validation confirms that the exported `.docx` behavior is understandable

Dependencies:

- requires `TASK-056C`, `TASK-056E`, and `TASK-025`

---

## TASK-056G — Validate the simple operator mode with human review

Status: TODO

Description:

Run a guided validation pass with the user before resuming any advanced workstation expansion.

Acceptance Criteria:

- user validates the simple `pt-BR` flow
- user validates the simple Spanish flow
- user validates the export understanding and outcome
- follow-up adjustments are captured before returning to advanced backlog items

Dependencies:

- requires `TASK-056B`, `TASK-056C`, `TASK-056D`, `TASK-056E`, and `TASK-056F`

---

## TASK-056 — Expose Spanish consistency report in the web workstation

Status: TODO

Description:

Surface the separate Spanish consistency report in the local web interface without mixing it into the `pt-BR` review workflow.

Acceptance Criteria:

- dashboard shows Spanish consistency summary separately from `pt-BR`
- operator can trigger the Spanish report from the web
- findings remain navigable by type

Dependencies:

- requires `TASK-051` and `TASK-053`
- deferred until `TASK-056G`

---

## TASK-057 — Add web-triggered batch copyedit execution

Status: TODO

Description:

Allow the operator to launch resumable copyedit batches from the workstation instead of invoking the CLI manually.

Acceptance Criteria:

- batch execution can be triggered from the web
- batch progress is persisted in job logs
- failures stop cleanly with auditable status

Dependencies:

- requires `TASK-009`, `TASK-030`, and `TASK-053`

---

## TASK-058 — Add web-triggered batch style execution

Status: TODO

Description:

Expose resumable style batches in the workstation after `pt-BR` chunks become eligible.

Acceptance Criteria:

- style batches can be launched from the web
- eligibility rules remain aligned with approved `pt-BR` state
- job logs distinguish style batches from copyedit batches

Dependencies:

- requires `TASK-057` and `TASK-011`

---

## TASK-059 — Add web-triggered batch Spanish translation execution

Status: TODO

Description:

Expose resumable Spanish translation batches in the workstation for eligible chunks only.

Acceptance Criteria:

- translation batches can be launched from the web
- ineligible chunks are skipped with explicit reasons
- job logs preserve batch and per-chunk outcomes

Dependencies:

- requires `TASK-012`, `TASK-030`, and `TASK-056`

---

## TASK-060 — Add operator timeline for approvals, rollbacks, and exports

Status: TODO

Description:

Provide a unified timeline view of editorial operations so the operator can understand what changed and when.

Acceptance Criteria:

- timeline groups approvals, rollbacks, exports, and major jobs
- entries link back to the relevant chunk or deliverable artifact
- view is derived entirely from repository-backed state

Dependencies:

- requires `TASK-047`, `TASK-052`, and `TASK-053`

---

## TASK-061 — Add searchable approval history by chunk and chapter

Status: TODO

Description:

Make the approval trail searchable without manually opening review files.

Acceptance Criteria:

- approval history can be filtered by chunk, chapter, and pass type
- results link back to consolidated text or review artifacts
- no hidden database is introduced

Dependencies:

- requires `TASK-010`, `TASK-029`, and `TASK-060`

---

## TASK-062 — Add chapter-scoped export generation

Status: TODO

Description:

Allow partial deliverables to be generated for selected chapters without exporting the whole manuscript.

Acceptance Criteria:

- operator can export a subset of chapters in `pt-BR`
- chapter-scoped exports remain auditable with manifests
- full-book export path remains unchanged

Dependencies:

- requires `TASK-052`

---

## TASK-063 — Add chapter-scoped Spanish export generation

Status: TODO

Description:

Allow selected Spanish-ready chapters to be exported independently for review and comparison.

Acceptance Criteria:

- chapter-scoped Spanish export validates translation coverage before writing
- manifests differentiate chapter-scoped and full-book exports
- missing translations remain explicit blockers

Dependencies:

- requires `TASK-056` and `TASK-062`

---

## TASK-064 — Add consolidated diff report between source and approved manuscript state

Status: TODO

Description:

Generate a reproducible diff-oriented report showing how the consolidated manuscript diverges from the source segmentation.

Acceptance Criteria:

- report groups changes by chapter and paragraph
- applied review provenance remains traceable from the diff
- report is non-destructive and reproducible

Dependencies:

- requires `TASK-010` and `TASK-047`

---

## TASK-065 — Add reviewer notes per chunk

Status: TODO

Description:

Allow the operator to attach manual notes to chunks without mutating the manuscript text.

Acceptance Criteria:

- notes are repository-backed and chunk-scoped
- notes are visible in the web workstation
- notes can be referenced by later editorial passes

Dependencies:

- requires `TASK-014` and `TASK-060`

---

## TASK-066 — Add bulk approval actions for homogeneous review suggestions

Status: TODO

Description:

Speed up repetitive editorial work by allowing controlled bulk approval of compatible suggestions.

Acceptance Criteria:

- bulk approval requires explicit operator intent
- incompatible suggestions are excluded automatically
- audit metadata preserves per-suggestion provenance

Dependencies:

- requires `TASK-020`, `TASK-021`, and `TASK-065`

---

## TASK-067 — Add explicit approval workflow for Spanish translations

Status: TODO

Description:

Treat Spanish translations as reviewable editorial output rather than implicitly accepted artifacts.

Acceptance Criteria:

- Spanish translation approvals are persisted separately from generation
- export readiness for Spanish depends on approved translation state
- rollback safety rules remain explicit

Dependencies:

- requires `TASK-012`, `TASK-047`, and `TASK-056`

---

## TASK-068 — Add glossary-to-registry conflict detection

Status: TODO

Description:

Detect conflicts between glossary, characters, and world-rule registries before they propagate into review and translation passes.

Acceptance Criteria:

- conflict report identifies contradictory preferred forms or aliases
- report links back to the affected registry entries
- report is consumable before running consistency or translation batches

Dependencies:

- requires `TASK-048`, `TASK-049`, and `TASK-050`

---

## TASK-069 — Add deliverable bundle packaging for handoff

Status: TODO

Description:

Package deliverables, manifests, and relevant reports into a single handoff artifact for external review.

Acceptance Criteria:

- package includes selected deliverables and their manifests
- package includes readiness and consistency reports relevant to the handoff
- package generation is reproducible and non-destructive

Dependencies:

- requires `TASK-052`, `TASK-056`, and `TASK-063`

---

## TASK-070 — Add preview smoke-check script

Status: TODO

Description:

Create a lightweight script that validates preview startup, health, and diagnostics expectations.

Acceptance Criteria:

- script checks `/healthz` and authenticated `/diagnostics`
- script fails clearly when preview access control is misconfigured
- script is documented for preview operators

Dependencies:

- requires `TASK-053` and `TASK-054`

---

## TASK-071 — Upload operational artifacts from CI

Status: TODO

Description:

Preserve useful build outputs from CI so branch verification can include reports and manifests, not only test status.

Acceptance Criteria:

- CI can retain selected reports or manifests as artifacts
- artifact set excludes manuscript-sensitive raw content beyond what is already tracked
- workflow remains reproducible on branches

Dependencies:

- requires `TASK-052` and `TASK-053`

---

## TASK-072 — Add repository backup and restore scripts for editorial state

Status: TODO

Description:

Provide explicit backup and restore automation for the repository-backed editorial state.

Acceptance Criteria:

- backup script captures the critical editorial and manuscript state paths
- restore path is documented and testable
- scripts avoid overwriting data silently

Dependencies:

- requires `TASK-052` and `TASK-069`

---

## TASK-073 — Add manuscript bootstrap command for a second book

Status: TODO

Description:

Prepare the workflow to initialize another manuscript project from a fresh `.docx` without hand-editing repository structure.

Acceptance Criteria:

- bootstrap command creates the expected directory and document skeleton
- command does not destroy the current manuscript state
- resulting project layout matches governance conventions

Dependencies:

- requires `TASK-003`, `TASK-004`, and `TASK-072`

---

## TASK-074 — Add manuscript profile configuration for multi-book reuse

Status: TODO

Description:

Externalize manuscript-specific parameters so the workflow can be reused on future books with controlled configuration.

Acceptance Criteria:

- manuscript-specific paths and boundaries can be configured explicitly
- current `eXilados da Terra` profile is preserved as the default
- new manuscript bootstrap can select or create a profile cleanly

Dependencies:

- requires `TASK-073`

---

## TASK-075 — Add future bot-channel contract validation workflow

Status: TODO

Description:

Validate future WhatsApp or bot adapters against repository-backed fixture contracts before any live integration work begins.

Acceptance Criteria:

- fixture validation command checks queue, chunk, job, and export-readiness contracts
- no live bot provider dependency is introduced
- future adapter work can start from repeatable local validation

Dependencies:

- requires `TASK-055`, `TASK-070`, and `TASK-074`

# Notes for Agents

- the current manuscript is the only available source of truth
- there is no pre-review versus post-review diff for the already revised section
- the already reviewed corpus must be treated as the primary editorial reference
- completed tasks belong in `TASKS-HISTORY.md`, not in this file
- interface work belongs after backend/core stabilization, not before
