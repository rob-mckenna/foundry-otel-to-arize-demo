# Arize Trace Visualization — Validation (#57)

**Status: FUTURE-STATE dependency, fully BLOCKED. No live Arize UI exists to screenshot — see §2.**

Validation record for
[#57 Validate Arize trace visualization](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/57),
depends on #56 (validate Arize ingestion, see
[`arize-ingestion-validation.md`](./arize-ingestion-validation.md) — also blocked).

## 1. Acceptance criteria under validation

1. At least one synthetic multi-span trace (agent → LLM call → tool call) is confirmed to render
   with correct nesting in the Arize trace view.
2. Span kind labels in the UI match the OpenInference span kinds emitted (LLM, tool, retriever,
   chain, as applicable).
3. Token counts are visible/readable on the LLM span in the UI, not just present in underlying
   data.

## 2. Why this is fully blocked

This issue directly depends on #56, which is blocked (no deployed Arize instance). There is no
Arize UI to open, so there is nothing to screenshot or visually confirm. This is a strict
dependency chain: #53/#54/#55/#56/#57 all terminate at the same root cause — no Function
transform code and no deployed Arize instance exist in this repo.

## 3. What exists and was reviewed: a dashboard/visualization *spec*, not a rendered screenshot

[`docs/telemetry/arize-trace-visualization-dashboard.md`](./../telemetry/arize-trace-visualization-dashboard.md)
(#42) specifies the intended 4-panel dashboard layout (timeline, span-kind breakdown, error-rate,
latency distribution) a real Arize deployment should present. This is a design spec for what the
UI *should* show, reviewed for consistency with the OpenInference span kinds this repo's own code
emits (`CHAIN`, `TOOL`, `LLM` — confirmed directly in `tests/test_agent_spans.py`'s attribute
assertions), but it is not a screenshot of an actual rendered Arize trace view, because none can
exist without a live instance.

## 4. Sandbox limitation

No deployed Arize instance and no Python interpreter exist in this session; a screenshot cannot be
fabricated and none is provided here.

## 5. Validation checklist (to run once a deployed Arize instance has ingested a real trace, #56)

- [ ] Send the same multi-span synthetic trace used in #53's cross-system-trace-join procedure
      (agent → LLM call → tool call) through to Arize.
- [ ] Open that trace in the Arize UI; visually confirm parent/child nesting matches the known
      synthetic trace shape (`prompt_agent.invoke` → `tool.lookup_plan_details` +
      `llm.chat_completion`).
- [ ] Confirm the UI's span-kind labels read `CHAIN`/`TOOL`/`LLM` (or Arize's equivalent rendering
      of those OpenInference kinds) matching what the spans actually carry.
- [ ] Confirm `llm.token_count.prompt`/`.completion`/`.total` are visible and readable directly on
      the LLM span in the UI, not only retrievable via API/export.
- [ ] Capture a screenshot (synthetic data only, redact any account/org identifiers) and attach it
      to a `demo-validation.yml` entry as the evidence this issue's acceptance criteria call for.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | Multi-span trace renders with correct nesting | ❌ Blocked — no live Arize UI exists |
| 2 | Span-kind labels match emitted OpenInference kinds | ⚠️ Spec-reviewed only (#42); emitted kinds (`CHAIN`/`TOOL`/`LLM`) confirmed correct at the source, UI rendering not confirmed |
| 3 | Token counts visible/readable in UI | ❌ Blocked — same reason |

**Overall verdict: Blocked — cannot be validated in any form in this sandbox.** Directly downstream
of #56; re-run §5's checklist once a live Arize instance exists and has ingested a real trace.
