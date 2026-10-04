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

Export-health observability (#130):
  - Every configured exporter is wrapped in `_CountingSpanExporter`, which
    tallies how many spans were successfully exported vs. failed/dropped
    and logs a warning (logger name `prompt_agent.telemetry`) the moment an
    `export()` call reports `SpanExportResult.FAILURE`. This makes export
    health observable from logs/metrics alone, without needing to query
    Application Insights or Arize after the fact.
  - `shutdown_tracing()` now inspects `force_flush()`'s boolean return value
    instead of discarding it. A `False` result (flush did not complete
    within its timeout — some buffered spans may not have made it out
    before shutdown) is logged as a warning, and the final export
    success/failure tally is logged at shutdown time.
"""
from __future__ import annotations

import atexit
import logging
import sys
import threading
from typing import Sequence

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
    SpanExportResult,
)

from prompt_agent.config import PromptAgentConfig, load_config

# Standard Azure Monitor env var name for the Application Insights
# connection string. Documented for Infrastructure in the Milestone 1
# decision log — this is the exact name the exporter below reads.
APPLICATION_INSIGHTS_CONNECTION_STRING_ENV_VAR = "APPLICATIONINSIGHTS_CONNECTION_STRING"

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_configured = False
# Populated by `configure_tracing()`; used by `shutdown_tracing()` to log a
# final export success/failure tally. `None` until tracing is configured.
_span_exporter: "_CountingSpanExporter | None" = None


class _CountingSpanExporter(SpanExporter):
    """Wraps a `SpanExporter`, counting exported vs. failed/dropped spans.

    This is the lightweight, infra-free counter requested in #130: it makes
    span-export health observable via logging (or by reading
    `exported_count`/`failed_count` from a metrics scrape/test) without
    needing to query Application Insights or Arize. A failed `export()`
    call logs a warning immediately so export failures are visible as soon
    as they happen, not only at shutdown.
    """

    def __init__(self, wrapped: SpanExporter) -> None:
        self._wrapped = wrapped
        self.exported_count = 0
        self.failed_count = 0

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        result = self._wrapped.export(spans)
        span_count = len(spans)
        if result == SpanExportResult.SUCCESS:
            self.exported_count += span_count
        else:
            self.failed_count += span_count
            logger.warning(
                "prompt_agent.telemetry: failed to export %d span(s); "
                "running totals: exported=%d failed=%d",
                span_count,
                self.exported_count,
                self.failed_count,
            )
        return result

    def shutdown(self) -> None:
        self._wrapped.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._wrapped.force_flush(timeout_millis)


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
    global _configured, _span_exporter
    with _lock:
        if _configured:
            return trace.get_tracer_provider()  # type: ignore[return-value]

        config = config or load_config()
        provider = TracerProvider(resource=_build_resource(config))
        counting_exporter = _CountingSpanExporter(_build_exporter())
        provider.add_span_processor(BatchSpanProcessor(counting_exporter))
        _span_exporter = counting_exporter
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

    #130: `force_flush()`'s boolean return value is now checked rather than
    discarded. It returns `False` when the flush did not complete within
    its timeout, meaning some buffered spans may still have been in flight
    (or dropped) at shutdown — that case is logged as a warning so a
    shutdown-time export failure/timeout produces a signal instead of
    disappearing silently. The running export success/failure tally from
    `_CountingSpanExporter` is also logged here as a final summary.
    """
    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if callable(force_flush):
        flushed = force_flush()
        if flushed is False:
            logger.warning(
                "prompt_agent.telemetry: force_flush() did not complete "
                "within its timeout during shutdown; some buffered spans "
                "may not have been exported."
            )
    if _span_exporter is not None:
        logger.info(
            "prompt_agent.telemetry: span export summary at shutdown - "
            "exported=%d failed=%d",
            _span_exporter.exported_count,
            _span_exporter.failed_count,
        )
    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        shutdown()


def get_tracer(name: str = "prompt_agent") -> trace.Tracer:
    """Return a tracer, configuring the SDK first if it hasn't been yet."""
    configure_tracing()
    return trace.get_tracer(name)
