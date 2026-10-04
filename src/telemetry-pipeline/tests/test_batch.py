"""Batch-processing tests: Event Hub message decoding + whole-batch export.

Uses in-memory/mocked Event Hub message objects only - no live Azure Event
Hub or Function host required, per this issue's testability requirement.
"""
from __future__ import annotations

import json

import pytest
from opentelemetry.sdk.trace.export import SpanExportResult

from telemetry_pipeline.batch import transform_batch
from telemetry_pipeline.mapping import MalformedRecordError

from .conftest import StubSpanExporter, make_record


class _FakeEventHubEvent:
    """Stand-in for `azure.functions.EventHubEvent` - only `get_body()` matters."""

    def __init__(self, body: bytes):
        self._body = body

    def get_body(self) -> bytes:
        return self._body


def _event(payload) -> _FakeEventHubEvent:
    return _FakeEventHubEvent(json.dumps(payload).encode("utf-8"))


def test_single_record_message_is_transformed_and_exported(stub_exporter):
    record = make_record()
    result = transform_batch([_event(record)], stub_exporter)

    assert len(result.spans) == 1
    assert result.skipped == []
    assert result.export_result == SpanExportResult.SUCCESS
    assert len(stub_exporter.export_calls) == 1  # one export() call for the whole batch


def test_log_analytics_records_envelope_is_unwrapped(stub_exporter):
    """Log Analytics Data Export commonly wraps rows as {"records": [...]}."""
    payload = {"records": [make_record(id="b7ad6b7169203331"), make_record(id="c8be7c8270314442")]}
    result = transform_batch([_event(payload)], stub_exporter)

    assert len(result.spans) == 2
    assert result.skipped == []


def test_array_of_records_message_is_transformed(stub_exporter):
    payload = [make_record(id="b7ad6b7169203331"), make_record(id="c8be7c8270314442")]
    result = transform_batch([_event(payload)], stub_exporter)

    assert len(result.spans) == 2


def test_multiple_messages_in_one_batch_export_together(stub_exporter):
    """Whole-batch checkpointing: every message's spans go out in ONE
    exporter.export() call, never one call per message/record (see
    trace-correlation-preservation.md §4)."""
    messages = [_event(make_record(id="b7ad6b7169203331")), _event(make_record(id="c8be7c8270314442"))]
    result = transform_batch(messages, stub_exporter)

    assert len(result.spans) == 2
    assert len(stub_exporter.export_calls) == 1
    assert len(stub_exporter.export_calls[0]) == 2


def test_malformed_record_is_skipped_not_fatal_to_the_batch(stub_exporter):
    good_record = make_record(id="b7ad6b7169203331")
    bad_record = make_record(id="not-valid-hex", operation_Id="0af7651916cd43dd8448eb211c80319c")
    payload = {"records": [good_record, bad_record]}

    result = transform_batch([_event(payload)], stub_exporter)

    assert len(result.spans) == 1
    assert len(result.skipped) == 1
    assert "id" in result.skipped[0].reason


def test_unreadable_message_body_is_skipped_not_fatal(stub_exporter):
    unreadable = _FakeEventHubEvent(b"{not valid json")
    good = _event(make_record())

    result = transform_batch([unreadable, good], stub_exporter)

    assert len(result.spans) == 1
    assert len(result.skipped) == 1


def test_empty_batch_does_not_call_export(stub_exporter):
    result = transform_batch([], stub_exporter)
    assert result.spans == []
    assert result.export_result is None
    assert stub_exporter.export_calls == []


def test_plain_str_message_body_is_supported_for_unit_tests(stub_exporter):
    """Convenience: a plain str body (not wrapped in a get_body() object) is
    also accepted, making ad-hoc unit tests simpler to write."""
    body_text = json.dumps(make_record())
    result = transform_batch([body_text], stub_exporter)
    assert len(result.spans) == 1
