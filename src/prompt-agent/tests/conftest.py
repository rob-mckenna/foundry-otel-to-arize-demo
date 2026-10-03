"""Shared pytest fixtures for the Foundry Prompt Agent test suite (#31).

Uses OpenTelemetry's `InMemorySpanExporter` so span assertions run entirely
in-process — no console/Azure Monitor export, no network, fully
deterministic. `prompt_agent.telemetry.configure_tracing()` is idempotent
and (via `prompt_agent/agent.py`'s module-level `get_tracer()` call) a real
`TracerProvider` already exists by the time tests run; rather than fighting
OpenTelemetry's "only one global TracerProvider per process" rule, this
fixture adds an *additional* `SimpleSpanProcessor(InMemorySpanExporter())`
onto whatever provider is already configured — so every span produced by
the existing module-level tracers also lands in `span_exporter`, fully
isolated from (and in addition to) the console exporter from #26.
"""
from __future__ import annotations

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from prompt_agent.telemetry import configure_tracing


@pytest.fixture(scope="session")
def span_exporter() -> InMemorySpanExporter:
    """Session-scoped in-memory span exporter attached to the real provider.

    Session-scoped (not per-test) because OpenTelemetry's `TracerProvider`
    only accepts new processors being added, never removed — a fresh
    processor per test would leak one processor per test for the life of
    the process. Tests instead rely on the `clear_spans` autouse fixture
    below to reset captured spans between tests.
    """
    provider = configure_tracing()
    exporter = InMemorySpanExporter()
    # add_span_processor() is safe to call on an already-in-use provider —
    # the processor list is read fresh every time a span is created/ended.
    provider.add_span_processor(SimpleSpanProcessor(exporter))  # type: ignore[attr-defined]
    return exporter


@pytest.fixture(autouse=True)
def _clear_spans(span_exporter: InMemorySpanExporter):
    """Ensure every test starts with a clean slate of captured spans."""
    span_exporter.clear()
    yield
    span_exporter.clear()


def find_span(spans, name: str):
    """Return the first captured span with the given name, or raise."""
    for span in spans:
        if span.name == name:
            return span
    raise AssertionError(f"No span named {name!r} found among: {[s.name for s in spans]}")


def find_spans(spans, name: str):
    """Return all captured spans with the given name, in capture order."""
    return [span for span in spans if span.name == name]
