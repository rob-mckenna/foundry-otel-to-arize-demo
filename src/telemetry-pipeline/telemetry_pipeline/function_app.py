"""Azure Functions (Python v2 programming model) Event Hub trigger wiring.

Deploys as the `telemetry-pipeline` Function App's one function, consuming
batches of Event Hub messages (Log Analytics Data Export rows) and handing
them to `batch.transform_batch()` for the actual field-mapping work.

This module is the ONLY one in this package that imports `azure.functions`
- `mapping.py`/`batch.py`/`exporter.py` do not, so the transform logic they
implement is importable and unit-testable without the Azure Functions
runtime or the `azure-functions` package installed (per the task's
dependency-injection/testability requirement). This module itself is not
covered by this package's unit tests for that reason - it is thin wiring
over already-tested logic, consistent with how thin Azure Function
entrypoints are conventionally left untested in favor of testing the
logic they call.

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

import azure.functions as func

from .batch import transform_batch
from .exporter import build_arize_otlp_exporter, get_default_exporter

logger = logging.getLogger(__name__)

# Must match `eventHubConnectionSettingPrefix` in
# infra/modules/function-app.bicep (default "EventHubConnection").
EVENT_HUB_CONNECTION_SETTING_PREFIX = os.environ.get(
    "EVENT_HUB_CONNECTION_SETTING_PREFIX", "EventHubConnection"
)
EVENT_HUB_NAME = os.environ.get("EVENT_HUB_NAME", "telemetry-export")
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
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=EVENT_HUB_NAME,
    connection=f"{EVENT_HUB_CONNECTION_SETTING_PREFIX}",
    consumer_group=EVENT_HUB_CONSUMER_GROUP,
    cardinality="many",
)
def telemetry_transform(events: list[func.EventHubEvent]) -> None:
    """Event Hub trigger entrypoint: transform one batch, export the spans.

    Uses whole-batch checkpointing (the Functions host's default behavior
    for a Python v2 Event Hub trigger that doesn't raise) deliberately -
    per `trace-correlation-preservation.md` §4, per-event checkpointing
    with silent drops on partial failure is the dangerous configuration
    for correlation preservation and must not be used here.
    """
    exporter = _resolve_exporter()
    result = transform_batch(events, exporter)
    logger.info(
        "telemetry_transform: processed batch of %d record(s): %d span(s) exported, "
        "%d skipped (malformed/unreadable)",
        result.total_records,
        len(result.spans),
        len(result.skipped),
    )
    for skipped in result.skipped:
        logger.warning("telemetry_transform: skipped record - %s", skipped.reason)
