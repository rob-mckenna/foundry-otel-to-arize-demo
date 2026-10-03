# Field Mapping Spec — Token Fields

> Detail doc for issue [#90](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/90),
> the "token" field group defined in [`field-mapping.md`](../field-mapping.md) (#36). This doc is
> the authoritative, field-level spec for these three fields — `field-mapping.md` stays the
> cross-group summary/index.

**Status: CURRENT-STATE DESIGN, pending Azure Function transform implementation.** No Function
transform code exists in this repo yet (`src/telemetry-pipeline/` is still a placeholder). Every
claim below is a spec requirement the eventual Function implementation must satisfy, not a
description of already-deployed, already-validated behavior.

## 1. Fields in this group

| Field | Azure Monitor source | OpenInference attribute | Arize destination | Type coercion required? |
|---|---|---|---|---|
| Prompt tokens | `customDimensions["llm.token_count.prompt"]` | `llm.token_count.prompt` | `attributes.llm.token_count.prompt` | **Yes** — string → `int` |
| Completion tokens | `customDimensions["llm.token_count.completion"]` | `llm.token_count.completion` | `attributes.llm.token_count.completion` | **Yes** — string → `int` |
| Total tokens | `customDimensions["llm.token_count.total"]` | `llm.token_count.total` | `attributes.llm.token_count.total` | **Yes** — string → `int` |

**Source record:** `AppDependencies`, span kind `CLIENT` — specifically the OpenInference LLM span
(`llm.chat_completion`, see `src/prompt-agent/prompt_agent/agent.py`).

**OTel field note:** this repo uses the OpenInference key directly (`llm.token_count.*`) rather than
the newer `gen_ai.usage.*` semantic convention. This is a deliberate current-state choice (the
Prompt Agent's instrumentation predates the `gen_ai.*` convention's adoption here) — not a gap.

## 2. Transformation logic

1. Parse the `customDimensions` JSON blob from the Log Analytics row.
2. Extract the three `llm.token_count.*` keys.
3. **Cast each from the Log Analytics string representation to an OTLP `INT_VALUE`-typed span
   attribute.** App Insights stores every `customDimensions` value as a string in the exported JSON
   even though the OTel SDK set them as native `int` — see
   [`token-usage-validation.md`](../token-usage-validation.md) (#34) and `field-mapping.md`'s
   "Transform-wide rule." The Function **must** `int()`-cast, not just pass the string through, or
   Arize's numeric aggregation views (#40) receive quoted strings instead of queryable numbers —
   this is the single highest-risk correctness bug class in the whole transform step.
4. Set as OTLP span attributes with unchanged key names — no renaming.

## 3. Correlation requirements

Token fields carry no identity information themselves — they only need to stay attached to the
correct `trace_id`/`span_id` as that span passes through Event Hub/Function (see
[`identity-correlation-fields.md`](./identity-correlation-fields.md), #89). No special correlation
handling is needed beyond that.

## 4. Validation query

```kql
AppDependencies
| where customDimensions["openinference.span.kind"] == "LLM"
| extend promptTok = toint(customDimensions["llm.token_count.prompt"])
| extend compTok = toint(customDimensions["llm.token_count.completion"])
| extend totalTok = toint(customDimensions["llm.token_count.total"])
| extend consistent = (promptTok + compTok == totalTok)
| summarize count(), countif(consistent == false)
```

Paired Arize-side aggregation (see #40 for the dashboard/view this feeds):

```
query {
  spanAggregation(
    groupBy: "attributes.llm.model_name",
    metric: SUM,
    field: "attributes.llm.token_count.total",
    timeRange: last_1h
  ) { group, value }
}
```

Expected result: `count_` ≥ 20 (per #34's "20+ synthetic spans" bar), `countif_` (inconsistent
count) == 0, and the Arize sum matches the hand-computed total for the same synthetic batch exactly
(no sampling in this demo's data path).

## 5. Acceptance criteria (from issue #90)

- [ ] Field appears in Azure Monitor with the documented name/type
- [ ] Azure Function transformation maps it to the documented OTel/OpenInference attribute without data loss
- [ ] Field is visible on the corresponding span/trace in Arize
- [ ] `trace_id`, `span_id`, and `parent_span_id` remain joinable across all hops for this record
- [ ] Validation query above returns non-null synthetic sample rows, zero inconsistent rows

**Validated-via-review today:** the field inventory and type-coercion requirement are grounded in
`token-usage-validation.md` (#34), which already proves (via source inspection + an unexecuted-but-
reasoned test suite — no Python interpreter in this sandbox) that `agent.py` sets these three
attributes as native `int` on every LLM span, with `prompt + completion == total` structurally
guaranteed. **Requires live-environment re-verification:** the KQL query has not been run against a
live App Insights instance, and the Arize aggregation query cannot be run until #38 (OTLP export
conformance) and #40 (token analysis views) exist with a live Arize space.

## Related

- [`field-mapping.md`](../field-mapping.md) (#36) — summary/index across all four field groups
- [`token-usage-validation.md`](../token-usage-validation.md) (#34) — source-side token capture proof
- [`identity-correlation-fields.md`](./identity-correlation-fields.md) (#89) — correlation requirement this group depends on
- [#40 Token analysis views in Arize](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/40)
- [#43 Combined token-analysis query set (App Insights + Arize parity check)](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/43)
