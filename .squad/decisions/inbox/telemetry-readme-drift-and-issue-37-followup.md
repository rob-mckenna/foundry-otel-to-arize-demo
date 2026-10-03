# Decision/Follow-up: telemetry-pipeline README corrected; issue #37 closed without evidence

**From:** Telemetry (Observability / Telemetry Pipeline Engineer)
**Date:** 2026-10-03
**Affects:** Telemetry track, Lead (audit owner), anyone relying on issue #37 as closed/proven
**Related:** `.squad/decisions/inbox/lead-telemetry-pipeline-readme-drift.md` (Lead's original
finding), issues #14, #19, #36, #37, #60

## Action taken on the README drift finding

Applied **option 1** from Lead's finding: `src/telemetry-pipeline/README.md` now states
`Status: CURRENT-STATE (architecture track), implementation PENDING`, explicitly calls out that
the directory holds no Function transform/consumer code yet, and links to the mapping specs
(#89–#92, #36) and to `docs/telemetry/trace-correlation-preservation.md` as the source of truth on
what's validated-via-review vs. still open. No code was written — this is a documentation-accuracy
fix only, same pattern as `src/prompt-agent/README.md`.

## Additional finding: issue #37 was closed without a backing artifact

While fixing the README I checked issue #37 ("Trace/span/parent-span/correlation-ID preservation
across Event Hub and Function hops"). It is **closed (stateReason: COMPLETED)** with **zero
comments** and no linked PR/commit. Its acceptance criteria require:

1. A synthetic multi-span trace round-tripping through Event Hub + Function + landing in Arize as
   one connected trace — **cannot be true**, since no Event Hub consumer/Function transform code
   exists in `src/telemetry-pipeline` (confirmed above) and no Arize instance is deployed in this
   sandbox.
2. Flagged risks at every hop where correlation IDs could drop — this part **is** satisfied, by
   `docs/telemetry/trace-correlation-preservation.md` §3–§4 (written in Milestone 2).
3. Expected evidence: "KQL result + Arize trace detail view/API query result showing matching span
   count and parent linkage" — **no such evidence is attached to the issue or exists in the repo.**

`trace-correlation-preservation.md` itself is explicit that this validation is **not yet run** (see
its own §5 "Validation plan (to run once #17 and #19 are merged and deployed)" and §6 "Known
risks" table, both still open). So the doc and the issue's actual state agree with each other —
the mismatch is specifically that **issue #37 was marked closed/completed despite its own
documented validation plan saying the work hasn't happened.**

## Resolution

Reopened issue #37 with a comment linking to `trace-correlation-preservation.md` §5/§6 as the
live status of record, and reframing its remaining scope as "blocked on #19's Function transform
code + a deployed Event Hub/Arize environment" rather than "done." No new acceptance criteria were
added — the original criteria stand; they're just now accurately marked not-yet-met.

## Follow-up risk for whoever implements #19's Function code

Once the Function transform exists, re-run `trace-correlation-preservation.md` §5's validation
plan end-to-end and update both that doc's §6 risk table and issue #37 with the real pass/fail
result before re-closing #37. Do not close #37 again without attaching the KQL + Arize evidence its
acceptance criteria call for.
