"""Correlation ID generation/propagation helpers.

A correlation ID identifies one end-to-end request through the Foundry
Prompt Agent (one `PromptAgent.invoke()` call) independent of the
OpenTelemetry trace ID. This matters for two reasons:

1. An inbound caller (e.g. an upstream API gateway or chat front-end) may
   already have its own request/correlation ID it wants preserved across
   the whole call chain — `invoke()` accepts one so it is never
   regenerated/lost at this layer.
2. It gives a trace-system-agnostic join key: `correlation.id` is attached
   to *every* span in the request's tree (see #29), so even if spans were
   ever split across multiple traces (e.g. a future async/queued hop), they
   remain correlatable without depending on OTel's `trace_id` alone.

Attribute key used everywhere this is attached to a span: `correlation.id`
(see README.md "Correlation ID propagation (#29)" section — this exact key
name is the Telemetry-coordination contract referenced in the Milestone 1
decision doc).
"""
from __future__ import annotations

import uuid

CORRELATION_ID_ATTRIBUTE = "correlation.id"


def generate_correlation_id() -> str:
    """Generate a new correlation ID for a request that doesn't already have one."""
    return str(uuid.uuid4())
