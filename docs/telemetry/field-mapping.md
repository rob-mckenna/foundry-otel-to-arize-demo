# Azure Function Transformation — Field-by-Field Mapping (Authoritative Spec)

**Status: CURRENT-STATE DESIGN, pending #19 (Azure Function infrastructure) merge.** This is the
living specification the Azure Function transform step (`Microsoft Monitor record → OTLP`) must
match. **No Azure Function code exists in this repo yet** (`src/telemetry-pipeline/` currently has
only a placeholder `README.md`) — this doc is the authoritative spec to build/audit that Function
against once #19 lands, not a description of deployed behavior. Every field below is grounded in
the attribute inventory already validated in #32/#33/#34 against the merged Prompt Agent source
(`src/prompt-agent/prompt_agent/agent.py`, `retry.py`) — nothing here is invented.

## Field groups and their telemetry-mapping issues

Rather than filing one `telemetry-mapping.yml` issue per individual attribute (which would mean
11+ near-duplicate issues for attributes sharing identical source/transformation/correlation
logic), this doc groups fields by shared transformation characteristics, matching this issue's own
acceptance criterion ("one Telemetry Mapping issue filed per field group"):

| Field group | Fields | Telemetry Mapping issue |
|---|---|---|
| Identity/correlation | `operation_Id`→`trace_id`, `operation_ParentId`→`parent_span_id`, `id`→`span_id`, `correlation.id` | [#89](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/89) |
| Token | `llm.token_count.prompt`, `llm.token_count.completion`, `llm.token_count.total` | [#90](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/90) |
| LLM I/O | `input.value`, `output.value`, `llm.model_name` | [#91](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/91) |
| Span kind/status | `openinference.span.kind`, `Name`, `Success`, `retry.attempt`, `retry.max_attempts`, `retry.will_retry` | [#92](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/92) |

Each linked issue carries the full field-level detail (App Insights source record → Azure Monitor
field → OTel field → OpenInference attribute → Arize destination field → transformation logic →
correlation requirements → validation query) per the `telemetry-mapping.yml` schema. This doc is
the summary/index; the issues are the detailed, independently-trackable spec per group.

## Summary mapping table

| Azure Monitor field | OTLP destination | Type coercion required? | Group |
|---|---|---|---|
| `operation_Id` | `trace_id` | No — already 32 hex chars / 16 bytes, matches W3C `trace_id` width exactly | Identity/correlation |
| `operation_ParentId` | `parent_span_id` | No — already 16 hex chars / 8 bytes | Identity/correlation |
| `id` | `span_id` | No | Identity/correlation |
| `customDimensions["correlation.id"]` | `attributes.correlation.id` | No (string passthrough) | Identity/correlation |
| `customDimensions["llm.token_count.prompt"]` | `attributes.llm.token_count.prompt` | **Yes** — string → `int` (App Insights stores `customDimensions` as strings in the exported JSON even though the SDK set native `int`; see #90) | Token |
| `customDimensions["llm.token_count.completion"]` | `attributes.llm.token_count.completion` | **Yes** — string → `int` | Token |
| `customDimensions["llm.token_count.total"]` | `attributes.llm.token_count.total` | **Yes** — string → `int` | Token |
| `customDimensions["input.value"]` | `attributes.input.value` | No (string passthrough) | LLM I/O |
| `customDimensions["output.value"]` | `attributes.output.value` | No (string passthrough) | LLM I/O |
| `customDimensions["llm.model_name"]` | `attributes.llm.model_name` | No (string passthrough) | LLM I/O |
| `Name` | `span.name` | No | Span kind/status |
| `Success` | `span.status_code` | **Yes** — bool → OTLP status code enum (`true`→`STATUS_CODE_OK`, `false`→`STATUS_CODE_ERROR`) | Span kind/status |
| `customDimensions["openinference.span.kind"]` | `attributes.openinference.span.kind` | No (string passthrough; absent on retry/attempt spans — must not be synthesized) | Span kind/status |
| `customDimensions["retry.attempt"]`, `["retry.max_attempts"]` | `attributes.retry.attempt`, `.max_attempts` | **Yes** — string → `int` | Span kind/status |
| `customDimensions["retry.will_retry"]` | `attributes.retry.will_retry` | **Yes** — string → `bool` (present only on failed retry attempts) | Span kind/status |

**Transform-wide rule:** App Insights exports every `customDimensions` value as a JSON string
regardless of the OTel SDK's original attribute type — any field documented above as a native
`int`/`bool` at the OTel source (per #32/#34) requires an explicit type-cast in the Function, not a
raw passthrough, or it lands in Arize as a quoted string instead of a queryable number/boolean.
This single rule is the most common correctness bug risk in this transform step — call it out
prominently in Function code review once #19/this mapping is implemented.

## No field silently dropped

Every attribute documented in #32 (App Insights custom-dimensions inventory) and #33
(custom-dimensions schema) appears in the mapping table above, in one of the four groups. No
column excluded — consistent with #35's finding that the Log Analytics Data Export mechanism
exports entire rows, not a column subset.

## Dependencies

- Depends on #35 (Log Analytics export baseline) — the Function consumes what that export rule
  streams to Event Hub.
- Depends on #19 (Azure Function infrastructure) — no Function code exists to implement this
  mapping against yet.
- QA should cross-check the eventual Function source against this doc for drift once #19 lands
  (per issue #36's own validation step, see also #61 in the traceability matrix).

## Related

- [`app-insights-custom-dimensions.md`](./app-insights-custom-dimensions.md) (#32)
- [`custom-dimensions-schema.md`](./custom-dimensions-schema.md) (#33)
- [`token-usage-validation.md`](./token-usage-validation.md) (#34)
- [`log-analytics-export-baseline.md`](./log-analytics-export-baseline.md) (#35)
- [`trace-correlation-preservation.md`](./trace-correlation-preservation.md) (#37, the correlation-ID proof this mapping depends on)
