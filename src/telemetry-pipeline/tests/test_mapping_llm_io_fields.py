"""LLM I/O field-group tests (#91): string passthrough, no coercion."""
from __future__ import annotations

from telemetry_pipeline.mapping import map_llm_io_fields, record_to_span

from .conftest import make_record


def test_llm_io_fields_pass_through_unchanged():
    custom_dimensions = {
        "input.value": "What is my synthetic deductible?",
        "output.value": "Your synthetic deductible is $500.",
        "llm.model_name": "gpt-4o-mini-synthetic",
    }
    attrs = map_llm_io_fields(custom_dimensions)
    assert attrs == custom_dimensions


def test_llm_io_fields_absent_are_omitted():
    assert map_llm_io_fields({}) == {}
    assert map_llm_io_fields({"input.value": "only input"}) == {"input.value": "only input"}


def test_llm_io_fields_not_truncated_further_by_the_transform():
    """The transform must not introduce additional truncation beyond
    whatever already happened upstream at the App Insights hop (#91 §2)."""
    long_value = "x" * 10_000
    attrs = map_llm_io_fields({"output.value": long_value})
    assert attrs["output.value"] == long_value
    assert len(attrs["output.value"]) == 10_000


def test_record_to_span_sets_llm_io_attributes():
    record = make_record(
        custom_dimensions={
            "input.value": "input text",
            "output.value": "output text",
            "llm.model_name": "test-model",
        }
    )
    span = record_to_span(record)
    assert span.attributes["input.value"] == "input text"
    assert span.attributes["output.value"] == "output text"
    assert span.attributes["llm.model_name"] == "test-model"
