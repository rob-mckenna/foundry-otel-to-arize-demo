"""Production mapper/frozen OTLP regression tests with synthetic data, no network.

Durable admission, restart, deduplication and delivery outcomes are covered by
src/telemetry-pipeline/tests/test_durable.py and test_strict_sender.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

from telemetry_pipeline.mapping import MalformedRecordError
from telemetry_pipeline.strict_sender import freeze_record

FIXTURES = Path(__file__).parents[1] / "telemetry-mapping" / "fixtures"
PROJECT = "synthetic-project"


def wire(record):
    request = ExportTraceServiceRequest.FromString(freeze_record(record, PROJECT))
    resource = request.resource_spans[0]
    span = resource.scope_spans[0].spans[0]
    attributes = {attribute.key: attribute.value for attribute in span.attributes}
    routing = {attribute.key: attribute.value for attribute in resource.resource.attributes}
    assert routing["openinference.project.name"].string_value == PROJECT
    assert routing["service.name"].string_value
    return span, attributes


def test_fifty_span_graph_identity_status_and_typed_usage_roundtrip():
    spans = []
    for trace_number in range(1, 11):
        trace = f"{trace_number:032x}"
        for index, parent in enumerate((None, 1, 1, 3, 3), 1):
            row = {
                "operation_Id": trace, "id": f"{index:016x}",
                "operation_ParentId": f"{parent:016x}" if parent else "",
                "Name": f"synthetic.operation.{index}", "Success": index != 4,
                "timestamp": "2026-10-03T12:00:00.000Z", "duration": 1.25,
                "customDimensions": {
                    "correlation.id": f"synthetic-request-{trace_number}",
                    "openinference.span.kind": "LLM" if index == 3 else "CHAIN",
                    **({"llm.model_name": "synthetic-model", "llm.token_count.prompt": "42",
                        "llm.token_count.completion": "18", "llm.token_count.total": "60"}
                       if index == 3 else {}),
                },
            }
            span, attrs = wire(row)
            spans.append(span)
            assert span.trace_id.hex() == trace
            assert span.span_id.hex() == row["id"]
            assert span.parent_span_id.hex() == row["operation_ParentId"]
            assert span.name == row["Name"]
            assert span.end_time_unix_nano - span.start_time_unix_nano == 1_250_000
            assert span.status.code == (2 if index == 4 else 1)
            assert attrs["correlation.id"].string_value == f"synthetic-request-{trace_number}"
            if index == 3:
                for key, count in (("prompt", 42), ("completion", 18), ("total", 60)):
                    value = attrs[f"llm.token_count.{key}"]
                    assert value.WhichOneof("value") == "int_value"
                    assert value.int_value == count
    assert len(spans) == 50


@pytest.mark.parametrize("encoded", [False, True])
def test_native_foundry_service_graph_precision_content_and_available_usage(encoded):
    rows = json.loads((FIXTURES / "foundry_service_spans.json").read_text())
    messages = {
        "input": [{"role": "user", "parts": [{"type": "text", "content": "Synthetic question"}]}],
        "output": [{"role": "assistant", "parts": [
            {"type": "text", "content": "Synthetic answer"}, {"type": "synthetic", "nested": [1]},
        ]}],
    }
    rows[1]["Properties"].update({
        f"gen_ai.{side}.messages": json.dumps(value) if encoded else value
        for side, value in messages.items()
    })
    rows[1]["Properties"]["correlation.id"] = "synthetic-message-request"
    agent, agent_attrs = wire(rows[0])
    chat, attrs = wire(rows[1])
    assert agent.trace_id.hex() == chat.trace_id.hex() == rows[0]["OperationId"]
    assert agent.parent_span_id.hex() == rows[0]["ParentId"]
    assert agent.span_id == chat.parent_span_id
    assert chat.span_id.hex() == rows[1]["Id"]
    assert agent.name == rows[0]["Name"] and chat.name == rows[1]["Name"]
    assert agent.start_time_unix_nano == 1792052765472348200
    assert chat.start_time_unix_nano == 1792052766118237000
    assert agent.end_time_unix_nano - agent.start_time_unix_nano == 1_962_073_100
    assert chat.end_time_unix_nano - chat.start_time_unix_nano == 765_187_400
    assert agent.status.code == chat.status.code == 1
    assert agent.kind == 1 and chat.kind == 3
    assert agent_attrs["openinference.span.kind"].string_value == "AGENT"
    assert attrs["openinference.span.kind"].string_value == "LLM"
    assert attrs["llm.model_name"].string_value == "synthetic-response-model"
    assert attrs["gen_ai.response.id"].string_value == "resp_synthetic"
    assert attrs["gen_ai.conversation.id"].string_value == "conv_synthetic"
    for source, alias, expected in (
        ("gen_ai.usage.input_tokens", "llm.token_count.prompt", 121),
        ("gen_ai.usage.output_tokens", "llm.token_count.completion", 84),
    ):
        for key in (source, alias):
            assert attrs[key].WhichOneof("value") == "int_value"
            assert attrs[key].int_value == expected
    assert attrs["correlation.id"].string_value == "synthetic-message-request"
    for side, expected in messages.items():
        assert json.loads(attrs[f"{side}.value"].string_value) == expected
        assert attrs[f"{side}.mime_type"].string_value == "application/json"
        assert f"{side}.value" not in agent_attrs
    for absent in ("llm.token_count.total", "gen_ai.input.messages", "gen_ai.output.messages", "span_type"):
        assert absent not in attrs
    assert "llm.token_count.prompt" not in agent_attrs
    assert len(chat.events) == len(chat.links) == 0


@pytest.mark.parametrize("hierarchical_parent", [False, True])
def test_native_root_and_child_preserve_missing_parent_zero_usage_and_error(hierarchical_parent):
    root = json.loads((FIXTURES / "native_preflight_root.json").read_text())
    parent = f"|{root['OperationId']}.{root['Id']}." if hierarchical_parent else root["Id"]
    child = {
        **root, "Type": "AppDependencies", "Id": "d9cf8d9381425553", "ParentId": parent,
        "Name": "llm.chat_completion", "DurationMs": 0, "Success": False,
        "Properties": {
            **json.loads(root["Properties"]), "llm.model_name": "synthetic-model",
            "openinference.span.kind": "LLM", "llm.token_count.prompt": "0",
            "llm.token_count.completion": 0, "llm.token_count.total": "0",
        },
    }
    root_pb, _ = wire(root)
    child_pb, attrs = wire(child)
    assert root_pb.trace_id.hex() == child_pb.trace_id.hex() == root["OperationId"]
    assert root_pb.span_id.hex() == child_pb.parent_span_id.hex() == root["Id"]
    assert root_pb.parent_span_id == b""
    assert child_pb.span_id.hex() == child["Id"]
    assert child_pb.kind == 3 and child_pb.status.code == 2
    assert child_pb.end_time_unix_nano == child_pb.start_time_unix_nano
    assert attrs["correlation.id"].string_value == json.loads(root["Properties"])["correlation.id"]
    assert attrs["llm.model_name"].string_value == "synthetic-model"
    for name in ("prompt", "completion", "total"):
        value = attrs[f"llm.token_count.{name}"]
        assert value.WhichOneof("value") == "int_value"
        assert value.int_value == 0
    with pytest.raises(MalformedRecordError, match="root marker differs"):
        wire({**child, "ParentId": "1" * 32})


@pytest.mark.parametrize("properties", ["{broken", {"llm.model_name": {}},
                                        {"gen_ai.usage.input_tokens": -1}])
def test_invalid_native_fields_fail_instead_of_freezing_a_success(properties):
    row = json.loads((FIXTURES / "native_preflight_root.json").read_text())
    with pytest.raises(MalformedRecordError):
        wire({**row, "Properties": properties})
