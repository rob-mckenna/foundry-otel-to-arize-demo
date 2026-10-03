"""OpenTelemetry SDK bootstrap for the Foundry Prompt Agent.

This module is setup/plumbing only (#26) — it configures a `TracerProvider`
with resource attributes and an exporter pipeline, and exposes `get_tracer()`
for the rest of the application. Span creation around model/tool calls
happens in #27; OpenInference attribute population in #28.

Exporter selection:
  - If `APPLICATIONINSIGHTS_CONNECTION_STRING` is set, spans export to
    Application Insights via the Azure Monitor OpenTelemetry exporter
    (`azure-monitor-opentelemetry-exporter`, the `[azure]` extra in
    pyproject.toml). This is the env var name Infrastructure's App Insights
    provisioning (#16) is expected to supply.
  - Otherwise, spans export to the console. This keeps the agent runnable
    end-to-end (and testable in #31 via an in-memory exporter) without any
    live Azure resources — important for this sandbox, which has no
    provisioned Application Insights instance yet.
"""
from __future__ import annotations

import atexit
import sys
import threading

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)

from prompt_agent.config import PromptAgentConfig, load_config

# Standard Azure Monitor env var name for the Application Insights
# connection string. Documented for Infrastructure in the Milestone 1
# decision log — this is the exact name the exporter below reads.
APPLICATION_INSIGHTS_CONNECTION_STRING_ENV_VAR = "APPLICATIONINSIGHTS_CONNECTION_STRING"

_lock = threading.Lock()
_configured = False


def _build_resource(config: PromptAgentConfig) -> Resource:
    return Resource.create(
        {
            "service.name": config.service_name,
            "service.version": config.service_version,
            "deployment.environment": config.deployment_environment,
        }
    )


def _build_exporter() -> SpanExporter:
    """Build the span exporter, preferring Azure Monitor when configured.

    Falls back to a console exporter when no Application Insights
    connection string is present (e.g. local dev or this sandbox, which has
    no live Azure resources provisioned) so the SDK is still exercisable
    and testable end-to-end.
    """
    import os

    connection_string = os.environ.get(APPLICATION_INSIGHTS_CONNECTION_STRING_ENV_VAR)
    if connection_string:
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        except ImportError as exc:  # pragma: no cover - exercised only when extra isn't installed
            raise RuntimeError(
                f"{APPLICATION_INSIGHTS_CONNECTION_STRING_ENV_VAR} is set but the "
                "'azure-monitor-opentelemetry-exporter' package is not installed. "
                "Install the optional extra: pip install -e \".[azure]\"."
            ) from exc
        return AzureMonitorTraceExporter(connection_string=connection_string)

    # No Application Insights connection string available — fall back to a
    # console exporter so the agent still runs and emits visible span output.
    return ConsoleSpanExporter(out=sys.stderr)


def configure_tracing(config: PromptAgentConfig | None = None) -> TracerProvider:
    """Initialize the global `TracerProvider` exactly once per process.

    Safe to call multiple times (idempotent) — subsequent calls return the
    already-configured global provider rather than re-registering a second
    one or duplicating exporters/processors.
    """
    global _configured
    with _lock:
        if _configured:
            return trace.get_tracer_provider()  # type: ignore[return-value]

        config = config or load_config()
        provider = TracerProvider(resource=_build_resource(config))
        provider.add_span_processor(BatchSpanProcessor(_build_exporter()))
        trace.set_tracer_provider(provider)

        # Ensure buffered spans are flushed (not dropped) on normal process
        # exit — required by #26's acceptance criteria.
        atexit.register(shutdown_tracing)

        _configured = True
        return provider


def shutdown_tracing() -> None:
    """Flush and shut down the tracer provider so no spans are dropped.

    Safe to call more than once (OpenTelemetry's `shutdown()` is itself
    idempotent-safe against being called after shutdown).
    """
    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if callable(force_flush):
        force_flush()
    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        shutdown()


def get_tracer(name: str = "prompt_agent") -> trace.Tracer:
    """Return a tracer, configuring the SDK first if it hasn't been yet."""
    configure_tracing()
    return trace.get_tracer(name)
