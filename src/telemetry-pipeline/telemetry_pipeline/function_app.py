"""Azure Functions bindings for durable admission and bounded OTLP delivery."""
from __future__ import annotations

import logging
import os
from typing import List

import azure.functions as func

from . import durable_runtime

logger = logging.getLogger(__name__)

# Identity-based binding prefix, not an Event Hub connection string.
EVENT_HUB_CONNECTION_SETTING_PREFIX = os.environ.get(
    "EVENT_HUB_CONNECTION_SETTING_PREFIX", "EventHubConnection"
)
EVENT_HUB_NAME = os.environ.get("EVENT_HUB_NAME", "telemetry")
EVENT_HUB_CONSUMER_GROUP = os.environ.get("EVENT_HUB_CONSUMER_GROUP", "$Default")

app = func.FunctionApp()


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
    connection=EVENT_HUB_CONNECTION_SETTING_PREFIX,
    consumer_group=EVENT_HUB_CONSUMER_GROUP,
    cardinality="many",
)
def telemetry_transform(events: List[func.EventHubEvent]) -> None:
    """Return only after durable admission; propagate failures for host retry.

    Checkpoints can advance after bounded host retry exhaustion. Persistent
    admission failures therefore still require explicit operator recovery.
    """
    with durable_runtime.DurableRuntime() as runtime:
        count = runtime.correlator.admit_batch(events)
        logger.info("telemetry_transform: durably_admitted=%d", count)


@app.function_name(name="DurableGenAIOutbox")
@app.timer_trigger(
    arg_name="timer", schedule="*/30 * * * * *", run_on_startup=False, use_monitor=True,
)
def durable_genai_outbox(timer: func.TimerRequest) -> None:
    with durable_runtime.DurableRuntime() as runtime:
        count = runtime.correlator.drain(runtime.sender)
        logger.info("durable_genai_outbox: scanned=%d", count)
