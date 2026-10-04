"""Batch-level processing: decode an Event Hub message batch into spans.

Per `docs/telemetry/trace-correlation-preservation.md` §4, the Function
must checkpoint (and therefore export) a whole batch together rather than
per-event, to avoid the "orphaned child spans with no visible parent"
failure mode when a parent span's event is dropped mid-batch. This module
reflects that: `transform_batch()` exports every successfully-transformed
span from one batch in a single `exporter.export()` call.

Malformed individual records are flagged (not silently dropped and not
allowed to fail the whole batch) - see `BatchResult.skipped`.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from .mapping import MalformedRecordError, record_to_span

logger = logging.getLogger(__name__)


@dataclass
class SkippedRecord:
    """One record that failed validation and was excluded from the batch."""

    reason: str
    raw_record: Any


@dataclass
class BatchResult:
    """Outcome of processing one Event Hub message batch."""

    spans: list[ReadableSpan] = field(default_factory=list)
    skipped: list[SkippedRecord] = field(default_factory=list)
    export_result: SpanExportResult | None = None

    @property
    def total_records(self) -> int:
        return len(self.spans) + len(self.skipped)


def _message_body_to_text(message: Any) -> str:
    """Normalize one Event Hub message to its decoded text body.

    Accepts, in order of preference:
      - an `azure.functions.EventHubEvent`-like object exposing
        `get_body() -> bytes` (the real Python v2 programming-model shape);
      - raw `bytes`/`bytearray`;
      - a plain `str` (already-decoded body, convenient for unit tests).
    """
    get_body = getattr(message, "get_body", None)
    if callable(get_body):
        body = get_body()
    else:
        body = message
    if isinstance(body, (bytes, bytearray)):
        return body.decode("utf-8")
    if isinstance(body, str):
        return body
    raise MalformedRecordError(f"unsupported Event Hub message body type: {type(body)!r}")


def _extract_records(body_text: str) -> list[dict]:
    """Parse one decoded message body into a list of raw record dicts.

    Handles the shapes this pipeline's upstream hops can produce:
      - a single JSON object (one record);
      - a JSON array of record objects;
      - the Log Analytics Data Export envelope `{"records": [...]}`.
    """
    parsed = json.loads(body_text)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, Mapping):
        if "records" in parsed and isinstance(parsed["records"], list):
            return parsed["records"]
        return [dict(parsed)]
    raise MalformedRecordError(f"unsupported parsed message body shape: {type(parsed)!r}")


def transform_batch(
    messages: Iterable[Any],
    exporter: SpanExporter,
) -> BatchResult:
    """Transform one Event Hub message batch and export the resulting spans.

    `messages` is whatever iterable of Event Hub message objects the
    trigger binding hands the Function (a `List[azure.functions.EventHubEvent]`
    in the real `cardinality="many"` binding) - or, for unit tests, any
    iterable of objects/bytes/strs `_message_body_to_text` understands.

    One `exporter.export()` call covers the whole batch (see module
    docstring) - never a call per record.
    """
    result = BatchResult()
    for message in messages:
        try:
            body_text = _message_body_to_text(message)
            raw_records = _extract_records(body_text)
        except (MalformedRecordError, json.JSONDecodeError) as exc:
            result.skipped.append(SkippedRecord(reason=str(exc), raw_record=message))
            logger.warning("telemetry_pipeline.batch: skipping unreadable message: %s", exc)
            continue

        for raw_record in raw_records:
            try:
                span = record_to_span(raw_record)
            except MalformedRecordError as exc:
                result.skipped.append(SkippedRecord(reason=str(exc), raw_record=raw_record))
                logger.warning(
                    "telemetry_pipeline.batch: skipping malformed record: %s", exc
                )
                continue
            result.spans.append(span)

    if result.spans:
        result.export_result = exporter.export(result.spans)
    return result
