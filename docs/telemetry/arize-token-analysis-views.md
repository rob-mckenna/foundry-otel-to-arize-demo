# Arize Token Analysis Views

> Spec for issue [#40](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/40) — an
> Arize dashboard/saved view aggregating `llm.token_count.*` across traces, groupable by model name
> and time window, for cost-governance conversations with customers.

**Status: CURRENT-STATE DESIGN, pending live Arize space.** No live Arize tenant is provisioned in
this sandbox. This doc specifies the view's query/config and a hand-computed synthetic dataset with
known expected totals, so the view is reproducible and verifiable the moment a live Arize space
exists. It does not claim the view has been built or verified live.

## 1. Customer/demo value

Turns raw token telemetry into the demo's cost-governance payoff screen: "here's how much this
agent is costing you, broken down by model." Depends on #38 (OTLP export conformance) since the
view can't show anything until spans are actually ingested by Arize.

## 2. View definition

**Reproducible query/config (not just a manually-built UI dashboard with no spec)**, per issue #40's
acceptance criterion:

```
query {
  spanAggregation(
    groupBy: "attributes.llm.model_name",
    metric: SUM,
    field: "attributes.llm.token_count.total",
    timeRange: last_24h
  ) { group, value }
}
```

Companion breakdown (prompt vs. completion, same grouping):

```
query {
  promptTokens: spanAggregation(
    groupBy: "attributes.llm.model_name", metric: SUM,
    field: "attributes.llm.token_count.prompt", timeRange: last_24h
  ) { group, value }
  completionTokens: spanAggregation(
    groupBy: "attributes.llm.model_name", metric: SUM,
    field: "attributes.llm.token_count.completion", timeRange: last_24h
  ) { group, value }
}
```

**View layout:** a stacked bar chart — one bar per `llm.model_name`, segmented into
prompt/completion token sub-totals, with a time-window selector (default `last_24h`, selectable down
to `last_1h` for demo-pace walkthroughs) and a numeric total-tokens-per-model legend.

## 3. Synthetic dataset with hand-computed expected totals

Per issue #40's validation steps ("load a known synthetic dataset with hand-computed totals,
confirm displayed totals match"), the following 10-trace synthetic dataset is the fixture to load:

| Trace | Model | Prompt tokens | Completion tokens | Total tokens |
|---|---|---|---|---|
| 1 | `synthetic-model-v1` | 120 | 45 | 165 |
| 2 | `synthetic-model-v1` | 98 | 32 | 130 |
| 3 | `synthetic-model-v1` | 150 | 60 | 210 |
| 4 | `synthetic-model-v1` | 110 | 40 | 150 |
| 5 | `synthetic-model-v1` | 85 | 28 | 113 |
| 6 | `synthetic-model-v2-large` | 300 | 120 | 420 |
| 7 | `synthetic-model-v2-large` | 275 | 95 | 370 |
| 8 | `synthetic-model-v2-large` | 310 | 130 | 440 |
| 9 | `synthetic-model-v2-large` | 260 | 88 | 348 |
| 10 | `synthetic-model-v2-large` | 290 | 105 | 395 |

**Hand-computed expected totals (the numbers the view must reproduce exactly — no sampling in this
demo's data path, so exact match is the bar, not an approximation):**

| Model | Sum prompt | Sum completion | Sum total |
|---|---|---|---|
| `synthetic-model-v1` | 563 | 205 | 768 |
| `synthetic-model-v2-large` | 1,435 | 538 | 1,973 |
| **Grand total (all models)** | **1,998** | **743** | **2,741** |

(Hand-computed: `563 = 120+98+150+110+85`; `205 = 45+32+60+40+28`; `768 = 165+130+210+150+113`;
`1,435 = 300+275+310+260+290`; `538 = 120+95+130+88+105`; `1,973 = 420+370+440+348+395`. Grand
totals are the column sums across both models.)

## 4. Acceptance criteria (from issue #40)

- [ ] Arize view/dashboard exists showing total tokens over time, grouped by `llm.model_name` —
      **spec complete (§2); not yet built in a live Arize space**
- [ ] View is reproducible from a documented query/config, not just a manually-built UI dashboard —
      **done — §2's `spanAggregation` queries are the reproducible spec**
- [ ] Validated against synthetic data with known expected totals — **dataset + hand-computed totals
      documented (§3); not yet loaded into a live Arize space for comparison**

## 5. Validated-via-review vs. requires live-environment re-verification

- **Validated-via-review:** the 10-row synthetic dataset's per-model and grand-total sums in §3 are
  arithmetically verified by hand (shown inline) against the per-trace values in the table — these
  numbers are correct regardless of environment.
- **Requires live-environment re-verification:** the `spanAggregation` query has not been run
  against any live Arize space (none provisioned in this sandbox), and no spans from this synthetic
  dataset have actually been ingested yet — that requires #38 (OTLP export conformance) to be
  implemented against a real Function and a live Arize tenant. Once that exists, load this exact
  10-trace dataset and confirm the view's displayed totals equal §3's grand totals exactly.

## Related

- [`mapping/token-fields.md`](./mapping/token-fields.md) (#90)
- [`otlp-export-conformance.md`](./otlp-export-conformance.md) (#38)
- [#43 Combined token-analysis query set (App Insights + Arize parity check)](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/43)
- [#42 Arize dashboards for trace visualization](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/42)
