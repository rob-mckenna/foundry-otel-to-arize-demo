"""Identity/correlation field-group tests (#89).

Covers trace_id/span_id/parent_span_id verbatim-hex copying, the
root-span-no-parent edge case (must NOT become a zero-filled parent), the
correlation.id passthrough, and malformed-identity-field rejection.
"""
from __future__ import annotations

import pytest

from telemetry_pipeline.mapping import (
    MalformedRecordError,
    build_parent_context,
    map_correlation_id,
    parse_parent_span_id,
    parse_span_id,
    parse_trace_id,
    record_to_span,
)

from .conftest import make_record


def test_trace_id_copied_verbatim_as_int():
    trace_id = parse_trace_id("0af7651916cd43dd8448eb211c80319c")
    assert trace_id == int("0af7651916cd43dd8448eb211c80319c", 16)


def test_span_id_copied_verbatim_as_int():
    span_id = parse_span_id("b7ad6b7169203331")
    assert span_id == int("b7ad6b7169203331", 16)


@pytest.mark.parametrize("empty_value", [None, ""])
def test_root_span_has_no_parent_not_zero_filled(empty_value):
    """A root span's missing operation_ParentId must become None, never
    an all-zero span ID - coercing to zero would fake a parent."""
    parent_span_id = parse_parent_span_id(empty_value)
    assert parent_span_id is None

    parent_context = build_parent_context(trace_id=0x1234, parent_span_id=parent_span_id)
    assert parent_context is None


def test_child_span_parent_id_copied_verbatim():
    parent_span_id = parse_parent_span_id("b7ad6b7169203331")
    assert parent_span_id == int("b7ad6b7169203331", 16)

    parent_context = build_parent_context(trace_id=0x1234, parent_span_id=parent_span_id)
    assert parent_context is not None
    assert parent_context.span_id == parent_span_id
    assert parent_context.trace_id == 0x1234


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("operation_Id", "not-hex!!"),
        ("operation_Id", "0af7651916cd43dd8448eb211c80319"),  # 31 chars, too short
        ("id", "zzzzzzzzzzzzzzzz"),
        ("id", "b7ad6b716920333"),  # 15 chars, too short
    ],
)
def test_malformed_identity_fields_are_rejected_not_coerced(field_name, bad_value):
    record = make_record(**{field_name: bad_value})
    with pytest.raises(MalformedRecordError):
        record_to_span(record)


def test_malformed_operation_parent_id_is_rejected_when_present_but_invalid():
    record = make_record(operation_ParentId="not-valid-hex!!!")
    with pytest.raises(MalformedRecordError):
        record_to_span(record)


def test_correlation_id_passthrough():
    attrs = map_correlation_id({"correlation.id": "abc-123"})
    assert attrs == {"correlation.id": "abc-123"}


def test_correlation_id_absent_when_not_in_source():
    assert map_correlation_id({}) == {}


def test_record_to_span_sets_correlation_id_attribute():
    record = make_record(custom_dimensions={"correlation.id": "xyz-789"})
    span = record_to_span(record)
    assert span.attributes["correlation.id"] == "xyz-789"


def test_record_to_span_preserves_ids_end_to_end():
    record = make_record()
    span = record_to_span(record)

    assert span.context.trace_id == int(record["operation_Id"], 16)
    assert span.context.span_id == int(record["id"], 16)
    assert span.parent is None  # root span: operation_ParentId == ""
