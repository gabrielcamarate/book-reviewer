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
