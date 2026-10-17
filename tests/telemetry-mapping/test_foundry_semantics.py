"""Sanitized shapes from arize-fidelity-20261016 source/details LAW receipts.

Only observed metadata keys/types are fixtures; no live content was read.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from opentelemetry.sdk.trace.export import SpanExportResult
from telemetry_pipeline.batch import transform_batch
from telemetry_pipeline.mapping import MalformedRecordError, record_to_span


@pytest.fixture
def service_chat():
    rows = json.loads((Path(__file__).parent / "fixtures" / "foundry_service_spans.json").read_text())
    return rows[1]


@pytest.mark.parametrize("encoded", [False, True])
def test_observed_service_metadata_is_typed_and_input_is_not_mutated(service_chat, encoded):
    properties = dict(service_chat["Properties"])
    if encoded:
        service_chat["Properties"] = json.dumps(properties)
    span = record_to_span(service_chat)
    assert span.attributes["llm.model_name"] == properties["gen_ai.response.model"]
    assert span.attributes["gen_ai.request.model"] == properties["gen_ai.request.model"]
    assert span.attributes["openinference.span.kind"] == "LLM"
    for source, alias, expected in (
        ("gen_ai.usage.input_tokens", "llm.token_count.prompt", 121),
        ("gen_ai.usage.output_tokens", "llm.token_count.completion", 84),
    ):
        assert span.attributes[source] == span.attributes[alias] == expected
        assert type(span.attributes[source]) is type(span.attributes[alias]) is int
    assert "llm.token_count.total" not in span.attributes
    assert "correlation.id" not in span.attributes
    assert span.attributes["gen_ai.response.id"] == properties["gen_ai.response.id"]
    assert span.attributes["gen_ai.conversation.id"] == properties["gen_ai.conversation.id"]
    assert "llm.token_count.prompt" not in properties
    assert service_chat["Properties"] == (json.dumps(properties) if encoded else properties)


def test_explicit_openinference_values_remain_authoritative(service_chat):
    service_chat["Properties"].update({
        "llm.model_name": "existing-model", "openinference.span.kind": "TOOL",
        "llm.token_count.prompt": 121, "llm.token_count.total": "205",
    })
    attributes = record_to_span(service_chat).attributes
    assert attributes["llm.model_name"] == "existing-model"
    assert attributes["openinference.span.kind"] == "TOOL"
    assert attributes["llm.token_count.total"] == 205
    assert attributes["gen_ai.response.model"] == "synthetic-response-model"


def test_request_model_fallback_and_missing_fields_are_not_fabricated(service_chat):
    properties = service_chat["Properties"]
    del properties["gen_ai.response.model"]
    properties["gen_ai.operation.name"] = "unrecognized"
    del properties["gen_ai.usage.output_tokens"]
    properties["gen_ai.usage.input_tokens"] = "0"
    attributes = record_to_span(service_chat).attributes
    assert attributes["llm.model_name"] == properties["gen_ai.request.model"]
    assert attributes["llm.token_count.prompt"] == 0
    assert "llm.token_count.completion" not in attributes
    assert "llm.token_count.total" not in attributes
    assert "openinference.span.kind" not in attributes
    del properties["gen_ai.request.model"]
    assert "llm.model_name" not in record_to_span(service_chat).attributes


@pytest.mark.parametrize("value", [None, True, -1, 1.5, "1.5", 2**63])
def test_invalid_service_usage_is_rejected(service_chat, value):
    service_chat["Properties"]["gen_ai.usage.input_tokens"] = value
    with pytest.raises(MalformedRecordError):
        record_to_span(service_chat)


def test_disagreeing_usage_conventions_do_not_silently_replace_counts(service_chat):
    service_chat["Properties"]["llm.token_count.prompt"] = "122"
    with pytest.raises(MalformedRecordError, match="conflicting"):
        record_to_span(service_chat)


@pytest.mark.parametrize("field", ["gen_ai.response.id", "gen_ai.response.model",
                                  "gen_ai.operation.name", "gen_ai.conversation.id"])
def test_invalid_service_metadata_follows_observable_skip_contract(service_chat, field):
    service_chat["Properties"][field] = {}
    with pytest.raises(MalformedRecordError, match="must be a string"):
        record_to_span(service_chat)


@pytest.mark.parametrize("explicit_side", ["input", "output"])
@pytest.mark.parametrize("explicit_mime", [False, True])
def test_message_bridge_preserves_explicit_value_and_matching_mime_independently(
    service_chat, explicit_side, explicit_mime, caplog,
):
    other_side = "output" if explicit_side == "input" else "input"
    properties = service_chat["Properties"]
    properties.update({
        f"{explicit_side}.value": "",
        f"gen_ai.{explicit_side}.messages": "invalid synthetic content",
        f"gen_ai.{other_side}.messages": [],
        f"{other_side}.mime_type": "text/plain",
    })
    if explicit_mime:
        properties[f"{explicit_side}.mime_type"] = "text/plain"
    attributes = record_to_span(service_chat).attributes
    assert attributes[f"{explicit_side}.value"] == ""
    if explicit_mime:
        assert attributes[f"{explicit_side}.mime_type"] == "text/plain"
    else:
        assert f"{explicit_side}.mime_type" not in attributes
    assert attributes[f"{other_side}.value"] == "[]"
    assert attributes[f"{other_side}.mime_type"] == "application/json"
    assert not caplog.records  # The overridden source is not parsed.


def test_both_explicit_values_and_mimes_win_over_inline_messages(service_chat, caplog):
    explicit = {
        "input.value": "Synthetic explicit question", "input.mime_type": "text/plain",
        "output.value": '{"synthetic": "explicit response"}', "output.mime_type": "application/json",
    }
    service_chat["Properties"].update({
        **explicit, "gen_ai.input.messages": None, "gen_ai.output.messages": "invalid",
    })
    attributes = record_to_span(service_chat).attributes
    assert {key: attributes[key] for key in explicit} == explicit
    assert not caplog.records


@pytest.mark.parametrize("payload,reason", [
    ("{synthetic-private-body", "invalid JSON"),
    ('{"synthetic": "private-body"}', "expected role/parts messages"),
    (None, "expected role/parts messages"),
    ({}, "expected role/parts messages"),
    ([{"role": "user", "content": "synthetic-private-body"}], "expected role/parts messages"),
    ([{"role": "user", "parts": ["synthetic-private-body"]}], "expected role/parts messages"),
    ([{"role": "user", "parts": [{"type": "text", "content": float("nan")}]}],
     "non-JSON content"),
])
def test_invalid_messages_omit_only_affected_io_without_logging_content(
    service_chat, payload, reason, caplog,
):
    service_chat["Properties"].update({
        "gen_ai.input.messages": payload,
        "input.mime_type": "text/plain",
        "gen_ai.output.messages": [{"role": "assistant", "parts": []}],
    })

    class InMemoryExporter:
        def export(self, spans):
            return SpanExportResult.SUCCESS

    neighbor = {**service_chat, "Id": "4444444444444444", "Properties": {}}
    result = transform_batch([json.dumps([service_chat, neighbor])], InMemoryExporter())
    assert len(result.spans) == 2
    assert result.skipped == []
    assert result.export_result == SpanExportResult.SUCCESS
    attributes = result.spans[0].attributes
    assert "input.value" not in attributes
    assert "input.mime_type" not in attributes
    assert json.loads(attributes["output.value"]) == [{"role": "assistant", "parts": []}]
    assert attributes["output.mime_type"] == "application/json"
    assert len(caplog.records) == 1
    assert caplog.messages == [f"telemetry_pipeline.mapping: omitting gen_ai.input.messages: {reason}"]


def test_missing_messages_do_not_fabricate_io_or_emit_orphan_mime(service_chat, caplog):
    service_chat["Properties"].update({"input.mime_type": "text/plain", "output.mime_type": 42})
    attributes = record_to_span(service_chat).attributes
    assert all(f"{side}.{field}" not in attributes
               for side in ("input", "output") for field in ("value", "mime_type"))
    assert not caplog.records
