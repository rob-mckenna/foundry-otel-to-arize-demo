"""Shared fixtures/synthetic record builders for the telemetry_pipeline tests.

Follows `src/prompt-agent/tests/conftest.py`'s conventions: small, focused
fixtures plus a couple of plain helper functions (not fixtures) used across
multiple test modules.
"""
from __future__ import annotations

from typing import Any

import pytest
from opentelemetry.sdk.trace.export import SpanExportResult


def make_record(**overrides: Any) -> dict:
    """Build one synthetic Azure Monitor `AppDependencies`-style record.

    Defaults describe a root `prompt_agent.invoke` CHAIN span (no parent),
    matching the shape used throughout
    `docs/telemetry/trace-correlation-preservation.md` §5's validation plan.
    Override any field (including nested `customDimensions` keys via the
    `custom_dimensions` kwarg) to build a child/LLM/retry-attempt span.
    """
    custom_dimensions = {
        "correlation.id": "synthetic-correlation-id-123",
        "openinference.span.kind": "CHAIN",
        "input.value": "What is my synthetic deductible?",
        "output.value": "Your synthetic deductible is $500.",
    }
    custom_dimensions.update(overrides.pop("custom_dimensions", {}) or {})

    record = {
        "operation_Id": "0af7651916cd43dd8448eb211c80319c",
        "operation_ParentId": "",
        "id": "b7ad6b7169203331",
        "Name": "prompt_agent.invoke",
        "Success": True,
        "timestamp": "2026-10-03T12:00:00.000Z",
        "duration": 123.456,
        "customDimensions": custom_dimensions,
    }
    record.update(overrides)
    return record


class StubSpanExporter:
    """Minimal `SpanExporter` test-double recording every exported batch.

    Mirrors the `_StubSpanExporter` pattern already used in
    `src/prompt-agent/tests/test_telemetry_export_observability.py`.
    """

    def __init__(self, result: SpanExportResult = SpanExportResult.SUCCESS) -> None:
        self._result = result
        self.export_calls: list[list] = []

    def export(self, spans):
        self.export_calls.append(list(spans))
        return self._result

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    @property
    def all_exported_spans(self) -> list:
        return [span for call in self.export_calls for span in call]


@pytest.fixture
def stub_exporter() -> StubSpanExporter:
    return StubSpanExporter()
