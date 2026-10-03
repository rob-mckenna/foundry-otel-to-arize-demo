# Arize Dashboard — Trace Visualization

> Spec for issue [#42](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/42) — the
> primary visual artifact for customer-facing demo sessions. "Look, it just works."

**Status: CURRENT-STATE DESIGN, pending live Arize space.** No live Arize tenant is provisioned in
this sandbox. This doc specifies the dashboard's panel layout, the query/config backing each panel,
and the setup steps to recreate it in a fresh Arize space. It does not claim the dashboard has been
built or rendered live. Depends on #39 (trace/span correlation preserved into Arize) per the issue's
stated dependency — a dashboard showing broken/orphaned traces would be worse than no dashboard.

## 1. Panel layout (minimum per issue #42's acceptance criteria)

| Panel | Purpose | Backing query/config |
|---|---|---|
| Trace timeline | Shows one trace's span tree over time — the "look, it just works" view | §2 |
| Span-kind breakdown | Count of spans by `openinference.span.kind` (`CHAIN`/`TOOL`/`LLM`) over a window | §3 |
| Error-rate by span kind | % of spans with `status_code == STATUS_CODE_ERROR`, grouped by span kind | §4 |
| Latency distribution per span kind | p50/p95/max span duration, grouped by span kind | §5 |

## 2. Trace timeline panel

Uses Arize's native trace-detail view (not a custom query) — navigate to a trace by `trace_id`
(e.g. the synthetic trace documented in
[`cross-system-trace-join.md`](./cross-system-trace-join.md), #39) and Arize renders the span tree
as a Gantt-style timeline automatically from the ingested OTLP data (parent/child nesting comes
from `parent_span_id`, duration from span start/end timestamps). **Setup requirement:** this panel
has no separate "config" beyond successful OTLP ingestion with correct `parent_span_id` linkage —
it is the direct payoff of #38 (OTLP export conformance) and #39 (cross-system join) both passing.

## 3. Span-kind breakdown panel

```
query {
  spanAggregation(
    groupBy: "attributes.openinference.span.kind",
    metric: COUNT,
    timeRange: last_24h
  ) { group, value }
}
```

Rendered as a pie or bar chart — one segment per span kind (`CHAIN`, `TOOL`, `LLM`, and an
`(empty)` bucket for retry-attempt spans which carry no `openinference.span.kind`, see
[`span-kind-status-fields.md`](./mapping/span-kind-status-fields.md) §2).

## 4. Error-rate by span kind panel

```
query {
  errorRate: spanAggregation(
    groupBy: "attributes.openinference.span.kind",
    metric: COUNT,
    filter: { field: "status_code", value: "STATUS_CODE_ERROR" },
    timeRange: last_24h
  ) { group, value }
  totalBySpanKind: spanAggregation(
    groupBy: "attributes.openinference.span.kind",
    metric: COUNT,
    timeRange: last_24h
  ) { group, value }
}
```

Rendered as `errorRate[kind] / totalBySpanKind[kind]` percentage bars per span kind. For a healthy
synthetic demo run this should be near-zero except where the demo intentionally injects a failure
scenario (see `docs/next-actions.md`'s "induced-failure walkthrough" / issue #30's retry-logic demo
step) — a non-zero error rate on `LLM`-kind spans with corresponding `retry.attempt` children on
`llm.chat_completion.attempt` spans is expected, intentional demo content, not a defect.

## 5. Latency distribution per span kind panel

```
query {
  latencyP50: spanAggregation(groupBy: "attributes.openinference.span.kind", metric: PERCENTILE_50, field: "duration_ms", timeRange: last_24h) { group, value }
  latencyP95: spanAggregation(groupBy: "attributes.openinference.span.kind", metric: PERCENTILE_95, field: "duration_ms", timeRange: last_24h) { group, value }
  latencyMax: spanAggregation(groupBy: "attributes.openinference.span.kind", metric: MAX, field: "duration_ms", timeRange: last_24h) { group, value }
}
```

Rendered as a box-plot or grouped-bar chart, one group per span kind, showing p50/p95/max span
duration in milliseconds.

## 6. Setup steps to recreate in a fresh Arize space

1. Provision/select an Arize space and confirm OTLP ingestion is receiving traffic (per #38).
2. Create a new dashboard, add the trace-timeline panel first (no config — verify by opening any
   ingested trace by `trace_id`).
3. Add the span-kind breakdown panel (§3's query) as a pie/bar visualization.
4. Add the error-rate panel (§4's two queries, combined into a computed percentage series).
5. Add the latency-distribution panel (§5's three queries) as a box-plot/grouped-bar visualization.
6. Load a multi-span, at-least-one-tool-call synthetic trace (e.g.
   `docs/telemetry/cross-system-trace-join.md`'s documented trace) and confirm all four panels
   render without missing data or empty panels.

## 7. Acceptance criteria (from issue #42)

- [ ] Dashboard includes at minimum trace timeline, span-kind breakdown, latency distribution —
      **spec complete (§2-§5); not yet built in a live Arize space**
- [ ] Dashboard config/setup steps documented so it can be recreated in a fresh Arize space —
      **done, §6**
- [ ] Verified against synthetic data showing realistic (non-trivial) trace shapes (multi-span, at
      least one tool call) — **the reference trace from #39 satisfies this shape requirement on
      paper (5 spans, 1 tool call, 1 LLM call with 2 retry attempts); not yet rendered/verified live**

## 8. Validated-via-review vs. requires live-environment re-verification

- **Validated-via-review:** every query here follows the same `spanAggregation`
  groupBy/metric/field/timeRange shape already used and reasoned through in
  [`arize-token-analysis-views.md`](./arize-token-analysis-views.md) (#40), and every attribute
  referenced (`openinference.span.kind`, `status_code`, `duration_ms`) is grounded in the merged
  field-mapping specs (#89-#92).
- **Requires live-environment re-verification:** no panel has actually been built or rendered in a
  live Arize space (none provisioned in this sandbox). §6's recreate-steps dry run is the explicit
  open follow-up, blocked on #38/#39 reaching a live, ingesting Arize tenant.

## Related

- [`cross-system-trace-join.md`](./cross-system-trace-join.md) (#39)
- [`arize-token-analysis-views.md`](./arize-token-analysis-views.md) (#40)
- [`mapping/span-kind-status-fields.md`](./mapping/span-kind-status-fields.md) (#92)
