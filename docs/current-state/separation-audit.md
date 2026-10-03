# Current-State vs. Future-State Separation Audit

**Status: CURRENT-STATE (validated audit finding — this is a record of a review, not a design doc).**

Full-repo audit confirming that no future-state/conceptual content has leaked into `/src` or
`/infra`, and that every current-state claim is accurate, per `/.github/copilot-instructions.md`
§4/§16 and issue #14. Performed as part of Milestone 4 (Customer Demo Readiness).

## Scope and method

- Searched every file under `/src` and `/infra` for conceptual/future-state language
  (`future-state`, `conceptual`, `direct OTLP`/`direct-otlp`, `sidecar`).
- Searched every file under `/docs` (outside `/docs/future-state`) for the same terms, to confirm
  any hit is a legitimate cross-reference pointing *at* `/docs/future-state` rather than
  conceptual content leaking into a current-state document.
- Confirmed every file under `/docs/future-state` carries the "CONCEPTUAL — NOT IMPLEMENTED" label.
- Cross-checked every "Status: CURRENT-STATE (validated, implemented)" header found in `/src` and
  `/infra` READMEs against the actual files present in that directory.

## Findings

### 1. Zero conceptual code found under `/src` or `/infra` ✅

Every `future-state`/`conceptual`/`direct OTLP`/`sidecar` hit under `/src` and `/infra` is a guard
-rail cross-reference pointing at `/docs/future-state` (e.g. `src/prompt-agent/README.md` and
`src/telemetry-pipeline/README.md` both explicitly state that conceptual direct-OTLP export ideas
belong under `/docs/future-state`, not as stubs here). No implementation code, partial
implementation, or stub for the future-state direct-OTLP design exists anywhere under `/src` or
`/infra`. `infra/main.bicep` wires exactly six current-state modules (`foundry-project`,
`app-insights`, `event-hub`, `function-app`, `key-vault`, `networking`/`naming`) — no
direct-to-Arize or sidecar-exporter module exists.

### 2. Every file under `/docs/future-state` carries the required label ✅

`/docs/future-state/README.md` is currently the only file in the directory and carries the
"⚠️ **CONCEPTUAL — NOT IMPLEMENTED.**" label in its first paragraph. (The direct-OTLP design doc
itself, `/docs/future-state/direct-otlp.md`, is being authored under issue #63 as part of the same
Milestone 4/5 effort and will carry the same label per its own acceptance criteria.)

### 3. One current-state labeling drift found 🟡 — not fixed here, routed to Telemetry

`src/telemetry-pipeline/README.md` opens with `**Status: CURRENT-STATE (validated, implemented)**`
and states "This directory holds the Azure Function transform/mapping code and Event Hub consumer
logic that forms the validated telemetry pipeline." In reality, `src/telemetry-pipeline/` contains
only that README — no Function or consumer code exists yet. By contrast,
`src/prompt-agent/README.md` carries the same status header but is accurate, because it explicitly
calls out which parts are implemented vs. still a placeholder (*"This scaffold (#24) ships a
placeholder 'hello agent' response only... added incrementally in follow-on issues (#25–#31)"*).

This is a genuine drift, not a false positive: a reader of `src/telemetry-pipeline/README.md` alone
would reasonably believe Function transform code already exists and is validated, when it does not.
It does not violate the "no conceptual code in `/src`" rule (nothing here is future-state content —
the directory is simply ahead of its own documentation), but it does violate the "every
current-state claim is cross-checked... any mismatch is filed as a doc-bug" requirement of this
audit (#14) and the "no reader should infer validation that hasn't happened" rule
(`copilot-instructions.md` §16).

**Disposition:** Filed as a finding here rather than corrected in place, because
`/src/telemetry-pipeline` is owned by the Telemetry track (see `.squad/agents/telemetry/charter.md`)
and Lead's charter is explicit that Lead does not write telemetry pipeline code or edit another
track's owned files. Recommended fix (for Telemetry or a future PR against that directory): either
soften the status line to reflect what's actually implemented today (mirroring
`src/prompt-agent/README.md`'s pattern of calling out the placeholder/incremental state explicitly),
or implement the Function transform code referenced by issue #19/#36 so the claim becomes true. This
finding is also captured in the Milestone 4 capability matrix (`/docs/architecture/capability-matrix.md`,
issue #60, capability #7) and in a decision note routed to Telemetry
(`.squad/decisions/inbox/lead-telemetry-pipeline-readme-drift.md`).

### 4. Capability matrix cross-reference ✅

See `/docs/architecture/capability-matrix.md` (issue #60) for the full capability-by-capability
done/partial/not-started breakdown this audit informed.

## Conclusion

- **Zero conceptual code found under `/src` or `/infra`.** ✅ Acceptance criterion met.
- **Every file under `/docs/future-state` carries the "CONCEPTUAL — NOT IMPLEMENTED" label.** ✅
  Acceptance criterion met.
- **One doc-accuracy drift found and documented** (see Finding 3) — routed to Telemetry rather than
  silently fixed, per track-ownership boundaries. No other drift found across `/docs`, `/src`, or
  `/infra`.

This audit should be re-run (or at minimum re-skimmed) whenever Milestone 3 (Arize Integration) or
Milestone 5 (Future-State Design) issues close, since both introduce new current-state and
future-state content respectively.
