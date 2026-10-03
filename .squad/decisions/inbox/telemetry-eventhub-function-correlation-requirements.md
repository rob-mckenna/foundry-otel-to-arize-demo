# Decision: Event Hub partition-key and Function checkpointing requirements for correlation-ID preservation

**From:** Telemetry
**Affects:** Infra (#17 Event Hub, #19 Azure Function)
**Date:** 2026-10-03

## Context

While documenting trace/span/correlation-ID preservation across Event Hub and Function hops (#37),
two implementation requirements were identified that Infra's #17/#19 Bicep modules and any
accompanying Function code should satisfy to avoid breaking cross-system trace correlation:

1. **Event Hub partition key:** whatever writes spans to Event Hub (Log Analytics Data Export, #35)
   should use `operation_Id` (the App Insights trace ID) as the partition key, so every span
   belonging to one trace stays in relative order within a single partition. Without this, spans
   from one trace could be delivered out of order across partitions.
2. **Function checkpointing strategy:** the Azure Function's Event Hub trigger should use
   whole-batch checkpointing (checkpoint only after the full batch succeeds), not per-event
   checkpointing with silent drop-on-failure. Per-event checkpointing risks orphaning child spans
   if a parent span's event fails mid-batch while children already succeeded.

## Why this matters

Both are flagged in `/docs/telemetry/trace-correlation-preservation.md` §3/§4 as **blocking
concerns** for correlation-ID preservation, not optional tuning — per Telemetry's charter policy of
treating any hop where correlation IDs could be dropped as a blocking defect unless Lead explicitly
accepts it as a known limitation.

## Requested action

Infra: please consider these two requirements when implementing #17 (Event Hub) and #19 (Azure
Function). Not blocking #17/#19's current scope — flagging now so the requirement is visible before
those modules are built, rather than discovered as a bug afterward.
