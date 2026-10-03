# Field Mapping Spec — Span Kind/Status Fields

> Detail doc for issue [#92](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/92),
> the "span kind/status" field group defined in [`field-mapping.md`](../field-mapping.md) (#36).
> This doc is the authoritative, field-level spec for these fields — `field-mapping.md` stays the
> cross-group summary/index.

**Status: CURRENT-STATE DESIGN, pending Azure Function transform implementation.** No Function
transform code exists in this repo yet (`src/telemetry-pipeline/` is still a placeholder). Every
claim below is a spec requirement the eventual Function implementation must satisfy, not a
description of already-deployed, already-validated behavior.

## 1. Fields in this group

| Field | Azure Monitor source | OTel/Arize destination |
|---|---|---|
| Span name | `Name` (standard `AppDependencies` column) | `span.name` |
| Status | `Success` (standard `AppDependencies` column, bool) | `span.status_code` (`STATUS_CODE_OK`/`STATUS_CODE_ERROR`) |
| Span kind | `customDimensions["openinference.span.kind"]` | `attributes.openinference.span.kind` |
| Retry attempt | `customDimensions["retry.attempt"]` | `attributes.retry.attempt` (int) |
| Retry max attempts | `customDimensions["retry.max_attempts"]` | `attributes.retry.max_attempts` (int) |
| Retry will-retry flag | `customDimensions["retry.will_retry"]` | `attributes.retry.will_retry` (bool) |

**Source record:** `AppDependencies` (span kind varies — applies to every span).

## 2. Transformation logic

1. Read `Name` → set as OTLP span `name`, unchanged.
2. Read `Success` (bool) → map to OTLP `status.code`: `true` → `STATUS_CODE_OK`, `false` →
   `STATUS_CODE_ERROR`. (Status *message*, if any, comes from the span's recorded
   exception/status description, not from `Success` alone.)
3. Read `customDimensions["openinference.span.kind"]` → pass through unchanged as an OTLP span
   attribute. **Present** on `CHAIN`/`TOOL`/`LLM` spans; **absent** on
   `llm.chat_completion.attempt` retry spans. The Function must not inject a synthetic value for
   spans where the source span never set this attribute — absence is meaningful, not a gap to
   paper over.
4. Read the three `retry.*` customDimensions (present only on `llm.chat_completion.attempt` spans,
   and `retry.will_retry` only on failed attempts):
   - `retry.attempt` / `retry.max_attempts` → cast string → `int`.
   - `retry.will_retry` → cast string → `bool`.
   - Pass through with unchanged key names.

## 3. Correlation requirements

Standard `trace_id`/`span_id`/`parent_span_id` preservation applies (see
[`identity-correlation-fields.md`](./identity-correlation-fields.md), #89). **Additionally:**
retry-attempt spans must preserve their parent-child relationship to the enclosing
`llm.chat_completion` span, so a retried call is still visible in Arize as one logical call with N
attempt children, not N disconnected spans with no visible relationship to each other.

## 4. Validation query

```kql
AppDependencies
| where Name in ("prompt_agent.invoke", "tool.lookup_plan_details", "llm.chat_completion", "llm.chat_completion.attempt")
| extend spanKind = tostring(customDimensions["openinference.span.kind"])
| extend retryAttempt = toint(customDimensions["retry.attempt"])
| project timestamp, operation_Id, operation_ParentId, Name, Success, spanKind, retryAttempt
| order by timestamp asc
| take 20
```

Paired Arize-side query (once #38 OTLP export conformance lands):

```
query {
  spans(filter: { resourceAttribute: "service.name", value: "foundry-prompt-agent-demo" },
        timeRange: last_1h) {
    spanId
    parentSpanId
    name
    statusCode
    attributes { key value }
  }
}
```

Expected result: every retry-attempt span in the KQL result has a matching `parentSpanId` in the
Arize result pointing back to the same `llm.chat_completion` span's `spanId`/`operation_ParentId` -
i.e. the attempt tree is reconstructable identically in both systems.

## 5. Acceptance criteria (from issue #92)

- [ ] Field appears in Azure Monitor with the documented name/type
- [ ] Azure Function transformation maps it to the documented OTel/OpenInference attribute without data loss
- [ ] Field is visible on the corresponding span/trace in Arize
- [ ] `trace_id`, `span_id`, and `parent_span_id` remain joinable across all hops for this record
- [ ] Validation query above returns non-null synthetic sample rows

**Validated-via-review today:** the field inventory and retry-span semantics are grounded in #33's
already-merged custom-dimensions schema reference (`custom-dimensions-schema.md`) and the merged
Prompt Agent retry instrumentation (`src/prompt-agent/prompt_agent/retry.py`,
`tests/test_correlation_and_retry.py`). **Requires live-environment re-verification:** the KQL query
has not been run against a live App Insights instance, and the Arize query cannot be run until #38
and a live Arize space exist.

## Related

- [`field-mapping.md`](../field-mapping.md) (#36) — summary/index across all four field groups
- [`custom-dimensions-schema.md`](../custom-dimensions-schema.md) (#33) — schema reference for span-kind/retry fields
- [`identity-correlation-fields.md`](./identity-correlation-fields.md) (#89) — correlation requirement this group depends on
