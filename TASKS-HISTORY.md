# TASKS-HISTORY.md — Completed Task History

This file stores completed tasks moved out of `TASKS.md`.

If `TASKS.md` contains active and future work, this file is the source of truth for completed work.

---

# How Agents Must Use This File

- Read this file when historical implementation context may affect current work
- Append completed tasks in chronological order
- Do not move active tasks here prematurely
- Do not rewrite or delete older completed task entries without explicit reason

Task status legend:

- `DONE` → completed and locally verified

---

# Completed Tasks

## TASK-001 — Project documentation bootstrap

Status: DONE

Description:

Create the base governance, architecture, and backlog documents for the editorial review project.

Acceptance Criteria:

- `AGENTS.md` created
- `ARCHITECTURE.md` created
- `TASKS.md` created
- documents aligned with the editorial product goal

---

## TASK-001A — Git bootstrap and workflow policy

Status: DONE

Description:

Initialize Git for the repository and define the branch, commit, and push workflow policy for agents.

Acceptance Criteria:

- Git repository initialized
- `main` branch exists
- dedicated working branch created
- governance documents define branch, commit, and push rules
- first repository commit created for the current documented baseline

---

## TASK-002 — Initialize the pipeline directory structure

Status: DONE

Description:

Create the minimum directory structure for manuscript assets, editorial guides, reviews, reports, and source code.

Acceptance Criteria:

- initial directories created
- structure aligned with `ARCHITECTURE.md`

---

## TASK-003 — Implement `.docx` ingestion

Status: DONE

Description:

Create the first command or script capable of reading `livro.docx` and extracting raw operational content.

Acceptance Criteria:

- `.docx` file can be read
- relevant text and metadata are extracted
- outputs are persisted in reproducible files

---

## TASK-003D — Align governance with the staged development roadmap

Status: DONE

Description:

Align repository governance with the staged development model: AI jail first, foundation second, TDD before new features, backend/core before interfaces, and deployment last.

Acceptance Criteria:

- `AGENTS.md` defines the staged roadmap explicitly
- `TASKS.md` prioritizes isolation, foundation, and TDD before new core features
- backlog makes backend-first execution explicit

---

## TASK-003A — Establish AI jail and containerized workflow

Status: DONE

Description:

Create the isolated execution environment and governance baseline for assisted development.

Acceptance Criteria:

- container-based workflow defined
- development commands run inside the isolated environment
- repository documentation explains the jail workflow

---

## TASK-003B — Establish foundation, configs, dependencies, and monorepo layout

Status: DONE

Description:

Restructure the repository foundation so future implementation follows the intended monorepo-first workflow.

Acceptance Criteria:

- monorepo structure defined
- configs and dependency strategy documented or implemented
- repository layout aligned with the staged roadmap

---

## TASK-003C — Establish testing foundation and enforce TDD

Status: DONE

Description:

Create the testing baseline and make test-first development mandatory for upcoming feature work.

Acceptance Criteria:

- testing toolchain selected and configured
- first executable test command available
- governance documents explicitly enforce `test -> feature`

---

## TASK-004 — Segment the manuscript into chapters and paragraphs

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

Description:

Build the first output interface only after backend/core flow is stable.

Acceptance Criteria:

- interface type explicitly chosen
- interface consumes stable backend/core outputs
- no business logic is moved into the interface layer
- first interface is `web` local-first
- architecture remains compatible with a future WhatsApp channel

Dependencies:

- requires `TASK-010` and, preferably, `TASK-011`

---

## TASK-015 — Prepare CI/CD and deployment baseline

Status: DONE

Description:

Create the delivery pipeline and production readiness workflow.

Acceptance Criteria:

- CI/CD script or workflow defined
- code validation and test automation included
- security or vulnerability scanning included
- deployment path documented

Dependencies:

- requires stable backend/core workflow and test foundation

---

## TASK-016 — Build chapter and chunk navigation in the web interface

Status: DONE

Description:

Expand the dashboard into an operational view with navigable chapters and chunks.

Acceptance Criteria:

- chapters are listed in the web interface
- chunks are listed per chapter
- chunk detail page is reachable from the web layer
- interface remains read-only over persisted state

Dependencies:

- requires `TASK-014`

---

## TASK-017 — Show chunk source, context, and persisted review artifacts in the web interface

Status: DONE

Description:

Expose the selected chunk, surrounding context, and existing review files for operator inspection.

Acceptance Criteria:

- chunk base text is visible
- previous and next context are visible
- persisted `copyedit` and `translation-es` artifacts are surfaced when present

Dependencies:

- requires `TASK-016`

---

## TASK-018 — Trigger `copyedit` from the web interface

Status: DONE

Description:

Allow operators to launch the `pt-BR` copyedit pass for a selected chunk from the web workflow.

Acceptance Criteria:

- web action triggers the existing backend command or use case
- resulting review file is persisted in `reviews/ptbr/`
- interface reflects the newly created review artifact

Dependencies:

- requires `TASK-017`

---

## TASK-019 — Render structured `copyedit` suggestions with diff-oriented review view

Status: DONE

Description:

Present copyedit suggestions in a way that supports fast literary review.

Acceptance Criteria:

- each suggestion shows original, suggested text, reason, and confidence
- chunk page distinguishes untouched text from proposed changes
- operator can inspect suggestions without leaving the chunk flow

Dependencies:

- requires `TASK-018`

---

## TASK-020 — Approve and apply selected `copyedit` suggestions from the web interface

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

Description:

Document the exact operator sequence to review, approve, translate, and export the manuscript.

Acceptance Criteria:

- runbook covers `pt-BR` review flow
- runbook covers Spanish translation flow
- runbook covers web, CLI fallback, and deliverable generation

Dependencies:

- requires `TASK-025`, `TASK-030`, and `TASK-031`

---

## TASK-036 — Repair chapter segmentation gaps and missing chapter discovery

Status: DONE

Description:

Investigate and fix the segmentation pipeline so missing chapters such as `3` and `5` are either recovered correctly or explicitly classified.

Acceptance Criteria:

- segmentation explains every detected chapter transition
- missing chapter identifiers are resolved or reported explicitly
- web chapter navigation reflects the corrected structure

Dependencies:

- requires `TASK-004`, `TASK-016`, and `TASK-033`

---

## TASK-037 — Add a repository doctor command for operator diagnostics

Status: DONE

Description:

Create a richer repository diagnostics command that goes beyond the minimum startup validation.

Acceptance Criteria:

- doctor output summarizes required artifacts and common failure modes
- command distinguishes blocking versus advisory findings
- output is usable from both CLI and future web/operator surfaces

Dependencies:

- requires `TASK-033`

---

## TASK-038 — Version prompt and model configuration explicitly

Status: DONE

Description:

Persist prompt and model settings so review provenance remains auditable across runs.

Acceptance Criteria:

- prompt versioning strategy is persisted
- model selection is recorded with review artifacts
- changing prompt or model inputs becomes traceable

Dependencies:

- requires `TASK-009` and `TASK-012`

---

## TASK-039 — Implement the `style` pass in `pt-BR`

Status: DONE

Description:

Add the second editorial pass focused on fluency and cadence while preserving the author's voice.

Acceptance Criteria:

- style pass runs only on already copyedited and stable material
- output remains structured and auditable
- prompts consume style guide, glossary, and decisions

Dependencies:

- requires `TASK-009`, `TASK-010`, and `TASK-026`

---

## TASK-040 — Add approval and application flow for the `style` pass

Status: DONE

Description:

Allow style suggestions to be selectively approved and applied without bypassing the existing audit trail.

Acceptance Criteria:

- style suggestions can be approved partially
- consolidated state records style-origin changes separately from copyedit
- audit trail remains reproducible

Dependencies:

- requires `TASK-039`

---

## TASK-041 — Expose the `style` pass in the web interface

Status: DONE

Description:

Extend the editorial workstation so the operator can review and apply the style pass through the web UI.

Acceptance Criteria:

- chunk page exposes style pass actions and persisted artifacts
- operator can compare copyedit and style outputs clearly
- no editorial business logic moves into the web layer

Dependencies:

- requires `TASK-039` and `TASK-040`

---

## TASK-042 — Add chapter completion summaries and progress rollups

Status: DONE

Description:

Summarize chapter-level progress so the operator can see what is complete, pending, blocked, or ready for translation.

Acceptance Criteria:

- chapter progress metrics are persisted or reproducible
- dashboard exposes chapter completion summaries
- queue decisions can rely on chapter-level visibility

Dependencies:

- requires `TASK-030`

---

## TASK-043 — Add a batch copyedit runner over the review queue

Status: DONE

Description:

Support controlled background execution over multiple queued chunks without losing per-chunk auditability.

Acceptance Criteria:

- batch runner consumes the same queue state as the web flow
- every chunk still produces an individual persisted review artifact
- failures stop or isolate cleanly without corrupting queue state

Dependencies:

- requires `TASK-030`, `TASK-031`, and `TASK-033`

---

## TASK-044 — Add a resumable batch translation runner for Spanish

Status: DONE

Description:

Automate translation over eligible stable chunks while preserving resumability and traceability.

Acceptance Criteria:

- runner skips ineligible or already translated chunks
- translation jobs are resumable
- outputs remain per-chunk and auditable

Dependencies:

- requires `TASK-012`, `TASK-030`, and `TASK-031`

---

## TASK-045 — Generate a bilingual deliverable readiness report

Status: DONE

Description:

Create a consolidated report that explains whether `pt-BR` and Spanish exports are currently safe to generate.

Execution Notes:

- task expanded to absorb segmentation normalization required to make readiness trustworthy
- Word-export split headings such as `C` + `Apítulo` were normalized in the canonical parser
- manuscript state was rebuilt from `paragraphs.json`, not from ad-hoc edits to `document.txt`
- chapter navigation was revalidated by the user after the rebuild

Subtasks Completed:

- `TASK-045A` — Consolidated split-heading parser support, readiness report generation, and web visibility
- `TASK-045B` — Captured the previous section/chunk baseline and measured migration impact
- `TASK-045C` — Regenerated canonical chapter artifacts from extracted paragraphs
- `TASK-045D` — Reapplied review-boundary marking and regenerated pending-review chunks
- `TASK-045E` — Produced integrity and migration reporting in `reports/manuscript-rebuild.json`
- `TASK-045F` — Refreshed repository-backed web/report state to reflect the rebuilt manuscript
- `TASK-045G` — Completed human validation of rebuilt chapter navigation and manuscript coverage

Acceptance Criteria:

- readiness report covers both languages
- blocking gaps are explicit by chunk or chapter
- report is visible in the web workflow

Dependencies:

- requires `TASK-011`, `TASK-012`, and `TASK-025`

---

## TASK-046 — Add snapshot backups before deliverable export

Status: DONE

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

Status: DONE

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

Status: DONE

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

Status: DONE

Description:

Allow the operator to refine generated character and world-rule registries without bypassing the repository as source of truth.

Acceptance Criteria:

- characters and world rules can be edited intentionally
- changes are persisted in deterministic files
- web views expose current manual curation status

Dependencies:

- requires `TASK-027`, `TASK-028`, and `TASK-014`
