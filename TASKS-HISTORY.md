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
