"""Synthetic source isolation across native and normalized legacy batches."""
import json

import pytest

from telemetry_pipeline.batch import transform_batch
from telemetry_pipeline.mapping import MalformedRecordError, record_to_span
from telemetry_pipeline.source_policy import SourcePolicy

from .conftest import make_record

ROLE = "fotoa-demo-func-eastus2"
COMPONENT = "/subscriptions/synthetic/resourceGroups/demo/providers/Microsoft.Insights/components/health"
POLICY = SourcePolicy.from_environment({
    "PIPELINE_EXCLUDED_SERVICE_NAMES": json.dumps([ROLE, "telemetry-pipeline-function"]),
    "PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS": json.dumps([COMPONENT]),
})


def native(record):
    record = dict(record)
    for source, destination in {
        "operation_Id": "OperationId", "operation_ParentId": "ParentId",
        "id": "Id", "timestamp": "TimeGenerated", "duration": "DurationMs",
        "customDimensions": "Properties", "cloud_RoleName": "AppRoleName",
    }.items():
        if source in record:
            record[destination] = record.pop(source)
    record["Type"] = "AppDependencies"
    return record


@pytest.mark.parametrize("name,kind", [
    ("TelemetryTransform", "CHAIN"), ("DurableGenAIOutbox", "AGENT"),
    ("POST /v1/traces", "LLM"), ("GET storage", "TOOL"),
    ("retriever.query", "RETRIEVER"), ("arbitrary operational dependency", None),
])
@pytest.mark.parametrize("native_form", [True, False])
def test_pipeline_identity_excluded_regardless_of_operation(stub_exporter, name, kind, native_form):
    record = make_record(Name=name, cloud_RoleName=ROLE, customDimensions=(
        {"openinference.span.kind": kind} if kind else {}
    ))
    if native_form:
        record = native(record)
    result = transform_batch([json.dumps(record)], stub_exporter, POLICY)
    assert not result.spans
    assert result.skipped[0].reason == "excluded:service_identity"
    assert not stub_exporter.export_calls


@pytest.mark.parametrize("kind", ["CHAIN", "LLM", "TOOL", "RETRIEVER", None])
def test_agent_children_roots_and_missing_roles_retained(stub_exporter, kind):
    rows = [
        make_record(cloud_RoleName=ROLE + "-agent", Name="TelemetryTransform.agent.child",
                    operation_ParentId="1111111111111111",
                    customDimensions={"openinference.span.kind": kind} if kind else {}),
        make_record(Name="DurableGenAIOutbox"),
        native(make_record(cloud_RoleName="synthetic-agent", Name="GET storage")),
    ]
    # The mapper's fallback name is explicitly excluded, but is not source evidence.
    result = transform_batch([json.dumps(rows)], stub_exporter, POLICY)
    assert len(result.spans) == 3 and not result.skipped
    assert result.spans[0].parent.span_id == int("1111111111111111", 16)
    assert result.spans[1].parent is None
    assert len(stub_exporter.export_calls) == 1
    for source, actual in zip(rows, result.spans):
        expected = record_to_span(source)
        assert actual.context == expected.context
        assert actual.attributes == expected.attributes


def test_mixed_native_normalized_aliases_and_component(stub_exporter):
    good = make_record(cloud_RoleName="synthetic-agent")
    conflict = native(make_record(cloud_RoleName=ROLE))
    conflict["cloud_RoleName"] = "synthetic-agent"
    rows = [
        native(good), make_record(cloud_RoleName=ROLE),
        native(make_record(_ResourceId=COMPONENT.upper())),
        conflict, good, make_record(AppRoleName=ROLE, cloud_RoleName=ROLE),
    ]
    result = transform_batch([json.dumps({"records": rows})], stub_exporter, POLICY)
    assert len(result.spans) == 2 and len(result.skipped) == 4
    assert sum(row.reason.startswith("excluded:") for row in result.skipped) == 3
    assert any("conflicting" in row.reason for row in result.skipped)
    assert len(stub_exporter.export_calls) == 1


@pytest.mark.parametrize("record", [
    {"AppRoleName": ROLE, "cloud_RoleName": "synthetic-agent"},
    {"AppRoleName": "synthetic-agent", "cloud_RoleName": ROLE},
    {"AppRoleName": ROLE, "cloud_RoleName": None},
    {"AppRoleName": 3}, {"cloud_RoleName": []}, {"_ResourceId": 3},
])
def test_invalid_identity_never_silently_selects_alias(record):
    with pytest.raises(MalformedRecordError):
        POLICY.exclusion_reason(record)


@pytest.mark.parametrize("name", [
    "PIPELINE_EXCLUDED_SERVICE_NAMES", "PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS",
])
@pytest.mark.parametrize("value", ["", "not-json", "null", "{}", '"role"', "[1]", '[""]', '[" role "]'])
def test_malformed_settings_fail_explicitly_before_any_batch_export(stub_exporter, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name):
        transform_batch([json.dumps(make_record())], stub_exporter)
    assert not stub_exporter.export_calls


def test_defaults_empty_and_service_names_case_sensitive(monkeypatch):
    monkeypatch.delenv("PIPELINE_EXCLUDED_SERVICE_NAMES", raising=False)
    monkeypatch.delenv("PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS", raising=False)
    assert not SourcePolicy.from_environment().exclusion_reason({"AppRoleName": ROLE})
    assert not POLICY.exclusion_reason({"AppRoleName": ROLE.upper()})
    assert not POLICY.exclusion_reason({"_ResourceId": COMPONENT + "-agent"})
