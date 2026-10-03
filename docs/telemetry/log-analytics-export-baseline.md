# Log Analytics Continuous Export Baseline — AppDependencies/AppTraces/AppRequests → Event Hub

**Status: CURRENT-STATE DESIGN, pending #17 (Event Hub infrastructure) merge.** This doc specifies
the exact export mechanism, included tables/columns, and expected cadence/latency for streaming
Application Insights telemetry to Event Hub. The naming below follows the already-merged
`infra/modules/naming.bicep` convention (`resourceTypeTokens.eventHubNamespace = "ehns"`) so this
doc stays consistent with whatever `infra/modules/event-hub.bicep` lands as part of #17. **No Event
Hub resource exists in this repo yet** — this is the specification the eventual resource/export
rule must satisfy, not a description of something already deployed. Do not read this as proof of a
live export pipeline.

## 1. Export mechanism: Log Analytics data export (not a saved/scheduled query)

Azure offers two ways to stream Log Analytics data to Event Hub:

1. **Log Analytics workspace "Data Export" rule** — a first-class, continuously-running
   platform feature (`Microsoft.OperationalInsights/workspaces/dataExports`) that streams every new
   row landing in specified tables to a target (Event Hub namespace or Storage account), with no
   query/polling involved and minimal added latency.
2. **A scheduled KQL query (Azure Monitor "Scheduled query rule" / Logic App on a timer)** that
   polls the workspace on an interval and pushes matching rows to Event Hub itself.

**This repo uses approach (1), the native Data Export rule**, not a scheduled/polling query — it's
lower-latency (no polling interval to tune), doesn't risk missing rows between poll windows, and is
simpler to reason about for correlation-ID preservation (every row is forwarded in near-real-time,
in ingestion order, rather than batched by a query's own time-window semantics). This choice is
recorded here as a design decision Infra's #17 Bicep module should implement as a
`dataExports` child resource on the Log Analytics workspace Infra already provisions (#16,
`infra/modules/app-insights.bicep`).

## 2. Tables and columns included

| Table | Included? | Why |
|---|---|---|
| `AppDependencies` | ✅ Yes | Every span the Prompt Agent emits today lands here (see `app-insights-custom-dimensions.md` §1) — this is the primary table the export rule must include. |
| `AppTraces` | ✅ Yes | Reserved for any future `logger`/trace-level telemetry (not currently emitted by the agent, but required by the issue's own table list — included so the export rule doesn't need to change if/when the agent adds plain log telemetry). |
| `AppRequests` | ✅ Yes | Reserved for any future `SERVER`/`CONSUMER`-kind span (none exist today — see §1 gap note in `app-insights-custom-dimensions.md`) — included for the same forward-compatibility reason as `AppTraces`. |

**No column is excluded within an included table** — a Log Analytics Data Export rule exports entire
table rows, not a column subset; this means `customDimensions` (and therefore every OpenInference
attribute documented in #32/#33/#34) is exported intact, along with `operation_Id`,
`operation_ParentId`, `id` (span ID), `timestamp`, `Name`, and every other standard column. This
satisfies issue #35's acceptance criterion "no column silently excluded that a downstream mapping
depends on" by construction — there is no column-level filtering in this export mechanism to
accidentally misconfigure.

**Filter predicate:** none at the export-rule level (table-level export only, no `where` clause
available on a Data Export rule). Any row-level filtering (e.g. dropping non-Prompt-Agent telemetry
if the workspace is ever shared with other apps) would have to happen downstream, in the Azure
Function transform step (#36) — not at this hop. No such filtering is needed today since this
workspace is dedicated to the Prompt Agent demo (single Foundry project, see `app-insights.bicep`).

## 3. Cadence / latency

Log Analytics Data Export is near-real-time but **not instantaneous** — Microsoft's published
guidance (and consistent operational experience) puts typical row-to-Event-Hub latency in the
**low single-digit minutes** for workspace ingestion-to-export, on top of the Application Insights
SDK's own batch-export interval (the Azure Monitor OpenTelemetry Exporter / `BatchSpanProcessor`
batches locally before sending — see `telemetry.py`'s `BatchSpanProcessor` usage, default batch
delay is a few seconds, not instant-per-span either).

**End-to-end latency budget (documented estimate, not yet measured against a live resource):**

| Hop | Estimated added latency |
|---|---|
| Span end → `BatchSpanProcessor` flush → Azure Monitor exporter network call | seconds (SDK batch interval) |
| Application Insights ingestion → queryable in Log Analytics | typically under a few minutes (standard App Insights ingestion latency) |
| Log Analytics Data Export → Event Hub enqueue | low single-digit minutes (platform-documented) |
| **Total, agent call → Event Hub enqueue** | **~2–6 minutes, estimated** |

This estimate is explicitly **not yet validated** — §4 below is the measurement plan to replace
estimate with a measured number once #17 (Event Hub) is merged and deployed.

## 4. Validation plan (to run once #17 is merged and deployed)

```kql
// Step 1: trigger a synthetic agent call (see src/prompt-agent samples), note its operation_Id.
// Step 2: once it lands in Log Analytics:
AppDependencies
| where operation_Id == "<synthetic-test-trace-id>"
| project timestamp, ingestion_time(), operation_Id
```

Step 3: on the Event Hub consumer side (or via the Function's own execution logs once #19 lands),
record the enqueue/receive timestamp for the matching event and compute
`eventHubEnqueueTime - timestamp` as the measured end-to-end latency, replacing the estimate in §3.

## 5. Dependencies and current gaps

- **Depends on #17** (Event Hub infrastructure) — the `dataExports` child resource needs a target
  Event Hub namespace/hub to point at. This doc specifies the export rule's shape; it cannot be
  deployed until #17 merges.
- Cross-checked against #32/#33/#34's field inventory per this issue's own acceptance criterion —
  no gap found; see §2.
- Latency figures in §3 are estimates pending live measurement (§4) — flagged explicitly, not
  presented as measured fact.

## Related

- [`app-insights-custom-dimensions.md`](./app-insights-custom-dimensions.md) (#32)
- [`custom-dimensions-schema.md`](./custom-dimensions-schema.md) (#33)
- [`token-usage-validation.md`](./token-usage-validation.md) (#34)
- [`field-mapping.md`](./field-mapping.md) (#36, Azure Function transform step this export feeds)
