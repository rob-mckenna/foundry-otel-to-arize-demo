"""Token field-group tests (#90): the string -> int type-coercion rule.

This is the "Transform-wide rule" `field-mapping.md` calls out as the
highest-risk correctness bug class: App Insights exports every
customDimensions value as a JSON string even for attributes the OTel SDK
set as native int/bool.
"""
from __future__ import annotations

import pytest

from telemetry_pipeline.mapping import MalformedRecordError, map_token_fields, record_to_span

from .conftest import make_record


def test_token_fields_coerced_from_string_to_int():
    custom_dimensions = {
        "llm.token_count.prompt": "5",
        "llm.token_count.completion": "7",
        "llm.token_count.total": "12",
    }
    attrs = map_token_fields(custom_dimensions)
    assert attrs == {
        "llm.token_count.prompt": 5,
        "llm.token_count.completion": 7,
        "llm.token_count.total": 12,
    }
    for value in attrs.values():
        assert isinstance(value, int)


def test_token_fields_absent_are_omitted_not_synthesized():
    assert map_token_fields({}) == {}
    assert map_token_fields({"llm.token_count.prompt": "5"}) == {"llm.token_count.prompt": 5}


def test_token_fields_already_int_pass_through():
    """Defensive: if a source ever delivers a native int (not the usual App
    Insights string export), it must still coerce cleanly, not error."""
    attrs = map_token_fields({"llm.token_count.total": 12})
    assert attrs == {"llm.token_count.total": 12}


def test_non_numeric_token_value_raises_malformed_record_error():
    with pytest.raises(MalformedRecordError):
        map_token_fields({"llm.token_count.prompt": "not-a-number"})


def test_record_to_span_sets_token_attributes_as_real_ints():
    record = make_record(
        custom_dimensions={
            "llm.token_count.prompt": "5",
            "llm.token_count.completion": "7",
            "llm.token_count.total": "12",
        }
    )
    span = record_to_span(record)

    assert span.attributes["llm.token_count.prompt"] == 5
    assert span.attributes["llm.token_count.completion"] == 7
    assert span.attributes["llm.token_count.total"] == 12
    # Explicitly assert these did NOT land as quoted strings - the bug this
    # rule exists to prevent.
    assert isinstance(span.attributes["llm.token_count.prompt"], int)
    assert not isinstance(span.attributes["llm.token_count.prompt"], bool)
