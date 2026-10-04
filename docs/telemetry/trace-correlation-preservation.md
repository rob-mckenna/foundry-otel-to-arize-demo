# Trace/Span/Parent-Span/Correlation-ID Preservation Across Event Hub and Function Hops

**Status: PARTIALLY VALIDATED.** Source-side (Prompt Agent → OTel SDK) identifier generation and
propagation is validated today with synthetic multi-span traces (§2). Preservation across Event
Hub partitioning/batching and the Azure Function transform (§3–§4) **cannot be validated
end-to-end yet** — the Azure Function transform code now exists and is unit-tested with synthetic
data (`src/telemetry-pipeline/telemetry_pipeline/`, see §5's update), but no live Event Hub (#17)
has been deployed and no live Arize space exists, so the actual cross-system round trip this issue's
third acceptance criterion requires still cannot be run. This doc documents the exact conversion
logic those components must implement, and explicitly flags every hop where identifiers could be
lost, per this issue's own acceptance criteria. Per Telemetry's charter, any hop that *could* drop a
correlation ID is flagged here as a risk requiring Lead sign-off before being accepted as a known
limitation — it is not silently waved through.

## 1. Format compatibility: App Insights `operation_Id`/`operation_ParentId` ↔ OTel `trace_id`/`span_id`

| Identifier | App Insights format | OTel W3C Trace Context format | Compatible? |
|---|---|---|---|
| Trace ID | `operation_Id` — 32 lowercase hex characters (GUID-like, no dashes) | `trace_id` — 16 bytes, rendered as 32 lowercase hex characters | ✅ **Exact width match.** No zero-padding, truncation, or re-encoding needed — this is because the Azure Monitor OpenTelemetry Exporter (used in `telemetry.py`) already writes the OTel SDK's own 16-byte `trace_id` into `operation_Id` in this exact hex format at the App Insights hop. There is no lossy round-trip here as long as the Function treats `operation_Id` as an opaque 32-hex-char string and copies it verbatim. |
| Span ID | `id` — 16 lowercase hex characters | `span_id` — 8 bytes, rendered as 16 lowercase hex characters | ✅ Exact width match, same reasoning. |
| Parent span ID | `operation_ParentId` — 16 lowercase hex characters (empty/absent for a root span) | `parent_span_id` — 8 bytes / 16 hex characters | ✅ Exact width match. **Root spans** (e.g. `prompt_agent.invoke`, the top of every request tree) have no `operation_ParentId` — the Function must treat an empty/missing value as "no parent," not coerce it to a zero-filled span ID, which would make a root span look like a child of a bogus all-zero span. |

**Conclusion: no hex-encoding or zero-padding conversion is actually needed** between App
Insights' and OTel's identifier formats for this pipeline — they are already the same width and
encoding. The real risk is entirely in *whether the value survives each hop unchanged*, not in any
format conversion (§3).

## 2. Source-side validation (today, synthetic data, in-memory span capture)

`src/prompt-agent/tests/test_agent_spans.py::test_invoke_creates_expected_span_tree` already proves
a synthetic 3-span tree (`prompt_agent.invoke` → `tool.lookup_plan_details` + `llm.chat_completion`,
both children) shares one `trace_id` and has correct `parent.span_id` linkage, via
`InMemorySpanExporter` — no live Azure resources required. `test_correlation_and_retry.py` further
proves `correlation.id` (the app-level join key, independent of OTel's own trace_id) is identical
across every span in a request tree, including every retry attempt span, both on success and on
exhausted-retry failure.

This satisfies the **generation and in-process propagation** half of this issue's acceptance
criteria. It does **not** by itself prove anything about Event Hub/Function behavior — that
requires §3/§4 below, which are currently a documented design + risk list, not a live-validated
result.

## 3. Risk: Event Hub partitioning/batching

Event Hub distributes events across partitions (by partition key, or round-robin if no key is
set) and delivers them to consumers in batches. Two risks follow directly from this:

1. **Partition-key choice determines ordering guarantees.** Event Hub only guarantees in-order
   delivery *within* a single partition. If the Log Analytics Data Export rule (or whatever writes
   to Event Hub) does not use a consistent partition key per trace (e.g. `operation_Id` as the
   partition key), spans belonging to the same trace could land in different partitions and be
   delivered out of order relative to each other. **Recommendation for #17's Bicep module /
   whatever wiring owns this:** use `operation_Id` (the trace ID) as the Event Hub partition key so
   every span of one trace is guaranteed to stay in relative order within one partition. This is a
   design requirement this doc is flagging now, before #17 implements the export wiring — not an
   already-solved problem.
2. **Consumer group checkpoint failure.** If the Function's Event Hub consumer crashes or scales
   between reading a batch and checkpointing its position, Event Hub's at-least-once delivery
   model means that batch is redelivered — this is safe for trace/span IDs (same span re-processed
   with the same identifiers, not regenerated) **as long as the Function's downstream OTLP export
   to Arize is idempotent or Arize safely de-duplicates by `(trace_id, span_id)`**. This is flagged
   as a risk requiring validation once #19 (Function) exists — not yet validated.

**No span is dropped-vs-reordered scenario has been empirically tested** (no live Event Hub
exists) — §5 below is the plan to validate this once #17/#19 land.

## 4. Risk: Function batch partial failure

If the Function processes a batch of N Event Hub events and fails partway through (e.g. an
unhandled exception on event 7 of 10), the standard Azure Functions Event Hub trigger behavior
depends on checkpointing configuration:

- If checkpointing happens **after the whole batch succeeds**, a partial failure means the *entire*
  batch (including the 6 already-successfully-transformed events) is redelivered and reprocessed —
  safe for identifier preservation (same IDs reprocessed), but means downstream Arize ingestion
  must tolerate duplicate spans for the same `(trace_id, span_id)`.
- If checkpointing happens **per-event**, a partial failure means events 1–6 are durably
  checkpointed (sent to Arize, not reprocessed) but event 7 (and 8–10) are lost unless the Function
  explicitly retries them before returning. **This is the dangerous configuration for correlation
  preservation** — if event 7 was, say, the parent `prompt_agent.invoke` span and it's dropped
  while its children (tool/LLM spans) already made it through, Arize would show orphaned child
  spans with no visible parent.

**Recommendation, flagged for #19's implementation:** the Function must use whole-batch
checkpointing (or equivalent explicit retry-before-checkpoint logic) specifically *because* of this
risk — a per-event-checkpoint-with-silent-drop configuration would be a blocking defect for trace
correlation, not an acceptable known limitation, per Telemetry's charter policy on correlation-ID
loss.

## 5. Validation plan

**Update (this pass):** the Azure Function transform code this plan depends on now exists —
`src/telemetry-pipeline/telemetry_pipeline/` (`mapping.py`, `batch.py`, `exporter.py`,
`function_app.py`). Its synthetic 3-span batch test
(`src/telemetry-pipeline/tests/test_batch_trace_preservation.py`) already proves, in-memory/mocked
(no live Event Hub or Function host), that a `prompt_agent.invoke` → `tool.lookup_plan_details` +
`llm.chat_completion` batch delivered as one Event Hub message (the Log Analytics
`{"records": [...]}` envelope) is transformed into 3 `ReadableSpan`s sharing one `trace_id` with
correct parent linkage, exported together in a single `exporter.export()` call. **This closes the
"no code exists" blocker** that previously stood in front of every step below — it does not, by
itself, satisfy steps 3–4, which require a live Event Hub (#17) and a live Arize space (#38) that
still do not exist in this repo. The plan below is otherwise unchanged:

1. Generate a synthetic 3-span trace via the Prompt Agent (`prompt_agent.invoke` → `llm.chat_completion`
   → `tool.lookup_plan_details`, using `synthetic/scenarios.py` fixtures only).
2. Confirm it in Log Analytics:
   ```kql
   AppDependencies
   | where operation_Id == "<synthetic-trace-id>"
   | project operation_Id, operation_ParentId, id, Name
   | order by timestamp asc
   ```
3. Confirm the same `operation_Id` appears in the Event Hub consumer / Function execution logs
   (once #19 exists) with 3 events, in the order shown above (or provably reconstructable in order
   via timestamps if the partition-key recommendation in §3 isn't followed).
4. Query Arize by `trace_id` (== the 32-hex `operation_Id` value, per §1's "no conversion needed"
   conclusion) and confirm span count == 3 with correct parent linkage matching the
   `operation_ParentId` values from step 2.
5. Record pass/fail and any discrepancy explicitly in this doc's "Known Risks" section below —
   never silently drop a failed check.

## 6. Known risks (flagged, not yet accepted as limitations)

| Risk | Status |
|---|---|
| Event Hub partition-key choice not yet implemented (no #17 code exists yet to set it) | **Open — flagged for #17 implementation, see §3.1** |
| Function batch-checkpointing strategy | **Addressed in code (this pass):** `telemetry_pipeline.batch.transform_batch()` exports every span from one Event Hub message batch in a single `exporter.export()` call, never per-record — matching §4's whole-batch-checkpointing recommendation. Still **unvalidated against the Functions host's real checkpointing behavior**, since no live Function App deployment exists to observe it against. |
| No live end-to-end round trip has been run (blocked on #17 deployment + live Arize) | **Open — §5 is the plan to close this once a live Event Hub and Arize space exist. The Function code itself (the other half of this blocker) now exists and is unit-tested — see `src/telemetry-pipeline/`.** |

None of the above are accepted as current-state limitations — they are open implementation
requirements this doc puts in front of whoever implements #17/#19, consistent with charter policy
of treating correlation-ID risk as a blocking concern rather than a silently-accepted gap.

## Related

- [`app-insights-custom-dimensions.md`](./app-insights-custom-dimensions.md) (#32)
- [`field-mapping.md`](./field-mapping.md) (#36) — identity/correlation field group ([#89](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/89)) is this doc's direct companion
- [`log-analytics-export-baseline.md`](./log-analytics-export-baseline.md) (#35)
