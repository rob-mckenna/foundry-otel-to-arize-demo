"""Span kind/status field-group tests (#92).

Covers Name->span.name, Success(bool)->OTLP status code enum, the
openinference.span.kind passthrough-but-never-synthesized rule, and the
retry.* string->int/bool coercions.
"""
from __future__ import annotations

from opentelemetry.trace import SpanKind
from opentelemetry.trace.status import StatusCode

from telemetry_pipeline.mapping import map_span_kind_status_fields, record_to_span

from .conftest import make_record


def test_success_true_maps_to_status_code_ok():
    record = make_record(Success=True)
    span = record_to_span(record)
    assert span.status.status_code == StatusCode.OK


def test_success_false_maps_to_status_code_error():
    record = make_record(Success=False)
    span = record_to_span(record)
    assert span.status.status_code == StatusCode.ERROR


def test_name_maps_to_span_name_unchanged():
    record = make_record(Name="tool.lookup_plan_details")
    span = record_to_span(record)
    assert span.name == "tool.lookup_plan_details"


def test_openinference_span_kind_present_is_passed_through():
    name, status, kind, attrs = map_span_kind_status_fields(
        {"Name": "llm.chat_completion", "Success": True},
        {"openinference.span.kind": "LLM"},
    )
    assert attrs["openinference.span.kind"] == "LLM"
    assert kind == SpanKind.CLIENT


def test_openinference_span_kind_absent_is_not_synthesized():
    """Retry-attempt spans never set this customDimension - the Function
    must not invent a value when the source span never set one (#92 §2.3)."""
    name, status, kind, attrs = map_span_kind_status_fields(
        {"Name": "llm.chat_completion.attempt", "Success": False},
        {"retry.attempt": "1", "retry.max_attempts": "3", "retry.will_retry": "true"},
    )
    assert "openinference.span.kind" not in attrs


def test_retry_int_fields_coerced_from_string():
    name, status, kind, attrs = map_span_kind_status_fields(
        {"Name": "llm.chat_completion.attempt", "Success": False},
        {"retry.attempt": "2", "retry.max_attempts": "3"},
    )
    assert attrs["retry.attempt"] == 2
    assert attrs["retry.max_attempts"] == 3
    assert isinstance(attrs["retry.attempt"], int)


def test_retry_will_retry_coerced_from_string_to_bool():
    name, status, kind, attrs = map_span_kind_status_fields(
        {"Name": "llm.chat_completion.attempt", "Success": False},
        {"retry.will_retry": "true"},
    )
    assert attrs["retry.will_retry"] is True

    name, status, kind, attrs = map_span_kind_status_fields(
        {"Name": "llm.chat_completion.attempt", "Success": False},
        {"retry.will_retry": "false"},
    )
    assert attrs["retry.will_retry"] is False


def test_retry_fields_absent_on_non_retry_spans():
    name, status, kind, attrs = map_span_kind_status_fields(
        {"Name": "prompt_agent.invoke", "Success": True},
        {"openinference.span.kind": "CHAIN"},
    )
    assert "retry.attempt" not in attrs
    assert "retry.max_attempts" not in attrs
    assert "retry.will_retry" not in attrs


def test_record_to_span_full_retry_attempt_scenario():
    record = make_record(
        Name="llm.chat_completion.attempt",
        Success=False,
        custom_dimensions={
            "openinference.span.kind": None,  # simulate absence below
            "retry.attempt": "1",
            "retry.max_attempts": "3",
            "retry.will_retry": "true",
        },
    )
    # Remove the None sentinel - make_record merges dicts, so pop it to
    # simulate a key that's genuinely absent rather than present-with-None.
    record["customDimensions"].pop("openinference.span.kind")

    span = record_to_span(record)
    assert span.name == "llm.chat_completion.attempt"
    assert span.status.status_code == StatusCode.ERROR
    assert "openinference.span.kind" not in span.attributes
    assert span.attributes["retry.attempt"] == 1
    assert span.attributes["retry.max_attempts"] == 3
    assert span.attributes["retry.will_retry"] is True
