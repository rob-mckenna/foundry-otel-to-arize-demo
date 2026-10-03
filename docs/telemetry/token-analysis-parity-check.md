# Combined Token-Analysis Query Set — App Insights + Arize Parity Check

> Spec for issue [#43](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/43) — a
> recurring post-POC health check that lets a customer detect silent pipeline drift (e.g. a Function
> deployment regressing a field mapping) by comparing the same token-usage aggregate computed
> independently in both systems.

**Status: CURRENT-STATE DESIGN, pending live Application Insights + Arize instances.** No live
Azure or Arize environment exists in this sandbox. Depends on #34 (token-usage metrics, merged/
documented), #40 (token analysis views in Arize, spec-only in this pass), and #41 (KQL query pack,
merged in this milestone) per the issue's stated dependencies.

## 1. Paired queries — same metric, same window, two independent systems

**Metric:** total tokens consumed per hour, over the last 1 hour.

**App Insights side (KQL)** — identical to
[`kql/token-count-consistency.kql`](./kql/token-count-consistency.kql)'s source span filter, but
summing rather than validating consistency:

```kql
AppDependencies
| where timestamp > ago(1h) and customDimensions["openinference.span.kind"] == "LLM"
| summarize sum(toint(customDimensions["llm.token_count.total"]))
```

**Arize side** — the same `spanAggregation` shape already specified in
[`arize-token-analysis-views.md`](./arize-token-analysis-views.md) (#40), narrowed to `last_1h`:

```
query {
  spanAggregation(
    metric: SUM,
    field: "attributes.llm.token_count.total",
    timeRange: last_1h
  ) { value }
}
```

## 2. Expected tolerance

**Exact match, not an approximate tolerance band.** This demo's data path has no ingestion
sampling anywhere (every span emitted by the Prompt Agent is exported through every hop) — so unlike
a production observability pipeline that might sample, the two sums must be bit-for-bit identical
for the same synthetic time window. A query pack like this that silently accepted a tolerance band
would mask a real correctness bug in the Function's token-field casting (the "string → int"
requirement in [`token-fields.md`](./mapping/token-fields.md), #90), not just measurement noise.

## 3. Runbook: what a mismatch implies

| Symptom | Most likely cause | Where to look first |
|---|---|---|
| Arize sum < App Insights sum | Function silently dropped spans, or a batch partial-failure checkpointing bug | [`trace-correlation-preservation.md`](./trace-correlation-preservation.md) §4 (batch checkpointing strategy) |
| Arize sum == 0 or null, App Insights sum > 0 | Function failed to cast `llm.token_count.total` from string to int (lands as a quoted string, which Arize's `SUM` aggregation can't sum) | [`token-fields.md`](./mapping/token-fields.md) §2 (string→int coercion rule) |
| Arize sum > App Insights sum | Duplicate span ingestion — likely an Event Hub at-least-once-redelivery edge case where the Function's OTLP export isn't idempotent | [`trace-correlation-preservation.md`](./trace-correlation-preservation.md) §3.2 (consumer-group checkpoint redelivery risk) |
| Both sums are 0 | No synthetic traffic was generated in the window, or the time-window filters (`ago(1h)` / `last_1h`) are misaligned between systems (clock skew, timezone) | Confirm synthetic scenario run timestamps before suspecting the pipeline |

A mismatch is a **pipeline-health signal pointing at a specific hop**, not a vague "something's
wrong" — consistent with the posture already established in
[`cross-system-trace-join.md`](./cross-system-trace-join.md) (#39) §4.

## 4. Validation steps (per issue #43)

1. Run both queries against the same synthetic 1-hour window, confirm exact match.
2. **Intentionally break one Function mapping** (e.g. skip the `int()` cast on
   `llm.token_count.total`) to confirm the mismatch is actually detected by this comparison, not
   silently passed through — this is the "prove the test can fail" step that makes the parity
   check trustworthy as a recurring health check, not just a happy-path demo.
3. Record the before/after result pair (matched, then deliberately mismatched) as the evidence this
   issue's acceptance criteria call for.

## 5. Acceptance criteria (from issue #43)

- [ ] One KQL query and one Arize query, documented side by side, computing the same metric over
      the same synthetic time window — **done, §1**
- [ ] Documented expected tolerance (exact match for synthetic data, no ingestion sampling) —
      **done, §2**
- [ ] Runbook note on what a mismatch implies (which pipeline hop to investigate first) — **done,
      §3**

## 6. Validated-via-review vs. requires live-environment re-verification

- **Validated-via-review:** both queries' field references and the `spanAggregation`/KQL syntax are
  cross-checked against the already-merged `token-usage-validation.md` (#34), the merged
  `kql/` pack (#41), and `token-fields.md` (#90). The runbook's cause/effect mapping (§3) is
  reasoned directly from the already-documented risks in `trace-correlation-preservation.md` (#37).
- **Requires live-environment re-verification:** neither query has been executed against a live
  system (none exists in this sandbox), and the "intentionally break the mapping, confirm detection"
  step (§4.2) requires a deployed Function to actually break — this is explicitly deferred, not
  silently assumed to work.

## Related

- [`token-usage-validation.md`](./token-usage-validation.md) (#34)
- [`arize-token-analysis-views.md`](./arize-token-analysis-views.md) (#40)
- [`kql/token-count-consistency.kql`](./kql/token-count-consistency.kql) (#41)
- [`cross-system-trace-join.md`](./cross-system-trace-join.md) (#39)
