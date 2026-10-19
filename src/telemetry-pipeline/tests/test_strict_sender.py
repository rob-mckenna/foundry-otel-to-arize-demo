"""No-network tests of one-attempt OTLP outcomes and strict configuration."""
from __future__ import annotations

import contextlib
import logging
from types import SimpleNamespace

import pytest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceResponse

from telemetry_pipeline import function_app
from telemetry_pipeline.durable_runtime import DurableRuntime
from telemetry_pipeline.durable_store import AdmissionError
from telemetry_pipeline.strict_sender import Delivery, MAX_RESPONSE_BYTES, StrictSender


class Connection:
    def __init__(self, status=200, body=b"", error=None):
        self.status = status
        self.body = body
        self.error = error
        self.requests = []
        self.closed = False

    def request(self, method, path, body, headers):
        self.requests.append((method, path, body, headers))
        if self.error:
            raise self.error

    def getresponse(self):
        return SimpleNamespace(status=self.status, read=lambda length: self.body[:length])

    def close(self):
        self.closed = True


@pytest.mark.parametrize("status,body,error,expected", [
    (200, b"", None, Delivery.CONFIRMED),
    (429, b"", None, Delivery.RETRYABLE_REJECTION),
    (400, b"", None, Delivery.REJECTED),
    (401, b"", None, Delivery.REJECTED),
    (403, b"", None, Delivery.REJECTED),
    (413, b"", None, Delivery.REJECTED),
    (500, b"", None, Delivery.AMBIGUOUS),
    (503, b"", None, Delivery.AMBIGUOUS),
    (302, b"", None, Delivery.AMBIGUOUS),
    (200, b"bad protobuf", None, Delivery.AMBIGUOUS),
    (200, b"x" * (MAX_RESPONSE_BYTES + 1), None, Delivery.AMBIGUOUS),
    (200, b"", TimeoutError("synthetic sensitive timeout detail"), Delivery.AMBIGUOUS),
    (200, b"", ConnectionError("synthetic sensitive socket detail"), Delivery.AMBIGUOUS),
], ids=lambda value: f"bytes-{len(value)}" if isinstance(value, bytes) else str(value))
def test_single_attempt_no_redirect_or_automatic_retry(status, body, error, expected, caplog):
    connection = Connection(status, body, error)
    sender = StrictSender(
        "https://synthetic.invalid/v1/traces", "synthetic-space", "synthetic-key",
        connection_factory=lambda *args, **kwargs: connection,
    )
    with caplog.at_level(logging.DEBUG):
        assert sender.send(b"synthetic-wire") == expected
    assert len(connection.requests) == 1 and connection.closed
    assert caplog.text == ""


@pytest.mark.parametrize("rejected,message", [(1, ""), (0, "synthetic partial warning")])
def test_partial_success_is_never_acknowledged(rejected, message):
    response = ExportTraceServiceResponse()
    response.partial_success.rejected_spans = rejected
    response.partial_success.error_message = message
    connection = Connection(body=response.SerializeToString())
    sender = StrictSender(
        "https://synthetic.invalid/v1/traces", "synthetic-space", "synthetic-key",
        connection_factory=lambda *args, **kwargs: connection,
    )
    assert sender.send(b"synthetic-wire") == Delivery.AMBIGUOUS
    assert len(connection.requests) == 1


@pytest.mark.parametrize("endpoint,space,key", [
    ("http://synthetic.invalid/v1/traces", "space", "key"),
    ("https://user:secret@synthetic.invalid/v1/traces", "space", "key"),
    ("https://synthetic.invalid/v1/traces?token=secret", "space", "key"),
    ("https://synthetic.invalid/v1/traces", "", "key"),
    ("https://synthetic.invalid/v1/traces", "space", ""),
    ("https://synthetic.invalid/v1/traces", "space", "synthetic\r\nkey"),
])
def test_invalid_live_configuration_fails_without_console_success(endpoint, space, key):
    with pytest.raises(ValueError):
        StrictSender(endpoint, space, key)


CONFIGURATION = {
    "DURABLE_GENAI_ENABLED": "true",
    "DURABLE_ALLOWED_WORKSPACE_ID": "11111111-1111-4111-8111-111111111111",
    "DURABLE_ALLOWED_COMPONENT_RESOURCE_ID": (
        "/subscriptions/22222222-2222-4222-8222-222222222222"
        "/resourceGroups/synthetic/providers/Microsoft.Insights/components/synthetic"
    ),
    "DURABLE_ARIZE_PROJECT": "synthetic-project",
    "ARIZE_OTLP_ENDPOINT": "https://synthetic.invalid/v1/traces",
    "ARIZE_SPACE_ID": "synthetic-space",
    "ARIZE_API_KEY": "synthetic-test-only",
    "AzureWebJobsStorage__accountName": "syntheticaccount",
}


@pytest.fixture
def strict_configuration(monkeypatch):
    from telemetry_pipeline import durable_runtime

    # Replace the module's environment view, never read/restore real credentials.
    configuration = dict(CONFIGURATION)
    monkeypatch.setattr(durable_runtime, "os", SimpleNamespace(environ=configuration))
    return configuration


@pytest.mark.parametrize("missing", [
    "DURABLE_ALLOWED_WORKSPACE_ID", "DURABLE_ALLOWED_COMPONENT_RESOURCE_ID",
    "DURABLE_ARIZE_PROJECT", "ARIZE_OTLP_ENDPOINT", "ARIZE_SPACE_ID",
    "ARIZE_API_KEY", "AzureWebJobsStorage__accountName",
])
def test_strict_mode_requires_all_storage_source_destination_and_live_settings(
    strict_configuration, monkeypatch, missing,
):
    strict_configuration.pop(missing)
    with pytest.raises((AdmissionError, ValueError)):
        DurableRuntime()


def test_runtime_uses_only_managed_identity_and_dedicated_container(strict_configuration, monkeypatch):
    from telemetry_pipeline import durable_runtime

    observed = {}

    class Service:
        def __init__(self, uri, **kwargs):
            observed.update(uri=uri, kwargs=kwargs)

        def get_container_client(self, name):
            observed["container"] = name
            return object()

    monkeypatch.setattr(
        durable_runtime, "ManagedIdentityCredential",
        lambda: contextlib.nullcontext("synthetic-managed-identity"),
    )
    monkeypatch.setattr(
        durable_runtime, "BlobServiceClient",
        lambda *args, **kwargs: contextlib.nullcontext(Service(*args, **kwargs)),
    )
    with DurableRuntime() as runtime:
        assert runtime.correlator.scope.project == "synthetic-project"
    assert observed["uri"] == "https://syntheticaccount.blob.core.windows.net"
    assert observed["kwargs"]["credential"] == "synthetic-managed-identity"
    assert observed["container"] == "genai-correlation"


def test_trigger_admission_failure_raises_without_legacy_export_or_ack(
    monkeypatch, registered_pipeline_functions,
):
    from telemetry_pipeline import durable_runtime

    monkeypatch.setenv("DURABLE_GENAI_ENABLED", "true")

    def admit(events):
        raise AdmissionError("synthetic_storage_failure")

    runtime = SimpleNamespace(correlator=SimpleNamespace(admit_batch=admit))
    monkeypatch.setattr(durable_runtime, "DurableRuntime", lambda: contextlib.nullcontext(runtime))
    monkeypatch.setattr(
        function_app, "_resolve_exporter", lambda: pytest.fail("legacy exporter selected"),
    )
    invoke = registered_pipeline_functions[0].get_user_function()
    with pytest.raises(AdmissionError, match="synthetic_storage_failure"):
        invoke(["synthetic event"])


def test_trigger_admits_and_timer_drains_only_when_enabled(monkeypatch, registered_pipeline_functions):
    from telemetry_pipeline import durable_runtime

    calls = []
    runtime = SimpleNamespace(
        sender="synthetic-sender",
        correlator=SimpleNamespace(
            admit_batch=lambda events: calls.append(("admit", events)) or 1,
            drain=lambda sender: calls.append(("drain", sender)) or 1,
        ),
    )
    monkeypatch.setattr(durable_runtime, "DurableRuntime", lambda: contextlib.nullcontext(runtime))
    monkeypatch.setattr(
        function_app, "_resolve_exporter", lambda: pytest.fail("legacy exporter selected"),
    )
    trigger, timer = [item.get_user_function() for item in registered_pipeline_functions]
    monkeypatch.setenv("DURABLE_GENAI_ENABLED", "false")
    timer(None)
    assert calls == []
    monkeypatch.setenv("DURABLE_GENAI_ENABLED", "true")
    trigger(["synthetic event"])
    timer(None)
    assert calls == [("admit", ["synthetic event"]), ("drain", "synthetic-sender")]
    timer_metadata = registered_pipeline_functions[1].get_trigger().get_dict_repr()
    assert timer_metadata["type"] == "timerTrigger"
    assert timer_metadata["runOnStartup"] is False
