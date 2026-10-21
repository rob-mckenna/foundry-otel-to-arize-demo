"""Decode the supported Event Hub envelopes; admission enforces size limits."""
from __future__ import annotations

import json
from typing import Any, Mapping

from .mapping import MalformedRecordError


def message_body_to_text(message: Any) -> str:
    get_body = getattr(message, "get_body", None)
    body = get_body() if callable(get_body) else message
    if isinstance(body, (bytes, bytearray)):
        return body.decode("utf-8")
    if isinstance(body, str):
        return body
    raise MalformedRecordError("unsupported Event Hub message body type")


def extract_records(body_text: str) -> list[dict]:
    """Accept single rows, arrays, and the synthetic compatibility wrapper."""
    parsed = json.loads(body_text)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, Mapping):
        if "records" in parsed:
            if not isinstance(parsed["records"], list):
                raise MalformedRecordError("records wrapper must contain an array")
            return parsed["records"]
        return [dict(parsed)]
    raise MalformedRecordError("unsupported parsed message body shape")
