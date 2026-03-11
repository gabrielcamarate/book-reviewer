# WhatsApp Integration Boundary

This document defines the future WhatsApp integration boundary for the editorial review project.

The goal is to keep the current repository architecture ready for a bot-style channel later without pushing WhatsApp concerns into the existing backend or web workflow too early.

## Current Decision

WhatsApp is a future secondary operator channel.

It is not the primary editorial workstation.

The primary operator experience remains:

- local-first web interface
- repository-backed state
- explicit review artifacts on disk

## Why WhatsApp Is Not the Primary Interface

The manuscript review workflow depends on:

- reading chunk source and adjacent context
- comparing original text against conservative suggestions
- approving only selected suggestions
- checking consistency findings across chapters
- comparing `pt-BR` against Spanish outputs

These activities are dense and audit-oriented.

WhatsApp is better suited to:

- notifications
- lightweight status checks
- simple acknowledgements
- limited follow-up actions

It is not the right first interface for long-form literary review.

## Scope Allowed for a Future WhatsApp Channel

Allowed scope:

- notify that a `copyedit`, `consistency`, `translation-es`, or export job finished
- show queue progress and the next recommended chunk
- show a short summary for a specific chunk
- link the operator back to the local web workflow when deeper inspection is needed
- accept lightweight commands that delegate to existing backend actions

Examples of acceptable future commands:

- `status`
- `fila`
- `próximo chunk`
- `job <id>`
- `export pt-br`

## Scope Explicitly Out of Bounds

Out of scope for the first WhatsApp integration:

- long-form chunk review inside chat messages
- free-form rewriting requests detached from repository state
- direct business logic implemented in the WhatsApp adapter
- any hidden storage for editorial memory outside repository artifacts
- translation workflows that bypass consolidated `pt-BR` state
- approvals that cannot be traced back to persisted review files

## Required Backend Contracts

The future adapter must call backend/core contracts that already exist or remain compatible with the current architecture.

Required read contracts:

- queue summary from repository-backed chunk and review state
- chunk detail summary derived from `manuscript/chunks/`, `manuscript/consolidated/`, `reviews/ptbr/`, and `reviews/es/`
- recent job summaries from `reports/jobs/`
- export readiness summary for `pt-BR` and Spanish

Required write contracts:

- trigger `copyedit` for a known `chunk_id`
- trigger `translation-es` only for eligible chunks
- trigger export for a supported language
- append editorial decisions through the same repository-backed decision flow

Required blocking rules:

- no action may bypass repository validation
- no action may mutate the manuscript without persisted artifacts
- no action may create hidden conversation-only state

## Adapter Responsibilities

The future WhatsApp adapter may:

- parse inbound commands
- authenticate the operator identity
- map supported commands to existing backend/core actions
- format compact responses for WhatsApp delivery

The future WhatsApp adapter must not:

- decide editorial policy
- build alternative prompt logic
- duplicate queue or consistency logic
- maintain an independent manuscript state store

## Message and State Model

The transport layer should remain transient.

Persistent state must continue living in repository artifacts such as:

- `editorial/DECISIONS.md`
- `manuscript/chunks/index.json`
- `manuscript/consolidated/index.json`
- `reviews/ptbr/`
- `reviews/es/`
- `reports/jobs/`

WhatsApp message history must never become the source of truth.

## Security and Access Expectations

Any future WhatsApp adapter should assume:

- explicit operator allowlisting
- command authentication or signature verification
- rate limiting and replay protection
- read-only defaults for uncertain inputs

Sensitive actions should require extra confirmation, especially:

- export generation
- translation triggers
- any future rollback action

## Architectural Guardrail

If a future WhatsApp integration requires backend changes, those changes must improve shared backend/core contracts first and only then expose them to the adapter.

No WhatsApp-specific business rule should be introduced directly into the current web app or core editorial flows.
