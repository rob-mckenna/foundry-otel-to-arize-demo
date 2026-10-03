# src/telemetry-pipeline

**Status: CURRENT-STATE (validated, implemented)**

This directory holds the Azure Function transform/mapping code and Event Hub consumer logic that
forms the validated telemetry pipeline:

`Application Insights -> Log Analytics -> Event Hub -> Azure Function (transform/map) -> Arize (OTLP)`

The Function here is responsible for mapping Application Insights/Log Analytics telemetry schema
into valid OTLP spans Arize can ingest, while preserving trace ID, span ID, parent span ID,
correlation ID, and token-usage attributes end-to-end (see `/.github/copilot-instructions.md`
§11-§13).

Only validated, implemented code belongs here. The future-state idea of bypassing this pipeline
with a direct OTLP exporter is conceptual only and lives under `/docs/future-state` — it must
never be partially implemented here ahead of an accepted architecture decision.
