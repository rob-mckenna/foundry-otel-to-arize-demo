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
import logging
import math
import re
from typing import Any, Mapping

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.util.instrumentation import InstrumentationScope
from opentelemetry.trace import SpanContext, SpanKind, TraceFlags
from opentelemetry.trace.status import Status, StatusCode

logger = logging.getLogger(__name__)

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
# operation_Id/id and real parent IDs retain their exact OTel byte widths.
# Native dependency root markers are handled during row normalization.
# Strict |trace.span. wrappers are unwrapped without regenerating IDs.
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
    if (
        not isinstance(value, str)
        or len(value) != expected_len
        or any(char not in "0123456789abcdefABCDEF" for char in value)
        or not _is_hex(value)
        or int(value, 16) == 0
    ):
        raise MalformedRecordError(
            f"{field_name!r} must be a {expected_len}-char lowercase hex string, "
            f"got {value!r}"
        )
    return value.lower()


def parse_trace_id(operation_id: Any) -> int:
    """`operation_Id` -> OTel `trace_id` (int). No re-encoding - verbatim hex."""
    hex_value = _validate_hex_id(operation_id, _TRACE_ID_HEX_LEN, "operation_Id")
    return int(hex_value, 16)


def _span_hex(value: Any, field_name: str, trace_id: int | None = None) -> str:
    if isinstance(value, str) and value.startswith("|"):
        match = re.fullmatch(r"\|([0-9a-fA-F]{32})\.([0-9a-fA-F]{16})\.", value)
        if match is None:
            raise MalformedRecordError(f"{field_name!r} has an unsupported hierarchical ID")
        embedded_trace = parse_trace_id(match.group(1))
        if trace_id is not None and embedded_trace != trace_id:
            raise MalformedRecordError(f"{field_name!r} hierarchical trace differs from operation_Id")
        value = match.group(2)
    return _validate_hex_id(value, _SPAN_ID_HEX_LEN, field_name)


def parse_span_id(span_id_field: Any, trace_id: int | None = None) -> int:
    """`id` -> OTel `span_id` (int). No re-encoding - verbatim hex."""
    hex_value = _span_hex(span_id_field, "id", trace_id)
    return int(hex_value, 16)


def parse_parent_span_id(operation_parent_id: Any, trace_id: int | None = None) -> int | None:
    """`operation_ParentId` -> OTel parent `span_id` (int), or `None`.

    Root spans (e.g. `prompt_agent.invoke`) have an empty/absent
    `operation_ParentId`. Per trace-correlation-preservation.md §1, this
    MUST become "no parent" (`None`), never a zero-filled span ID - a
    zero-filled parent would make a root span look like a child of a bogus
    all-zero span.
    """
    if operation_parent_id in (None, ""):
        return None
    hex_value = _span_hex(operation_parent_id, "operation_ParentId", trace_id)
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

    Accept a parsed object or a JSON-encoded object. Native LAW `Properties`
    uses the same parser during normalization; no captured wire shape is assumed.
    """
    raw = record.get("customDimensions", {})
    if raw is None:
        return {}
    if isinstance(raw, str):
        if not raw.strip():
            return {}
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MalformedRecordError("customDimensions must contain a JSON object") from exc
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
            if coerced is None or not 0 <= coerced <= 2**63 - 1:
                raise MalformedRecordError(f"{field!r} must be a nonnegative int64")
            attributes[field] = coerced
    return attributes


# ---------------------------------------------------------------------------
# LLM I/O fields (#91)
# ---------------------------------------------------------------------------

_LLM_IO_FIELDS = ("input.value", "output.value", "llm.model_name")

_GEN_AI_STRING_FIELDS = (
    "gen_ai.operation.name",
    "gen_ai.request.model",
    "gen_ai.response.model",
    "gen_ai.response.id",
    "gen_ai.conversation.id",
    "gen_ai.provider.name",
)
_GEN_AI_TOKEN_ALIASES = {
    "gen_ai.usage.input_tokens": "llm.token_count.prompt",
    "gen_ai.usage.output_tokens": "llm.token_count.completion",
}
_GEN_AI_OPERATION_KINDS = {"chat": "LLM", "invoke_agent": "AGENT"}


def map_gen_ai_fields(custom_dimensions: Mapping[str, Any]) -> dict[str, Any]:
    """Bridge observed Foundry span metadata, without inventing missing usage/content.

    Keep the original model/usage/join attributes alongside OpenInference aliases.
    A response model is more specific than a request model (which may be an alias).
    Existing explicit OpenInference model/kind values remain authoritative.
    """
    attributes: dict[str, Any] = _string_attributes(custom_dimensions, _GEN_AI_STRING_FIELDS)
    for source, destination in _GEN_AI_TOKEN_ALIASES.items():
        if source not in custom_dimensions:
            continue
        count = coerce_int(custom_dimensions[source])
        if count is None or not 0 <= count <= 2**63 - 1:
            raise MalformedRecordError(f"{source!r} must be a nonnegative int64")
        if destination in custom_dimensions and coerce_int(custom_dimensions[destination]) != count:
            raise MalformedRecordError(f"conflicting {source!r} and {destination!r} values")
        attributes[source] = count
        attributes[destination] = count
    if "llm.model_name" not in custom_dimensions:
        model = attributes.get("gen_ai.response.model") or attributes.get("gen_ai.request.model")
        if model:
            attributes["llm.model_name"] = model
    if "openinference.span.kind" not in custom_dimensions:
        kind = _GEN_AI_OPERATION_KINDS.get(attributes.get("gen_ai.operation.name"))
        if kind:
            attributes["openinference.span.kind"] = kind
    return attributes


def map_llm_io_fields(custom_dimensions: Mapping[str, Any]) -> dict[str, str]:
    """Preserve explicit I/O; bridge inline GenAI role/parts messages as JSON.

    Per `docs/telemetry/mapping/llm-io-fields.md` §2: no *additional*
    truncation is introduced here beyond whatever the App Insights 8KB
    customDimensions limit already did upstream.
    """
    attributes = _string_attributes(custom_dimensions, _LLM_IO_FIELDS)
    for side in ("input", "output"):
        value_field, mime_field = f"{side}.value", f"{side}.mime_type"
        if value_field in attributes:
            attributes.update(_string_attributes(custom_dimensions, (mime_field,)))
            continue
        source = f"gen_ai.{side}.messages"
        if source not in custom_dimensions:
            continue
        value = _message_json(custom_dimensions[source], source)
        if value is not None:
            attributes[value_field] = value
            # A MIME without its explicit value cannot describe the generated JSON.
            attributes[mime_field] = "application/json"
    return attributes


def _message_json(value: Any, source: str) -> str | None:
    """Validate only the message envelope; preserve nested part content unchanged."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            logger.warning("telemetry_pipeline.mapping: omitting %s: invalid JSON", source)
            return None
    if not isinstance(value, list) or any(
        not isinstance(message, dict)
        or not isinstance(message.get("role"), str)
        or not message["role"]
        or not isinstance(message.get("parts"), list)
        or any(
            not isinstance(part, dict)
            or not isinstance(part.get("type"), str)
            or not part["type"]
            for part in message["parts"]
        )
        for message in value
    ):
        logger.warning("telemetry_pipeline.mapping: omitting %s: expected role/parts messages", source)
        return None
    try:
        return json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        logger.warning("telemetry_pipeline.mapping: omitting %s: non-JSON content", source)
        return None


def _string_attributes(values: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, str]:
    attributes = {}
    for field in fields:
        if field in values:
            if not isinstance(values[field], str):
                raise MalformedRecordError(f"{field!r} must be a string")
            attributes[field] = values[field]
    return attributes


# ---------------------------------------------------------------------------
# Span kind/status fields (#92)
# ---------------------------------------------------------------------------

_RETRY_INT_FIELDS = ("retry.attempt", "retry.max_attempts")
_RETRY_BOOL_FIELD = "retry.will_retry"
_SPAN_KIND_FIELD = "openinference.span.kind"

# Azure Monitor's `AppDependencies` schema does not carry an explicit OTel
# `SpanKind` column; the available signal is the OpenInference
# `openinference.span.kind` dimension (explicit or bridged from GenAI operation), which is an
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
    if not isinstance(record.get("Name"), str) or not record["Name"]:
        raise MalformedRecordError("record is missing required 'Name' field")
    name = record["Name"]

    success = record.get("Success")
    coerced_success = coerce_bool(success)
    if coerced_success is None:
        raise MalformedRecordError("record is missing required 'Success' field")
    status = Status(StatusCode.OK if coerced_success else StatusCode.ERROR)

    kind_attrs = _string_attributes(custom_dimensions, (_SPAN_KIND_FIELD,))
    kind_value = kind_attrs.get(_SPAN_KIND_FIELD)
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
    return _string_attributes(custom_dimensions, (_CORRELATION_ID_FIELD,))


# ---------------------------------------------------------------------------
# Resource (service.name et al.) - best-effort from standard App Insights
# columns, not itself part of the field-mapping.md table.
# ---------------------------------------------------------------------------

_DEFAULT_SERVICE_NAME = "telemetry-pipeline-function"


def build_resource(record: Mapping[str, Any]) -> Resource:
    _string_attributes(
        {key: record[key] for key in ("cloud_RoleName", "cloud_RoleInstance")
         if record.get(key) is not None},
        ("cloud_RoleName", "cloud_RoleInstance"),
    )
    service_name = record.get("cloud_RoleName") or _DEFAULT_SERVICE_NAME
    attrs: dict[str, Any] = {"service.name": service_name}
    role_instance = record.get("cloud_RoleInstance")
    if role_instance:
        attrs["service.instance.id"] = role_instance
    return Resource.create(attrs)


_INSTRUMENTATION_SCOPE = InstrumentationScope(name="telemetry_pipeline.transform")


_SPAN_COLUMN_ALIASES = {
    "OperationId": "operation_Id",
    "Id": "id",
    "ParentId": "operation_ParentId",
    "Properties": "customDimensions",
    "TimeGenerated": "timestamp",
    "DurationMs": "duration",
    "AppRoleName": "cloud_RoleName",
    "AppRoleInstance": "cloud_RoleInstance",
}


def normalize_dependency_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Accept native LAW AppDependencies/AppRequests alongside legacy fixtures.

    Aliases must agree when both are present; neither value wins silently.
    This is a span-row contract, not a log/exception-to-span mapping.
    """
    if not isinstance(record, Mapping):
        raise MalformedRecordError("span record must be a JSON object")
    if "Type" in record and record["Type"] not in ("AppDependencies", "AppRequests"):
        raise MalformedRecordError("only AppDependencies and AppRequests records are supported")
    normalized = dict(record)
    for native, legacy in _SPAN_COLUMN_ALIASES.items():
        if native not in record:
            continue
        value = record[native]
        if native == "Properties":
            value = parse_custom_dimensions({"customDimensions": value})
        if legacy in record:
            legacy_value = record[legacy]
            if native == "Properties":
                legacy_value = parse_custom_dimensions(record)
            if legacy_value != value or (
                isinstance(legacy_value, bool) != isinstance(value, bool)
            ):
                raise MalformedRecordError(f"conflicting {native!r} and {legacy!r} values")
        normalized[legacy] = value
    # Actual synthetic b58 source root: native LAW ParentId == OperationId.
    # This is a root marker, not a 128-bit parent span; legacy rows stay strict.
    if (
        record.get("Type") == "AppDependencies"
        and "OperationId" in record
        and isinstance(record.get("ParentId"), str)
        and len(record["ParentId"]) == _TRACE_ID_HEX_LEN
    ):
        parent_trace = parse_trace_id(record["ParentId"])
        operation_trace = parse_trace_id(normalized["operation_Id"])
        if parent_trace != operation_trace:
            raise MalformedRecordError("native ParentId root marker differs from OperationId")
        normalized["operation_ParentId"] = None
    if "TimeGenerated" in record:
        timestamp = record["TimeGenerated"]
        if not isinstance(timestamp, str) or _parse_time_ns(timestamp) is None:
            raise MalformedRecordError("TimeGenerated must be a valid ISO-8601 timestamp")
    if "DurationMs" in record and record["DurationMs"] is None:
        raise MalformedRecordError("DurationMs must be a finite nonnegative millisecond value")
    return normalized


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
    record = normalize_dependency_record(record)
    custom_dimensions = parse_custom_dimensions(record)
    gen_ai_attrs = map_gen_ai_fields(custom_dimensions)
    custom_dimensions = {**custom_dimensions, **gen_ai_attrs}

    trace_id = parse_trace_id(record.get("operation_Id"))
    span_id = parse_span_id(record.get("id"), trace_id)
    parent_span_id = parse_parent_span_id(record.get("operation_ParentId"), trace_id)

    context = build_span_context(trace_id, span_id)
    parent = build_parent_context(trace_id, parent_span_id)

    name, status, kind, span_kind_attrs = map_span_kind_status_fields(record, custom_dimensions)
    if record.get("Type") == "AppRequests":
        kind = SpanKind.SERVER

    attributes: dict[str, Any] = {}
    attributes.update(gen_ai_attrs)
    attributes.update(map_correlation_id(custom_dimensions))
    attributes.update(map_token_fields(custom_dimensions))
    attributes.update(map_llm_io_fields(custom_dimensions))
    attributes.update(span_kind_attrs)

    timestamp = record.get("timestamp")
    start_time = _parse_time_ns(timestamp) if timestamp is not None else None
    if timestamp is not None and (
        start_time is None or not 0 <= start_time <= 2**64 - 1
    ):
        raise MalformedRecordError("timestamp must be a valid nonnegative OTLP timestamp")
    duration_ms = record.get("duration")
    end_time = None
    if duration_ms is not None:
        try:
            duration = float(duration_ms)
        except (TypeError, ValueError, OverflowError) as exc:
            raise MalformedRecordError("duration must be a finite nonnegative millisecond value") from exc
        if (
            isinstance(duration_ms, bool)
            or not math.isfinite(duration * 1_000_000)
            or duration < 0
        ):
            raise MalformedRecordError("duration must be a finite nonnegative millisecond value")
        if start_time is not None:
            end_time = start_time + int(duration * 1_000_000)
            if end_time > 2**64 - 1:
                raise MalformedRecordError("span end time exceeds OTLP timestamp range")

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
    """ISO-8601 or legacy epoch nanoseconds -> nanoseconds; invalid -> None.

    Callers reject invalid supplied timestamps. Missing legacy times remain
    unset rather than being fabricated as the Function's invocation time.
    """
    import datetime

    if isinstance(timestamp, int) and not isinstance(timestamp, bool):
        return timestamp
    if isinstance(timestamp, float):
        if not math.isfinite(timestamp):
            return None
        return int(timestamp)
    if isinstance(timestamp, str):
        fraction = re.search(r"T\d{2}:\d{2}:\d{2}[.,](\d+)", timestamp)
        extra_ns = 0
        normalized = timestamp.replace("Z", "+00:00")
        if fraction:
            digits = fraction.group(1)
            if len(digits) > 9:
                return None
            extra_ns = int(digits.ljust(9, "0")) % 1000
            # Python 3.10 accepts microseconds; preserve the remaining nanos separately.
            start, end = fraction.span(1)
            normalized = normalized[:start] + digits[:6].ljust(6, "0") + normalized[end:]
            normalized = normalized.replace(",", ".")
        try:
            dt = datetime.datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            return None
        delta = dt - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        return (
            (delta.days * 86400 + delta.seconds) * 1_000_000_000
            + delta.microseconds * 1000
            + extra_ns
        )
    return None
