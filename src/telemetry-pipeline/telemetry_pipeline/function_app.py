"""Azure Functions (Python v2 programming model) Event Hub trigger wiring.

Deploys as the `telemetry-pipeline` Function App's one function, consuming
batches of Event Hub messages (Log Analytics Data Export rows) and handing
them to `batch.transform_batch()` for the actual field-mapping work.

This module is the ONLY one in this package that imports `azure.functions`
- `mapping.py`/`batch.py`/`exporter.py` do not, so the transform logic they
implement is importable and unit-testable without the Azure Functions
runtime or the `azure-functions` package installed. Entrypoint tests use
the real decorator metadata and injected in-memory exporters, without a
Functions host or network calls.

Connection binding: per `infra/modules/function-app.bicep`'s header
comments, the Event Hub trigger uses an IDENTITY-BASED binding via app
settings named `<prefix>__fullyQualifiedNamespace`/`<prefix>__credential`
(prefix defaults to `EventHubConnection`, see
`eventHubConnectionSettingPrefix` in that Bicep module) - NOT a
connection-string binding. The `connection=` value below must match that
app-setting prefix.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import List

import azure.functions as func
from opentelemetry.sdk.trace.export import SpanExportResult

from .batch import transform_batch
from .exporter import build_arize_otlp_exporter, get_default_exporter

logger = logging.getLogger(__name__)

# Must match `eventHubConnectionSettingPrefix` in
# infra/modules/function-app.bicep (default "EventHubConnection").
EVENT_HUB_CONNECTION_SETTING_PREFIX = os.environ.get(
    "EVENT_HUB_CONNECTION_SETTING_PREFIX", "EventHubConnection"
)
EVENT_HUB_NAME = os.environ.get("EVENT_HUB_NAME", "telemetry")
EVENT_HUB_CONSUMER_GROUP = os.environ.get("EVENT_HUB_CONSUMER_GROUP", "$Default")

app = func.FunctionApp()


def _resolve_exporter():
    """Build the live Arize exporter when configured, else the console default.

    Live export is opt-in via `ARIZE_OTLP_ENDPOINT` (see `exporter.py`) -
    unset in this sandbox and in any environment that hasn't been given
    real Arize credentials, so the Function remains safely deployable
    (and its output observable via Function logs) without one.
    """
    if os.environ.get("ARIZE_OTLP_ENDPOINT"):
        return build_arize_otlp_exporter()
    return get_default_exporter()


@app.function_name(name="TelemetryTransform")
@app.retry(
    strategy="exponential_backoff",
    max_retry_count="3",
    minimum_interval="00:00:05",
    maximum_interval="00:01:00",
)
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=EVENT_HUB_NAME,
    connection=f"{EVENT_HUB_CONNECTION_SETTING_PREFIX}",
    consumer_group=EVENT_HUB_CONSUMER_GROUP,
    cardinality="many",
)
def telemetry_transform(events: List[func.EventHubEvent]) -> None:
    """Event Hub trigger entrypoint: transform one batch, export the spans.

    Export failure raises so the host retries the whole batch. Checkpoints
    are deferred during retries, but can advance after retry exhaustion;
    operator recovery/replay is still required for persistent failures.
    """
    exporter = _resolve_exporter()
    try:
        result = transform_batch(events, exporter)
        mapped = len(result.spans)
        succeeded = result.export_result == SpanExportResult.SUCCESS
        failed = result.export_result == SpanExportResult.FAILURE
        status = "success" if succeeded else "failure" if failed else "no_export"
        log = logger.error if failed else logger.info
        log(
            "telemetry_transform: records=%d mapped=%d exported=%d failed=%d "
            "skipped=%d export_status=%s",
            result.total_records,
            mapped,
            mapped if succeeded else 0,
            mapped if failed else 0,
            len(result.skipped),
            status,
        )
        if failed:
            raise RuntimeError(f"Span export failed for {mapped} mapped span(s)")
    finally:
        primary_failure = sys.exc_info()[0] is not None
        try:
            exporter.shutdown()
        except Exception as exc:
            if not primary_failure:
                raise
            logger.error(
                "telemetry_transform: exporter shutdown failed during invocation "
                "failure (%s)",
                type(exc).__name__,
            )
