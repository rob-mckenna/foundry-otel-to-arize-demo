# Decision: Doc-drift checklist (issue #62)

**By:** QA

**What:** Added `CONTRIBUTING.md` at the repo root with a 5-question doc-drift checklist PR
authors should run through before opening a PR (does this change current-state behavior,
future-state design, a referenced setup step, the telemetry transform path, or add a new known
limitation — if so, update the matching doc in the same PR). Validated it retroactively against
PR #74 (network requirements, issue #21) as a worked example showing it would have passed with no
gaps.

**Why:** Per QA's charter, stale docs should be treated as a bug, not a follow-up chore. This is
intentionally lightweight (a mental checklist, not a blocking gate) so it doesn't slow down PR
velocity, while giving reviewers a concrete, repeatable thing to check for rather than relying on
memory.

**Ask for whoever owns `.github/pull_request_template.md` (Lead/Scribe):** please add a short
reference line to `CONTRIBUTING.md` under the template's existing **Documentation Updates**
section (e.g. "See CONTRIBUTING.md's doc-drift checklist"). QA deliberately did not edit the
template directly, per issue #62's own instruction to coordinate on that file rather than editing
it unilaterally.

**Status:** Open for Scribe to merge into `.squad/decisions.md`; open for Lead/Scribe to action the
PR-template reference above.
