# Future-State: Direct OTLP Export — Product Dependency Tracking

> ⚠️ **CONCEPTUAL — NOT IMPLEMENTED.** This is a living tracking document for a design proposal,
> not working code or a confirmed roadmap. See
> [`direct-otlp.md`](direct-otlp.md) for the full design this tracks dependencies for, and
> [`/docs/future-state/README.md`](README.md) for the directory's scope.

## Purpose

Tracks which specific Foundry/Azure/Arize product capabilities must exist for the direct-OTLP
future-state design (issue #63) to become implementable. Each row has a status and a source so the
team (and customer architects) can see exactly what's blocking the future-state path today — a
credible, cited answer to "when will this be real?" instead of a guess.

**Status key:**
- **Confirmed-available** — verified against current vendor/product documentation (source linked).
- **Confirmed-unavailable** — verified that the capability does not exist in the form this design
  needs (source linked); a workaround or alternative would be required.
- **Unconfirmed** — not yet verified one way or the other, or verified only partially / for an
  adjacent product surface that may not map exactly onto what this repo calls a "Prompt Agent."

| # | Dependency | Status | Source / Reference | Notes |
|---|---|---|---|---|
| 1 | Arize accepts OTLP (trace) ingestion natively, without an intermediate transform | ✅ Confirmed-available | [Arize AX docs — Exporter and OTLP](https://arize.com/docs/ax/concepts/otel-openinference/exporter) (fetched 2026-10-03): *"Arize AX accepts spans over OTLP"*, with public gRPC (`:4317`) and HTTP (`:4318`) endpoints at `https://otlp.arize.com/v1` | Confirms the *receiving* side of this design is real today. Authentication uses `space_id`/`api_key` HTTP headers, not Azure managed identity (see dependency #4). |
| 2 | A Microsoft Foundry agent can export OpenTelemetry trace/log/metric data to an arbitrary external OTLP endpoint (not just Application Insights) | 🟡 Unconfirmed (verified for a related but not identical product surface) | [Microsoft Learn — Export hosted agent telemetry by using OpenTelemetry](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/configure-hosted-agent-telemetry) (fetched 2026-10-03): documents OTLP export to "any other OpenTelemetry-compliant endpoint or a self-hosted OpenTelemetry Collector" | This Microsoft Learn page is written for Foundry **hosted agents**, not explicitly for the **Prompt Agent** product surface this repo targets (`src/prompt-agent/`). Whether the same OTLP-export configuration is available/supported for a Prompt Agent specifically has not been confirmed in this review — treat the two as related-but-distinct until confirmed against the exact SDK/runtime this repo's Prompt Agent uses. |
| 3 | A sidecar process (e.g. an OpenTelemetry Collector) can be deployed alongside the Prompt Agent's specific hosting/compute target | 🟡 Unconfirmed | Same Microsoft Learn page references a "self-hosted OpenTelemetry Collector" pattern generally, but does not confirm what compute/hosting model this repo's Prompt Agent will ultimately run on (this repo's current-state Prompt Agent is a local Python package today — see `src/prompt-agent/README.md` — not yet deployed to any specific Azure hosting target) | Needs to be re-checked once Infrastructure confirms the actual Prompt Agent hosting target (App Service, Container App, Foundry-managed hosting, etc.). |
| 4 | Authenticating to Arize's OTLP endpoint without storing a long-lived secret in Prompt Agent code/config (i.e., something equivalent to today's Key Vault + managed identity pattern) | ❌ Confirmed-unavailable as described | [Arize AX docs — Exporter and OTLP](https://arize.com/docs/ax/concepts/otel-openinference/exporter): authentication is via `space_id`/`api_key` request headers | Azure managed identity has no first-party integration with Arize (a non-Azure SaaS product), so the current-state secrets pattern (`copilot-instructions.md` §8) does not transfer directly. A direct-OTLP implementation would still need to store an Arize API key somewhere (Key Vault-backed secret pulled at runtime is the obvious fallback, but that is a design choice to make later, not something already solved by this proposal). |
| 5 | Outbound network egress from wherever the Prompt Agent/sidecar runs to a public internet endpoint (`otlp.arize.com`) is permitted under this repo's networking model | 🟡 Unconfirmed — needs follow-up | Current-state baseline is documented in `infra/modules/networking.bicep` and issue #21 ("baseline public access + optional private endpoint"); that work was scoped to the current-state Azure-only pipeline and has not been evaluated against an external (non-Azure) destination | A private-endpoint-only deployment of the current-state pipeline would likely need an explicit egress exception (or would be incompatible without one) for this future-state design; not evaluated here. |

## Re-check cadence

Per issue #64's validation guidance, this table should be re-checked **quarterly, or whenever
Arize or Microsoft Foundry ship a relevant product update** — this is a recurring task, not a
one-and-done. The audit date on each confirmed/unconfirmed row above should be updated (not just
appended to) when re-verified, so staleness is visible at a glance.

**Last reviewed:** 2026-10-03 (Lead, issue #64).

## Acceptance Criteria (from issue #64)

- [x] Tracking table lives in `/docs/future-state/dependencies.md`
- [x] Each dependency has a status and a source/reference (vendor doc, product announcement, or
      "unconfirmed — needs follow-up")
