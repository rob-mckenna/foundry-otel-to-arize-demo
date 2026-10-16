"""Sanitized shapes from arize-fidelity-20261016 source/details LAW receipts.

Only observed metadata keys/types are fixtures; no live content was read.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

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
