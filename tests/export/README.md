# tests/export

**Status: CURRENT-STATE (validated, implemented)**

Tests validating OTLP export behavior from the Azure Function transform step to Arize — correct
OTLP span construction, successful ingestion handling, and bounded retry/backoff behavior on
transient failures (see `/.github/copilot-instructions.md` §11, §14, §15).

Use synthetic fixtures only — no real telemetry captures from production systems, and never real
PII/PHI, even as test data.
