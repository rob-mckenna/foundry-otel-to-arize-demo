"""Core prompt/response flow for the Foundry Prompt Agent.

This module implements the primary request/response pipeline described in
#25: accept a user prompt, optionally resolve it via a small lookup "tool"
call, invoke the model, and return a response.

#27 wraps every externally-visible call (the tool lookup and the model
call) in its own OpenTelemetry span, nested under a top-level
`prompt_agent.invoke` span so parent-child relationships are correct for a
full request. #28 adds OpenInference semantic-convention attributes
(prompt/completion text, token counts, `openinference.span.kind`) on top of
these same spans, using the `openinference-semantic-conventions` package
pinned to the 0.1.x spec (see pyproject.toml) so attribute key names track
the upstream spec rather than being hand-typed string literals. #29 adds a
correlation ID (accepted from the caller, or generated if absent) that is
attached as a `correlation.id` attribute on every span in the request's
tree, giving a trace-system-agnostic join key alongside OTel's own
`trace_id` (see `correlation.py`). #30 wraps the model call with bounded
exponential-backoff retry logic (`retry.py`) — every retry attempt is its
own child span, still carrying the same `correlation.id`, so a retried
request remains fully traceable back to the original request even across
multiple attempts.
"""
from __future__ import annotations

from dataclasses import dataclass

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry.trace import SpanKind, Status, StatusCode

from prompt_agent.config import PromptAgentConfig, load_config
from prompt_agent.correlation import CORRELATION_ID_ATTRIBUTE, generate_correlation_id
from prompt_agent.model_client import ModelClient, ModelResponse, StubFoundryModelClient
from prompt_agent.retry import RetryConfig, call_with_retry
from prompt_agent.telemetry import get_tracer

_tracer = get_tracer("prompt_agent.agent")

# Synthetic plan directory used by the `lookup_plan_details` tool call below.
# Entirely fabricated — see synthetic/README.md.
_SYNTHETIC_PLAN_DIRECTORY: dict[str, str] = {
    "acme synthetic ppo": "Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible.",
    "acme synthetic hmo": "Acme Synthetic HMO — requires in-network PCP referral, $15 PCP copay, no out-of-network coverage.",
}


def lookup_plan_details(plan_name: str, correlation_id: str) -> str:
    """Synthetic "tool" call: looks up fabricated plan details by name.

    Wrapped in its own span (`tool.lookup_plan_details`) so every tool
    invocation is independently traceable, timed, and status-tagged — not
    just the model call. `start_as_current_span` is used as a context
    manager, so if this function ever raises, OpenTelemetry's default
    behavior (`record_exception=True`, `set_status_on_exception=True`)
    records the exception as a span event and marks the span `ERROR`
    automatically before the exception propagates.

    `correlation_id` is the caller's request correlation ID (see #29 /
    `correlation.py`), attached to this span so the tool call remains
    joinable to its parent request even outside of OTel's own trace_id.
    """
    with _tracer.start_as_current_span("tool.lookup_plan_details", kind=SpanKind.CLIENT) as span:
        span.set_attribute(
            SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.TOOL.value
        )
        span.set_attribute(CORRELATION_ID_ATTRIBUTE, correlation_id)
        span.set_attribute(SpanAttributes.INPUT_VALUE, plan_name)
        result = _SYNTHETIC_PLAN_DIRECTORY.get(
            plan_name.strip().lower(),
            f"No synthetic plan details on file for '{plan_name}'.",
        )
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, result)
        span.set_status(Status(StatusCode.OK))
        return result


@dataclass(frozen=True)
class AgentResult:
    """Full result of one `PromptAgent.invoke()` call."""

    prompt: str
    response: ModelResponse
    tool_output: str | None
    correlation_id: str


class PromptAgent:
    """Primary request/response entry point for the Foundry Prompt Agent."""

    def __init__(self, config: PromptAgentConfig | None = None, model_client: ModelClient | None = None) -> None:
        self._config = config or load_config()
        # Real-SDK wiring lives behind the ModelClient protocol — swap this
        # default for a real Foundry-backed client once credentials exist.
        self._model_client = model_client or StubFoundryModelClient(self._config)
        self._retry_config = RetryConfig(
            max_attempts=self._config.retry_max_attempts,
            initial_backoff_seconds=self._config.retry_initial_backoff_seconds,
            backoff_multiplier=self._config.retry_backoff_multiplier,
        )

    def invoke(self, prompt: str, plan_name: str | None = None, correlation_id: str | None = None) -> AgentResult:
        """Run one request through the core prompt/response flow.

        Every externally-visible call in this method (the optional tool
        lookup, and the model call) executes inside its own child span of
        the top-level `prompt_agent.invoke` span, so a full request's span
        tree has correct parent-child nesting end-to-end — no call path
        here is left uninstrumented. The model call is further wrapped in
        bounded exponential-backoff retry logic (#30, `retry.py`) — every
        attempt is its own child span (`llm.chat_completion.attempt`), and a
        retry that eventually succeeds still reports this call as an
        overall success.

        `correlation_id`: if the caller already has a request/correlation ID
        (e.g. from an upstream API gateway header), pass it here so it is
        preserved rather than regenerated. If omitted, a new one is
        generated for this request and attached to every span in its tree,
        plus returned on `AgentResult` so the caller can log/return it too.
        """
        correlation_id = correlation_id or generate_correlation_id()
        with _tracer.start_as_current_span("prompt_agent.invoke", kind=SpanKind.INTERNAL) as invoke_span:
            invoke_span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.CHAIN.value
            )
            invoke_span.set_attribute(CORRELATION_ID_ATTRIBUTE, correlation_id)
            invoke_span.set_attribute(SpanAttributes.INPUT_VALUE, prompt)
            tool_output: str | None = None
            effective_prompt = prompt
            if plan_name:
                tool_output = lookup_plan_details(plan_name, correlation_id)
                effective_prompt = f"{prompt}\n\n[Synthetic plan lookup result: {tool_output}]"

            with _tracer.start_as_current_span("llm.chat_completion", kind=SpanKind.CLIENT) as model_span:
                model_span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.LLM.value
                )
                model_span.set_attribute(CORRELATION_ID_ATTRIBUTE, correlation_id)
                model_span.set_attribute(SpanAttributes.INPUT_VALUE, effective_prompt)
                response = call_with_retry(
                    lambda: self._model_client.complete(effective_prompt),
                    tracer=_tracer,
                    span_name="llm.chat_completion",
                    correlation_id=correlation_id,
                    config=self._retry_config,
                )
                model_span.set_attribute(SpanAttributes.OUTPUT_VALUE, response.text)
                model_span.set_attribute(SpanAttributes.LLM_MODEL_NAME, response.model_name)
                model_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, response.prompt_tokens)
                model_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, response.completion_tokens)
                model_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, response.total_tokens)
                model_span.set_status(Status(StatusCode.OK))

            invoke_span.set_attribute(SpanAttributes.OUTPUT_VALUE, response.text)
            invoke_span.set_status(Status(StatusCode.OK))
            return AgentResult(
                prompt=prompt,
                response=response,
                tool_output=tool_output,
                correlation_id=correlation_id,
            )
