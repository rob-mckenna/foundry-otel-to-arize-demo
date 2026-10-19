# Azure Function Transformation — Field-by-Field Mapping (Authoritative Spec)

**Status: CURRENT-STATE mapping specification and implementation reference.** The Azure Function
transform (`Azure Monitor record → OTLP`) is implemented in
`src/telemetry-pipeline/telemetry_pipeline/mapping.py`. Local mapping and durable-admission tests
validate the native root-marker behavior below; they do not establish deployment or durable
activation. Every field in the original mapping table below is grounded in
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

## Native LAW span rows and observed root markers

The mapper accepts native `AppDependencies` and `AppRequests` rows alongside legacy fixtures.
Native columns normalize as follows: `OperationId` → `operation_Id`, `Id` → `id`,
`ParentId` → `operation_ParentId`, `Properties` → `customDimensions`,
`TimeGenerated` → `timestamp`, `DurationMs` → `duration`, and
`AppRoleName`/`AppRoleInstance` → `cloud_RoleName`/`cloud_RoleInstance`.
Supplied native and legacy aliases must agree; conflicts are rejected.

**Observed AppRequests evidence (2026-10-19):** the coordinator's metadata-only LAW query
reported 1,939 native `AppRequests` rows in the preceding 24 hours, all with a 32-hex W3C
`OperationId`, a 16-hex W3C `Id`, and `ParentId == OperationId`. `Name` was present,
`Success` was boolean, and `DurationMs` was real-valued; no GenAI request kind was present.
This is evidence for the observed native AppRequests shape, not a claim that all undocumented
32-hex parent values are root markers. The same equal marker was already supported for the
observed synthetic AppDependencies root.

For these native tables, when native `OperationId` and a 32-character native `ParentId`
are supplied, both must parse as valid nonzero trace IDs and be equal (hex case-insensitive).
Only that equal marker maps to an absent OTLP parent: a true root span, not an invented parent.
`AppRequests` maps to OTLP `SERVER` even without GenAI/OpenInference kind attributes.
Original trace/span IDs, name, status, timestamp precision, duration, and supplied token
attributes retain their existing mappings; missing token/kind attributes are not fabricated.
Normalization does not mutate the source row.

A mismatched or malformed 32-hex native parent is still rejected. Legacy-only or partially
aliased identity rows retain strict parent-span validation and do not gain this exception.
Invalid originals still fail durable admission with backpressure; this change does not skip
them or filter AppRequests out of the export.

Regression coverage reuses the native root-marker tests in
`tests/telemetry-mapping/test_native_dependencies.py` and the admission/export tests in
`src/telemetry-pipeline/tests/test_durable.py`, including native AppRequests without GenAI
attributes and optional token-preserving enrichment. Local success is not rollout evidence.

## No field silently dropped

Every attribute documented in #32 (App Insights custom-dimensions inventory) and #33
(custom-dimensions schema) appears in the mapping table above, in one of the four groups. No
column excluded — consistent with #35's finding that the Log Analytics Data Export mechanism
exports entire rows, not a column subset.

## Dependencies

- Depends on #35 (Log Analytics export baseline) — the Function consumes what that export rule
  streams to Event Hub.
- Azure Function infrastructure is tracked in #19; the mapping implementation exists under
  `src/telemetry-pipeline/`.
- QA should cross-check the Function source against this doc for drift
  (per issue #36's own validation step, see also #61 in the traceability matrix).

## Related

- [`app-insights-custom-dimensions.md`](./app-insights-custom-dimensions.md) (#32)
- [`custom-dimensions-schema.md`](./custom-dimensions-schema.md) (#33)
- [`token-usage-validation.md`](./token-usage-validation.md) (#34)
- [`log-analytics-export-baseline.md`](./log-analytics-export-baseline.md) (#35)
- [`trace-correlation-preservation.md`](./trace-correlation-preservation.md) (#37, the correlation-ID proof this mapping depends on)
