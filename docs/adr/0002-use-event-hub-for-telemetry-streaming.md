# ADR-0002: Use Event Hub for telemetry streaming instead of a direct Log Analytics trigger

## Status

Accepted

## Context

The validated current-state pipeline needs to move Foundry Prompt Agent telemetry from
Application Insights/Log Analytics into Arize, via a transform step that maps the schema into
valid OTLP spans (see [`/docs/current-state/architecture.md`](../current-state/architecture.md)
and `/.github/copilot-instructions.md` §2). Two approaches were considered for getting telemetry
out of Log Analytics and into the transform step: stream it through an Event Hub, or trigger the
Azure Function transform directly off Log Analytics (e.g., via a scheduled query / Log Analytics
alert rule invoking the Function).

## Decision

We will stream telemetry through an **Event Hub** between Log Analytics and the Azure Function
transform step, rather than triggering the Function directly from Log Analytics.

**Options considered:**
1. **Event Hub streaming (chosen)** — Log Analytics continuous export streams relevant telemetry
   to an Event Hub; the Azure Function consumes the Event Hub via an Event Hub trigger.
   - *Pros:* Near-real-time streaming suitable for a live demo; natural backpressure/buffering if
     Arize or the Function is temporarily unavailable; decouples the Function's scaling behavior
     from Log Analytics query limits; Event Hub trigger bindings are a first-class, well-documented
     Azure Functions pattern with built-in checkpointing and retry semantics.
   - *Cons:* One additional Azure resource to provision, tag, and secure (see
     `/.github/copilot-instructions.md` §6-§7).
2. **Direct Log Analytics trigger (e.g., scheduled query → Function)** — a scheduled query or
   alert rule periodically polls Log Analytics and invokes the Function with matching results.
   - *Pros:* One fewer resource to provision.
   - *Cons:* Polling-based, not streaming — introduces latency that would be visible and
     confusing in a live customer demo; scheduled queries have query-result size/row limits that
     risk silently dropping telemetry under load; no built-in buffering if the Function or Arize
     is briefly unavailable, risking lost spans; harder to reason about exactly-once vs.
     at-least-once delivery semantics for trace/span preservation.

## Consequences

- **Current-state impact:** The validated pipeline includes an Event Hub as a required hop
  between Log Analytics and the Azure Function transform (see
  `/.github/copilot-instructions.md` §2 and `/infra/bicep`, which provisions it as
  `event-hub.bicep`).
- **Future-state impact:** None directly. The conceptual future-state direct-OTLP design (see
  `/docs/future-state`) proposes removing this entire current-state chain, including the Event
  Hub hop, in favor of exporting OTLP directly from the Prompt Agent — this ADR does not affect
  that separate, unimplemented proposal.
- **Security considerations:** The Event Hub namespace/hub requires the same Key Vault-backed
  secret handling and managed-identity access pattern as other resources in this repo (see
  `/.github/copilot-instructions.md` §8) — no connection strings committed, prefer managed
  identity for the Function's Event Hub access where supported.
- **Observability considerations:** Streaming through Event Hub preserves trace ID, span ID,
  parent span ID, and correlation ID in the event payload end-to-end into the Function transform
  step (see `/docs/current-state/architecture.md`, "Zoomed View" section); this must be verified
  with telemetry-mapping tests under `/tests/telemetry-mapping`.
- **Trade-offs accepted:** One additional resource (Event Hub namespace + hub) to provision, tag,
  and operate, in exchange for near-real-time streaming and built-in buffering/retry semantics
  appropriate for a live demo.
- **Open questions:** Exact Event Hub partition count and throughput-unit sizing appropriate for
  demo-scale synthetic load has not yet been load-tested; to be validated alongside the
  Infrastructure Deployment epic.
