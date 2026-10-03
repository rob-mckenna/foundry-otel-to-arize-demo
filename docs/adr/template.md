# ADR-00NN: <Short, specific decision title>

## Status

Proposed | Accepted | Superseded by ADR-00NN | Deprecated

## Context

What situation or problem prompts this decision? What is the current state of things? Include
enough background that a reader unfamiliar with the discussion can follow the reasoning.

## Decision

What did we decide to do? State it plainly and specifically — this is the part a future reader
will scan first.

## Consequences

What becomes easier or harder as a result of this decision? Include:
- **Current-state impact:** effect on the validated, implemented pipeline under `/src` and
  `/infra`. State "None" explicitly if there is no current-state impact.
- **Future-state impact:** effect on the conceptual direct-OTLP design under `/docs/future-state`.
  State "None" explicitly if there is no future-state impact.
- **Security considerations:** secrets/Key Vault, managed identity, data classification, PII/PHI
  exposure risk. State "None" explicitly if there are none.
- **Observability considerations:** impact on trace/span/parent-span/correlation-ID preservation,
  token-usage telemetry, Application Insights custom dimensions, or Arize ingestion. State "None"
  explicitly if there are none.
- **Trade-offs accepted:** anything given up by choosing this option over the alternatives.
- **Open questions:** anything unresolved, unvalidated, or dependent on product/platform behavior
  not yet confirmed.
