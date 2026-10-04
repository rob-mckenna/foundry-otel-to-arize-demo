"""telemetry_pipeline: the Azure Function transform for issue #37/#36.

Maps Azure Monitor / Log Analytics-exported `AppDependencies`/`AppTraces`
records (as delivered via Event Hub) onto OTLP span objects, per the field
mapping spec in `docs/telemetry/field-mapping.md` and the correlation-ID
risk analysis in `docs/telemetry/trace-correlation-preservation.md` (#37).

Package layout:
  - `mapping.py`   — pure, per-record field-group transform logic (no Azure
                     SDK dependency; this is what the unit tests exercise).
  - `batch.py`     — batches a Event Hub message payload into spans and
                     hands them to an injected exporter.
  - `exporter.py`  — exporter factory/DI seam; the live OTLP-to-Arize export
                     path is deliberately NOT exercised by default (no
                     live Azure/Arize credentials exist in this sandbox).
  - `function_app.py` — the actual `azure.functions` Event Hub trigger
                     wiring. Only this module requires the `azure-functions`
                     package to import; `mapping`/`batch`/`exporter` do not,
                     so the transform logic is unit-testable without any
                     Azure Functions runtime or live infrastructure.
"""
from __future__ import annotations

__all__ = ["mapping", "batch", "exporter"]
