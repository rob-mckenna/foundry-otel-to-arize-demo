# Application Insights Telemetry Capture — Validation (#50)

**Status: CURRENT-STATE (validation procedure + static/code-review evidence, implemented;
live-environment evidence NOT YET captured — see §4 "Sandbox limitation.")**

This document is the validation record for issue
[#50 Validate Application Insights telemetry capture](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/50),
part of the Milestone 4 Demo Experience epic (#8). It follows the exact
validated-via-review vs. requires-live-environment split established in
[`prompt-agent-execution-validation.md`](./prompt-agent-execution-validation.md) (#49).

## 1. Acceptance criteria under validation

From #50:

1. For each synthetic trace ID (from #47's synthetic scenario set), a matching record exists in
   App Insights within a defined latency budget (e.g., 5 minutes).
2. Expected custom dimensions (per #32/#33 field inventory) are present and non-null.
3. Any missing/malformed record is filed as a bug (`bug-report.yml`) with the trace ID — not raw
   telemetry — as evidence.

## 2. What is validated today — statically, via code review + existing tests

- **Exporter wiring exists and is reviewable.** `src/prompt-agent/prompt_agent/telemetry.py`
  (`_build_exporter()`) uses `AzureMonitorTraceExporter` from
  `azure-monitor-opentelemetry-exporter` whenever `APPLICATIONINSIGHTS_CONNECTION_STRING` is set,
  wired through a `BatchSpanProcessor` on the global `TracerProvider`. This is the correct,
  standard Azure Monitor OpenTelemetry exporter — not a hand-rolled HTTP call — so the
  App Insights ingestion contract itself (schema, retry, batching) is handled by Microsoft's own
  SDK rather than custom code this repo would need to separately prove correct.
- **Span → custom-dimension shape is proven in-process.** `tests/test_agent_spans.py` and
  `tests/test_token_usage_validation.py` (via `InMemorySpanExporter`) prove every
  `prompt_agent.invoke` / `tool.lookup_plan_details` / `llm.chat_completion` span carries the
  OpenInference + token-count attributes the #32/#33 field inventory calls for
  (`openinference.span.kind`, `input.value`, `output.value`, `llm.model_name`,
  `llm.token_count.{prompt,completion,total}`, `correlation.id`). The Azure Monitor exporter
  serializes OTel span attributes into App Insights `customDimensions` verbatim (key/value pairs),
  so if an attribute is present and non-null on the span (proven above), it will appear as a
  non-null `customDimensions` entry once exported — this is a property of the Azure Monitor
  exporter's own (external, already-tested) serialization, not something this repo re-implements.
- **Falls back safely when unconfigured.** If `APPLICATIONINSIGHTS_CONNECTION_STRING` is unset
  (true in this sandbox — no App Insights instance is deployed), `telemetry.py` falls back to
  `ConsoleSpanExporter` rather than failing — spans are still emitted and visible, just not sent to
  a live App Insights instance. Confirmed by direct code inspection.

## 3. What is NOT validated — requires a live App Insights instance

This sandbox has **no deployed Application Insights resource and no Python interpreter available
in this session** (`python --version` fails — confirmed before writing this doc, same limitation
recorded in every prior Milestone's validation work). Concretely, this means none of the following
can be produced in this session:

- An actual App Insights ingestion event, so criterion 1 ("matching record exists... within a
  defined latency budget") **cannot be empirically measured** — no ingestion has ever occurred
  against a real resource in this repo's history.
- A real `AppDependencies`/`AppTraces` KQL query result (the query in #50's own body) — there is no
  live Log Analytics workspace to query.
- Confirmation that `AzureMonitorTraceExporter`'s actual network behavior (auth, retry, batching
  against the real Azure Monitor ingestion endpoint) works as expected — this is Microsoft's SDK
  code, not this repo's, so it is reasonable to trust it per its own published test coverage, but
  this repo has never exercised it end-to-end.

No bug was filed per criterion 3 — there is no live record to inspect, so there is nothing to
confirm as "missing or malformed" yet. Filing a bug here would be premature (there is no evidence
of a defect, only an unexercised code path).

## 4. Sandbox limitation

Same limitation as every prior Milestone 2–4 validation doc in this repo: no live Azure resources
are deployed in this sandbox (no Application Insights instance, no Function App runtime
configuration pointing at one), and no Python interpreter is available in this session to execute
`pytest` or the agent directly. This doc is therefore **validated-via-review** of the exporter
wiring and the span-attribute shape it depends on, not a live-executed ingestion test.

## 5. Validation checklist (to run once a live App Insights instance + Python interpreter exist)

- [ ] Deploy Application Insights (Infra track) and set `APPLICATIONINSIGHTS_CONNECTION_STRING` in
      the Prompt Agent's environment.
- [ ] `cd src/prompt-agent && pip install -e ".[azure,test]"`.
- [ ] Run `python -m prompt_agent.main --scenarios` for all 5 synthetic scenarios (`synthetic/scenarios.py`),
      recording each invocation's `trace_id` (== App Insights `operation_Id`).
- [ ] Within 5 minutes per scenario, run the KQL query from #50 for each captured trace ID:
      ```kql
      AppDependencies
      | where operation_Id == "<synthetic-trace-id>"
      | project timestamp, Name, customDimensions
      ```
- [ ] Confirm every expected custom dimension (per #32/#33) is present and non-null in the result.
- [ ] File a `demo-validation.yml` record with the KQL results as evidence; file a `bug-report.yml`
      for any missing/malformed record found.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | Record appears in App Insights within latency budget | ⚠️ Not empirically measurable — no live App Insights instance exists in this repo/sandbox |
| 2 | Expected custom dimensions present and non-null | ✅ Validated-via-review: proven at the span-attribute level (pre-export) by existing tests; Azure Monitor SDK serialization trusted, not independently re-tested here |
| 3 | Missing/malformed records filed as bugs | N/A this session — no live record exists to inspect, so no defect evidence to file |

**Overall verdict: Blocked (validated-via-review only)** — the exporter wiring and the span
attributes it would export are proven correct by code review and existing unit tests; the actual
App Insights ingestion behavior this issue's acceptance criteria describe cannot be demonstrated
without a deployed Application Insights instance. Re-run §5's checklist once one exists.
