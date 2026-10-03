"""Span + OpenInference attribute assertions for PromptAgent.invoke() (#31).

Covers the acceptance criteria from issue #31:
  - spans are created with expected attributes (names, kind, parent linkage)
  - token counts are captured
  - OpenInference attributes are present
Correlation ID propagation (including across retries) is covered in
test_correlation_and_retry.py.
"""
from __future__ import annotations

from opentelemetry.trace import SpanKind, StatusCode

from prompt_agent.agent import PromptAgent
from prompt_agent.config import load_config
from prompt_agent.model_client import ModelResponse

from .conftest import find_span, find_spans


class _FixedModelClient:
    """Deterministic test double standing in for the real/stub model client."""

    def __init__(self, text: str = "synthetic test response", prompt_tokens: int = 5, completion_tokens: int = 7):
        self.calls: list[str] = []
        self._text = text
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens

    def complete(self, prompt: str) -> ModelResponse:
        self.calls.append(prompt)
        return ModelResponse(
            text=self._text,
            model_name="test-model",
            prompt_tokens=self._prompt_tokens,
            completion_tokens=self._completion_tokens,
        )


def _invoke(plan_name: str | None = "Acme Synthetic PPO", correlation_id: str | None = None):
    agent = PromptAgent(config=load_config(), model_client=_FixedModelClient())
    result = agent.invoke("What is my synthetic deductible?", plan_name=plan_name, correlation_id=correlation_id)
    return agent, result


def test_invoke_creates_expected_span_tree(span_exporter):
    _invoke()
    spans = span_exporter.get_finished_spans()

    invoke_span = find_span(spans, "prompt_agent.invoke")
    tool_span = find_span(spans, "tool.lookup_plan_details")
    llm_span = find_span(spans, "llm.chat_completion")

    assert invoke_span.kind == SpanKind.INTERNAL
    assert tool_span.kind == SpanKind.CLIENT
    assert llm_span.kind == SpanKind.CLIENT

    # Parent-child linkage: both tool + llm spans are direct children of
    # prompt_agent.invoke, and all three share one trace.
    assert tool_span.parent.span_id == invoke_span.context.span_id
    assert llm_span.parent.span_id == invoke_span.context.span_id
    assert tool_span.context.trace_id == invoke_span.context.trace_id
    assert llm_span.context.trace_id == invoke_span.context.trace_id

    assert invoke_span.status.status_code == StatusCode.OK
    assert tool_span.status.status_code == StatusCode.OK
    assert llm_span.status.status_code == StatusCode.OK


def test_invoke_without_plan_name_skips_tool_span(span_exporter):
    _invoke(plan_name=None)
    spans = span_exporter.get_finished_spans()

    assert find_spans(spans, "tool.lookup_plan_details") == []
    # The model call still happens even with no tool lookup.
    find_span(spans, "llm.chat_completion")


def test_llm_span_has_openinference_attributes_and_token_counts(span_exporter):
    _invoke()
    spans = span_exporter.get_finished_spans()
    llm_span = find_span(spans, "llm.chat_completion")

    assert llm_span.attributes["openinference.span.kind"] == "LLM"
    assert llm_span.attributes["input.value"].startswith("What is my synthetic deductible?")
    assert llm_span.attributes["output.value"] == "synthetic test response"
    assert llm_span.attributes["llm.model_name"] == "test-model"
    assert llm_span.attributes["llm.token_count.prompt"] == 5
    assert llm_span.attributes["llm.token_count.completion"] == 7
    assert llm_span.attributes["llm.token_count.total"] == 12


def test_tool_span_has_openinference_attributes(span_exporter):
    _invoke()
    spans = span_exporter.get_finished_spans()
    tool_span = find_span(spans, "tool.lookup_plan_details")

    assert tool_span.attributes["openinference.span.kind"] == "TOOL"
    assert tool_span.attributes["input.value"] == "Acme Synthetic PPO"
    assert "deductible" in tool_span.attributes["output.value"].lower()


def test_invoke_span_has_openinference_chain_attributes(span_exporter):
    _, result = _invoke()
    spans = span_exporter.get_finished_spans()
    invoke_span = find_span(spans, "prompt_agent.invoke")

    assert invoke_span.attributes["openinference.span.kind"] == "CHAIN"
    assert invoke_span.attributes["input.value"] == "What is my synthetic deductible?"
    assert invoke_span.attributes["output.value"] == result.response.text


def test_invoke_returns_token_counts_matching_response(span_exporter):
    _, result = _invoke()
    assert result.response.prompt_tokens == 5
    assert result.response.completion_tokens == 7
    assert result.response.total_tokens == 12
