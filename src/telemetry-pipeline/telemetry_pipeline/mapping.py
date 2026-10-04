"""Per-record field-group transform logic: Azure Monitor record -> OTLP span.

This module implements every mapping in `docs/telemetry/field-mapping.md`'s
summary table and its four detail docs (`docs/telemetry/mapping/*.md`,
issues #89-#92), plus the correlation-ID handling documented in
`docs/telemetry/trace-correlation-preservation.md` (#37) §1.

It has no dependency on `azure.functions` or any live Azure/Arize SDK -
only `opentelemetry-api`/`opentelemetry-sdk`, the same OTel packages
already adopted by `src/prompt-agent` (see that package's
`pyproject.toml`). This keeps the transform logic unit-testable with
plain Python dicts standing in for Event Hub message bodies.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.util.instrumentation import InstrumentationScope
from opentelemetry.trace import SpanContext, SpanKind, TraceFlags
from opentelemetry.trace.status import Status, StatusCode

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class MalformedRecordError(ValueError):
    """Raised when a source record fails identity-field validation.

    Per `docs/telemetry/mapping/identity-correlation-fields.md` §2 step 2:
    "The Function must explicitly validate length/hex-format and reject or
    flag malformed rows rather than silently truncating or coercing them."
    Callers (see `batch.py`) catch this per-record and flag/skip rather than
    letting one malformed row take down an entire batch.
    """


# ---------------------------------------------------------------------------
# Identity/correlation fields (#89) - trace_id / span_id / parent_span_id /
# correlation.id. See trace-correlation-preservation.md §1: App Insights'
# operation_Id/id/operation_ParentId are already the exact byte-width OTel
# expects, so these are opaque-hex-string copies, never re-encoded.
# ---------------------------------------------------------------------------

_TRACE_ID_HEX_LEN = 32  # 16 bytes
_SPAN_ID_HEX_LEN = 16  # 8 bytes


def _is_hex(value: str) -> bool:
    try:
        int(value, 16)
    except (TypeError, ValueError):
        return False
    return True


def _validate_hex_id(value: Any, expected_len: int, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != expected_len or not _is_hex(value):
        raise MalformedRecordError(
            f"{field_name!r} must be a {expected_len}-char lowercase hex string, "
            f"got {value!r}"
        )
    return value.lower()


def parse_trace_id(operation_id: Any) -> int:
    """`operation_Id` -> OTel `trace_id` (int). No re-encoding - verbatim hex."""
    hex_value = _validate_hex_id(operation_id, _TRACE_ID_HEX_LEN, "operation_Id")
    return int(hex_value, 16)


def parse_span_id(span_id_field: Any) -> int:
    """`id` -> OTel `span_id` (int). No re-encoding - verbatim hex."""
    hex_value = _validate_hex_id(span_id_field, _SPAN_ID_HEX_LEN, "id")
    return int(hex_value, 16)


def parse_parent_span_id(operation_parent_id: Any) -> int | None:
    """`operation_ParentId` -> OTel parent `span_id` (int), or `None`.

    Root spans (e.g. `prompt_agent.invoke`) have an empty/absent
    `operation_ParentId`. Per trace-correlation-preservation.md §1, this
    MUST become "no parent" (`None`), never a zero-filled span ID - a
    zero-filled parent would make a root span look like a child of a bogus
    all-zero span.
    """
    if operation_parent_id in (None, ""):
        return None
    hex_value = _validate_hex_id(operation_parent_id, _SPAN_ID_HEX_LEN, "operation_ParentId")
    return int(hex_value, 16)


def build_span_context(trace_id: int, span_id: int) -> SpanContext:
    return SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )


def build_parent_context(trace_id: int, parent_span_id: int | None) -> SpanContext | None:
    """Return the parent `SpanContext`, or `None` for a root span.

    Returning `None` (rather than an all-zero `SpanContext`) is what keeps a
    root span from being coerced into looking like a child span - see
    `parse_parent_span_id` above.
    """
    if parent_span_id is None:
        return None
    return SpanContext(
        trace_id=trace_id,
        span_id=parent_span_id,
        is_remote=True,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )


# ---------------------------------------------------------------------------
# customDimensions parsing + the transform-wide string->typed coercion rule
# ---------------------------------------------------------------------------


def parse_custom_dimensions(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return `customDimensions` as a dict, decoding it if it is a JSON string.

    Azure Monitor/Log Analytics export rows sometimes carry `customDimensions`
    as an already-parsed dict (e.g. in tests) and sometimes as a raw JSON
    string (the literal Log Analytics Data Export wire format) - handle both.
    """
    raw = record.get("customDimensions", {})
    if raw is None:
        return {}
    if isinstance(raw, str):
        if not raw.strip():
            return {}
        return json.loads(raw)
    if isinstance(raw, Mapping):
        return dict(raw)
    raise MalformedRecordError(f"customDimensions must be a dict or JSON string, got {type(raw)!r}")


def coerce_int(value: Any) -> int | None:
    """App Insights exports every customDimensions value as a string - cast
    to `int` explicitly (see field-mapping.md's "Transform-wide rule" and
    `docs/telemetry/mapping/token-fields.md` §2 step 3). Returns `None` for
    an absent field so the caller can decide whether to omit the attribute.
    """
    if value is None:
        return None
    if isinstance(value, bool):  # guard: bool is an int subclass in Python
        raise MalformedRecordError(f"expected an int-like value, got bool {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            raise MalformedRecordError(f"could not coerce {value!r} to int") from exc
    raise MalformedRecordError(f"could not coerce {value!r} to int")


_TRUE_STRINGS = {"true", "1", "yes"}
_FALSE_STRINGS = {"false", "0", "no"}


def coerce_bool(value: Any) -> bool | None:
    """String -> bool coercion for `retry.will_retry` (and `Success`, which
    App Insights' standard `AppDependencies` schema already stores as a
    native bool, but is coerced defensively the same way in case the Event
    Hub payload round-tripped it through JSON-string form too).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_STRINGS:
            return True
        if lowered in _FALSE_STRINGS:
            return False
        raise MalformedRecordError(f"could not coerce {value!r} to bool")
    raise MalformedRecordError(f"could not coerce {value!r} to bool")


# ---------------------------------------------------------------------------
# Token fields (#90)
# ---------------------------------------------------------------------------

_TOKEN_FIELDS = (
    "llm.token_count.prompt",
    "llm.token_count.completion",
    "llm.token_count.total",
)


def map_token_fields(custom_dimensions: Mapping[str, Any]) -> dict[str, int]:
    """string -> int cast for the three `llm.token_count.*` attributes.

    Per `docs/telemetry/mapping/token-fields.md` §2: this is the single
    highest-risk correctness bug class in the transform - omission here
    would let Arize's numeric aggregation views receive quoted strings.
    Fields absent from the source record are simply omitted (not
    synthesized as zero).
    """
    attributes: dict[str, int] = {}
    for field in _TOKEN_FIELDS:
        if field in custom_dimensions:
            coerced = coerce_int(custom_dimensions[field])
            if coerced is not None:
                attributes[field] = coerced
    return attributes


# ---------------------------------------------------------------------------
# LLM I/O fields (#91)
# ---------------------------------------------------------------------------

_LLM_IO_FIELDS = ("input.value", "output.value", "llm.model_name")


def map_llm_io_fields(custom_dimensions: Mapping[str, Any]) -> dict[str, str]:
    """String passthrough, unchanged key names, no type coercion needed.

    Per `docs/telemetry/mapping/llm-io-fields.md` §2: no *additional*
    truncation is introduced here beyond whatever the App Insights 8KB
    customDimensions limit already did upstream.
    """
    return {field: custom_dimensions[field] for field in _LLM_IO_FIELDS if field in custom_dimensions}


# ---------------------------------------------------------------------------
# Span kind/status fields (#92)
# ---------------------------------------------------------------------------

_RETRY_INT_FIELDS = ("retry.attempt", "retry.max_attempts")
_RETRY_BOOL_FIELD = "retry.will_retry"
_SPAN_KIND_FIELD = "openinference.span.kind"

# Azure Monitor's `AppDependencies` schema does not carry an explicit OTel
# `SpanKind` column; the only kind-ish signal is the OpenInference
# `openinference.span.kind` custom dimension (CHAIN/TOOL/LLM), which is an
# *attribute*, not OTel core `SpanKind`. This best-effort INTERNAL/CLIENT
# inference is not itself part of the field-mapping.md spec (nothing there
# requires it) - it is included only so the produced `ReadableSpan.kind`
# isn't left meaningless, and must not be read as an authoritative mapping.
_CLIENT_OPENINFERENCE_KINDS = {"TOOL", "LLM"}


def infer_span_kind(openinference_kind: str | None) -> SpanKind:
    if openinference_kind in _CLIENT_OPENINFERENCE_KINDS:
        return SpanKind.CLIENT
    return SpanKind.INTERNAL


def map_span_kind_status_fields(
    record: Mapping[str, Any], custom_dimensions: Mapping[str, Any]
) -> tuple[str, Status, SpanKind, dict[str, Any]]:
    """Returns (span name, Status, SpanKind, extra attributes dict).

    Per `docs/telemetry/mapping/span-kind-status-fields.md` §2:
      - `Name` -> span name, unchanged.
      - `Success` (bool) -> `STATUS_CODE_OK`/`STATUS_CODE_ERROR`.
      - `openinference.span.kind` -> passthrough attribute; absent on
        retry-attempt spans - must NOT be synthesized when missing.
      - `retry.attempt`/`retry.max_attempts` -> string -> int.
      - `retry.will_retry` -> string -> bool. Present only on failed
        attempts.
    """
    if "Name" not in record:
        raise MalformedRecordError("record is missing required 'Name' field")
    name = record["Name"]

    success = record.get("Success")
    coerced_success = coerce_bool(success)
    if coerced_success is None:
        raise MalformedRecordError("record is missing required 'Success' field")
    status = Status(StatusCode.OK if coerced_success else StatusCode.ERROR)

    kind_value = custom_dimensions.get(_SPAN_KIND_FIELD)
    kind = infer_span_kind(kind_value)

    attributes: dict[str, Any] = {}
    # Absence is meaningful (e.g. retry.attempt spans) - only set when present.
    if kind_value is not None:
        attributes[_SPAN_KIND_FIELD] = kind_value
    for field in _RETRY_INT_FIELDS:
        if field in custom_dimensions:
            coerced = coerce_int(custom_dimensions[field])
            if coerced is not None:
                attributes[field] = coerced
    if _RETRY_BOOL_FIELD in custom_dimensions:
        coerced_retry = coerce_bool(custom_dimensions[_RETRY_BOOL_FIELD])
        if coerced_retry is not None:
            attributes[_RETRY_BOOL_FIELD] = coerced_retry

    return name, status, kind, attributes


# ---------------------------------------------------------------------------
# Correlation ID (part of the identity/correlation group, #89)
# ---------------------------------------------------------------------------

_CORRELATION_ID_FIELD = "correlation.id"


def map_correlation_id(custom_dimensions: Mapping[str, Any]) -> dict[str, str]:
    """`customDimensions["correlation.id"]` -> `attributes.correlation.id`.

    String passthrough, unchanged key name - no OTel-core equivalent (it is
    an app-level join key, see `identity-correlation-fields.md` §1).
    """
    if _CORRELATION_ID_FIELD in custom_dimensions:
        return {_CORRELATION_ID_FIELD: custom_dimensions[_CORRELATION_ID_FIELD]}
    return {}


# ---------------------------------------------------------------------------
# Resource (service.name et al.) - best-effort from standard App Insights
# columns, not itself part of the field-mapping.md table.
# ---------------------------------------------------------------------------

_DEFAULT_SERVICE_NAME = "telemetry-pipeline-function"


def build_resource(record: Mapping[str, Any]) -> Resource:
    service_name = record.get("cloud_RoleName") or _DEFAULT_SERVICE_NAME
    attrs: dict[str, Any] = {"service.name": service_name}
    role_instance = record.get("cloud_RoleInstance")
    if role_instance:
        attrs["service.instance.id"] = role_instance
    return Resource.create(attrs)


_INSTRUMENTATION_SCOPE = InstrumentationScope(name="telemetry_pipeline.transform")


# ---------------------------------------------------------------------------
# Full-record transform
# ---------------------------------------------------------------------------


def record_to_span(record: Mapping[str, Any]) -> ReadableSpan:
    """Transform one Azure Monitor record into an OTel SDK `ReadableSpan`.

    Implements every mapping in `docs/telemetry/field-mapping.md`'s summary
    table. Raises `MalformedRecordError` (caught by `batch.py`, never
    silently swallowed) for identity fields that fail validation, a missing
    `Name`, or a missing/non-boolean `Success`.
    """
    custom_dimensions = parse_custom_dimensions(record)

    trace_id = parse_trace_id(record.get("operation_Id"))
    span_id = parse_span_id(record.get("id"))
    parent_span_id = parse_parent_span_id(record.get("operation_ParentId"))

    context = build_span_context(trace_id, span_id)
    parent = build_parent_context(trace_id, parent_span_id)

    name, status, kind, span_kind_attrs = map_span_kind_status_fields(record, custom_dimensions)

    attributes: dict[str, Any] = {}
    attributes.update(map_correlation_id(custom_dimensions))
    attributes.update(map_token_fields(custom_dimensions))
    attributes.update(map_llm_io_fields(custom_dimensions))
    attributes.update(span_kind_attrs)

    timestamp = record.get("timestamp")
    start_time = _parse_time_ns(timestamp) if timestamp else None
    duration_ms = record.get("duration")
    end_time = None
    if start_time is not None and duration_ms is not None:
        end_time = start_time + int(float(duration_ms) * 1_000_000)

    return ReadableSpan(
        name=name,
        context=context,
        parent=parent,
        resource=build_resource(record),
        attributes=attributes or None,
        events=(),
        links=(),
        kind=kind,
        status=status,
        start_time=start_time,
        end_time=end_time,
        instrumentation_scope=_INSTRUMENTATION_SCOPE,
    )


def _parse_time_ns(timestamp: Any) -> int | None:
    """Best-effort ISO-8601 timestamp -> epoch nanoseconds.

    Not part of the field-mapping.md spec (no acceptance criterion
    references start/end time), but populated on a best-effort basis so
    exported spans carry a plausible timestamp rather than `None` for every
    span. Returns `None` (rather than raising) on an unparsable value - a
    missing/odd timestamp is not grounds to reject an otherwise-valid
    identity/correlation record.
    """
    import datetime

    if isinstance(timestamp, (int, float)):
        return int(timestamp)
    if isinstance(timestamp, str):
        try:
            normalized = timestamp.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return int(dt.timestamp() * 1_000_000_000)
    return None
