"""In-process span assertions only; no exporter or credential reaches Azure."""
import socket

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture(scope="session")
def span_exporter():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    yield exporter
    provider.shutdown()


@pytest.fixture(autouse=True)
def _offline_only(monkeypatch, span_exporter):
    def loopback_only(connect):
        def guarded(sock, address):
            # Windows asyncio creates a loopback socket pair for its event loop.
            if not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1"):
                raise AssertionError("Offline caller tests must never contact an external service")
            return connect(sock, address)
        return guarded

    monkeypatch.setattr(socket.socket, "connect", loopback_only(socket.socket.connect))
    monkeypatch.setattr(socket.socket, "connect_ex", loopback_only(socket.socket.connect_ex))
    span_exporter.clear()
    yield
    span_exporter.clear()
