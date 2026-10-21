"""Synthetic source-identity rules; durable integration lives in test_durable."""
import json

import pytest

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
def test_pipeline_identity_excluded_regardless_of_operation(name, kind, native_form):
    record = make_record(Name=name, cloud_RoleName=ROLE, customDimensions=(
        {"openinference.span.kind": kind} if kind else {}
    ))
    if native_form:
        record = native(record)
    assert POLICY.exclusion_reason(record) == "service_identity"


@pytest.mark.parametrize("kind", ["CHAIN", "LLM", "TOOL", "RETRIEVER", None])
def test_agent_children_roots_and_missing_roles_retained(kind):
    rows = [
        make_record(cloud_RoleName=ROLE + "-agent", Name="TelemetryTransform.agent.child",
                    operation_ParentId="1111111111111111",
                    customDimensions={"openinference.span.kind": kind} if kind else {}),
        make_record(Name="DurableGenAIOutbox"),
        native(make_record(cloud_RoleName="synthetic-agent", Name="GET storage")),
    ]
    # The mapper's fallback name is explicitly excluded, but is not source evidence.
    assert all(POLICY.exclusion_reason(row) == "" for row in rows)
    spans = [record_to_span(row) for row in rows]
    assert spans[0].parent.span_id == int("1111111111111111", 16)
    assert spans[1].parent is None


def test_mixed_native_normalized_aliases_and_component():
    good = make_record(cloud_RoleName="synthetic-agent")
    conflict = native(make_record(cloud_RoleName=ROLE))
    conflict["cloud_RoleName"] = "synthetic-agent"
    rows = [
        native(good), make_record(cloud_RoleName=ROLE),
        native(make_record(_ResourceId=COMPONENT.upper())),
        good, make_record(AppRoleName=ROLE, cloud_RoleName=ROLE),
    ]
    assert [POLICY.exclusion_reason(row) for row in rows] == [
        "", "service_identity", "component_identity", "", "service_identity",
    ]
    with pytest.raises(MalformedRecordError, match="conflicting"):
        POLICY.exclusion_reason(conflict)


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
def test_malformed_settings_fail_explicitly(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name):
        SourcePolicy.from_environment()


def test_defaults_empty_and_service_names_case_sensitive(monkeypatch):
    monkeypatch.delenv("PIPELINE_EXCLUDED_SERVICE_NAMES", raising=False)
    monkeypatch.delenv("PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS", raising=False)
    assert not SourcePolicy.from_environment().exclusion_reason({"AppRoleName": ROLE})
    assert not POLICY.exclusion_reason({"AppRoleName": ROLE.upper()})
    assert not POLICY.exclusion_reason({"_ResourceId": COMPONENT + "-agent"})
