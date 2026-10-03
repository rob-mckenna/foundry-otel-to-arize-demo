# Demo Validation Plan

> Consolidated from QA's Demo Experience validation issues ([#49](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/49)–[#58](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/58))
> and Telemetry's pipeline validation work ([#32](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/32)–[#43](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/43)).
> **Synthetic prompts and data only** — no raw production telemetry, healthcare data, or personal data
> appears in any step or piece of evidence. No capability below is considered demo-ready until its
> validation task has passed with real, captured evidence (not just "it looked fine").

## Shared Synthetic Test-Data Set

Defined once in [#48 Demo Validation Plan: structure and synthetic test-data set](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/48)
and reused across every step below:

- 5–10 synthetic, non-clinical, generic health-education-style prompts (e.g., "What are common cold
  symptoms?", "What is my synthetic deductible?") — never real member/plan/clinical data.
- Fake member IDs prefixed `SYN-` (e.g., `SYN-00042`), fake plan name ("Acme Synthetic PPO").
- At least one multi-span scenario (agent → LLM call → tool call) for correlation/visualization tests.
- At least one long prompt/response near Application Insights' 8KB property size limit, to test truncation.

**Evidence-capture convention:** every step captures (a) the trace ID used, (b) the exact query run (KQL
and/or Arize), (c) the result, and (d) a Pass / Pass with caveats / Fail verdict, using the
`demo-validation.yml` issue form fields. Screenshots, when used, must redact any account/org identifiers.

## Validation Steps

### 1. Prompt Agent execution — [#49](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/49)
Run every synthetic prompt through the deployed Prompt Agent. Confirm a well-formed, non-empty, relevant
response and a root span with a valid trace ID for each.
**Pass condition:** 100% of prompts return a coherent response + valid root span.

### 2. Application Insights telemetry capture — [#50](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/50)
For each trace ID from step 1, confirm a matching record lands in `AppDependencies`/`AppTraces` within 5
minutes, with the expected custom dimensions (per [#32](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/32)/[#33](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/33)) present and non-null.
```kql
AppDependencies
| where operation_Id == "<synthetic-trace-id>"
| project timestamp, Name, customDimensions
```
**Pass condition:** every trace ID from step 1 has a matching, complete App Insights record.

### 3. Prompt/response telemetry behavior — [#51](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/51)
Diff captured `input.value`/`output.value` against the actual synthetic prompt/response sent, character for
character, including one long-prompt edge case for truncation.
**Pass condition:** exact match on short cases; long case either matches or documents truncation as a known
limitation.

### 4. Token metric collection — [#52](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/52)
Run the token-consistency KQL query ([#34](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/34)) across the full synthetic set.
```kql
AppDependencies
| where customDimensions["openinference.span.kind"] == "LLM"
| extend promptTok = toint(customDimensions["llm.token_count.prompt"])
| extend compTok = toint(customDimensions["llm.token_count.completion"])
| extend totalTok = toint(customDimensions["llm.token_count.total"])
| extend consistent = (promptTok + compTok == totalTok)
| summarize count(), countif(consistent == false)
```
**Pass condition:** `countif(consistent == false) == 0` across the full set.

### 5. Trace-correlation preservation end-to-end — [#53](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/53)
Using a multi-span synthetic trace, run the paired KQL (App Insights) and Arize query for the same trace ID
and diff span count + parent/child graph.
```kql
AppDependencies
| where operation_Id == "<synthetic-trace-id>"
| project operation_Id, operation_ParentId, id, Name
| order by timestamp asc
```
Arize side: query the trace by `trace_id` and confirm matching span count/parent linkage.
**Pass condition:** exact match between systems; any break is filed as a bug naming the specific hop
(App Insights → Event Hub, Event Hub → Function, Function → Arize).

### 6. Export-pipeline execution — [#54](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/54)
For each synthetic trace, confirm the Event Hub message was consumed (no consumer-group backlog beyond the
expected window) and the Function execution log shows success (no exceptions).
**Pass condition:** zero stuck messages, zero Function execution failures across the synthetic batch.

### 7. Telemetry transformation correctness — [#55](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/55)
Capture the Function's transformed OTLP payload for a sample of traces and diff field-by-field against the
mapping doc ([#36](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/36)), including a
no-tool-call vs. multi-tool-call structural edge case.
**Pass condition:** every field matches the mapping doc's spec; any mismatch is filed as a bug referencing
the specific mapping-doc row.

### 8. Arize ingestion — [#56](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/56)
Send a known-count synthetic batch (50+ spans); compare sent count vs. Arize-visible count.
**Pass condition:** span count sent == span count visible in Arize, no rejected/partial-success responses.

### 9. Arize trace visualization — [#57](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/57)
Open the multi-span synthetic trace in the Arize UI; confirm correct timeline nesting, span-kind labels
matching OpenInference kinds (LLM/tool/retriever/chain), and visible token counts on the LLM span.
**Pass condition:** structure and labels render correctly; token counts are human-visible, not just present
in underlying data.

### 10. Error/retry handling and exporter observability — [#58](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/58)
Induce three failure modes against a synthetic request:
  a. Transient model/tool failure → confirm bounded retry per policy ([#30](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/30)), with each retry attempt visible as its own span carrying `retry.attempt`.
  b. Export-pipeline outage (e.g., Function temporarily disabled) → confirm no silent data loss (Event Hub
     queues messages, or failure is logged/alerted).
  c. Exporter observability → confirm export success/failure counts are visible (Function's own App
     Insights telemetry or Event Hub metrics); file a gap issue for anything missing.
**Pass condition:** each scenario marked Pass / Pass with caveats / Fail with evidence; no silent failures.

## Summary Table

| # | Capability | Issue | Depends On |
|---|---|---|---|
| 1 | Prompt Agent execution | [#49](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/49) | #48 |
| 2 | App Insights telemetry capture | [#50](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/50) | #49, #32 |
| 3 | Prompt/response telemetry behavior | [#51](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/51) | #50 |
| 4 | Token metric collection | [#52](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/52) | #50, #34 |
| 5 | Trace-correlation preservation | [#53](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/53) | #50, #37 |
| 6 | Export-pipeline execution | [#54](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/54) | #50, #35, #36 |
| 7 | Telemetry transformation correctness | [#55](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/55) | #36 |
| 8 | Arize ingestion | [#56](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/56) | #38 |
| 9 | Arize trace visualization | [#57](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/57) | #56 |
| 10 | Error/retry handling + exporter observability | [#58](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/58) | #30, #36 |

Each row maps to exactly one of the 11 demo-proof capabilities listed in the README's "What this demo
proves" section (capability #1, Prompt Agent execution, is also implicitly validated by step 1 above, and
appears twice across the original 11-item list and this 10-step plan because "OpenTelemetry trace
generation" is folded into step 1's root-span check).
