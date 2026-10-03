# Decision/Risk: Milestone 4 (Customer Demo Readiness) telemetry-validation batch summary

**From:** Telemetry (Observability / Telemetry Pipeline Engineer)
**Date:** 2026-10-03
**Affects:** Whoever picks up #19's Function implementation; Lead (Milestone 5 planning); QA
**Related:** #50-#58, #37 (reopened), #121-#129, #131, #130 (new gap issue)

## Summary

Delivered validation docs for all 9 Milestone 4 issues assigned (#50-#58) plus a README-drift fix
(#121, addressing Lead's finding in
`.squad/decisions/inbox/lead-telemetry-pipeline-readme-drift.md`). No live Azure/Arize environment
or Python interpreter exists in this sandbox, so every doc is explicit about
validated-via-review vs. blocked/requires-live-environment, per repo convention.

## Net result, grouped by what's actually provable today

- **Source-side (Prompt Agent) telemetry capture is solid.** #50 (App Insights capture, partial —
  exporter wiring + span-attribute shape proven, live ingestion blocked), #51 (prompt/response
  fidelity, pre-export proven exact-match; long-prompt truncation test identified as a genuine gap
  and not yet written), #52 (token metrics, fully proven by an existing 25-span test suite),
  and #58 part (a) (retry visibility, fully proven) are all backed by real, already-written,
  already-passing-by-design unit tests in `src/prompt-agent/tests/`.
- **Everything downstream of the Prompt Agent is blocked, not partially passing.** #53
  (cross-system correlation), #54 (export-pipeline execution), #55 (transformation correctness),
  #56 (Arize ingestion), #57 (Arize visualization), and #58 part (b) (export-pipeline outage
  handling) all terminate at the same root cause: **no Azure Function transform/consumer code
  exists under `src/telemetry-pipeline`, and no Arize instance has ever been deployed in this
  repo's history.** These are marked Blocked, not Pass-with-caveats — there is a real difference
  between "an acceptance criterion that's awkward to test" and "an acceptance criterion whose
  subject doesn't exist yet," and conflating them would misrepresent demo readiness to Lead/QA.

## Issue #37 reopened

While fixing the README drift, found issue #37 ("Trace/span/parent-span/correlation-ID
preservation across Event Hub and Function hops") was closed (`COMPLETED`, zero comments, no
linked PR) despite requiring live KQL+Arize evidence that doesn't exist. Reopened it with an
explanatory comment. See `.squad/decisions/inbox/telemetry-readme-drift-and-issue-37-followup.md`
(PR #121) for the full writeup — not repeating it here to avoid duplication.

## New gap filed: #130 (exporter observability)

Found a concrete, fixable-today gap while validating #58: `telemetry.py`'s `shutdown_tracing()`
discards `force_flush()`'s return value, and no export success/failure counter exists. Filed as
issue #130 (Effort: S, no new infra required) rather than deferred.

## Recommendation for Milestone 5 / whoever implements #19

Treat #53-#57 and #58(b) as the concrete scope of "implement + validate the export pipeline,"
using the Milestone 3 specs (`docs/telemetry/*.md`) as the build spec and the Milestone 4 docs
created in this batch (`docs/current-state/*-validation.md`) as the checklists to re-run once
real infrastructure exists — do not treat any of those 6 items as already passing.
