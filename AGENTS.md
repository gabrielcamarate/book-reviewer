# Editorial Review Project — Agent Operating Guide

Always reply to the user in Brazilian Portuguese (`pt-BR`).

This repository exists to build an AI-assisted editorial review workflow for the manuscript `eXilados da Terra`.

If there is any conflict between default agent behavior and this document, this document takes priority.

---

# Operating Principles (MUST)

- Plan before changing code or structural documentation
- Work in small, verifiable steps
- Persist editorial context in files, never depend on chat history
- Build backend/core before building output interfaces
- Preserve the author's voice
- Prefer conservative revision over free rewriting
- Treat glossary, characters, world concepts, and style decisions as persistent state
- Complete the `pt-BR` editorial flow before starting Spanish translation
- Update `ARCHITECTURE.md` and `TASKS.md` whenever the workflow or project structure changes materially

---

# Project Objective

Build a reproducible workflow to:

- import the manuscript from `.docx`
- segment the text into chapters, paragraphs, and stable chunks
- preserve editorial memory outside the chat
- review the text in `pt-BR` with conservative intervention
- validate global consistency across the book
- generate an equivalent Spanish version only after the `pt-BR` text is consolidated
- export final deliverables back to `.docx`

---

# Development Roadmap (MANDATORY)

This project follows a staged development model.

Stage 1: AI Jail and Governance

- isolate execution with container-based workflow
- define safety and governance before expanding implementation

Stage 2: Foundation

- finalize architecture
- define configs and dependencies
- establish monorepo structure
- keep `AGENTS.md` as the complete operational source for these rules

Stage 3: TDD

- tests must be written before new feature code
- if a new function or module requires behavior validation, test-first is mandatory
- if code was added without tests and the task requires testable behavior, that gap must be fixed before moving forward

Stage 4: Core Backend

- implement core features only after stages 1 through 3 are in place
- follow `test -> feature`, never `feature -> test`

Stage 5: Optimization

- heavy processing
- jobs and queues
- refactoring and performance work

Stage 6: Output Interfaces

- web
- mobile
- bot

Current interface decision:

- build `web` first as a local-first interface over the stable backend
- keep future `bot` integration possible, including WhatsApp, without moving business logic out of the backend/core

Stage 7: Deploy

- CI/CD
- code validation and linting
- test automation
- vulnerability scanning
- production setup
- deployment

Current deploy baseline:

- GitHub Actions CI validates bytecode compilation, unit tests, and `bandit`
- deployment path remains documented and staged in `DEPLOYMENT.md`

Rules:

- stages do not represent literal calendar days
- backend/core work comes before output interface work
- no interface-first implementation unless the user explicitly overrides this roadmap

---

# AI Jail Workflow (MANDATORY)

This repository must use an isolated container-based workflow before expanding feature work.

Required artifacts:

- `Dockerfile`
- `docker-compose.yml`
- `scripts/jail.sh`

Rules:

- development commands should run inside the jail whenever feasible
- the host machine should be treated as orchestration only
- repository paths are mounted into the container workspace
- local environment drift should not be the default execution path for core development

Default usage:

```bash
./scripts/jail.sh
./scripts/jail.sh python3 -m src.cli.import_docx --help
./scripts/jail.sh python3 -m src.cli.import_docx
```

Verification baseline:

- `docker compose config`
- at least one project development command must be runnable through the jail workflow

Notes:

- if image build requires network access and the environment blocks it, validate the jail configuration structurally and record the limitation
- later tasks may expand this jail into a richer dev environment, but the repository must already define the isolated path

---

# Editorial Source of Truth

The current source of truth is:

- `livro.docx`

Current project assumptions:

- the manuscript already contains a user-approved reviewed section
- that approved section is the primary reference corpus for editorial style and decisions
- the initial operational boundary for pending review starts at the excerpt:

`Todo cuidado é pouco, tratando-se do Sistema Terra estabelecido`

If this boundary changes after technical validation, update `TASKS.md` and the relevant state artifacts.

---

# Editorial Review Rules

When reviewing literary text, agents must:

- preserve meaning, tone, cadence, and authorial literalness whenever possible
- fix spelling, grammar, punctuation, agreement, and syntax with minimal stylistic deviation
- avoid over-normalizing the author's voice
- avoid removing expressive marks without justification
- respect the manuscript glossary
- respect proper names, cosmological concepts, internal philosophy, and deliberate repetitions
- distinguish real errors from stylistic choices

Agents must NOT:

- rewrite entire chapters unless explicitly requested
- translate to Spanish before the `pt-BR` text is consolidated
- mix grammar review, style polishing, and translation in the same step without a clear reason
- mutate the final manuscript without a traceable review record

---

# Persistent Memory Policy (MANDATORY)

The project must keep editorial context in versionable files.

Expected artifacts over time:

- `editorial/STYLE_GUIDE.md`
- `editorial/GLOSSARY.md`
- `editorial/CHARACTERS.md`
- `editorial/WORLD_RULES.md`
- `editorial/DECISIONS.md`
- `manuscript/` with extracted book structure
- `reviews/` with per-chunk and per-chapter review outputs
- `reports/` with audits and validation reports
- `DEPLOYMENT.md` with the current delivery path and CI/deploy baseline

No agent should depend on implicit memory from earlier turns when the information can be persisted in these files.

---

# Agent Task Protocol

Before starting meaningful implementation work:

1. Read `AGENTS.md`
2. Read `ARCHITECTURE.md`
3. Read `TASKS.md`
4. Read `TASKS-HISTORY.md` when historical task context is relevant
5. Identify the active task
6. Work only within the required scope

Standard flow:

1. Plan
2. Inspect current state
3. Confirm the current work is allowed by the active roadmap stage
4. Implement the smallest useful increment
5. Verify locally
6. Update structural documentation when needed
7. If the task is complete, move it from `TASKS.md` to `TASKS-HISTORY.md`

Task board rules:

- `TASKS.md` must contain only active and future tasks
- completed tasks must be recorded in `TASKS-HISTORY.md`
- moving a completed task to `TASKS-HISTORY.md` is mandatory, not optional
- if relevant historical context exists, agents should consult `TASKS-HISTORY.md` before duplicating work

---

# Git Workflow (MANDATORY)

Agents must manage Git carefully in this repository.

Rules:

1. Work should happen on a dedicated branch, not directly on `main`
2. Branch names should be short and scoped, for example:
   `chore/git-bootstrap`
   `task-003-docx-ingestion`
3. Agents must review `git status --short` before creating a commit
4. Commit messages must use Conventional Commits
5. Push must never happen automatically
6. If the work requires human validation or user testing, do not commit until that validation is complete
7. If the work is documentation-only or otherwise fully verifiable by the agent locally, the agent may commit after verification
8. Agents must not mix unrelated changes in the same commit

Commit guidance:

- use small, scoped commits
- prefer one coherent commit per completed task or docs-only unit of work
- do not create a commit immediately after editing if verification is still pending

Push guidance:

- only push when explicitly requested by the user
- never assume a remote exists

---

# Monorepo Foundation (MANDATORY)

This repository follows a monorepo-first backend structure.

Top-level workspace areas:

- `apps/` for runnable applications
- `packages/` for shared backend packages
- `manuscript/`, `editorial/`, `reviews/`, and `reports/` for project state and outputs
- `deliverables/` for exported manuscript outputs

Current monorepo convention:

- `apps/review-cli` contains the first runnable CLI application
- `apps/review-web` contains the first local-first operator interface
- `packages/docx-adapter` contains document-format adapters
- `packages/editorial-core` contains core use cases
- `packages/editorial-prompts` is reserved for prompt templates
- `packages/editorial-schemas` is reserved for shared schemas

Configuration and dependency rules:

- prefer Python standard library first
- add external dependencies only with justification
- keep workspace configuration in root `pyproject.toml`
- keep package-local configuration in per-project `pyproject.toml`
- prefer workspace-local execution over global installation

Default local execution:

```bash
./scripts/workspace-python.sh -m review_cli.main --help
./scripts/workspace-python.sh -m review_web.server --help
./scripts/jail.sh ./scripts/workspace-python.sh -m review_cli.main --help
```

---

# Editorial Workflow

The editorial pipeline must separate responsibilities.

Preferred passes:

1. `copyedit`
   Fix spelling, grammar, punctuation, and agreement.
2. `style`
   Improve fluency without damaging the author's voice.
3. `consistency`
   Validate glossary, names, repetitions, timeline, and internal coherence.
4. `translation-es`
   Generate an equivalent Spanish version only after the `pt-BR` text is stable.

---

# LLM Output Rules

When the system uses an LLM for review, prefer structured outputs.

Preferred fields:

- `original`
- `suggested`
- `change_type`
- `reason`
- `confidence`

Avoid free-form outputs when later application or auditability is required.

---

# Code Architecture Rules

Principles:

- thin CLI
- business logic in core modules
- side effects isolated in adapters
- explicit data formats
- reproducible and auditable operations

Core logic must not depend on a conversational interface to function.

---

# TDD Policy (MANDATORY)

From the testing stage onward, the repository must follow test-first development for feature work.

Rules:

- do not implement new feature behavior before writing the test that proves it
- documentation-only work may be committed without tests
- environment bootstrap and governance work may proceed without strict TDD when appropriate
- once the testing foundation exists, feature tasks without tests must be treated as incomplete

Current testing baseline:

- framework: `unittest`
- command: `./scripts/test.sh`

---

# Definition of Done

A task is not DONE until:

- the scope defined in `TASKS.md` is implemented
- the result is verified locally at a level appropriate to the task
- structural documentation is updated if the architecture or workflow changed
- the produced output is reproducible from persisted repository state
- the completed task has been removed from `TASKS.md` and appended to `TASKS-HISTORY.md`

---

# Current Constraints

- the repository may initially be missing Git setup or remote configuration
- the source manuscript is a `.docx`, which is not reliable for fine-grained diffs
- there is no pre-review versus post-review diff available for the already revised section

These constraints must inform the initial system design.
