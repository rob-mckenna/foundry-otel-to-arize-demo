"""Unit tests for exporter observability in `telemetry.py` (#130).

Covers:
  1. `shutdown_tracing()` logging a warning when `force_flush()` returns
     `False` (a flush that did not complete within its timeout), using a
     stub `TracerProvider` test-double rather than the real OTel SDK
     provider — this keeps the assertion focused purely on the boolean
     branch being handled instead of real flush timing.
  2. `shutdown_tracing()` staying quiet (no such warning) when
     `force_flush()` returns `True`.
  3. `_CountingSpanExporter` incrementing `failed_count` and logging a
     warning when the wrapped `SpanExporter.export()` reports
     `SpanExportResult.FAILURE`, using a stub `SpanExporter` test-double.
  4. `_CountingSpanExporter` incrementing `exported_count` (and logging no
     warning) on a successful export.

These are synthetic test-doubles only — no real spans, Azure resources, or
Application Insights connection are involved.
"""
from __future__ import annotations

import logging

from opentelemetry.sdk.trace.export import SpanExportResult

from prompt_agent import telemetry


class _StubTracerProvider:
    """Minimal TracerProvider test-double with a scripted `force_flush()`.

    Only implements the two methods `shutdown_tracing()` actually calls,
    matching the "stub/test-double TracerProvider whose force_flush()
    returns False" requirement from #130's acceptance criteria.
    """

    def __init__(self, flush_result: bool) -> None:
        self._flush_result = flush_result
        self.shutdown_called = False

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._flush_result

    def shutdown(self) -> None:
        self.shutdown_called = True


class _StubSpanExporter:
    """Minimal SpanExporter test-double with a scripted `export()` result."""

    def __init__(self, result: SpanExportResult) -> None:
        self._result = result
        self.shutdown_called = False

    def export(self, spans):
        return self._result

    def shutdown(self) -> None:
        self.shutdown_called = True

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def test_shutdown_tracing_warns_when_force_flush_times_out(monkeypatch, caplog):
    """A `force_flush()` returning False must produce a warning signal."""
    stub_provider = _StubTracerProvider(flush_result=False)
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: stub_provider)
    monkeypatch.setattr(telemetry, "_span_exporter", None)

    with caplog.at_level(logging.WARNING, logger=telemetry.__name__):
        telemetry.shutdown_tracing()

    assert stub_provider.shutdown_called
    assert any(
        "force_flush" in record.message and "did not complete" in record.message
        for record in caplog.records
    ), f"Expected a force_flush timeout warning, got: {[r.message for r in caplog.records]}"


def test_shutdown_tracing_no_warning_when_force_flush_succeeds(monkeypatch, caplog):
    """A `force_flush()` returning True must not raise a false alarm."""
    stub_provider = _StubTracerProvider(flush_result=True)
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: stub_provider)
    monkeypatch.setattr(telemetry, "_span_exporter", None)

    with caplog.at_level(logging.WARNING, logger=telemetry.__name__):
        telemetry.shutdown_tracing()

    assert stub_provider.shutdown_called
    assert not any("did not complete" in record.message for record in caplog.records)


def test_counting_span_exporter_counts_and_warns_on_failed_export(caplog):
    """A failed export() must bump failed_count and log a warning."""
    wrapped = _StubSpanExporter(SpanExportResult.FAILURE)
    counting_exporter = telemetry._CountingSpanExporter(wrapped)

    with caplog.at_level(logging.WARNING, logger=telemetry.__name__):
        result = counting_exporter.export(["synthetic-span-1", "synthetic-span-2"])

    assert result == SpanExportResult.FAILURE
    assert counting_exporter.failed_count == 2
    assert counting_exporter.exported_count == 0
    assert any(
        "failed to export" in record.message for record in caplog.records
    ), f"Expected a failed-export warning, got: {[r.message for r in caplog.records]}"


def test_counting_span_exporter_counts_successful_export_without_warning(caplog):
    """A successful export() must bump exported_count and log no warning."""
    wrapped = _StubSpanExporter(SpanExportResult.SUCCESS)
    counting_exporter = telemetry._CountingSpanExporter(wrapped)

    with caplog.at_level(logging.WARNING, logger=telemetry.__name__):
        result = counting_exporter.export(["synthetic-span-1"])

    assert result == SpanExportResult.SUCCESS
    assert counting_exporter.exported_count == 1
    assert counting_exporter.failed_count == 0
    assert not any("failed to export" in record.message for record in caplog.records)


def test_shutdown_tracing_logs_export_summary_from_span_exporter(monkeypatch, caplog):
    """shutdown_tracing() must log the running exported/failed tally."""
    stub_provider = _StubTracerProvider(flush_result=True)
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: stub_provider)

    counting_exporter = telemetry._CountingSpanExporter(_StubSpanExporter(SpanExportResult.SUCCESS))
    counting_exporter.exported_count = 5
    counting_exporter.failed_count = 1
    monkeypatch.setattr(telemetry, "_span_exporter", counting_exporter)

    with caplog.at_level(logging.INFO, logger=telemetry.__name__):
        telemetry.shutdown_tracing()

    assert any(
        "exported=5" in record.message and "failed=1" in record.message
        for record in caplog.records
    ), f"Expected an export summary log line, got: {[r.message for r in caplog.records]}"
