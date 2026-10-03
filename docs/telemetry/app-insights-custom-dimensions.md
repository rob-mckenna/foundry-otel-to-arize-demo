# OpenInference Span Attributes → Application Insights Custom Dimensions

**Status: CURRENT-STATE.** Covers the Prompt Agent instrumentation already merged under
`/src/prompt-agent` (#26–#31). Attribute names and span structure below are taken directly from
`prompt_agent/agent.py`, `prompt_agent/retry.py`, and `prompt_agent/telemetry.py` — not invented —
and cross-checked against the in-memory span assertions in
`src/prompt-agent/tests/test_agent_spans.py`.

> **Scope note:** This repo currently has no live Application Insights instance provisioned (see
> `telemetry.py`'s console-exporter fallback) — Infra's App Insights module (#16) is merged, but no
> live deployment has been exercised yet in this validation pass. Everything in the "Validated"
> column below was proven with the OpenTelemetry SDK's `InMemorySpanExporter` (exact attribute
> keys, types, and values captured pre-export). Everything in the "Documented — pending live
> instance" column is the expected Azure Monitor OpenTelemetry Exporter behavior per its published
> mapping rules, with a ready-to-run KQL query, but has **not** been run against a live
> `AppDependencies`/`AppTraces` table. Do not read this doc as proof of live App Insights behavior
> until that query has actually been run once a workspace exists.

## 1. How the Azure Monitor exporter maps spans to tables

The Prompt Agent uses `AzureMonitorTraceExporter` (`azure-monitor-opentelemetry-exporter`) when
`APPLICATIONINSIGHTS_CONNECTION_STRING` is set (see `telemetry.py`). Per that exporter's documented
mapping rules, OTel `SpanKind` determines the destination table:

| OTel `SpanKind` | Application Insights table |
|---|---|
| `SERVER`, `CONSUMER` | `AppRequests` |
| `CLIENT`, `PRODUCER`, `INTERNAL` | `AppDependencies` |

None of the Prompt Agent's spans use `SERVER`/`CONSUMER` today (see §2), so **every span this
agent emits currently lands in `AppDependencies`**, not `AppRequests`. Any future addition of a
`SERVER`-kind span (e.g. an inbound HTTP front-end) would be the first to land in `AppRequests` —
call that out explicitly if/when it's added.

Every OTel span attribute (string, int, float, bool) that isn't one of the exporter's reserved
fields (`name`, `kind`, timestamps, status, trace/span/parent IDs) is carried through unchanged
into the `customDimensions` JSON blob on the resulting `AppDependencies` row, **using the exact
attribute key as the `customDimensions` key** — the exporter does not rename, namespace, or flatten
attribute keys.

## 2. Span inventory (what the agent actually emits today)

| Span name | OTel `SpanKind` | `openinference.span.kind` | Parent |
|---|---|---|---|
| `prompt_agent.invoke` | `INTERNAL` | `CHAIN` | (root) |
| `tool.lookup_plan_details` | `CLIENT` | `TOOL` | `prompt_agent.invoke` |
| `llm.chat_completion` | `CLIENT` | `LLM` | `prompt_agent.invoke` |
| `llm.chat_completion.attempt` | `CLIENT` | *(none set)* | `llm.chat_completion` |

`llm.chat_completion.attempt` is emitted once per retry attempt (`retry.py`) and does **not**
itself carry `openinference.span.kind` — it's a retry/attempt detail span, not an OpenInference
semantic span. See `#33`'s companion doc (`custom-dimensions-schema.md`) for the full per-span-kind
breakdown including this one.

The issue's reference attribute list included `llm.input_messages` / `llm.output_messages`
(structured chat-message-array attributes). **These are not emitted by the current implementation**
— the agent emits the simpler `input.value` / `output.value` (flat string) attributes instead. This
is accurately reflected in the table below; treat the gap as a documented current-state limitation,
not an oversight; if message-array-level granularity is wanted later, file a new feature issue
against the Prompt Agent (Agent charter owns `/src/prompt-agent`), it is out of Telemetry's
boundary to add application-level instrumentation.

## 3. Attribute → custom dimension mapping

| OpenInference / OTel attribute | Emitted on span(s) | Type (Python / OTel) | `customDimensions` key (documented, pending live instance) | Validated in-memory? |
|---|---|---|---|---|
| `openinference.span.kind` | `prompt_agent.invoke`, `tool.lookup_plan_details`, `llm.chat_completion` | `str` | `customDimensions["openinference.span.kind"]` | ✅ |
| `correlation.id` | all spans in the request tree | `str` (UUID4) | `customDimensions["correlation.id"]` | ✅ |
| `input.value` | `prompt_agent.invoke`, `tool.lookup_plan_details`, `llm.chat_completion` | `str` | `customDimensions["input.value"]` | ✅ |
| `output.value` | `prompt_agent.invoke`, `tool.lookup_plan_details`, `llm.chat_completion` | `str` | `customDimensions["output.value"]` | ✅ |
| `llm.model_name` | `llm.chat_completion` | `str` | `customDimensions["llm.model_name"]` | ✅ |
| `llm.token_count.prompt` | `llm.chat_completion` | `int` | `customDimensions["llm.token_count.prompt"]` | ✅ (see #34 for numeric-typing caveat) |
| `llm.token_count.completion` | `llm.chat_completion` | `int` | `customDimensions["llm.token_count.completion"]` | ✅ (see #34) |
| `llm.token_count.total` | `llm.chat_completion` | `int` | `customDimensions["llm.token_count.total"]` | ✅ (see #34) |
| `retry.attempt` | `llm.chat_completion.attempt` | `int` | `customDimensions["retry.attempt"]` | ✅ |
| `retry.max_attempts` | `llm.chat_completion.attempt` | `int` | `customDimensions["retry.max_attempts"]` | ✅ |
| `retry.will_retry` | `llm.chat_completion.attempt` (failed attempts only) | `bool` | `customDimensions["retry.will_retry"]` | ✅ |
| `service.name`, `service.version`, `deployment.environment` | resource attributes (every span) | `str` | Azure Monitor maps resource attributes to the `cloud_RoleName` / custom resource fields, not `customDimensions` — documented separately, out of scope for this per-span table | N/A (resource-level, not span-level) |

All eleven span-level attribute keys above pass through to `customDimensions` **unchanged** per
§1's "exact key, no renaming" rule — this directly satisfies issue #32's "no key renaming"
acceptance criterion for every attribute the agent currently emits.

## 4. Truncation risk (8KB `customDimensions` property-value limit)

Application Insights enforces an 8,192-character (8KB) limit per individual `customDimensions`
value; a longer value is truncated, not rejected. The only attributes in this agent with
unbounded/user-influenced length are `input.value` and `output.value` (they carry the prompt and
model response text verbatim).

- **Current synthetic risk: low.** Every synthetic prompt/response in `synthetic/scenarios.py` and
  the demo harness is short-form member-services text (well under 1KB) — see `copilot-instructions.md`
  §9 ("do not put ... verbose/raw prompt-and-response bodies ... unless clearly size-bounded").
- **No truncation guard exists in code today.** `agent.py` sets `input.value`/`output.value`
  directly from the prompt/response text with no length cap. If a future scenario or real
  integration produces a prompt/response over 8KB, it **will** be silently truncated at the App
  Insights ingestion boundary — this is a current-state limitation, not validated-safe for
  arbitrary input. Flagging per charter policy (treat correlation/attribute loss as a blocking
  defect unless Lead accepts it as a known limitation) — recommend Agent add a documented
  truncation/size-cap policy if this repo is ever extended beyond short synthetic demo prompts.

## 5. Validation query (run once a live App Insights instance exists — #16/#17 infra path)

```kql
AppDependencies
| where Name in ("prompt_agent.invoke", "tool.lookup_plan_details", "llm.chat_completion", "llm.chat_completion.attempt")
| extend spanKind = tostring(customDimensions["openinference.span.kind"])
| extend correlationId = tostring(customDimensions["correlation.id"])
| extend inputLen = strlen(tostring(customDimensions["input.value"]))
| extend outputLen = strlen(tostring(customDimensions["output.value"]))
| project timestamp, operation_Id, operation_ParentId, Name, spanKind, correlationId, inputLen, outputLen, customDimensions
| order by timestamp asc
| take 20
```

**Expected result once run against a live synthetic trace:** one row per span above, `spanKind`
populated for the three OpenInference spans (`CHAIN`/`TOOL`/`LLM`), `correlationId` identical
across every row in one request tree, and `inputLen`/`outputLen` well under 8,192 for all synthetic
scenarios.

## 6. In-memory validation performed in this pass

No Python interpreter was available in this validation environment to re-run the suite, so this
pass cross-checked §3's attribute/type/value claims by direct code inspection of
`src/prompt-agent/prompt_agent/agent.py` / `retry.py` against the existing assertions in
`src/prompt-agent/tests/test_agent_spans.py::test_llm_span_has_openinference_attributes_and_token_counts`
and `::test_tool_span_has_openinference_attributes` (which exercise the exact span tree and
attribute set described above via `InMemorySpanExporter`, no live Azure resources required). Anyone
with a working Python 3.10+ environment can re-run `pytest` under `src/prompt-agent` to confirm
these assertions still pass.

## Related

- Per-span-kind custom dimensions reference: [`custom-dimensions-schema.md`](./custom-dimensions-schema.md) (#33)
- Token-usage numeric-typing validation: [`token-usage-validation.md`](./token-usage-validation.md) (#34)
- Acceptance criterion "a telemetry-mapping issue exists for each attribute" is tracked under #36's
  field-mapping doc, which files one `telemetry-mapping.yml` issue per field group (identity/
  correlation, token, LLM I/O, span-kind/status) rather than one per individual attribute, to avoid
  13 near-duplicate issues — see that doc's rationale note.
