# OTLP export regression tests

Synthetic offline tests use the production mapper and frozen OTLP serializer,
covering a 50-span graph, native agent/child shapes, source timing/status,
typed available usage, I/O, and explicit project routing. No live Arize ingestion
is implied. Durable restart, correlation, deduplication, bounded retry and
ambiguous-delivery quarantine tests live in
[`src/telemetry-pipeline/tests`](../../src/telemetry-pipeline/tests).

Run from the repository root after installing the pipeline's `.[test]` dependencies:

```powershell
.\.venv\Scripts\python.exe -m pytest src\telemetry-pipeline\tests tests\telemetry-mapping tests\export -q
```
