# tests/telemetry-mapping

**Status: CURRENT-STATE (validated, implemented)**

Tests validating the Event Hub -> Azure Function -> Arize schema mapping: correctness of field
mapping, trace ID / span ID / parent span ID / correlation ID preservation, and token-usage field
preservation across the transform step (see `/.github/copilot-instructions.md` §11, §12, §15).

Use synthetic fixtures only — no real telemetry captures from production systems, and never real
PII/PHI, even as test data.
