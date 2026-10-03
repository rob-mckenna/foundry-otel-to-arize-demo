# Field Mapping Spec — LLM I/O Fields

> Detail doc for issue [#91](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/91),
> the "LLM I/O" field group defined in [`field-mapping.md`](../field-mapping.md) (#36). This doc is
> the authoritative, field-level spec for these three fields — `field-mapping.md` stays the
> cross-group summary/index.

**Status: CURRENT-STATE DESIGN, pending Azure Function transform implementation.** No Function
transform code exists in this repo yet (`src/telemetry-pipeline/` is still a placeholder). Every
claim below is a spec requirement the eventual Function implementation must satisfy, not a
description of already-deployed, already-validated behavior.

## 1. Fields in this group

| Field | Azure Monitor source | OpenInference attribute | Arize destination |
|---|---|---|---|
| Input value | `customDimensions["input.value"]` | `input.value` | `attributes.input.value` |
| Output value | `customDimensions["output.value"]` | `output.value` | `attributes.output.value` |
| Model name | `customDimensions["llm.model_name"]` | `llm.model_name` | `attributes.llm.model_name` |

**Source record:** `AppDependencies`, span kind `INTERNAL`/`CLIENT` — covers all three
OpenInference span kinds the agent emits (`CHAIN`, `TOOL`, `LLM`).

**OTel field note:** these fields have **no OTel-core equivalent** — they are OpenInference-specific
attributes, not part of base OTel semantic conventions.

## 2. Transformation logic

1. Parse the `customDimensions` JSON blob.
2. Extract `input.value`/`output.value` (strings, carried through unchanged — no type coercion
   needed) and `llm.model_name` (string).
3. Set as OTLP span attributes with unchanged key names. No flattening/renaming.

**Size note (known current-state gap, not fixable at this step):** `input.value`/`output.value` are
flagged in #32 §4 as having no truncation guard against the App Insights 8KB `customDimensions`
value limit. The Function's transformation logic must pass through whatever length survived the
App Insights hop — no *additional* truncation introduced at this step — but it cannot recover
anything already truncated upstream of it. This is documented here as an explicit current-state
limitation, not silently assumed away.

## 3. Correlation requirements

Standard `trace_id`/`span_id`/`parent_span_id` preservation applies (see
[`identity-correlation-fields.md`](./identity-correlation-fields.md), #89) — no additional
correlation logic specific to these three fields.

## 4. Validation query

```kql
AppDependencies
| where customDimensions["openinference.span.kind"] in ("CHAIN", "TOOL", "LLM")
| extend inputVal = tostring(customDimensions["input.value"])
| extend outputVal = tostring(customDimensions["output.value"])
| extend modelName = tostring(customDimensions["llm.model_name"])
| project timestamp, operation_Id, Name, inputVal, outputVal, modelName
| take 10
```

Paired Arize-side query (once #38 OTLP export conformance lands):

```
query {
  spans(filter: { resourceAttribute: "service.name", value: "foundry-prompt-agent-demo" },
        timeRange: last_1h) {
    spanId
    traceId
    attributes { key value }
  }
}
```

Expected result: non-null `inputVal`/`outputVal`/`modelName` for every `CHAIN`/`TOOL`/`LLM` span in
the KQL result, with the same string values (byte-for-byte, up to the 8KB truncation caveat above)
visible on the matching span's `attributes.input.value`/`attributes.output.value`/
`attributes.llm.model_name` in Arize.

## 5. Acceptance criteria (from issue #91)

- [ ] Field appears in Azure Monitor with the documented name/type
- [ ] Azure Function transformation maps it to the documented OTel/OpenInference attribute without data loss
- [ ] Field is visible on the corresponding span/trace in Arize
- [ ] `trace_id`, `span_id`, and `parent_span_id` remain joinable across all hops for this record
- [ ] Validation query above returns non-null synthetic sample rows

**Validated-via-review today:** the field inventory and 8KB-truncation gap are grounded in #32's
already-merged App Insights custom-dimensions inventory
(`app-insights-custom-dimensions.md`), cross-checked against the merged Prompt Agent source
(`agent.py` sets `input.value`/`output.value`, not `llm.input_messages`/`llm.output_messages` — see
Telemetry's Milestone 2 history entry on this exact discrepancy). **Requires live-environment
re-verification:** the KQL query has not been run against a live App Insights instance, and the
Arize query cannot be run until #38 and a live Arize space exist.

## Related

- [`field-mapping.md`](../field-mapping.md) (#36) — summary/index across all four field groups
- [`app-insights-custom-dimensions.md`](../app-insights-custom-dimensions.md) (#32) — source of the 8KB truncation-gap note
- [`identity-correlation-fields.md`](./identity-correlation-fields.md) (#89) — correlation requirement this group depends on
