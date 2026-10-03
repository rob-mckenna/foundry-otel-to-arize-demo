# Cross-System Trace/Span Correlation Join Test (App Insights ↔ Arize)

> Spec + paired query walkthrough for issue [#39](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/39) —
> this repo's "trust but verify" artifact for the core claim that correlation survives the full
> App Insights → Log Analytics → Event Hub → Function → Arize hop chain.

**Status: CURRENT-STATE DESIGN, pending live Application Insights + Arize instances.** No live
Azure or Arize environment exists in this sandbox. This doc documents one synthetic trace end to
end — the queries to run, and the exact expected-match shape — so the test is ready to execute the
moment #38 (OTLP export conformance) and a live Arize space exist. It is explicitly **not** a claim
that this join has been run and passed.

## 1. The one documented synthetic trace

A single synthetic trace ID, used consistently across both systems for this test:

```
trace_id: 4f1a9c2e7b3d4856a1f0d6e29c7b1234
```

This trace represents one synthetic Prompt Agent invocation with the standard 5-span tree (see
`src/prompt-agent/tests/test_agent_spans.py` and
`docs/telemetry/otlp-export-conformance.md` §4's synthetic batch shape):

| Span | `id` (span_id) | `operation_ParentId` (parent_span_id) | Name |
|---|---|---|---|
| Root | `a1b2c3d4e5f6a7b8` | *(none — root)* | `prompt_agent.invoke` |
| Tool call | `b2c3d4e5f6a7b8c9` | `a1b2c3d4e5f6a7b8` | `tool.lookup_plan_details` |
| LLM call | `c3d4e5f6a7b8c9d0` | `a1b2c3d4e5f6a7b8` | `llm.chat_completion` |
| Retry attempt 1 | `d4e5f6a7b8c9d0e1` | `c3d4e5f6a7b8c9d0` | `llm.chat_completion.attempt` |
| Retry attempt 2 | `e5f6a7b8c9d0e1f2` | `c3d4e5f6a7b8c9d0` | `llm.chat_completion.attempt` |

5 spans total, 2 levels of parent/child nesting below the root (root → LLM call → retry attempts),
matching the span tree already validated in-process by
`test_agent_spans.py`/`test_correlation_and_retry.py` (synthetic data only — none of these
identifiers correspond to any real request).

## 2. App Insights side (KQL)

```kql
AppDependencies
| where operation_Id == "4f1a9c2e7b3d4856a1f0d6e29c7b1234"
| project operation_Id, operation_ParentId, id, Name, Success, timestamp
| order by timestamp asc
```

**Expected result:** 5 rows, matching the table in §1 exactly — same `id`/`operation_ParentId`
pairs, same `Name` values, ordered root-first.

## 3. Arize side

```
query {
  spans(filter: { traceId: "4f1a9c2e7b3d4856a1f0d6e29c7b1234" }) {
    spanId
    parentSpanId
    name
  }
}
```

**Expected result:** 5 spans, with `spanId`/`parentSpanId`/`name` matching the KQL result's
`id`/`operation_ParentId`/`Name` values 1:1 (per
[`identity-correlation-fields.md`](./mapping/identity-correlation-fields.md)'s conclusion that no
hex-encoding conversion is needed between the two systems' identifier formats).

## 4. Diff procedure

1. Run the KQL query (§2) and the Arize query (§3) back-to-back against the same trace ID.
2. Build a comparison table: for each span, `(id, operation_ParentId)` from KQL vs.
   `(spanId, parentSpanId)` from Arize.
3. **Pass condition:** span count matches (5 == 5), and every `(id, operation_ParentId)` pair has
   an exact match in the Arize result — no reordering, no dropped span, no regenerated ID.
4. **Fail condition, and what it implies:**
   - Span count mismatch (fewer spans in Arize) → check Event Hub batch-checkpointing strategy and
     Function error logs first (see
     [`trace-correlation-preservation.md`](./trace-correlation-preservation.md) §4's partial-batch-
     failure risk).
   - Span count matches but parent/child graph doesn't → check the Function's
     `operation_ParentId` → `parent_span_id` mapping logic (see
     [`identity-correlation-fields.md`](./mapping/identity-correlation-fields.md) §2) for an
     accidental zero-padding/truncation bug.
   - IDs present but reordered/duplicated → check Event Hub partition-key assignment (see
     `trace-correlation-preservation.md` §3.1).

This mirrors the runbook posture in
[`token-analysis-parity-check.md`](./token-analysis-parity-check.md) (#43) — a mismatch is a
pipeline-health signal pointing at a specific hop to investigate, not a vague "something's wrong."

## 5. Acceptance criteria (from issue #39)

- [ ] Single documented synthetic trace ID that can be queried in both systems — **done, §1**
- [ ] KQL query (App Insights side) and Arize query (Arize side) both included side by side — **done, §2/§3**
- [ ] Span count and parent/child graph match exactly between the two systems — **not yet
      executed; requires #37 (correlation-ID preservation, documented/partially validated) and #38
      (OTLP export conformance, spec + reference-transform test only) plus a live Arize space**

## 6. Validated-via-review vs. requires live-environment re-verification

- **Validated-via-review:** the synthetic span tree in §1 matches the shape already proven
  in-process by `test_agent_spans.py`/`test_correlation_and_retry.py` (no live Azure resources
  needed for that proof). The KQL query syntax and field references are consistent with
  `identity-correlation-fields.md` (#89) and the existing, already-merged
  `trace-correlation-preservation.md` (#37).
- **Requires live-environment re-verification:** this join has not been executed against a live
  App Insights instance or Arize space — no such environment exists in this sandbox. This is the
  single highest-value validation to run manually the first time live infrastructure for #17/#19
  and an Arize tenant both exist, per this doc's own §4 procedure.

## Related

- [`trace-correlation-preservation.md`](./trace-correlation-preservation.md) (#37)
- [`mapping/identity-correlation-fields.md`](./mapping/identity-correlation-fields.md) (#89)
- [`otlp-export-conformance.md`](./otlp-export-conformance.md) (#38)
- [#42 Arize dashboards for trace visualization](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/42)
