"""Retry-with-backoff helper for externally-visible calls (#30).

Wraps a zero-argument callable in bounded exponential-backoff retry logic
where **every retry attempt is its own child span**, fully traceable back to
the original request/correlation ID — not just the final outcome. This is
deliberately generic (not hard-coded to the model call) so any future
externally-visible call (e.g. a real tool/API call) can reuse it.

Design:
  - Each attempt gets its own span (`{span_name}.attempt`), a child of
    whatever span is current when `call_with_retry` is invoked (in
    `agent.py`, that's `llm.chat_completion`) — so the full tree is
    `prompt_agent.invoke` -> `llm.chat_completion` -> `llm.chat_completion.attempt`
    (one per attempt), all sharing the same `correlation.id` and `trace_id`.
  - `retry.attempt` (1-indexed) and `retry.max_attempts` are attached to
    every attempt span so a trace viewer can tell which attempt is which and
    how many were configured.
  - A successful attempt sets that attempt's span `OK` and returns
    immediately — no further attempts are made, and the overall call is
    reported as a success (a recovered retry is still a success).
  - A failed attempt is caught *inside* this function (not left to escape
    the span's context manager) so a non-final attempt can retry instead of
    propagating — which means OpenTelemetry's default
    `record_exception`/`set_status_on_exception` behavior never fires for
    it (that only triggers when an exception escapes the `with` block).
    This module therefore explicitly calls `span.record_exception(...)`
    and `span.set_status(Status(StatusCode.ERROR, ...))` on **every**
    failed attempt, retried or not, so no attempt is ever left `UNSET` —
    every attempt's outcome is traceable, not just the final one. On the
    final attempt, after recording the failure, the exception is re-raised
    so it propagates up to (and marks `ERROR`) the enclosing spans —
    full traceability of a terminal failure, not just individual attempts.
  - Only exceptions in `config.retryable_exceptions` are retried; anything
    else fails immediately on the first attempt (no point retrying a
    non-transient error).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar

from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer

from prompt_agent.correlation import CORRELATION_ID_ATTRIBUTE
from prompt_agent.model_client import TransientModelError

T = TypeVar("T")

RETRY_ATTEMPT_ATTRIBUTE = "retry.attempt"
RETRY_MAX_ATTEMPTS_ATTRIBUTE = "retry.max_attempts"


@dataclass(frozen=True)
class RetryConfig:
    """Bounded exponential-backoff retry configuration.

    Sourced from `PromptAgentConfig` (env vars `RETRY_MAX_ATTEMPTS` /
    `RETRY_INITIAL_BACKOFF_SECONDS` / `RETRY_BACKOFF_MULTIPLIER`) in normal
    use — see `agent.py`.
    """

    max_attempts: int = 3
    initial_backoff_seconds: float = 0.1
    backoff_multiplier: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = field(default=(TransientModelError,))


def call_with_retry(
    func: Callable[[], T],
    *,
    tracer: Tracer,
    span_name: str,
    correlation_id: str,
    config: RetryConfig,
) -> T:
    """Call `func`, retrying on `config.retryable_exceptions` with backoff.

    Every attempt (including the first) runs inside its own
    `{span_name}.attempt` child span carrying `retry.attempt`,
    `retry.max_attempts`, and `correlation.id` attributes.
    """
    backoff_seconds = config.initial_backoff_seconds
    last_exception: Exception | None = None

    for attempt in range(1, config.max_attempts + 1):
        with tracer.start_as_current_span(f"{span_name}.attempt", kind=SpanKind.CLIENT) as span:
            span.set_attribute(CORRELATION_ID_ATTRIBUTE, correlation_id)
            span.set_attribute(RETRY_ATTEMPT_ATTRIBUTE, attempt)
            span.set_attribute(RETRY_MAX_ATTEMPTS_ATTRIBUTE, config.max_attempts)
            try:
                result = func()
            except config.retryable_exceptions as exc:  # noqa: PERF203 - clarity over micro-perf here
                last_exception = exc
                is_final_attempt = attempt >= config.max_attempts
                span.set_attribute("retry.will_retry", not is_final_attempt)
                # The exception is caught *inside* this `with` block (so a
                # non-final attempt can retry instead of propagating), which
                # means start_as_current_span's default
                # record_exception/set_status_on_exception behavior never
                # fires — that only triggers when an exception escapes the
                # context manager. So every failed attempt — retried or
                # not — must explicitly record the exception and mark
                # itself ERROR here; this is not optional/cosmetic, it's the
                # only thing that makes a retried-but-failed attempt
                # traceable at all.
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                if is_final_attempt:
                    raise
                time.sleep(backoff_seconds)
                backoff_seconds *= config.backoff_multiplier
                continue
            else:
                span.set_status(Status(StatusCode.OK))
                return result

    # Unreachable: the loop above always either returns or raises on the
    # final attempt. Kept only to satisfy static type-checkers.
    assert last_exception is not None  # noqa: S101
    raise last_exception
