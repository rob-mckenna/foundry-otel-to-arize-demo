# Architecture Decision Records (ADR) Log

**Status: process documentation — applies to both current-state and future-state work.**

This directory is the durable, customer-facing home for architecture decisions once they are
resolved — separate from `.squad/decisions.md`, which is the team-internal working log for
day-to-day Squad coordination decisions. An `architecture-decision.yml` issue that reaches a
recommended decision gets a corresponding ADR recorded here so a customer architect (or a new
team member) can trace *why* the pipeline looks the way it does, without digging through issue
history.

## When to Write an ADR

Write a new ADR when a decision:
- Affects more than one architecture track (Prompt Agent, Infrastructure, Telemetry Pipeline,
  Arize Integration), **or**
- Changes what counts as current-state vs. future-state (see
  [`/.github/copilot-instructions.md`](../../.github/copilot-instructions.md) §2-§4), **or**
- Chooses between materially different technical approaches that a future contributor might
  reasonably ask "why didn't we just do X instead?" about.

Small, single-track implementation details (e.g., a variable name, a minor refactor) do not need
an ADR. When in doubt, prefer recording it — a short ADR costs little and saves a repeated
discussion later.

ADRs are normally produced as the resolution of an `architecture-decision.yml` GitHub issue (see
`.github/ISSUE_TEMPLATE/architecture-decision.yml`), but can also be written directly for
retrospective decisions that were never filed as an issue.

## Template

Use [`template.md`](template.md) for every new ADR. It follows Michael Nygard's standard ADR
format: **Title / Status / Context / Decision / Consequences**.

## Numbering

ADRs are numbered sequentially, zero-padded to 4 digits, starting at `0001`:

```
docs/adr/0001-record-architecture-decisions.md
docs/adr/0002-use-event-hub-for-telemetry-streaming.md
docs/adr/0003-...
```

- Never reuse or renumber an existing ADR's number, even if it is later superseded.
- A superseded ADR is **not deleted** — its `Status` is updated to `Superseded by ADR-00NN` and a
  new ADR is filed recording the replacement decision.
- Pick the next unused number by checking the highest-numbered file currently in this directory.

## Status Values

- `Proposed` — drafted, not yet agreed by the affected tracks.
- `Accepted` — agreed and (if applicable) implemented or in progress.
- `Superseded by ADR-00NN` — replaced by a later decision; keep the file for history.
- `Deprecated` — no longer applies and has not been replaced by a specific later ADR.

## Current ADRs

| ADR | Title | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-use-event-hub-for-telemetry-streaming.md) | Use Event Hub for telemetry streaming instead of a direct Log Analytics trigger | Accepted |
