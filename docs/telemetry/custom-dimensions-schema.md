# Custom Dimensions Schema — Span Kind Coverage

**Status: CURRENT-STATE (with one documented gap).** Reference table for every span kind the
Foundry Prompt Agent emits today, built directly from `src/prompt-agent/prompt_agent/agent.py` and
`retry.py` (merged #26–#31), plus the attribute inventory in
[`app-insights-custom-dimensions.md`](./app-insights-custom-dimensions.md) (#32). Intended as the
one-page reference for customer architects — no need to read Azure Function or agent source to know
what telemetry exists.

All span kinds below land in Application Insights `AppDependencies` (see §1 of
`app-insights-custom-dimensions.md` for why — no `SERVER`/`CONSUMER`-kind spans exist yet).

## Span kind reference table

| Span kind (`openinference.span.kind`) | Example span name(s) | OTel `SpanKind` | Required custom dimensions | Optional / conditional custom dimensions |
|---|---|---|---|---|
| **LLM** (model/chat-completion call) | `llm.chat_completion` | `CLIENT` | `openinference.span.kind` = `LLM`, `correlation.id`, `input.value`, `output.value`, `llm.model_name`, `llm.token_count.prompt`, `llm.token_count.completion`, `llm.token_count.total` | none — all of the above are set unconditionally on every LLM span (see #34 for the "100% of LLM spans" validation) |
| **TOOL** (tool/function call) | `tool.lookup_plan_details` | `CLIENT` | `openinference.span.kind` = `TOOL`, `correlation.id`, `input.value`, `output.value` | none currently defined — the agent's one tool call has no optional/parameterized attributes today. A future tool with multiple named parameters would need its own `telemetry-mapping.yml` entry before being added |
| **CHAIN** (agent/orchestration span) | `prompt_agent.invoke` | `INTERNAL` | `openinference.span.kind` = `CHAIN`, `correlation.id`, `input.value`, `output.value` | none |
| **RETRIEVER** / **EMBEDDING** | *(not emitted — see gap note below)* | — | — | — |
| *(retry/attempt — not an OpenInference kind)* | `llm.chat_completion.attempt` | `CLIENT` | `correlation.id`, `retry.attempt`, `retry.max_attempts` | `retry.will_retry` (bool) — set only on failed attempts, per `retry.py`'s "only failed attempts record will_retry" behavior |

## Gap note: RETRIEVER / EMBEDDING span kind

The issue asks this doc to cover "LLM call, tool/function call, retriever/embedding call,
chain/agent orchestration span." **The Prompt Agent does not perform any retrieval or embedding
call today** — `agent.py`'s only externally-visible calls are the synthetic plan-lookup tool
(`TOOL` kind) and the model completion call (`LLM` kind). There is no RAG/vector-search step in the
current implementation, so no `RETRIEVER`/`EMBEDDING`-kind span exists to document.

This is recorded here as an explicit **documented gap**, not an invented/placeholder schema — per
`copilot-instructions.md` §16 ("clearly label assumptions, limitations, and unvalidated behavior").
If a retriever/embedding step is added to the Prompt Agent in the future (Agent's boundary, not
Telemetry's), the OpenInference spec's `RETRIEVER` span kind conventionally expects at minimum
`retrieval.documents` (or the current spec's equivalent) and an `embedding.*` attribute group for
embedding spans — documented here only as forward guidance for whoever implements it, not as
proof any such span exists.

## Cross-reference to telemetry-mapping issues (#32)

Per issue #33's acceptance criterion ("cross-referenced against the telemetry-mapping issues filed
under #32"): #32's doc does not itself file one `telemetry-mapping.yml` issue per individual
attribute (11 attributes would mean 11 near-duplicate issues for attributes that share identical
transformation logic). Issue #36's field-mapping doc instead files one `telemetry-mapping.yml`
issue per **field group** — identity/correlation, token, LLM I/O, and span-kind/status — each of
which is directly traceable back to a row in the table above via its "pipeline stage" and attribute
list. See [`field-mapping.md`](./field-mapping.md) once #36 lands.

## Validation queries (one per span kind, synthetic data only)

```kql
// LLM span kind
AppDependencies
| where customDimensions["openinference.span.kind"] == "LLM"
| take 3
```

```kql
// TOOL span kind
AppDependencies
| where customDimensions["openinference.span.kind"] == "TOOL"
| take 3
```

```kql
// CHAIN span kind
AppDependencies
| where customDimensions["openinference.span.kind"] == "CHAIN"
| take 3
```

```kql
// Retry/attempt spans (not an OpenInference kind, but part of the full schema)
AppDependencies
| where Name == "llm.chat_completion.attempt"
| take 3
```

```kql
// RETRIEVER / EMBEDDING — expected to return zero rows today; a non-zero
// result would mean a retriever/embedding span kind was added to the agent
// without this doc being updated first (doc-drift check, see copilot-instructions.md §16/#62)
AppDependencies
| where customDimensions["openinference.span.kind"] in ("RETRIEVER", "EMBEDDING")
| take 3
```

**Note on running these queries:** no live Application Insights instance exists in this validation
pass (same scope note as `app-insights-custom-dimensions.md` §Scope) — these queries are ready to
run once a live workspace is populated by a synthetic demo invocation; spot-checking them is listed
as this issue's own validation step and should be re-run by whoever deploys the first live App
Insights instance.
