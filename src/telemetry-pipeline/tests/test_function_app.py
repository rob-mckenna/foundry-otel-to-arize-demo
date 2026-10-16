"""Exercise the registered Function with synthetic messages and no network."""
from __future__ import annotations

import json
import logging
from typing import List, get_type_hints

import azure.functions as func
import pytest
from opentelemetry.sdk.trace.export import SpanExportResult

from telemetry_pipeline import function_app

from .conftest import StubSpanExporter, make_record


@pytest.fixture(scope="module")
def registered_function():
    return function_app.app.get_functions()[0]


@pytest.fixture
def invocation(monkeypatch, registered_function):
    exporter = StubSpanExporter()
    exporter.shutdown_calls = 0

    def shutdown():
        exporter.shutdown_calls += 1

    monkeypatch.setattr(exporter, "shutdown", shutdown)
    monkeypatch.setattr(function_app, "_resolve_exporter", lambda: exporter)
    return registered_function.get_user_function(), exporter


def test_batch_trigger_preserves_worker_compatible_event_annotation(registered_function):
    trigger = registered_function.get_trigger().get_dict_repr()
    assert trigger["type"] == "eventHubTrigger"
    assert trigger["cardinality"].value == "many"
    assert trigger["connection"] == function_app.EVENT_HUB_CONNECTION_SETTING_PREFIX
    assert trigger["eventHubName"] == function_app.EVENT_HUB_NAME
    assert get_type_hints(registered_function.get_user_function())["events"] == List[func.EventHubEvent]


def test_success_counts_only_accepted_spans(invocation, caplog):
    invoke, exporter = invocation
    with caplog.at_level(logging.INFO):
        invoke([json.dumps(make_record()), "not-json"])
    assert "mapped=1 exported=1 failed=0 skipped=1 export_status=success" in caplog.text
    assert len(exporter.export_calls) == 1
    assert exporter.shutdown_calls == 1


@pytest.mark.parametrize("events, skipped", [([], 0), (["not-json"], 1)])
def test_no_valid_spans_is_not_an_export_failure(invocation, caplog, events, skipped):
    invoke, exporter = invocation
    exporter._result = SpanExportResult.FAILURE
    with caplog.at_level(logging.INFO):
        invoke(events)
    assert f"mapped=0 exported=0 failed=0 skipped={skipped} export_status=no_export" in caplog.text
    assert exporter.export_calls == []
    assert exporter.shutdown_calls == 1


def test_export_failure_raises_and_registers_bounded_host_retry(
    invocation, registered_function, caplog
):
    invoke, exporter = invocation
    exporter._result = SpanExportResult.FAILURE
    with caplog.at_level(logging.INFO), pytest.raises(RuntimeError, match="Span export failed"):
        invoke([json.dumps(make_record())])
    assert "mapped=1 exported=0 failed=1 skipped=0 export_status=failure" in caplog.text
    assert "export_status=success" not in caplog.text
    assert "exported=1" not in caplog.text
    assert exporter.shutdown_calls == 1
    retry = registered_function.get_settings_dict("retry_policy")
    assert retry["strategy"] == "exponential_backoff"
    assert 0 < int(retry["max_retry_count"]) <= 3
    assert retry["minimum_interval"] == "00:00:05"
    assert retry["maximum_interval"] == "00:01:00"
    assert registered_function.get_trigger().get_dict_repr()["type"] == "eventHubTrigger"


@pytest.mark.parametrize("export_fails", [True, False])
def test_shutdown_does_not_mask_primary_failure(invocation, monkeypatch, export_fails, caplog):
    invoke, exporter = invocation
    if export_fails:
        exporter._result = SpanExportResult.FAILURE

    def shutdown():
        raise ValueError("synthetic cleanup failure")

    monkeypatch.setattr(exporter, "shutdown", shutdown)
    error_type = RuntimeError if export_fails else ValueError
    match = "Span export failed" if export_fails else "synthetic cleanup failure"
    with pytest.raises(error_type, match=match):
        invoke([json.dumps(make_record())])
    if export_fails:
        assert "exporter shutdown failed during invocation failure (ValueError)" in caplog.text


def test_export_exception_still_shuts_down_and_fails_invocation(invocation, monkeypatch):
    invoke, exporter = invocation

    def export(spans):
        raise RuntimeError("synthetic transport failure")

    monkeypatch.setattr(exporter, "export", export)
    with pytest.raises(RuntimeError, match="synthetic transport failure"):
        invoke([json.dumps(make_record())])
    assert exporter.shutdown_calls == 1
