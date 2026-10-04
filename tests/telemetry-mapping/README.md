# tests/telemetry-mapping

**Status: CURRENT-STATE (validated, implemented)**

Tests validating the Event Hub -> Azure Function -> Arize schema mapping: correctness of field
mapping, trace ID / span ID / parent span ID / correlation ID preservation, and token-usage field
preservation across the transform step (see `/.github/copilot-instructions.md` §11, §12, §15).

Use synthetic fixtures only — no real telemetry captures from production systems, and never real
PII/PHI, even as test data.

**Note (issue #37 follow-on):** the actual Azure Function transform package's unit tests live
co-located with the package at
[`src/telemetry-pipeline/tests/`](../../src/telemetry-pipeline/tests/), matching
`src/prompt-agent`'s co-located-tests convention (so `pip install -e ".[test]"; pytest tests/` works
the same way for both packages). This directory remains the place to add cross-cutting
mapping-focused tests that don't belong inside the package itself (e.g. broader end-to-end
schema-drift checks once a live Event Hub/Arize environment exists).
