# KQL Validation Query Pack

**Status: CURRENT-STATE, query pack for a live Application Insights instance.** These queries are
written and reasoned through against the documented schema in `docs/telemetry/`, but **have not been
executed against a live Application Insights instance** in this pass — no live Azure resources exist
in this sandbox (consistent with Telemetry's Milestone 2 history note). Each must be re-run against
a real workspace with synthetic demo traffic before being relied on as passing validation evidence.

This pack lets a customer's SRE/platform team self-serve pipeline validation during a POC instead of
depending on Telemetry to write bespoke queries live, per issue #41's customer/demo value statement.

## Queries in this pack

| Query | File | Validates |
|---|---|---|
| Span-kind coverage | [`span-kind-coverage.kql`](./span-kind-coverage.kql) | Every expected OpenInference span kind (`CHAIN`/`TOOL`/`LLM`) is present; no kind silently missing |
| Token-count consistency | [`token-count-consistency.kql`](./token-count-consistency.kql) | `prompt_tokens + completion_tokens == total_tokens` on every LLM span, no missing token fields (see #90) |
| Correlation-ID completeness | [`correlation-id-completeness.kql`](./correlation-id-completeness.kql) | Every span has `correlation.id` set and well-formed `operation_Id`/`operation_ParentId`/`id` (see #89) |
| Export latency | [`export-latency.kql`](./export-latency.kql) | App Insights → Log Analytics ingestion latency stays low (early warning for pipeline lag before Event Hub/Function) |
| Custom-dimension schema drift | [`custom-dimension-schema-drift.kql`](./custom-dimension-schema-drift.kql) | No unexpected/renamed `customDimensions` keys relative to the documented schema (#33) |

Each `.kql` file carries a one-line description and its expected output shape as a header comment,
per issue #41's acceptance criterion ("each query has a one-line description and expected output
shape documented inline").

## How to run

1. Open the target Application Insights resource's Logs (Log Analytics) blade in the Azure portal,
   or use `az monitor log-analytics query` / the Azure Monitor REST API.
2. Paste the query body (everything after the header comment block) in.
3. Run against synthetic demo traffic generated via `src/prompt-agent/synthetic/scenarios.py`.
4. Compare the result against the "Expected output shape" comment in the query file.

## Validated-via-review vs. requires live-environment re-verification

- **Validated-via-review:** every field reference in these queries (`operation_Id`, `id`,
  `customDimensions["..."]` keys, etc.) is cross-checked against the merged schema docs
  (`custom-dimensions-schema.md`, `app-insights-custom-dimensions.md`, `field-mapping.md`) and the
  merged Prompt Agent source. Query syntax is manually traced for correctness (KQL operators used:
  `summarize`, `extend`, `mv-expand`, `bag_keys`, `percentile`, `bin`, `ingestion_time()` - all
  standard, documented KQL functions).
- **Requires live-environment re-verification:** none of these queries have been executed against a
  real Log Analytics workspace. Sample output tables/screenshots (per issue #41's validation steps)
  must be captured once a live App Insights instance with synthetic demo traffic exists, and
  attached to this doc or a follow-up PR.

## Related

- [`../custom-dimensions-schema.md`](../custom-dimensions-schema.md) (#33)
- [`../field-mapping.md`](../field-mapping.md) (#36)
- [`../mapping/identity-correlation-fields.md`](../mapping/identity-correlation-fields.md) (#89)
- [`../mapping/token-fields.md`](../mapping/token-fields.md) (#90)
- [#43 Combined token-analysis query set (App Insights + Arize parity check)](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/43)
