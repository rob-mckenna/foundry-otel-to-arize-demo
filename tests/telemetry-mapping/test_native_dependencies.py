"""Synthetic LAW rows, including an observed preflight projection, not EH bodies."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from opentelemetry.trace.status import StatusCode
from opentelemetry.trace import SpanKind

from telemetry_pipeline.mapping import MalformedRecordError, record_to_span


@pytest.mark.parametrize("uppercase_parent", [False, True])
@pytest.mark.parametrize("table", ["AppDependencies", "AppRequests"])
def test_observed_native_root_marker_preserves_source_root(uppercase_parent, table):
    row = json.loads((Path(__file__).parent / "fixtures" / "native_preflight_root.json").read_text())
    row["Type"] = table
    if table == "AppRequests":
        row.update(Name="synthetic.native.request", DurationMs=12.5,
                   Properties={"correlation.id": "synthetic-native-request"})
    original_parent = row["ParentId"]
    if uppercase_parent:
        row["ParentId"] = original_parent.upper()
    span = record_to_span(row)
    assert span.parent is None
    assert span.context.trace_id == int(row["OperationId"], 16)
    assert span.context.span_id == int(row["Id"], 16)
    properties = json.loads(row["Properties"]) if isinstance(row["Properties"], str) else row["Properties"]
    assert span.attributes["correlation.id"] == properties["correlation.id"]
    assert span.kind == (SpanKind.SERVER if table == "AppRequests" else SpanKind.INTERNAL)
    assert span.name == row["Name"]
    assert span.status.status_code == StatusCode.OK
    assert span.end_time - span.start_time == int(row["DurationMs"] * 1_000_000)
    assert "llm.token_count.total" not in span.attributes
    assert row["ParentId"] == (original_parent.upper() if uppercase_parent else original_parent)


@pytest.mark.parametrize("table", ["AppDependencies", "AppRequests"])
def test_native_mismatching_trace_parent_is_rejected(native_dependency, table):
    native_dependency["Type"] = table
    native_dependency["ParentId"] = "11111111111111111111111111111111"
    with pytest.raises(MalformedRecordError, match="root marker differs"):
        record_to_span(native_dependency)


@pytest.mark.parametrize("table", ["AppDependencies", "AppRequests"])
@pytest.mark.parametrize("legacy_fields", [
    ("OperationId",), ("ParentId",), ("OperationId", "ParentId"),
])
def test_legacy_trace_parent_shapes_still_reject(native_dependency, table, legacy_fields):
    native_dependency["Type"] = table
    native_dependency["ParentId"] = native_dependency["OperationId"]
    for native, legacy in (("OperationId", "operation_Id"), ("ParentId", "operation_ParentId")):
        if native in legacy_fields:
            native_dependency[legacy] = native_dependency.pop(native)
    with pytest.raises(MalformedRecordError):
        record_to_span(native_dependency)


@pytest.fixture
def native_dependency():
    return {
        "Type": "AppDependencies",
        "OperationId": "0af7651916cd43dd8448eb211c80319c",
        "Id": "d9cf8d9381425553",
        "ParentId": "b7ad6b7169203331",
        "Name": "llm.chat_completion",
        "Success": True,
        "TimeGenerated": "2026-10-13T05:23:04.336109Z",
        "DurationMs": 12.5,
        "AppRoleName": "synthetic-prompt-agent",
        "AppRoleInstance": "synthetic-instance",
        "Properties": {
            "correlation.id": "synthetic-native-correlation",
            "openinference.span.kind": "LLM",
            "llm.model_name": "synthetic-model",
            "llm.token_count.prompt": "42",
            "llm.token_count.completion": "18",
            "llm.token_count.total": "60",
            "input.value": "Synthetic request",
            "output.value": "Synthetic response",
        },
    }


@pytest.mark.parametrize("encoded_properties", [False, True])
def test_native_identity_tokens_time_and_resource(native_dependency, encoded_properties, monkeypatch):
    monkeypatch.setenv("OTEL_RESOURCE_ATTRIBUTES", "openinference.project.name=synthetic-native")
    original_properties = dict(native_dependency["Properties"])
    if encoded_properties:
        native_dependency["Properties"] = json.dumps(original_properties)
    span = record_to_span(native_dependency)

    assert span.context.trace_id == int(native_dependency["OperationId"], 16)
    assert span.context.span_id == int(native_dependency["Id"], 16)
    assert span.parent.span_id == int(native_dependency["ParentId"], 16)
    assert span.name == native_dependency["Name"]
    assert span.status.status_code == StatusCode.OK
    assert span.start_time == 1791868984336109000
    assert span.end_time - span.start_time == 12_500_000
    assert span.resource.attributes["service.name"] == native_dependency["AppRoleName"]
    assert span.resource.attributes["service.instance.id"] == native_dependency["AppRoleInstance"]
    assert span.resource.attributes["openinference.project.name"] == "synthetic-native"
    for key in ("correlation.id", "llm.model_name", "input.value", "output.value"):
        assert span.attributes[key] == original_properties[key]
    for key, expected in (("prompt", 42), ("completion", 18), ("total", 60)):
        value = span.attributes[f"llm.token_count.{key}"]
        assert value == expected
        assert type(value) is int
    assert "operation_Id" not in native_dependency


@pytest.mark.parametrize("timestamp", [
    "2026-10-13T05:23:04.336109Z",
    "2026-10-13T01:23:04.336109-04:00",
    "2026-10-13T05:23:04.336109",
])
def test_native_root_error_and_utc_time(native_dependency, timestamp):
    native_dependency.update(ParentId="", Success=False, TimeGenerated=timestamp)
    span = record_to_span(native_dependency)
    assert span.parent is None
    assert span.status.status_code == StatusCode.ERROR
    assert span.start_time == 1791868984336109000


def test_native_seven_digit_timestamp_and_zero_duration(native_dependency):
    native_dependency.update(TimeGenerated="2026-10-13T05:23:04.3361096Z", DurationMs=0)
    span = record_to_span(native_dependency)
    assert span.start_time == 1791868984336109600
    assert span.end_time == span.start_time


def test_request_root_and_hierarchical_dependency_preserve_graph(native_dependency):
    root = {**native_dependency, "Type": "AppRequests", "ParentId": "",
            "Id": f"|{native_dependency['OperationId']}.{native_dependency['ParentId']}.",
            "Name": "prompt_agent.invoke", "Properties": {
                "correlation.id": "synthetic-native-correlation",
                "openinference.span.kind": "CHAIN",
            }}
    child = {**native_dependency,
             "Id": f"|{native_dependency['OperationId']}.{native_dependency['Id']}.",
             "ParentId": root["Id"]}
    root_span, child_span = map(record_to_span, (root, child))
    assert root_span.parent is None
    assert root_span.kind == SpanKind.SERVER
    assert child_span.kind == SpanKind.CLIENT
    assert root_span.context.trace_id == child_span.context.trace_id
    assert root_span.context.span_id == child_span.parent.span_id
    assert child_span.context.span_id == int(native_dependency["Id"], 16)
    assert root_span.attributes["correlation.id"] == child_span.attributes["correlation.id"]


@pytest.mark.parametrize("field", ["Id", "ParentId"])
@pytest.mark.parametrize("value", [
    "|11111111111111111111111111111111.b7ad6b7169203331.",
    "|0af7651916cd43dd8448eb211c80319c.b7ad6b7169203331.extra.",
    "|0af7651916cd43dd8448eb211c80319c.0000000000000000.",
])
def test_ambiguous_or_conflicting_hierarchical_ids_rejected(native_dependency, field, value):
    native_dependency[field] = value
    with pytest.raises(MalformedRecordError):
        record_to_span(native_dependency)


def test_zero_tokens_are_preserved_not_treated_as_missing(native_dependency):
    for field in ("prompt", "completion", "total"):
        native_dependency["Properties"][f"llm.token_count.{field}"] = "0"
    span = record_to_span(native_dependency)
    for field in ("prompt", "completion", "total"):
        assert span.attributes[f"llm.token_count.{field}"] == 0
        assert type(span.attributes[f"llm.token_count.{field}"]) is int


@pytest.mark.parametrize(("field", "value"), [
    ("openinference.span.kind", []), ("openinference.span.kind", {}),
    ("correlation.id", 1), ("llm.model_name", {}), ("input.value", False),
    ("output.value", None), ("llm.token_count.prompt", True),
    ("llm.token_count.completion", -1), ("llm.token_count.total", 2**63),
    ("llm.token_count.prompt", 1.5), ("llm.token_count.total", None),
])
def test_invalid_dimensions_are_observable_rejections(native_dependency, field, value):
    native_dependency["Properties"][field] = value
    with pytest.raises(MalformedRecordError):
        record_to_span(native_dependency)


@pytest.mark.parametrize(("native", "legacy"), [
    ("OperationId", "operation_Id"), ("Id", "id"), ("ParentId", "operation_ParentId"),
    ("Properties", "customDimensions"), ("TimeGenerated", "timestamp"),
    ("DurationMs", "duration"), ("AppRoleName", "cloud_RoleName"),
    ("AppRoleInstance", "cloud_RoleInstance"),
])
def test_alias_conflicts_are_rejected(native_dependency, native, legacy):
    native_dependency[legacy] = {} if native == "Properties" else "conflicting-value"
    with pytest.raises(MalformedRecordError, match="conflicting"):
        record_to_span(native_dependency)


def test_matching_aliases_and_legacy_only_remain_compatible(native_dependency):
    aliases = {
        "OperationId": "operation_Id", "Id": "id", "ParentId": "operation_ParentId",
        "Properties": "customDimensions", "TimeGenerated": "timestamp",
        "DurationMs": "duration", "AppRoleName": "cloud_RoleName",
        "AppRoleInstance": "cloud_RoleInstance",
    }
    mixed = dict(native_dependency)
    legacy = {key: value for key, value in native_dependency.items() if key not in aliases}
    for native, old in aliases.items():
        mixed[old] = native_dependency[native]
        legacy[old] = native_dependency[native]
    mixed["customDimensions"] = json.dumps(mixed["customDimensions"])
    native_span, mixed_span, legacy_span = map(record_to_span, (native_dependency, mixed, legacy))
    for span in (mixed_span, legacy_span):
        assert span.context == native_span.context
        assert span.parent == native_span.parent
        assert dict(span.attributes) == dict(native_span.attributes)
        assert span.start_time == native_span.start_time
        assert span.end_time == native_span.end_time
        assert span.resource == native_span.resource


@pytest.mark.parametrize(("field", "value"), [
    ("OperationId", "bad-id"), ("Id", "0" * 16), ("ParentId", "0" * 16),
    ("Id", "+" + "1" * 15), ("Properties", "{broken"),
    ("Properties", "[1, 2]"), ("Properties", "null"),
    ("TimeGenerated", "not-a-date"), ("TimeGenerated", 123),
    ("TimeGenerated", "2026-10-13T05:23:04.1234567890Z"),
    ("DurationMs", "not-a-number"), ("DurationMs", None),
    ("DurationMs", float("nan")), ("DurationMs", float("inf")),
    ("DurationMs", 1e308), ("DurationMs", -1), ("DurationMs", True),
    ("Name", None),
    ("Success", "not-a-bool"), ("Type", "AppTraces"), ("Type", "AppExceptions"),
])
def test_invalid_native_values_are_flagged(native_dependency, field, value):
    native_dependency[field] = value
    with pytest.raises(MalformedRecordError):
        record_to_span(native_dependency)
