# src/telemetry-pipeline

**Status: CURRENT-STATE (architecture track), implementation PENDING.**

This directory is the designated home for the Azure Function transform/mapping code and Event Hub
consumer logic that will form the telemetry pipeline:

`Application Insights -> Log Analytics -> Event Hub -> Azure Function (transform/map) -> Arize (OTLP)`

**As of this writing, this directory contains only this README — no Function transform/consumer
code has been implemented yet.** The field-by-field mapping *specs* that this code must implement
are complete and validated-via-review (not live-validated) under `/docs/telemetry/mapping/`
(issues #89–#92) and `/docs/telemetry/field-mapping.md` (#36). The Function App *infrastructure
shell* (Bicep) was provisioned under issue #19, but the transform/mapping logic itself — the actual
code that would belong in this directory — is tracked as outstanding follow-on work and has not
been built. Trace-correlation-ID preservation across the Event Hub/Function hops specifically is
documented as **open/unvalidated** in
[`/docs/telemetry/trace-correlation-preservation.md`](../../docs/telemetry/trace-correlation-preservation.md)
§5–§6 — that doc's validation plan requires this Function code to exist before it can run.

Once implemented, the Function here will be responsible for mapping Application Insights/Log
Analytics telemetry schema into valid OTLP spans Arize can ingest, while preserving trace ID, span
ID, parent span ID, correlation ID, and token-usage attributes end-to-end (see
`/.github/copilot-instructions.md` §11-§13) — per the specs already written under
`/docs/telemetry/mapping/`.

Only validated, implemented code belongs here once it exists. The future-state idea of bypassing
this pipeline with a direct OTLP exporter is conceptual only and lives under `/docs/future-state` —
it must never be partially implemented here ahead of an accepted architecture decision.

## Known gap (tracked)

This README previously stated an incorrect `validated, implemented` status while this directory
held no code — surfaced by Lead during the Milestone 4 current-state/future-state separation audit
(issue #14, see `/docs/current-state/separation-audit.md` Finding 3; also reflected as a "Partial"
capability in `/docs/architecture/capability-matrix.md`, issue #60 capability #7). Corrected here.
See `.squad/decisions/inbox/lead-telemetry-pipeline-readme-drift.md` for the full finding and
`.squad/decisions/inbox/telemetry-readme-drift-and-issue-37-followup.md` for this fix and the
related issue #37 follow-up.
