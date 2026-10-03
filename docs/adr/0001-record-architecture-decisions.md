# ADR-0001: Record architecture decisions

## Status

Accepted

## Context

This repository is a reusable observability demo that must stay credible and reusable across
multiple enterprise healthcare customers. Architecture choices here — what counts as current-state
vs. future-state, which Azure services sit in the validated pipeline, how telemetry schema is
mapped — need a durable, customer-facing record of *why* they were made, not just *what* was
built. Without a consistent log, this reasoning lives only in scattered issue comments, Squad
team-internal decision files, or people's memory, and gets lost or re-litigated.

## Decision

We will use Architecture Decision Records (ADRs), in the lightweight style described by Michael
Nygard, to record every architecturally significant decision for this project. ADRs live under
`/docs/adr`, are numbered sequentially starting at `0001`, and follow the
[template](template.md) (Title / Status / Context / Decision / Consequences). See
[`/docs/adr/README.md`](README.md) for the full process: when to write one, numbering rules, and
status values.

This is distinct from `.squad/decisions.md`, which remains the team-internal working log for
day-to-day Squad coordination decisions; ADRs under `/docs/adr` are the durable, customer-facing
architecture record.

## Consequences

- **Current-state impact:** None directly — this decision establishes a documentation process, it
  does not change any implemented pipeline behavior under `/src` or `/infra`.
- **Future-state impact:** None — future-state (conceptual) architecture proposals will also get
  ADRs once accepted, following the same process.
- **Security considerations:** None. ADRs must never contain secrets, connection strings, or real
  PII/PHI, consistent with every other document in this repository.
- **Observability considerations:** None directly, though future ADRs touching telemetry schema,
  trace/span/correlation-ID handling, or token-usage mapping will use this same template and
  process.
- **Trade-offs accepted:** A small amount of process overhead (writing an ADR) in exchange for a
  durable, scannable decision history. We judge this worthwhile given the multi-track,
  multi-customer nature of this repo.
- **Open questions:** None.
