# Project Architecture Guide

This document describes the target architecture for the AI-assisted editorial review system for the manuscript `eXilados da Terra`.

It works together with `AGENTS.md` and `TASKS.md`.

---

# Architectural Goals

The system must be:

- deterministic where possible
- auditable
- file-oriented
- agent-friendly
- safe for incremental review
- prepared for both `pt-BR` and Spanish outputs
- ready for CI validation before production deployment

---

# Core Premise

Editorial context must not live in a conversation.

Editorial context must live in:

- extracted manuscript files
- persistent editorial guides
- review reports
- recorded style decisions
- structured per-chunk outputs

---

# Primary Data Flow

The main workflow is:

1. import `livro.docx`
2. extract manuscript structure
3. segment into chapters, paragraphs, and chunks
4. mark approved versus pending material
5. learn style from the approved corpus
6. review pending chunks in `pt-BR`
7. approve and apply changes into consolidated manuscript state
8. run global consistency checks
9. translate to Spanish
10. export `.docx`

When segmentation rules change for a manuscript already under operation, rebuild must happen through an explicit normalization step:

1. regenerate canonical chapter structure
2. reapply review-boundary state
3. regenerate pending-review chunks
4. sync repository-backed indexes that depend on chapter identifiers
5. emit a rebuild report before resuming editorial work

---

# Target Directory Structure

Target end-state structure:

```text
backend/
  apps/
    review-cli/
      src/
    review-web/
      src/

  packages/
    docx-adapter/
      src/
    editorial-core/
      src/
    editorial-prompts/
      src/
    editorial-schemas/
      src/

frontend/
  src/
  public/

manuscript/
  source/
  extracted/
  chapters/
  chunks/
  consolidated/

editorial/
  STYLE_GUIDE.md
  GLOSSARY.md
  CHARACTERS.md
  WORLD_RULES.md
  DECISIONS.md

reviews/
  ptbr/
  es/

reports/

deliverables/
  ptbr/
  es/
  snapshots/

fixtures/
  bot-contracts/
```

Current transition note:

- `frontend/` now exists as the dedicated frontend application
- the Python backend workspace is still rooted in the current top-level `apps/`, `packages/`, and repository state directories
- a later normalization step may move the current backend workspace under `backend/` once the dedicated frontend track is stable enough to justify the structural migration

---

# Layered Architecture

## Application Layer

Responsibilities:

- provide runnable entrypoints
- wire command parsing to core use cases
- remain thin and orchestration-oriented
- expose local-first operator interfaces over persisted backend state

Current app:

- `backend/apps/review-cli`
- `backend/apps/review-web`

Future interface note:

- a future WhatsApp or bot channel must consume the same persisted backend/core outputs rather than duplicating editorial logic
- the future WhatsApp channel boundary is documented in `WHATSAPP-BOUNDARY.md`
- fixture examples for future adapter contract testing live under `fixtures/bot-contracts/`

## CLI Layer

Responsibilities:

- accept commands
- validate arguments
- trigger use cases
- print output paths and concise summaries

Rules:

- CLI must remain thin
- no editorial business logic here
- no complex parsing logic here

Contained in:

- `backend/apps/review-cli`

## Web Interface Layer

Responsibilities:

- expose local-first operational visibility over persisted repository state
- present summary metrics, recent chunks, consistency findings, and deliverables
- expose chapter-level completion rollups derived from repository state
- expose repository-backed editorial memory such as `DECISIONS.md`
- expose controlled curation workflows for repository-backed editorial memory such as `GLOSSARY.md`
- expose controlled curation workflows for derived registries such as `CHARACTERS.md` and `WORLD_RULES.md`
- keep all editorial decisions delegated to existing backend commands and persisted artifacts

Rules:

- no editorial business logic in the web layer
- no hidden mutable state outside repository artifacts
- future channels such as WhatsApp must reuse the same backend/core contracts
- operator actions such as recording editorial decisions must write back to repository state
- the web server must fail fast when minimum repository state is missing or invalid unless an explicit operator override is used for diagnostics only

Current operator-mode decision:

- the default home route must prioritize a simple operator experience for the manuscript author
- the current technical workstation must remain available on a separate advanced route
- the simple operator flow must be validated with the user step by step before further interface expansion

Frontend implementation policy:

- when frontend work moves into a dedicated `frontend/` application, that layer must consume backend contracts instead of reimplementing editorial logic
- frontend implementation must use the installed skills as working constraints:
  - `vercel-react-best-practices`
  - `frontend-design`
  - `tailwind-design-system`
  - `shadcn`
  - `web-design-guidelines`
- skill usage is mandatory for React, Tailwind, `shadcn`, and UI-review work
- `find-skills` must be used when a frontend need is not covered clearly by the installed set
- backend/core remains the source of truth for editorial state, prompts, decisions, and repository-backed persistence

Frontend transition decision:

- the current server-rendered `backend/apps/review-web` remains the working operator interface during transition
- a new dedicated `frontend/` application will be introduced incrementally
- the new `frontend/` must consume backend contracts instead of duplicating editorial rules
- the transition must preserve localhost-first operation with a single developer-friendly startup flow
- the transition must not block the current validated author workflow while the new frontend is still incomplete
- the first real frontend shell is implemented in `frontend/` with React + Vite + Tailwind v4
- local frontend development now runs through `./scripts/dev.sh`, which starts Vite and a Python backend watcher in one terminal
- the backend watcher restarts `review_web.server` automatically when Python source files change, while Vite handles frontend hot reload
- `shadcn/ui` adoption remains planned, but its initialization may be deferred temporarily if local `npx` cache errors block setup
- in the simple operator flow, generating a `pt-BR` review must also generate an immediate Spanish preview based on the revised `pt-BR` preview text, not on the original chunk text
- this Spanish preview is a repository-backed preview artifact and must remain distinct from the official post-approval Spanish translation flow

Contained in:

- `backend/apps/review-web`
- future `frontend/`

## Frontend Application Boundary

The dedicated frontend application exists to improve operator usability, not to replace backend responsibilities.

Responsibilities:

- render the simple author-facing review flow
- render a future advanced technical workstation when parity is sufficient
- consume backend-provided state and actions through explicit local contracts
- keep presentation, interaction, and visual design concerns inside the frontend app

Rules:

- the frontend must not read or mutate repository state directly
- the frontend must not invoke editorial core modules directly
- backend endpoints or adapters must remain the only write path for editorial state
- the frontend must be local-first and runnable on the author's machine
- the initial frontend foundation should prefer minimal dependencies plus the installed skill-guided stack

Initial technical direction:

- dedicated app under `frontend/`
- React-based implementation
- Tailwind-based styling system
- `shadcn/ui` available for composition where it improves clarity and speed
- localhost integration with the existing backend before any deploy-specific changes

## Simple Operator Mode Contract

The web application must support two interface levels:

1. simple operator mode for the author
2. advanced workstation mode for the technical operator

### Route Structure

- `/` → simple `pt-BR` review mode
- `/review/es` → simple Spanish review mode
- `/advanced` → current technical workstation

### Simple Review Flow

- operator opens one actionable chunk at a time
- `Revisar este trecho` generates a conservative `pt-BR` review proposal
- the same action also generates an immediate Spanish preview based on the revised `pt-BR` proposal
- the Spanish preview is informative only and does not replace the official stable translation flow
- `Aceitar` continues to operate only on the `pt-BR` review approval path

### Simple Navigation

The simple navigation must expose only:

- `Revisar PT-BR`
- `Revisar Espanhol`
- `Revisão Avançada`

### Simple `pt-BR` Screen

The simple `pt-BR` screen must focus on one actionable chunk at a time.

It must show:

- current chapter
- remaining chapters
- current chunk position inside the chapter
- remaining actionable chunks
- current review status

Primary comparison area:

- first column: current `Original`
- second column: current `Revisado`
- third column: current Spanish preview based on the revised `pt-BR` text

Primary actions:

- `Aceitar`
- `Recusar`

Secondary review explanation area:

- a lower row shows the `pt-BR` change cards only
- change cards remain tied to the `pt-BR` review proposal, not to the Spanish preview

The simple `pt-BR` screen must not include:

- technical reports
- operational diagnostics
- job internals
- registry curation controls
- large navigation trees

### Simple Spanish Screen

The simple Spanish screen must mirror the same visual structure, but only for chunks that are already stable in `pt-BR`.

Primary comparison area:

- left column: consolidated `pt-BR`
- right column: suggested Spanish text

Eligibility rule:

- Spanish review must only surface chunks whose `pt-BR` state is already stable enough for translation

### Meaning of Primary Actions

`Aceitar` means:

- apply the selected review result to repository-backed consolidated state
- preserve approval traceability in persisted artifacts

`Recusar` means:

- do not apply the proposed change
- remove the current `pt-BR` proposal and the derived Spanish preview for that chunk
- persist a rejection record with a short human reason
- make that rejection feedback available for a future rerun of the same chunk

`Pular` does not exist in simple mode.

### Export Communication Rule

Simple mode must explain exports in operator language instead of technical language:

- `pt-BR` export is generated from the current consolidated manuscript state
- Spanish export is only available after eligible translated content exists
- advanced manifests and technical metadata remain in advanced mode, not in the simple primary flow

## Core Layer

Responsibilities:

- import manuscript content
- segment chapters and chunks
- locate the approved/pending boundary
- build review context
- orchestrate editorial passes
- consolidate suggestions
- run consistency checks
- read persistent editorial decisions as part of review context
- prepare Spanish translation

Rules:

- core must be testable
- core must not depend directly on a chat session
- core should operate on explicit state and files

Contained in:

- `packages/editorial-core`

## Adapter Layer

Responsibilities:

- file I/O
- `.docx` parsing
- `.docx` export
- model calls
- diff generation
- final export

Rules:

- isolate side effects
- keep provider-specific logic out of core

Contained in:

- `packages/docx-adapter`

## Prompt Layer

Responsibilities:

- instruction templates for `copyedit`
- instruction templates for `style`
- instruction templates for `consistency`
- instruction templates for `translation-es`

Rules:

- prompts must be parameterized by persisted context
- prompts must not be the only source of editorial memory

Contained in:

- `packages/editorial-prompts`

## Schema Layer

Responsibilities:

- input and output formats
- JSON contracts for review results
- chunk metadata
- approval state

Contained in:

- `packages/editorial-schemas`

---

# State Model

Primary entities:

- `Manuscript`
- `Chapter`
- `Paragraph`
- `Chunk`
- `ReviewSuggestion`
- `ReviewPass`
- `Approval`
- `ChapterProgress`
- `ConsolidatedSection`
- `ExportJob`
- `ExportSnapshot`

`ExportSnapshot` manifests must be generated before writing a deliverable and should describe the repository-backed files that fed the export, including checksums and file roles.

Final deliverables must also emit their own manifests:

- deliverable manifests are generated after the `.docx` output exists
- each manifest records output checksum, size, language slug, and the snapshot manifest that fed the export
- snapshot manifests and deliverable manifests serve different audit purposes and must both remain persisted

Rollback of applied reviews is intentionally narrow:

- only the latest active approval may be reverted automatically
- rollback is safe only when that approval is still the topmost audit entry for every affected paragraph
- if consolidated text or audit ordering diverges, rollback must stop with an explicit error instead of guessing

Each `Chunk` should include at minimum:

- stable identifier
- chapter reference
- position
- base text
- short previous context
- short next context
- status

Suggested statuses:

- `approved_reference`
- `pending_review`
- `in_review`
- `reviewed`
- `approved`
- `exported`

---

# Consolidated State

The repository must distinguish between source segmentation and approved manuscript state.

Rules:

- `manuscript/chapters/` remains the segmented source derived from the imported manuscript and review-boundary processing
- approved applications must not overwrite `manuscript/chapters/`
- `manuscript/consolidated/` stores the mutable editorial state after approved review application
- consolidated paragraphs should preserve both `source_text` and current `text`
- each approved application must be traceable back to a persisted review file and approval file

Expected consolidated artifacts:

- `manuscript/consolidated/index.json`
- per-section JSON files mirroring source section identifiers
- paragraph-level audit metadata for applied reviews

Applied review audit metadata must preserve pass origin explicitly, so `copyedit` and `style` changes remain distinguishable in the consolidated manuscript state.

---

# Approved vs Pending Boundary

The system must support an explicit editorial checkpoint.

Initial assumption:

- everything before the excerpt `"Todo cuidado é pouco, tratando-se do Sistema Terra estabelecido"` may be treated as approved reference corpus
- that excerpt and everything after it should be treated as pending until validated more precisely

This boundary must be persisted in state, not inferred from scratch on every run.

---

# Chunking Strategy

The model must not operate on the entire book at once.

Requirements:

- chunks small enough for high-quality review
- enough side context to preserve continuity
- stable identifiers per block
- reliable chapter recomposition

Suggested starting approach:

- chunk by paragraph groups
- target window roughly equivalent to 12 to 20 useful lines
- light contextual overlap

## Chapter Number Integrity

The segmentation pipeline must not silently normalize chapter numbering gaps away.

Rules:

- declared chapter numbers should be persisted when they can be inferred from headings
- missing declared chapter numbers must be surfaced explicitly as metadata
- operator navigation should show missing chapter placeholders instead of pretending the gap does not exist
- existing repository-backed identifiers should remain stable unless a deliberate migration is performed

---

# Review Strategy

The editorial pipeline should use independent passes.

## Pass 1: Copyedit

Fix form without distorting voice.

## Pass 2: Style

Improve fluency, rhythm, and clarity while preserving literary intent.

## Pass 3: Consistency

Check terms, names, repeated formulas, internal philosophy, and coherence.

Cross-chapter consistency analysis must be registry-aware:

- glossary, characters, and world rules are consumed together
- findings may be grouped by entity or concept instead of only by paragraph anomaly
- grouped findings should preserve chapter and chunk traceability for operator follow-up

## Pass 4: Translation ES

Translate from the consolidated `pt-BR` text using a literary Spanish register compatible with the intended style.

Spanish validation remains a separate report path:

- Spanish consistency must not overwrite or merge into the `pt-BR` consistency report
- translated artifacts are validated against glossary-sensitive terms and curated registries
- Spanish findings remain auditable and non-destructive under their own report file

Persisted LLM review artifacts must also include explicit provenance.

Required provenance fields:

- model identifier
- prompt template identifier and version
- schema identifier and version
- prompt hash
- hashes of persisted editorial inputs such as style guide, glossary, and decisions

Current persisted pass artifacts:

- `reviews/ptbr/*.copyedit.json`
- `reviews/ptbr/*.style.json`
- `reviews/es/*.translation-es.json`

---

# Editorial Memory

The system should reuse the approved section to infer:

- punctuation patterns
- lexical preferences
- acceptable intervention level
- recurring philosophical formulas
- preferred spellings
- dialogue treatment patterns

This memory must be converted into explicit artifacts under `editorial/`, not kept only inside prompts.

Current persisted editorial memory includes:

- `STYLE_GUIDE.md`
- `GLOSSARY.md`
- `DECISIONS.md`
- `CHARACTERS.md`
- `WORLD_RULES.md`

The web layer may inspect and regenerate these artifacts, but it must not replace the repository as the source of truth.

Glossary curation is part of the operator workflow:

- operators may edit preferred forms and alias lists through controlled web forms
- glossary edits must preserve deterministic Markdown structure
- later review and translation passes must consume the curated glossary state from the repository

Registry curation is also part of the operator workflow:

- operators may edit preferred forms, aliases, and expanded forms for character and world-rule registries
- registry edits must preserve deterministic Markdown structure
- cross-chapter consistency analysis should consume manually curated registry state before reporting findings

Operator navigation is expected to remain local-first and deterministic:

- search reads repository artifacts directly
- search results link back to chunk, chapter, glossary, and decision workflows
- no external search index or hidden database is required for the initial operator experience
- the review queue is derived from chunk index plus persisted review artifacts, not from session memory
- chapter completion summaries are derived from chunk state plus persisted review artifacts, not from manual counters
- long-running operator actions persist job outcomes under `reports/jobs/`
- batch runners must consume the same repository-derived queue state used by the interactive workflow
- preview deployment must run against a checked-out repository branch, not against detached external state
- repository validation must gate both CI and default web startup to block unsafe runtime assumptions early
- repository diagnostics should separate blocking findings from advisory findings so operators can tell broken state apart from editorial anomalies
- preview health endpoints should expose a minimal readiness signal separately from the fuller diagnostics payload
- non-local preview binds should require explicit access-control configuration instead of assuming the workstation can be left open

---

# Editorial Safety Rules

- never apply changes without recording origin and reason
- never overwrite segmented source files when consolidating approved review
- never translate before the `pt-BR` text is stable
- never mix approved corpus and pending corpus without explicit markers
- never assume every repetition is an error
- never assume every grammatical deviation is intentional

The system must allow human intervention before final consolidation.

---

# Expected Evolution

Phase 1:

- `.docx` ingestion
- manuscript structuring
- review boundary marking
- initial style learning

Phase 2:

- per-chunk `pt-BR` review
- approval and application flow
- consistency reports

Phase 3:

- literary Spanish translation
- final export

Future architectural changes must be documented here.

The current operator sequence is documented in `RUNBOOK.md`.
