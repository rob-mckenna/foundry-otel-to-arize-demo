"""Correlation ID propagation + retry-with-backoff span assertions (#31).

Covers the remaining acceptance criteria from issue #31:
  - correlation ID propagates across every span in a request, including
    across retries
Spans/OpenInference-attribute assertions live in test_agent_spans.py.
"""
from __future__ import annotations

from opentelemetry.trace import StatusCode

from prompt_agent.agent import PromptAgent
from prompt_agent.config import load_config
from prompt_agent.model_client import ModelResponse, TransientModelError
from prompt_agent.retry import RetryConfig

from .conftest import find_span, find_spans


class _FixedModelClient:
    def complete(self, prompt: str) -> ModelResponse:
        return ModelResponse(text="ok", model_name="test-model", prompt_tokens=1, completion_tokens=1)


class _FlakyModelClient:
    """Fails `fail_first_n_calls` times with TransientModelError, then succeeds."""

    def __init__(self, fail_first_n_calls: int):
        self._fail_first_n_calls = fail_first_n_calls
        self.calls = 0

    def complete(self, prompt: str) -> ModelResponse:
        self.calls += 1
        if self.calls <= self._fail_first_n_calls:
            raise TransientModelError(f"synthetic transient failure #{self.calls}")
        return ModelResponse(text="recovered", model_name="test-model", prompt_tokens=2, completion_tokens=3)


def _fast_retry_config(max_attempts: int) -> RetryConfig:
    # Zero backoff so tests run instantly, not hostage to real sleeps.
    return RetryConfig(max_attempts=max_attempts, initial_backoff_seconds=0.0, backoff_multiplier=1.0)


def test_correlation_id_propagates_to_every_span_in_one_request(span_exporter):
    agent = PromptAgent(config=load_config(), model_client=_FixedModelClient())
    result = agent.invoke("What is my synthetic deductible?", plan_name="Acme Synthetic PPO")

    spans = span_exporter.get_finished_spans()
    invoke_span = find_span(spans, "prompt_agent.invoke")
    tool_span = find_span(spans, "tool.lookup_plan_details")
    llm_span = find_span(spans, "llm.chat_completion")
    attempt_span = find_span(spans, "llm.chat_completion.attempt")

    for span in (invoke_span, tool_span, llm_span, attempt_span):
        assert span.attributes["correlation.id"] == result.correlation_id


def test_correlation_id_is_generated_when_not_supplied(span_exporter):
    agent = PromptAgent(config=load_config(), model_client=_FixedModelClient())
    result_a = agent.invoke("Question A")
    result_b = agent.invoke("Question B")

    assert result_a.correlation_id
    assert result_b.correlation_id
    assert result_a.correlation_id != result_b.correlation_id


def test_correlation_id_is_honored_when_supplied(span_exporter):
    agent = PromptAgent(config=load_config(), model_client=_FixedModelClient())
    result = agent.invoke("Question", correlation_id="caller-supplied-id-123")

    assert result.correlation_id == "caller-supplied-id-123"
    spans = span_exporter.get_finished_spans()
    invoke_span = find_span(spans, "prompt_agent.invoke")
    assert invoke_span.attributes["correlation.id"] == "caller-supplied-id-123"


def test_correlation_id_propagates_across_a_recovered_retry(span_exporter):
    agent = PromptAgent(config=load_config(), model_client=_FlakyModelClient(fail_first_n_calls=2))
    agent._retry_config = _fast_retry_config(max_attempts=3)

    result = agent.invoke("What is my synthetic copay?", plan_name="Acme Synthetic PPO")

    spans = span_exporter.get_finished_spans()
    attempt_spans = find_spans(spans, "llm.chat_completion.attempt")
    assert len(attempt_spans) == 3
    assert [s.attributes["retry.attempt"] for s in attempt_spans] == [1, 2, 3]
    # Every attempt — including the two that failed — carries the same
    # correlation ID as the overall successful result.
    for span in attempt_spans:
        assert span.attributes["correlation.id"] == result.correlation_id
    assert [s.status.status_code for s in attempt_spans] == [
        StatusCode.ERROR,
        StatusCode.ERROR,
        StatusCode.OK,
    ]

    llm_span = find_span(spans, "llm.chat_completion")
    invoke_span = find_span(spans, "prompt_agent.invoke")
    assert llm_span.status.status_code == StatusCode.OK
    assert invoke_span.status.status_code == StatusCode.OK
    assert llm_span.attributes["correlation.id"] == result.correlation_id
    assert invoke_span.attributes["correlation.id"] == result.correlation_id


def test_retries_exhausted_raises_and_marks_every_span_error(span_exporter):
    agent = PromptAgent(config=load_config(), model_client=_FlakyModelClient(fail_first_n_calls=99))
    agent._retry_config = _fast_retry_config(max_attempts=2)

    try:
        agent.invoke("What is my synthetic deductible?", plan_name="Acme Synthetic PPO")
        raised = False
    except TransientModelError:
        raised = True

    assert raised, "expected TransientModelError to propagate once retries are exhausted"

    spans = span_exporter.get_finished_spans()
    attempt_spans = find_spans(spans, "llm.chat_completion.attempt")
    assert len(attempt_spans) == 2
    assert all(s.status.status_code == StatusCode.ERROR for s in attempt_spans)
    assert [s.attributes["retry.will_retry"] for s in attempt_spans] == [True, False]

    llm_span = find_span(spans, "llm.chat_completion")
    invoke_span = find_span(spans, "prompt_agent.invoke")
    assert llm_span.status.status_code == StatusCode.ERROR
    assert invoke_span.status.status_code == StatusCode.ERROR

    # Every span (successful tool lookup included) still shares one
    # correlation ID even though the overall request ultimately failed.
    correlation_ids = {
        span.attributes["correlation.id"]
        for span in spans
        if span.name
        in (
            "prompt_agent.invoke",
            "tool.lookup_plan_details",
            "llm.chat_completion",
            "llm.chat_completion.attempt",
        )
    }
    assert len(correlation_ids) == 1
