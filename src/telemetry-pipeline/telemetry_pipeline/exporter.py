"""Exporter factory / dependency-injection seam for the telemetry transform.

Mirrors `src/prompt-agent/prompt_agent/telemetry.py`'s `_build_exporter()`
pattern: the live network export to a real OTLP endpoint (Arize) is kept
behind an optional import and an explicit opt-in env var, so this package
is fully unit-testable - via `get_default_exporter()` or any test-double
`SpanExporter` passed in directly - without live Azure/Arize credentials or
network access in this sandbox.

**Out of scope here (deliberately):** actually exercising a live OTLP
network call to Arize. `build_arize_otlp_exporter()` below constructs a
real exporter object when asked, but nothing in this repo's test suite
calls it - see `docs/telemetry/trace-correlation-preservation.md` §5/§6 for
why that end-to-end round trip remains unvalidated.
"""
from __future__ import annotations

import logging
import os
from typing import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SpanExporter,
    SpanExportResult,
)

logger = logging.getLogger(__name__)

# Env var names the Function App would read in a live deployment. Mirrors
# the naming style of `APPLICATION_INSIGHTS_CONNECTION_STRING_ENV_VAR` in
# `src/prompt-agent/prompt_agent/telemetry.py`.
ARIZE_OTLP_ENDPOINT_ENV_VAR = "ARIZE_OTLP_ENDPOINT"
ARIZE_SPACE_ID_ENV_VAR = "ARIZE_SPACE_ID"
ARIZE_API_KEY_ENV_VAR = "ARIZE_API_KEY"


class _CountingSpanExporter(SpanExporter):
    """Wraps a `SpanExporter`, tallying exported vs. failed/dropped spans.

    Same pattern as `prompt_agent.telemetry._CountingSpanExporter` (#130,
    PR #134) - reused here for naming/observability consistency across the
    two packages rather than inventing a second convention.
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
                "telemetry_pipeline.exporter: failed to export %d span(s); "
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


def get_default_exporter() -> SpanExporter:
    """Return the default exporter used when the Function isn't given one.

    Deliberately a `ConsoleSpanExporter`, never a live network exporter -
    this keeps `function_app.py`'s wiring safe to import/run in any
    sandbox (including this one, which has no live Arize credentials) and
    matches `prompt_agent.telemetry._build_exporter()`'s console fallback
    for the same reason.
    """
    return _CountingSpanExporter(ConsoleSpanExporter())


def build_arize_otlp_exporter(
    endpoint: str | None = None,
    space_id: str | None = None,
    api_key: str | None = None,
) -> SpanExporter:
    """Construct a real OTLP-over-HTTP exporter targeting Arize.

    Reads `ARIZE_OTLP_ENDPOINT`/`ARIZE_SPACE_ID`/`ARIZE_API_KEY` when the
    corresponding argument isn't supplied. Requires the optional `otlp`
    extra (`opentelemetry-exporter-otlp-proto-http`) to be installed - not
    a core dependency, so the base package install stays credential- and
    network-dependency-free.

    **Not exercised by this repo's test suite or by `function_app.py`'s
    default wiring** - constructing this exporter requires real Arize
    credentials this sandbox does not have. It exists so a future live
    deployment has a ready-made factory function to call, per this
    package's dependency-injection design.
    """
    endpoint = endpoint or os.environ.get(ARIZE_OTLP_ENDPOINT_ENV_VAR)
    space_id = space_id or os.environ.get(ARIZE_SPACE_ID_ENV_VAR)
    api_key = api_key or os.environ.get(ARIZE_API_KEY_ENV_VAR)
    if not endpoint:
        raise RuntimeError(
            f"{ARIZE_OTLP_ENDPOINT_ENV_VAR} is not set and no endpoint was supplied; "
            "cannot build a live Arize OTLP exporter."
        )
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
    except ImportError as exc:  # pragma: no cover - exercised only when extra isn't installed
        raise RuntimeError(
            "ARIZE_OTLP_ENDPOINT is set but the "
            "'opentelemetry-exporter-otlp-proto-http' package is not installed. "
            "Install the optional extra: pip install -e \".[otlp]\"."
        ) from exc

    headers = {}
    if space_id:
        headers["space_id"] = space_id
    if api_key:
        headers["api_key"] = api_key
    return _CountingSpanExporter(OTLPSpanExporter(endpoint=endpoint, headers=headers or None))
