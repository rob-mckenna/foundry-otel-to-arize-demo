# Decision/Risk Note — Milestone 3 (Arize Integration) deliverables

**From:** Telemetry
**Date:** 2026-10-03

## What was delivered

All 10 Milestone 3 issues (#89, #90, #91, #92, #38, #39, #40, #41, #42, #43) were delivered as
doc/spec/query-pack/test-scaffold PRs, each in its own dedicated worktree + branch + PR (no
self-merge), per the same "no live Azure/Arize environment in this sandbox" posture Telemetry used
in Milestone 2:

- #89-#92: field-by-field mapping specs under `docs/telemetry/mapping/` for the four field groups
  `field-mapping.md` (#36) already indexes.
- #41: a 5-query KQL validation pack under `docs/telemetry/kql/`.
- #38: OTLP export conformance spec + a reference-transform test scaffold
  (`tests/export/test_otlp_export_conformance.py`) proving the mapping specs are internally
  consistent — explicitly **not** a test of the production Azure Function, which does not exist in
  this repo yet.
- #39, #40, #42, #43: cross-system trace join, Arize token-analysis view, Arize trace-visualization
  dashboard, and token-analysis parity-check specs, each with hand-computed/hand-traced synthetic
  evidence where executable validation wasn't possible.

## Standing risk/decision for the team

**None of Milestone 3's acceptance criteria that require a live Application Insights instance, a
live Arize space, or the as-yet-unwritten Azure Function transform code (src/telemetry-pipeline/ is
still a placeholder) have been executed.** Every doc in this milestone explicitly splits
"validated-via-review" (field inventory, query syntax, arithmetic, cross-references to already-
merged Milestone 1/2 docs — all correct independent of environment) from "requires
live-environment re-verification" (anything needing a real KQL run, a real Arize query, or a real
OTLP export). Whoever implements #19's Function transform code should treat these 10 docs as the
spec to build against and re-run every validation query/test listed once live infra exists — do not
treat "PR merged" as equivalent to "live-validated" for this milestone.

## Follow-up risk carried forward

Reconfirms the Milestone 2 flag already in Infra's history: Event Hub partition-key choice and
Function batch-checkpointing strategy remain the two places a correlation ID could still be lost
end-to-end, and nothing in this milestone's doc work closes that gap — it can only be closed once
#19's Function code and live infra exist to test against.
