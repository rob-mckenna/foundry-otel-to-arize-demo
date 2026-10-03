# Field Mapping Spec — Identity/Correlation Fields

> Detail doc for issue [#89](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/89),
> the "identity/correlation" field group defined in [`field-mapping.md`](../field-mapping.md) (#36).
> This doc is the authoritative, field-level spec for these four fields — `field-mapping.md` stays
> the cross-group summary/index.

**Status: CURRENT-STATE DESIGN, pending Azure Function transform implementation.** No Function
transform code exists in this repo yet (`src/telemetry-pipeline/` is still a placeholder — see that
directory's `README.md`); the Azure Function App *shell* (infra only, issue #19) is provisioned,
but it does not yet contain the Event Hub → OTLP mapping logic this doc specifies. Every claim
below is a spec requirement the eventual Function implementation must satisfy, not a description of
already-deployed, already-validated behavior.

## 1. Fields in this group

| Field | Azure Monitor source | OTel destination | OpenInference attribute | Arize destination |
|---|---|---|---|---|
| Trace ID | `operation_Id` | `trace_id` | — (OTel core, not OpenInference) | `context.trace_id` |
| Parent span ID | `operation_ParentId` | `parent_span_id` | — (OTel core) | `context.parent_span_id` |
| Span ID | `id` | `span_id` | — (OTel core) | `context.span_id` |
| Correlation ID | `customDimensions["correlation.id"]` | *(no direct OTel equivalent — app-level attribute, see `src/prompt-agent/prompt_agent/correlation.py`)* | `correlation.id` (custom, not part of the OpenInference spec — app-defined join key, see #29) | `attributes.correlation.id` |

**Source record:** `AppDependencies` (span kind varies — `INTERNAL`/`CLIENT` — this group applies
to *every* span the Prompt Agent emits, not just one span kind).

## 2. Transformation logic

1. Parse the Event Hub event envelope (the Log Analytics Data Export row, delivered as JSON).
2. Read `operation_Id` (32 lowercase hex characters, App Insights' GUID-like trace identifier).
   Validate it is exactly 32 hex characters, then set it verbatim as the OTLP span context
   `trace_id`. **No padding/re-encoding is needed** — `operation_Id` is already 32 hex chars / 16
   bytes, the exact width the W3C `trace_id` format requires (see
   [`trace-correlation-preservation.md`](../trace-correlation-preservation.md) §1 for the full
   byte-width proof). The Function must explicitly validate length/hex-format and reject or flag
   malformed rows rather than silently truncating or coercing them.
3. Read `operation_ParentId` (16 hex chars). If present, map directly to OTLP `parent_span_id` (8
   bytes / 16 hex chars — same width, no conversion). If **absent** (root spans, e.g.
   `prompt_agent.invoke`), the Function must represent "no parent," never a zero-filled span ID —
   coercing an empty value to all-zeros would make a root span look like a child of a bogus span.
4. Read `id` → map to OTLP `span_id` verbatim.
5. Read `customDimensions["correlation.id"]` → set as an OTLP span attribute `correlation.id`
   (string, unchanged key name, no renaming).

## 3. Correlation requirements

This is the **highest-risk field group in the entire pipeline**. See
[`trace-correlation-preservation.md`](../trace-correlation-preservation.md) (#37) for the full
proof/risk analysis of lossless preservation across Event Hub partitioning/batching and the
Function transform step. Any hop that regenerates, reorders, or truncates
`operation_Id`/`operation_ParentId`/`id` breaks cross-system trace stitching in Arize and **must be
treated as a blocking defect, not a known limitation**, unless Lead explicitly accepts it as a
current-state limitation (per Telemetry's charter).

## 4. Validation query

```kql
AppDependencies
| where operation_Id == "<synthetic-test-trace-id>"
| project operation_Id, operation_ParentId, id, Name
| order by timestamp asc
| take 10
```

Paired Arize-side query (once #38 OTLP export conformance lands and ingestion is live):

```
query {
  spans(filter: { traceId: "<synthetic-test-trace-id>" }) {
    traceId
    spanId
    parentSpanId
    attributes { key value }
  }
}
```

Expected result: the App Insights query's `operation_Id`/`operation_ParentId`/`id` triples match
the Arize query's `traceId`/`parentSpanId`/`spanId` values 1:1, same row count, same parent/child
structure. This is the field-level building block that issue #39's cross-system join test exercises
end-to-end.

## 5. Acceptance criteria (from issue #89)

- [ ] Field appears in Azure Monitor with the documented name/type
- [ ] Azure Function transformation maps it to the documented OTel/OpenInference attribute without data loss
- [ ] Field is visible on the corresponding span/trace in Arize
- [ ] `trace_id`, `span_id`, and `parent_span_id` remain joinable across all hops for this record
- [ ] Validation query above returns non-null synthetic sample rows

**Validated-via-review today:** the field inventory, format-compatibility proof (§1 above, backed by
`trace-correlation-preservation.md` §1), and transformation logic (§2) are reasoned through against
merged Prompt Agent source and documented App Insights export behavior. **Requires live-environment
re-verification:** the KQL query has not been run against a live App Insights instance in this pass
(no live Azure resources in this sandbox — see Telemetry's Milestone 2 history entry), and the Arize
query cannot be run at all until #38 (OTLP export conformance) and a live Arize space exist. Both
are flagged as open items, not silently assumed to pass.

## Related

- [`field-mapping.md`](../field-mapping.md) (#36) — summary/index across all four field groups
- [`trace-correlation-preservation.md`](../trace-correlation-preservation.md) (#37) — the correlation-ID risk proof this group depends on
- [#39 Trace/span correlation preserved into Arize (cross-system join test)](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/39)
