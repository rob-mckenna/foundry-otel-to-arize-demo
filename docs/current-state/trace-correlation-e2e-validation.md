# Trace-Correlation Preservation End-to-End — Validation (#53)

**Status: CURRENT-STATE (source-side validated; cross-system/live-environment validation BLOCKED
— see §3.)**

Validation record for
[#53 Validate trace-correlation preservation end-to-end](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/53),
depends on #50 and #37. **Note:** #37 was reopened during this validation pass (see
`.squad/decisions/inbox/telemetry-readme-drift-and-issue-37-followup.md`) because it had been
closed without the live evidence its own acceptance criteria require — this doc's conclusions are
consistent with, and build directly on, that finding.

## 1. Acceptance criteria under validation

1. A multi-span synthetic trace (agent span + at least one tool/child span) is used, not a
   single-span trivial case.
2. Trace ID, span count, and parent/child graph match exactly between App Insights (KQL) and Arize
   (UI/API).
3. Any correlation break is filed as a bug with the exact hop identified (App Insights → Event
   Hub, Event Hub → Function, Function → Arize).

## 2. What is validated today — statically, via code review + existing tests

- **Criterion 1's trace shape already exists and is proven in-process.**
  `tests/test_agent_spans.py::test_invoke_creates_expected_span_tree` proves exactly the required
  shape: `prompt_agent.invoke` (root/CHAIN) with two children, `tool.lookup_plan_details` (TOOL)
  and `llm.chat_completion` (CLIENT), all three sharing one `trace_id`, correct
  `parent.span_id` linkage, all `StatusCode.OK`. This is a real multi-span trace, not a trivial
  single-span case — criterion 1 is satisfied for the source (Prompt Agent) hop.
- **Format compatibility for the App Insights ↔ OTel hop is already documented.**
  [`docs/telemetry/trace-correlation-preservation.md`](./../telemetry/trace-correlation-preservation.md)
  §1 proves (by direct reasoning about the Azure Monitor OpenTelemetry Exporter's own behavior,
  not empirically) that `operation_Id`/`operation_ParentId` require no re-encoding to become
  `trace_id`/`parent_span_id` — same hex width, same encoding.
- **The exact paired query pattern this issue's criterion 2 calls for is already specified.**
  [`docs/telemetry/cross-system-trace-join.md`](./../telemetry/cross-system-trace-join.md) (#39)
  defines one synthetic 5-span trace with the paired KQL (App Insights side) and Arize (API/UI
  side) queries to run, plus a mismatch-diagnosis runbook that identifies exactly which of the
  three hops (App Insights → Event Hub, Event Hub → Function, Function → Arize) a break occurred
  at — directly satisfying criterion 3's "exact hop identified" requirement, as a procedure.

## 3. What is NOT validated — blocked on missing infrastructure

**This criterion cannot be satisfied today, for the same reason #37 was reopened:** there is no
Event Hub, no Azure Function transform code (`src/telemetry-pipeline` contains no implementation —
see the corrected README, PR #121), and no deployed Arize instance in this repo. Concretely:

- Criterion 2's "match exactly between App Insights (KQL) and Arize (UI/API)" **cannot be run** —
  there is no Arize side to query, and no App Insights side either (no deployed instance, same gap
  as #50).
- Criterion 3's bug-filing requirement is moot — there is no live pipeline to observe a correlation
  break in. Filing a bug here would fabricate a defect that cannot currently be observed to exist
  or not exist.
- `trace-correlation-preservation.md` §3–§4 already documents two specific, as-yet-unvalidated
  risks (Event Hub partition-key choice, Function batch-checkpointing strategy) that must be
  resolved by whoever implements #19's Function code, *before* this validation can even be
  attempted live — these are implementation requirements, not just test gaps.

## 4. Sandbox limitation

No Event Hub, no Function transform code, no deployed Arize instance, and no Python interpreter
exist in this session — identical limitation set to #37, #39, #50.

## 5. Validation checklist (to run once #19's Function code + Event Hub + Arize all exist)

Directly reuses [`cross-system-trace-join.md`](./../telemetry/cross-system-trace-join.md)'s (#39)
procedure:

- [ ] Generate the synthetic multi-span trace via `PromptAgent.invoke()` with a real
      `APPLICATIONINSIGHTS_CONNECTION_STRING` configured.
- [ ] Run the App Insights-side KQL query for the resulting `operation_Id`.
- [ ] Run the Arize-side trace query (UI or API) for the same ID.
- [ ] Diff span count and parent/child edges between the two results.
- [ ] If they match: record Pass in a `demo-validation.yml` entry, citing both query results as
      evidence.
- [ ] If they don't: use `cross-system-trace-join.md`'s mismatch-diagnosis runbook to localize the
      exact hop, then file a `bug-report.yml` citing that hop, the trace ID, and the specific
      divergence (span missing, parent mismatch, etc.) — never raw telemetry content.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | Multi-span synthetic trace used | ✅ Validated — existing test proves exactly this shape at the source hop |
| 2 | Trace ID/span count/parent-child match App Insights ↔ Arize | ❌ Blocked — no Event Hub, Function, or Arize deployment exists; cannot be run |
| 3 | Correlation breaks filed with exact hop identified | N/A — no live pipeline to observe a break in; procedure specified (#39) for when one exists |

**Overall verdict: Blocked** — this is the demo's single most scrutinized correctness claim, and
honesty here matters more than anywhere else in this batch: the source-side half (criterion 1) is
proven; the cross-system half (criteria 2–3) cannot be demonstrated until #19's Function
transform code is implemented and both an Event Hub and an Arize instance are deployed. This
mirrors, and does not contradict, the #37 reopening finding above.
