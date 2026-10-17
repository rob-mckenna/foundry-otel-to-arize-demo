"""Conformance test scaffold for issue #38 (OTLP export conformance, Azure Function -> Arize).

**Execution note:** no Python interpreter is available in this validation environment, so this
file could not actually be executed in this pass (consistent with Telemetry's Milestone 2 history
entry on the same sandbox limitation). It is written to the same conventions as the existing,
already-reasoned `src/prompt-agent/tests/test_agent_spans.py` /
`test_token_usage_validation.py` suites and manually traced against
`docs/telemetry/otlp-export-conformance.md` / the four field-mapping specs (#89-#92) to confirm the
assertions are correct given that spec. **This must be re-run with a working Python 3.10+
environment (e.g. `pip install pytest` then `pytest tests/export`) before being relied on as passing
CI evidence.**

This test does NOT exercise the production Azure Function (no such code exists in this repo yet -
see `src/telemetry-pipeline/README.md`) or a live Arize OTLP endpoint. It exercises a minimal
*reference transform* defined in this file, which implements the field-mapping specs
(docs/telemetry/mapping/*.md) closely enough to prove the specs are internally consistent and
implementable. Treat this as a spec-conformance scaffold, not production-equivalent coverage.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import pytest


# ---------------------------------------------------------------------------
# Synthetic input: Log Analytics / Event Hub envelope rows (one per span)
# ---------------------------------------------------------------------------

def _hex(n: int) -> str:
    """Deterministic n-hex-char synthetic identifier (never a real trace/span ID)."""
    return uuid.uuid4().hex[:n]


def build_synthetic_batch(trace_count: int = 10) -> list[dict]:
    """Builds a synthetic batch of Log Analytics rows shaped like AppDependencies export records.

    Each trace contributes 5 spans: prompt_agent.invoke (root) -> tool.lookup_plan_details and
    llm.chat_completion (children) -> llm.chat_completion.attempt x2 (grandchildren of the LLM
    span), mirroring the span tree already validated in
    src/prompt-agent/tests/test_agent_spans.py. Defaults to 10 traces x 5 spans = 50 spans, meeting
    issue #38's "50+ span synthetic batch" acceptance bar.
    """
    rows: list[dict] = []
    for _ in range(trace_count):
        trace_id = _hex(32)
        root_id = _hex(16)
        tool_id = _hex(16)
        llm_id = _hex(16)
        attempt_ids = [_hex(16), _hex(16)]

        rows.append(_row(trace_id, root_id, None, "prompt_agent.invoke", True, {}))
        rows.append(
            _row(
                trace_id,
                tool_id,
                root_id,
                "tool.lookup_plan_details",
                True,
                {"openinference.span.kind": "TOOL", "input.value": "synthetic-input",
                 "output.value": "synthetic-output"},
            )
        )
        rows.append(
            _row(
                trace_id,
                llm_id,
                root_id,
                "llm.chat_completion",
                True,
                {
                    "openinference.span.kind": "LLM",
                    "llm.model_name": "synthetic-model-v1",
                    "llm.token_count.prompt": "42",
                    "llm.token_count.completion": "18",
                    "llm.token_count.total": "60",
                    "correlation.id": f"SYN-{trace_id[:8]}",
                },
            )
        )
        for i, attempt_id in enumerate(attempt_ids):
            rows.append(
                _row(
                    trace_id,
                    attempt_id,
                    llm_id,
                    "llm.chat_completion.attempt",
                    i == len(attempt_ids) - 1,
                    {"retry.attempt": str(i + 1), "retry.max_attempts": "2",
                     "retry.will_retry": "false" if i == len(attempt_ids) - 1 else "true"},
                )
            )
    return rows


def _row(trace_id, span_id, parent_id, name, success, custom_dims):
    return {
        "operation_Id": trace_id,
        "operation_ParentId": parent_id or "",
        "id": span_id,
        "Name": name,
        "Success": success,
        "customDimensions": custom_dims,
    }


# ---------------------------------------------------------------------------
# Reference transform: Log Analytics row -> OTLP-shaped span (spec conformance only)
# ---------------------------------------------------------------------------

RESOURCE_SERVICE_NAME = "foundry-prompt-agent-demo"
RESOURCE_DEPLOYMENT_ENVIRONMENT = "demo"


@dataclass
class ReferenceSpan:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    status_code: str
    attributes: dict = field(default_factory=dict)


def transform_row_to_span(row: dict) -> ReferenceSpan:
    """Reference implementation of the field-mapping specs (#89-#92). Not the production Function."""
    attrs: dict = {}
    for key, value in row["customDimensions"].items():
        if key in ("llm.token_count.prompt", "llm.token_count.completion",
                   "llm.token_count.total", "retry.attempt", "retry.max_attempts"):
            attrs[key] = int(value)
        elif key == "retry.will_retry":
            attrs[key] = value == "true"
        else:
            attrs[key] = value

    return ReferenceSpan(
        trace_id=row["operation_Id"],
        span_id=row["id"],
        parent_span_id=row["operation_ParentId"] or None,
        name=row["Name"],
        status_code="STATUS_CODE_OK" if row["Success"] else "STATUS_CODE_ERROR",
        attributes=attrs,
    )


def build_resource_spans(rows: list[dict]) -> dict:
    """Groups transformed spans under one ResourceSpans message, per docs/telemetry/otlp-export-conformance.md §2."""
    return {
        "resource": {
            "attributes": {
                "service.name": RESOURCE_SERVICE_NAME,
                "deployment.environment": RESOURCE_DEPLOYMENT_ENVIRONMENT,
            }
        },
        "spans": [transform_row_to_span(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_span_count_in_equals_span_count_out_for_50_plus_batch():
    rows = build_synthetic_batch(trace_count=10)
    assert len(rows) >= 50, "fixture must meet issue #38's 50+ span acceptance bar"

    resource_spans = build_resource_spans(rows)

    assert len(resource_spans["spans"]) == len(rows), (
        "no span may be silently dropped by the transform (issue #38 acceptance criterion)"
    )


def test_resource_attributes_set_correctly():
    rows = build_synthetic_batch(trace_count=2)
    resource_spans = build_resource_spans(rows)

    assert resource_spans["resource"]["attributes"]["service.name"] == "foundry-prompt-agent-demo"
    assert resource_spans["resource"]["attributes"]["deployment.environment"]


def test_trace_and_span_ids_round_trip_unchanged():
    rows = build_synthetic_batch(trace_count=3)
    resource_spans = build_resource_spans(rows)

    for row, span in zip(rows, resource_spans["spans"]):
        assert span.trace_id == row["operation_Id"]
        assert span.span_id == row["id"]
        expected_parent = row["operation_ParentId"] or None
        assert span.parent_span_id == expected_parent


def test_root_spans_have_no_parent_span_id():
    rows = build_synthetic_batch(trace_count=1)
    resource_spans = build_resource_spans(rows)

    root_spans = [s for s in resource_spans["spans"] if s.name == "prompt_agent.invoke"]
    assert len(root_spans) == 1
    assert root_spans[0].parent_span_id is None, (
        "a root span's missing operation_ParentId must map to 'no parent', never a zero-filled ID"
    )


def test_token_count_attributes_are_native_int_on_llm_spans():
    rows = build_synthetic_batch(trace_count=1)
    resource_spans = build_resource_spans(rows)

    llm_spans = [s for s in resource_spans["spans"] if s.name == "llm.chat_completion"]
    assert len(llm_spans) == 1
    attrs = llm_spans[0].attributes
    assert isinstance(attrs["llm.token_count.prompt"], int)
    assert isinstance(attrs["llm.token_count.completion"], int)
    assert isinstance(attrs["llm.token_count.total"], int)
    assert attrs["llm.token_count.prompt"] + attrs["llm.token_count.completion"] == (
        attrs["llm.token_count.total"]
    )


def test_repo_openinference_graph_content_and_usage_roundtrip_without_deduplicating_replay():
    import json

    from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
    from opentelemetry.sdk.trace.export import SpanExportResult
    from telemetry_pipeline.batch import transform_batch

    rows = build_synthetic_batch(trace_count=1)
    for row in rows:
        row.update(timestamp="2026-10-15T08:26:05.1234567Z", duration=1.25)
    model = rows[2]
    model["customDimensions"].update({
        "input.value": "Synthetic request", "output.value": "Synthetic response",
        "input.mime_type": "text/plain", "output.mime_type": "text/plain",
        "gen_ai.input.messages": [{"role": "user", "parts": []}],
        "gen_ai.output.messages": [{"role": "assistant", "parts": []}],
    })
    rows[-1]["customDimensions"]["gen_ai.response.id"] = "resp_synthetic_attempt"

    class RoundtripExporter:
        def export(self, spans):
            self.request = ExportTraceServiceRequest.FromString(encode_spans(spans).SerializeToString())
            return SpanExportResult.SUCCESS

    exporter = RoundtripExporter()
    result = transform_batch([json.dumps(rows), json.dumps(rows)], exporter)
    assert not result.skipped
    spans = [span for resource in exporter.request.resource_spans
             for scope in resource.scope_spans for span in scope.spans]
    assert len(spans) == 10
    assert [(s.trace_id, s.span_id) for s in spans[:5]] == [
        (s.trace_id, s.span_id) for s in spans[5:]
    ]  # Batch replay sends duplicate identities; destination deduplication is not assumed.
    root, tool, llm, failed_attempt, successful_attempt = spans[:5]
    assert root.parent_span_id == b""
    assert root.span_id == tool.parent_span_id == llm.parent_span_id
    assert llm.span_id == failed_attempt.parent_span_id == successful_attempt.parent_span_id
    assert failed_attempt.status.code == 2 and successful_attempt.status.code == 1
    assert failed_attempt.events == []  # No exception events can be reconstructed from this span row.
    attrs = {attr.key: attr.value for attr in llm.attributes}
    for key, expected in (("input.value", "Synthetic request"),
                          ("output.value", "Synthetic response"),
                          ("input.mime_type", "text/plain"),
                          ("output.mime_type", "text/plain"),
                          ("llm.model_name", "synthetic-model-v1")):
        assert attrs[key].WhichOneof("value") == "string_value"
        assert attrs[key].string_value == expected
    for key, expected in (("prompt", 42), ("completion", 18), ("total", 60)):
        assert attrs[f"llm.token_count.{key}"].WhichOneof("value") == "int_value"
        assert attrs[f"llm.token_count.{key}"].int_value == expected
    assert attrs["correlation.id"].string_value == model["customDimensions"]["correlation.id"]
    attempt_attrs = {attr.key: attr.value for attr in successful_attempt.attributes}
    assert attempt_attrs["gen_ai.response.id"].string_value == "resp_synthetic_attempt"
    assert "openinference.span.kind" not in attempt_attrs
    assert all(s.end_time_unix_nano - s.start_time_unix_nano == 1_250_000 for s in spans)


@pytest.mark.parametrize("encoded_messages", [False, True])
def test_observed_foundry_service_shapes_roundtrip_real_otlp_without_inventing_root_or_total(
    encoded_messages,
):
    import json
    from pathlib import Path

    from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
    from opentelemetry.sdk.trace.export import SpanExportResult
    from telemetry_pipeline.batch import transform_batch

    fixture = Path(__file__).parents[1] / "telemetry-mapping" / "fixtures" / "foundry_service_spans.json"
    rows = json.loads(fixture.read_text())
    messages = {
        "input": [{"role": "user", "parts": [
            {"type": "text", "content": "Synthetic coverage question"},
            {"type": "tool_call", "id": "synthetic-call", "arguments": {"plan": ["SYN-1"]}},
        ]}],
        "output": [{"role": "assistant", "parts": [
            {"type": "text", "content": "Synthetic coverage response"},
        ]}],
    }
    rows[1]["Properties"].update({
        f"gen_ai.{side}.messages": json.dumps(value) if encoded_messages else value
        for side, value in messages.items()
    })
    rows[1]["Properties"]["correlation.id"] = "synthetic-message-request"
    bad = {**rows[1], "Properties": {**rows[1]["Properties"], "gen_ai.usage.input_tokens": -1}}

    class RoundtripExporter:
        def export(self, spans):
            self.request = ExportTraceServiceRequest.FromString(encode_spans(spans).SerializeToString())
            return SpanExportResult.SUCCESS

    exporter = RoundtripExporter()
    result = transform_batch([json.dumps([*rows, bad]).encode()], exporter)
    assert len(result.spans) == 2
    assert len(result.skipped) == 1
    spans = [span for resource in exporter.request.resource_spans
             for scope in resource.scope_spans for span in scope.spans]
    agent, chat = spans
    assert agent.trace_id.hex() == chat.trace_id.hex() == rows[0]["OperationId"]
    assert agent.parent_span_id.hex() == rows[0]["ParentId"]  # Missing upstream parent stays missing.
    assert agent.span_id == chat.parent_span_id
    assert chat.span_id.hex() == rows[1]["Id"]
    assert agent.name == rows[0]["Name"] and chat.name == rows[1]["Name"]
    assert agent.start_time_unix_nano == 1792052765472348200
    assert chat.start_time_unix_nano == 1792052766118237000
    assert agent.end_time_unix_nano - agent.start_time_unix_nano == 1_962_073_100
    assert chat.end_time_unix_nano - chat.start_time_unix_nano == 765_187_400
    assert agent.status.code == chat.status.code == 1  # Success -> OK, not original OTel status proof.
    assert agent.kind == 1 and chat.kind == 3  # Best effort, not original core-kind recovery.
    agent_attrs = {attr.key: attr.value for attr in agent.attributes}
    attrs = {attr.key: attr.value for attr in chat.attributes}
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
        assert attrs[f"{side}.value"].WhichOneof("value") == "string_value"
        assert json.loads(attrs[f"{side}.value"].string_value) == expected
        assert attrs[f"{side}.mime_type"].string_value == "application/json"
        assert f"{side}.value" not in agent_attrs  # Never copy child content to its parent.
    for absent in ("llm.token_count.total",
                   "gen_ai.input.messages", "gen_ai.output.messages", "span_type"):
        assert absent not in attrs
    assert "llm.token_count.prompt" not in agent_attrs
    assert len(chat.events) == len(chat.links) == 0
    resources = exporter.request.resource_spans
    assert any(attr.key == "service.name" and attr.value.string_value == "responsesapi"
               for resource in resources for attr in resource.resource.attributes)


@pytest.mark.parametrize("hierarchical_parent", [False, True])
def test_observed_native_root_roundtrips_otlp_with_child_and_rejected_neighbor(hierarchical_parent):
    import json
    from pathlib import Path

    from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
    from opentelemetry.sdk.trace.export import SpanExportResult
    from telemetry_pipeline.batch import transform_batch

    fixture = Path(__file__).parents[1] / "telemetry-mapping" / "fixtures" / "native_preflight_root.json"
    root = json.loads(fixture.read_text())
    parent = f"|{root['OperationId']}.{root['Id']}." if hierarchical_parent else root["Id"]
    child = {
        **root, "Id": "d9cf8d9381425553", "ParentId": parent, "Name": "llm.chat_completion",
        "Properties": {
            **json.loads(root["Properties"]), "llm.model_name": "synthetic-model",
            "openinference.span.kind": "LLM",
            "llm.token_count.prompt": "0", "llm.token_count.completion": "1",
            "llm.token_count.total": "1",
        },
    }
    invalid = {**child, "ParentId": "11111111111111111111111111111111"}

    class RoundtripExporter:
        def export(self, spans):
            self.request = ExportTraceServiceRequest.FromString(encode_spans(spans).SerializeToString())
            return SpanExportResult.SUCCESS

    exporter = RoundtripExporter()
    result = transform_batch([json.dumps([root, child, invalid]).encode()], exporter)
    assert result.total_records == 3
    assert len(result.spans) == 2
    assert len(result.skipped) == 1
    assert "root marker differs" in result.skipped[0].reason
    assert result.export_result == SpanExportResult.SUCCESS
    spans = [span for resource in exporter.request.resource_spans
             for scope in resource.scope_spans for span in scope.spans]
    root_pb, child_pb = spans
    assert root_pb.trace_id.hex() == child_pb.trace_id.hex() == root["OperationId"]
    assert root_pb.span_id.hex() == child_pb.parent_span_id.hex() == root["Id"]
    assert root_pb.parent_span_id == b""
    assert root_pb.kind == 1  # Existing best-effort INTERNAL when source kind is absent.
    assert child_pb.kind == 3  # OTLP CLIENT inferred from OpenInference LLM.
    assert child_pb.span_id.hex() == child["Id"]
    attrs = {attr.key: attr.value for attr in child_pb.attributes}
    assert attrs["correlation.id"].string_value == json.loads(root["Properties"])["correlation.id"]
    assert attrs["llm.model_name"].string_value == "synthetic-model"
    for name, expected in (("prompt", 0), ("completion", 1), ("total", 1)):
        value = attrs[f"llm.token_count.{name}"]
        assert value.WhichOneof("value") == "int_value"
        assert value.int_value == expected


def test_native_dependency_batch_uses_production_mapping_without_network():
    """SYNTHETIC LAW columns on existing batch surfaces; no captured envelope."""
    import json

    from opentelemetry.sdk.trace.export import SpanExportResult
    from telemetry_pipeline.batch import transform_batch
    from telemetry_pipeline.exporter import _CountingSpanExporter

    rows = build_synthetic_batch(trace_count=1)
    aliases = {
        "operation_Id": "OperationId",
        "operation_ParentId": "ParentId",
        "id": "Id",
        "customDimensions": "Properties",
    }
    native_rows = [
        {
            **{aliases.get(key, key): value for key, value in row.items()},
            "Type": "AppDependencies",
            "TimeGenerated": "2026-10-13T05:23:04Z",
            "DurationMs": 1.25,
            "AppRoleName": "synthetic-native-agent",
        }
        for row in rows
    ]

    class InMemoryExporter:
        def __init__(self):
            self.batches = []

        def export(self, spans):
            self.batches.append(list(spans))
            return SpanExportResult.SUCCESS

    for payload in (native_rows, {"records": native_rows}):
        sink = InMemoryExporter()
        exporter = _CountingSpanExporter(sink)
        result = transform_batch([json.dumps(payload)], exporter)
        assert result.skipped == []
        assert result.export_result == SpanExportResult.SUCCESS
        assert exporter.exported_count == len(rows)
        assert exporter.failed_count == 0
        assert len(sink.batches) == 1
        for row, span in zip(rows, sink.batches[0]):
            assert span.context.trace_id == int(row["operation_Id"], 16)
            assert span.context.span_id == int(row["id"], 16)
            if row["operation_ParentId"]:
                assert span.parent.span_id == int(row["operation_ParentId"], 16)
            else:
                assert span.parent is None
            assert span.end_time - span.start_time == 1_250_000
        llm = next(span for span in result.spans if span.name == "llm.chat_completion")
        assert llm.attributes["llm.token_count.total"] == 60
        assert llm.attributes["correlation.id"] == rows[2]["customDimensions"]["correlation.id"]


def test_native_invalid_properties_are_flagged_without_losing_valid_dependency():
    """Existing single-object surface with a malformed adjacent synthetic row."""
    import json

    from opentelemetry.sdk.trace.export import SpanExportResult
    from telemetry_pipeline.batch import transform_batch

    valid = {
        "Type": "AppDependencies",
        "OperationId": "0af7651916cd43dd8448eb211c80319c",
        "Id": "b7ad6b7169203331",
        "ParentId": "",
        "Name": "prompt_agent.invoke",
        "Success": True,
        "Properties": {"correlation.id": "synthetic-native-batch"},
    }
    invalid = {**valid, "Id": "c8be7c8270314442", "Properties": "{broken"}

    class InMemoryExporter:
        def __init__(self):
            self.spans = []

        def export(self, spans):
            self.spans.extend(spans)
            return SpanExportResult.SUCCESS

    sink = InMemoryExporter()
    result = transform_batch([json.dumps(valid), json.dumps(invalid)], sink)
    assert result.total_records == 2
    assert len(result.skipped) == 1
    assert "JSON object" in result.skipped[0].reason
    assert len(sink.spans) == 1
    assert sink.spans[0].context.span_id == int(valid["Id"], 16)


def test_native_mixed_request_dependency_serializes_real_otlp_graph():
    """SYNTHETIC consumer bytes through production mapping and protobuf, no network."""
    import json

    from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
    from opentelemetry.sdk.trace.export import SpanExportResult
    from telemetry_pipeline.batch import transform_batch

    trace = "0af7651916cd43dd8448eb211c80319c"
    root_id, child_id = "b7ad6b7169203331", "d9cf8d9381425553"
    root = {
        "Type": "AppRequests", "OperationId": trace, "Id": f"|{trace}.{root_id}.",
        "ParentId": "", "Name": "prompt_agent.invoke", "Success": True,
        "TimeGenerated": "2026-10-14T07:00:00.1234567Z", "DurationMs": 20,
        "Properties": {"correlation.id": "synthetic-native-e2e",
                       "openinference.span.kind": "CHAIN"},
    }
    child = {
        **root, "Type": "AppDependencies", "Id": child_id, "ParentId": root["Id"],
        "Name": "llm.chat_completion", "Success": False, "DurationMs": 0,
        "Properties": json.dumps({
            "correlation.id": "synthetic-native-e2e", "openinference.span.kind": "LLM",
            "llm.model_name": "synthetic-model", "llm.token_count.prompt": "0",
            "llm.token_count.completion": 0, "llm.token_count.total": "0",
        }),
    }

    class ConsumerEvent:
        def get_body(self):
            return json.dumps([root, child, {**child, "Properties": {"llm.model_name": {}}}]).encode()

    class EncodingExporter:
        def export(self, spans):
            self.request = encode_spans(spans)
            self.request.SerializeToString()
            return SpanExportResult.SUCCESS

    exporter = EncodingExporter()
    result = transform_batch([ConsumerEvent(), b"\xff", '{"records": null}'], exporter)
    assert len(result.skipped) == 3
    assert len(result.spans) == 2
    spans = [span for resource in exporter.request.resource_spans
             for scope in resource.scope_spans for span in scope.spans]
    request, dependency = spans
    assert request.trace_id.hex() == dependency.trace_id.hex() == trace
    assert request.span_id.hex() == dependency.parent_span_id.hex() == root_id
    assert request.parent_span_id == b""
    assert dependency.span_id.hex() == child_id
    assert request.kind == 2  # OTLP SERVER
    assert dependency.status.code == 2  # OTLP ERROR
    assert dependency.end_time_unix_nano == dependency.start_time_unix_nano
    attrs = {attr.key: attr.value for attr in dependency.attributes}
    assert attrs["llm.token_count.total"].WhichOneof("value") == "int_value"
    assert attrs["llm.token_count.total"].int_value == 0
    assert attrs["correlation.id"].string_value == "synthetic-native-e2e"
