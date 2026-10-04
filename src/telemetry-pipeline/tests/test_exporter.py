"""Exporter factory/DI tests - no live network or Arize credentials used."""
from __future__ import annotations

import logging

import pytest
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SpanExportResult

from telemetry_pipeline import exporter as exporter_module


def test_get_default_exporter_wraps_a_console_exporter():
    exp = exporter_module.get_default_exporter()
    assert isinstance(exp, exporter_module._CountingSpanExporter)
    assert isinstance(exp._wrapped, ConsoleSpanExporter)


def test_counting_span_exporter_tallies_success_and_failure(caplog):
    class _StubExporter:
        def __init__(self, result):
            self._result = result

        def export(self, spans):
            return self._result

        def shutdown(self):
            pass

        def force_flush(self, timeout_millis=30000):
            return True

    ok_exporter = exporter_module._CountingSpanExporter(_StubExporter(SpanExportResult.SUCCESS))
    result = ok_exporter.export(["span-a", "span-b"])
    assert result == SpanExportResult.SUCCESS
    assert ok_exporter.exported_count == 2
    assert ok_exporter.failed_count == 0

    failing_exporter = exporter_module._CountingSpanExporter(_StubExporter(SpanExportResult.FAILURE))
    with caplog.at_level(logging.WARNING, logger=exporter_module.__name__):
        result = failing_exporter.export(["span-c"])
    assert result == SpanExportResult.FAILURE
    assert failing_exporter.failed_count == 1
    assert any("failed to export" in r.message for r in caplog.records)


def test_build_arize_otlp_exporter_requires_endpoint(monkeypatch):
    """No live network call here - this only proves the fail-fast guard
    when no Arize endpoint/credentials are configured (this sandbox's
    permanent state)."""
    monkeypatch.delenv(exporter_module.ARIZE_OTLP_ENDPOINT_ENV_VAR, raising=False)
    with pytest.raises(RuntimeError, match="ARIZE_OTLP_ENDPOINT"):
        exporter_module.build_arize_otlp_exporter()
