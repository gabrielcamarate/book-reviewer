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

---

# Target Directory Structure

Suggested initial structure:

```text
apps/
  review-cli/
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
```

---

# Layered Architecture

## Application Layer

Responsibilities:

- provide runnable entrypoints
- wire command parsing to core use cases
- remain thin and orchestration-oriented
- expose local-first operator interfaces over persisted backend state

Current app:

- `apps/review-cli`
- `apps/review-web`

Future interface note:

- a future WhatsApp or bot channel must consume the same persisted backend/core outputs rather than duplicating editorial logic
- the future WhatsApp channel boundary is documented in `WHATSAPP-BOUNDARY.md`

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

- `apps/review-cli`

## Web Interface Layer

Responsibilities:

- expose local-first operational visibility over persisted repository state
- present summary metrics, recent chunks, consistency findings, and deliverables
- expose repository-backed editorial memory such as `DECISIONS.md`
- keep all editorial decisions delegated to existing backend commands and persisted artifacts

Rules:

- no editorial business logic in the web layer
- no hidden mutable state outside repository artifacts
- future channels such as WhatsApp must reuse the same backend/core contracts
- operator actions such as recording editorial decisions must write back to repository state
- the web server must fail fast when minimum repository state is missing or invalid unless an explicit operator override is used for diagnostics only

Contained in:

- `apps/review-web`

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
- `ConsolidatedSection`
- `ExportJob`

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

## Pass 4: Translation ES

Translate from the consolidated `pt-BR` text using a literary Spanish register compatible with the intended style.

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

Operator navigation is expected to remain local-first and deterministic:

- search reads repository artifacts directly
- search results link back to chunk, chapter, glossary, and decision workflows
- no external search index or hidden database is required for the initial operator experience
- the review queue is derived from chunk index plus persisted review artifacts, not from session memory
- long-running operator actions persist job outcomes under `reports/jobs/`
- preview deployment must run against a checked-out repository branch, not against detached external state
- repository validation must gate both CI and default web startup to block unsafe runtime assumptions early
- repository diagnostics should separate blocking findings from advisory findings so operators can tell broken state apart from editorial anomalies

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
