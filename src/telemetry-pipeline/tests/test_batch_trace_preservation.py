"""Synthetic 3-span batch trace-preservation test.

Mirrors the shape used in
`docs/telemetry/trace-correlation-preservation.md` §5's validation plan
(`prompt_agent.invoke` -> `tool.lookup_plan_details` + `llm.chat_completion`,
both children) and `src/prompt-agent/tests/test_agent_spans.py`'s
in-memory span-tree assertions. Proves the Function transform preserves
one shared `trace_id` across all 3 spans with correct parent linkage -
entirely via in-memory/mocked Event Hub message objects, no live Azure
needed.
"""
from __future__ import annotations

import json

from telemetry_pipeline.batch import transform_batch
from telemetry_pipeline.mapping import record_to_span

from .conftest import make_record

_SHARED_TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
_INVOKE_SPAN_ID = "b7ad6b7169203331"
_TOOL_SPAN_ID = "c8be7c8270314442"
_LLM_SPAN_ID = "d9cf8d9381425553"


def _synthetic_batch() -> list[dict]:
    """Build the synthetic 3-span tree: one root CHAIN span, two CLIENT
    children (TOOL + LLM), all sharing one trace_id."""
    invoke_record = make_record(
        operation_Id=_SHARED_TRACE_ID,
        operation_ParentId="",
        id=_INVOKE_SPAN_ID,
        Name="prompt_agent.invoke",
        Success=True,
        custom_dimensions={
            "openinference.span.kind": "CHAIN",
            "correlation.id": "synthetic-correlation-abc",
            "input.value": "What is my synthetic deductible?",
            "output.value": "Your synthetic deductible is $500.",
        },
    )
    tool_record = make_record(
        operation_Id=_SHARED_TRACE_ID,
        operation_ParentId=_INVOKE_SPAN_ID,
        id=_TOOL_SPAN_ID,
        Name="tool.lookup_plan_details",
        Success=True,
        custom_dimensions={
            "openinference.span.kind": "TOOL",
            "correlation.id": "synthetic-correlation-abc",
            "input.value": "Acme Synthetic PPO",
            "output.value": "deductible: $500",
        },
    )
    llm_record = make_record(
        operation_Id=_SHARED_TRACE_ID,
        operation_ParentId=_INVOKE_SPAN_ID,
        id=_LLM_SPAN_ID,
        Name="llm.chat_completion",
        Success=True,
        custom_dimensions={
            "openinference.span.kind": "LLM",
            "correlation.id": "synthetic-correlation-abc",
            "input.value": "What is my synthetic deductible?",
            "output.value": "Your synthetic deductible is $500.",
            "llm.model_name": "test-model",
            "llm.token_count.prompt": "5",
            "llm.token_count.completion": "7",
            "llm.token_count.total": "12",
        },
    )
    return [invoke_record, tool_record, llm_record]


def test_synthetic_3_span_batch_shares_one_trace_id_directly():
    """Direct record_to_span() check, no batch/Event Hub plumbing involved."""
    invoke_record, tool_record, llm_record = _synthetic_batch()

    invoke_span = record_to_span(invoke_record)
    tool_span = record_to_span(tool_record)
    llm_span = record_to_span(llm_record)

    assert invoke_span.context.trace_id == tool_span.context.trace_id == llm_span.context.trace_id

    assert invoke_span.parent is None  # root span
    assert tool_span.parent is not None
    assert tool_span.parent.span_id == invoke_span.context.span_id
    assert llm_span.parent is not None
    assert llm_span.parent.span_id == invoke_span.context.span_id

    # Correlation ID (app-level join key, independent of trace_id) is also
    # identical across every span in the tree.
    correlation_ids = {
        span.attributes["correlation.id"] for span in (invoke_span, tool_span, llm_span)
    }
    assert correlation_ids == {"synthetic-correlation-abc"}


def test_synthetic_3_span_batch_preserved_through_event_hub_message_batch(stub_exporter):
    """End-to-end (within this package): 3 records delivered as one Event
    Hub message batch (the Log Analytics `{"records": [...]}` envelope),
    transformed and exported together, with trace/parent linkage intact."""

    class _FakeEventHubEvent:
        def __init__(self, body: bytes):
            self._body = body

        def get_body(self) -> bytes:
            return self._body

    payload = {"records": _synthetic_batch()}
    message = _FakeEventHubEvent(json.dumps(payload).encode("utf-8"))

    result = transform_batch([message], stub_exporter)

    assert len(result.spans) == 3
    assert result.skipped == []
    # Whole-batch export: one export() call carries all 3 spans together.
    assert len(stub_exporter.export_calls) == 1
    assert len(stub_exporter.export_calls[0]) == 3

    spans_by_name = {span.name: span for span in result.spans}
    invoke_span = spans_by_name["prompt_agent.invoke"]
    tool_span = spans_by_name["tool.lookup_plan_details"]
    llm_span = spans_by_name["llm.chat_completion"]

    trace_ids = {invoke_span.context.trace_id, tool_span.context.trace_id, llm_span.context.trace_id}
    assert len(trace_ids) == 1, "all 3 spans must share exactly one trace_id"

    assert invoke_span.parent is None
    assert tool_span.parent.span_id == invoke_span.context.span_id
    assert llm_span.parent.span_id == invoke_span.context.span_id

    assert llm_span.attributes["llm.token_count.total"] == 12
    assert isinstance(llm_span.attributes["llm.token_count.total"], int)
