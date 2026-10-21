"""Exercise the registered durable-only Functions without a host or network."""
from __future__ import annotations

import contextlib
import logging
from types import SimpleNamespace
from typing import List, get_type_hints

import azure.functions as func
import pytest

from telemetry_pipeline import function_app
from telemetry_pipeline.durable_store import AdmissionError


def test_binding_contract_and_bounded_host_retry(registered_pipeline_functions):
    admission, outbox = registered_pipeline_functions
    assert admission.get_function_name() == "TelemetryTransform"
    assert outbox.get_function_name() == "DurableGenAIOutbox"
    trigger = admission.get_trigger().get_dict_repr()
    assert trigger["type"] == "eventHubTrigger"
    assert trigger["cardinality"].value == "many"
    assert trigger["connection"] == function_app.EVENT_HUB_CONNECTION_SETTING_PREFIX
    assert trigger["eventHubName"] == function_app.EVENT_HUB_NAME
    assert get_type_hints(admission.get_user_function())["events"] == List[func.EventHubEvent]
    retry = admission.get_settings_dict("retry_policy")
    assert retry["strategy"] == "exponential_backoff"
    assert int(retry["max_retry_count"]) == 3
    assert retry["minimum_interval"] == "00:00:05"
    assert retry["maximum_interval"] == "00:01:00"
    timer = outbox.get_trigger().get_dict_repr()
    assert timer["schedule"] == "*/30 * * * * *"
    assert timer["runOnStartup"] is False
    assert timer["useMonitor"] is True


@pytest.fixture
def runtime(monkeypatch):
    calls = []

    @contextlib.contextmanager
    def context():
        calls.append("open")
        try:
            yield SimpleNamespace(
                sender="synthetic-sender",
                correlator=SimpleNamespace(
                    admit_batch=lambda events: calls.append(("admit", events)) or 2,
                    drain=lambda sender: calls.append(("drain", sender)) or 3,
                ),
            )
        finally:
            calls.append("close")

    monkeypatch.setattr(function_app.durable_runtime, "DurableRuntime", context)
    return calls


@pytest.mark.parametrize("obsolete_gate", [None, "false", "true", "invalid"])
def test_both_functions_always_use_durable_path(
    runtime, monkeypatch, registered_pipeline_functions, obsolete_gate, caplog,
):
    if obsolete_gate is None:
        monkeypatch.delenv("DURABLE_GENAI_ENABLED", raising=False)
    else:
        monkeypatch.setenv("DURABLE_GENAI_ENABLED", obsolete_gate)
    admission, outbox = [item.get_user_function() for item in registered_pipeline_functions]
    with caplog.at_level(logging.INFO):
        admission(["synthetic event"])
        outbox(None)
    assert runtime == [
        "open", ("admit", ["synthetic event"]), "close",
        "open", ("drain", "synthetic-sender"), "close",
    ]
    assert "durably_admitted=2" in caplog.text
    assert "scanned=3" in caplog.text
    assert "export_status=success" not in caplog.text


@pytest.mark.parametrize("index", [0, 1])
def test_missing_configuration_fails_both_entrypoints_without_success(
    monkeypatch, registered_pipeline_functions, index, caplog,
):
    monkeypatch.setattr(function_app.durable_runtime, "os", SimpleNamespace(environ={}))
    with caplog.at_level(logging.INFO), pytest.raises(AdmissionError, match="configuration_required"):
        registered_pipeline_functions[index].get_user_function()([])
    assert "durably_admitted=" not in caplog.text
    assert "scanned=" not in caplog.text
