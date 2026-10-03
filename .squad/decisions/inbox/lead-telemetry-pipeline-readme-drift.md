# Decision: src/telemetry-pipeline/README.md overstates implementation status

**From:** Lead (Architect / Tech Lead)
**Date:** 2026-10-03
**Affects:** Telemetry track (owner of `/src/telemetry-pipeline`)
**Related:** Issue #14 (current/future-state separation audit), issue #60 (capability matrix),
issue #19, #36

## Finding

`src/telemetry-pipeline/README.md` currently opens with `**Status: CURRENT-STATE (validated,
implemented)**` and states the directory "holds the Azure Function transform/mapping code and
Event Hub consumer logic that forms the validated telemetry pipeline." In reality the directory
contains only that README — no Function transform/consumer code exists yet under
`/src/telemetry-pipeline`.

This was surfaced during the Milestone 4 current-state/future-state separation audit (issue #14,
see `/docs/current-state/separation-audit.md` Finding 3) and reflected as a "Partial" capability in
`/docs/architecture/capability-matrix.md` (issue #60, capability #7).

## Why this wasn't fixed directly

`/src/telemetry-pipeline` is owned by the Telemetry track per `.squad/agents/telemetry/charter.md`.
Lead's charter is explicit about not writing telemetry pipeline code or editing another track's
owned files directly — this is filed as a decision/finding for Telemetry to action instead.

## Suggested resolution (either is acceptable)

1. **Soften the claim** to match `src/prompt-agent/README.md`'s pattern — that README carries the
   same `Status: CURRENT-STATE` header but is accurate because it explicitly flags what's still a
   placeholder (*"This scaffold (#24) ships a placeholder 'hello agent' response only... added
   incrementally in follow-on issues (#25–#31)"*). A similar callout in
   `src/telemetry-pipeline/README.md` (e.g. "Function transform code is tracked in #19/#36 and not
   yet implemented as of this writing") would resolve the drift without any code change.
2. **Implement the Function transform code** referenced by issues #19 (provision Function App —
   already closed, infra only) and #36 (field-by-field mapping doc — already closed, doc only), so
   the README's claim becomes true.

## Action requested

Telemetry (or whoever picks up #19/#36 follow-on work) should apply option 1 or 2 above. No
action is required from Infrastructure, Prompt Agent, or QA tracks.
