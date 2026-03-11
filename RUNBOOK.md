# Editorial Operations Runbook

This runbook defines the first end-to-end operator workflow for reviewing, approving, translating, and exporting the manuscript.

The repository remains the source of truth for every step.

## Preconditions

Before starting:

1. confirm the repository is on the intended working branch
2. confirm required manuscript and editorial artifacts exist
3. validate repository state
4. start the local web interface

Recommended commands:

```bash
git status --short --branch
./scripts/workspace-python.sh -m review_cli.validate_repository_state
./scripts/workspace-python.sh -m review_cli.repository_doctor
./scripts/workspace-python.sh -m review_web.server
```

Then open:

```text
http://127.0.0.1:8765/
```

## Operator Goals

The operator workflow is split into four lanes:

1. `pt-BR` review
2. consistency validation
3. Spanish translation
4. final deliverable export

## A. PT-BR Review Flow Through the Web Interface

Use this as the default day-to-day workflow.

### 1. Open the queue

- open `/queue`
- identify the next recommended chunk
- follow the chunk link

### 2. Inspect the chunk

On the chunk page, verify:

- source text
- previous context
- next context
- any existing `copyedit`
- any existing applied approval

### 3. Run `copyedit`

- trigger `Rodar Copyedit`
- wait for the job result and refreshed chunk page
- inspect each structured suggestion

### 4. Approve suggestions conservatively

- approve only the suggestions that preserve the authorial voice
- apply the approved subset
- confirm the chunk now shows persisted approval and consolidated state

### 5. Record new editorial decisions when needed

If the chunk reveals a reusable editorial rule:

- open `/decisions`
- append the decision in operational language

Examples:

- preserve a recurring philosophical formula unchanged
- prefer a specific capitalization for a cosmological term
- keep a deliberate repetition pattern

### 6. Repeat queue-driven review

- return to `/queue`
- open the next recommended chunk
- repeat until the queue advances

## B. CLI Fallback for PT-BR Review

Use the CLI when the web layer is unavailable or when scripted operation is preferred.

### Run `copyedit`

```bash
./scripts/workspace-python.sh -m review_cli.run_copyedit --chunk-id <chunk-id>
```

### Apply approved suggestions

Approve all suggestions from a persisted review file:

```bash
./scripts/workspace-python.sh -m review_cli.apply_review \
  --review-file reviews/ptbr/<chunk-id>.copyedit.json
```

Approve only selected suggestions:

```bash
./scripts/workspace-python.sh -m review_cli.apply_review \
  --review-file reviews/ptbr/<chunk-id>.copyedit.json \
  --approve-index 0 \
  --approve-index 2
```

## C. Consistency Validation Flow

Consistency should run after a meaningful block of `pt-BR` approvals, not only at the very end.

### Web path

- trigger `Rodar Consistência` from the dashboard
- inspect grouped findings
- open linked chunks from the consistency detail pages
- resolve issues through normal chunk review and approval flow

### CLI fallback

```bash
./scripts/workspace-python.sh -m review_cli.run_consistency_report
```

Artifacts are persisted under:

- `reports/consistency-report.json`

## D. Spanish Translation Flow

Spanish translation starts only after the relevant `pt-BR` chunk is stable in consolidated state.

### Web path

- open a chunk page
- confirm the chunk is eligible for Spanish translation
- trigger `Gerar Tradução Espanhola`
- review the side-by-side `pt-BR` and Spanish output

### CLI fallback

```bash
./scripts/workspace-python.sh -m review_cli.run_translation_es --chunk-id <chunk-id>
```

Translation artifacts are persisted under:

- `reviews/es/<chunk-id>.translation-es.json`

## E. Deliverable Generation

Exports should happen only after enough review work is approved to justify a reproducible deliverable.

### Web path

- trigger `Gerar Export PT-BR` from the dashboard
- only trigger Spanish export when readiness allows it

### CLI fallback

Export `pt-BR`:

```bash
./scripts/workspace-python.sh -m review_cli.export_docx --language pt-BR
```

Export Spanish:

```bash
./scripts/workspace-python.sh -m review_cli.export_docx --language es
```

Deliverables are written to:

- `deliverables/ptbr/`
- `deliverables/es/`

## F. Full Bootstrap and Recovery Flow

Use this sequence when the repository needs to be rebuilt from source state.

### Import and structure the manuscript

```bash
./scripts/workspace-python.sh -m review_cli.main
./scripts/workspace-python.sh -m review_cli.segment_manuscript
./scripts/workspace-python.sh -m review_cli.mark_review_boundary
./scripts/workspace-python.sh -m review_cli.generate_style_guide
./scripts/workspace-python.sh -m review_cli.generate_glossary
./scripts/workspace-python.sh -m review_cli.generate_chunks
```

### Validate state again

```bash
./scripts/workspace-python.sh -m review_cli.validate_repository_state
```

## G. Operating Rules

- do not edit the final `.docx` deliverables manually and treat them as generated artifacts
- do not treat chat history as editorial memory
- do not translate pending `pt-BR` text before review approval
- do not approve suggestions just because they are grammatically correct; preserve voice first
- do not skip repository validation when starting the web server except for explicit diagnostics

## H. Daily Minimum Verification

At minimum, before ending a work session:

```bash
./scripts/test.sh
./scripts/ci.sh
```

If a task was completed:

- update `ARCHITECTURE.md` if structural behavior changed
- move the task from `TASKS.md` to `TASKS-HISTORY.md`
- commit only the intended scoped files
