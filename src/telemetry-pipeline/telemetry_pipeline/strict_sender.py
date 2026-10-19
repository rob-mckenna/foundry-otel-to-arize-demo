"""Single-attempt OTLP/HTTP delivery, without the exporter SDK's hidden retries."""
from __future__ import annotations

import http.client
import socket
import ssl
from enum import Enum
from urllib.parse import urlsplit

from google.protobuf.message import DecodeError
from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceResponse
from opentelemetry.sdk.resources import Resource

from .mapping import record_to_span

MAX_WIRE_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 64 * 1024


class Delivery(Enum):
    CONFIRMED = "confirmed"
    RETRYABLE_REJECTION = "retryable_rejection"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"


def freeze_record(record: dict, project: str) -> bytes:
    span = record_to_span(record)
    # Routing is explicit, not dependent on a later process's resource detector.
    span = type(span)(
        name=span.name, context=span.context, parent=span.parent,
        resource=Resource({**span.resource.attributes, "openinference.project.name": project}),
        attributes=span.attributes, events=span.events, links=span.links,
        kind=span.kind, status=span.status, start_time=span.start_time,
        end_time=span.end_time, instrumentation_scope=span.instrumentation_scope,
    )
    payload = encode_spans([span]).SerializeToString()
    if len(payload) > MAX_WIRE_BYTES:
        from .durable_store import AdmissionError
        raise AdmissionError("wire_payload_limit")
    return payload


class StrictSender:
    def __init__(self, endpoint: str, space_id: str, api_key: str, connection_factory=None):
        try:
            parsed = urlsplit(endpoint)
            port = parsed.port
        except ValueError:
            raise ValueError("strict_endpoint_requires_https_trace_url") from None
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or not parsed.path.endswith("/v1/traces")
        ):
            raise ValueError("strict_endpoint_requires_https_trace_url")
        if not space_id.strip() or not api_key.strip() or any(
            char in value for value in (space_id, api_key) for char in "\r\n"
        ):
            raise ValueError("strict_credentials_required")
        self.host = parsed.hostname
        self.port = port
        self.path = parsed.path
        self.headers = {
            "Content-Type": "application/x-protobuf",
            "space_id": space_id, "api_key": api_key,
        }
        self.connection_factory = connection_factory or http.client.HTTPSConnection

    def send(self, payload: bytes) -> Delivery:
        connection = self.connection_factory(self.host, self.port, timeout=20)
        try:
            connection.request("POST", self.path, body=payload, headers=self.headers)
            response = connection.getresponse()
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                return Delivery.AMBIGUOUS
            if response.status == 429:
                return Delivery.RETRYABLE_REJECTION
            if response.status in (400, 401, 403, 404, 405, 413, 415):
                return Delivery.REJECTED
            if response.status != 200:
                return Delivery.AMBIGUOUS
            result = ExportTraceServiceResponse()
            try:
                result.ParseFromString(body)
            except DecodeError:
                return Delivery.AMBIGUOUS
            if result.HasField("partial_success") and (
                result.partial_success.rejected_spans or result.partial_success.error_message
            ):
                return Delivery.AMBIGUOUS
            return Delivery.CONFIRMED
        except (OSError, socket.timeout, ssl.SSLError, http.client.HTTPException):
            return Delivery.AMBIGUOUS
        finally:
            connection.close()
