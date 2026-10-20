"""Offline only: no credential, service or paid request is used."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

from prompt_agent import foundry_responses as caller


@pytest.fixture
def root(monkeypatch):
    # Keep all fixture files inside this worktree, never a system temp directory.
    path = caller.repository_root() / ".azure-sandbox" / ("caller-test-" + uuid.uuid4().hex)
    path.mkdir(parents=True)
    monkeypatch.setattr(caller, "repository_root", lambda: path)
    yield path
    import shutil
    shutil.rmtree(path)


@pytest.fixture
def spec():
    return caller.Request(
        "https://synthetic-account.services.ai.azure.com/api/projects/synthetic-project",
        "synthetic-no-tool", "7", str(uuid.uuid4()), "synthetic-approval-147", "synthetic-private-runner-mi",
    )


def response(**overrides):
    values = dict(
        id="resp_synthetic_147", status="completed", output_text="Fabricated demo acknowledgement.",
        usage=SimpleNamespace(input_tokens=17, output_tokens=9, total_tokens=26),
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def receipts(root):
    return list((root / caller.LEDGER_NAME).glob("*.receipt.json"))


def test_exact_versioned_envelope(spec):
    request = spec
    assert request.envelope() == {
        "input": caller.FIXTURE, "max_output_tokens": 1024,
        "stream": False, "background": False, "tools": [], "tool_choice": "none",
        "extra_body": {
            "agent_reference": {"type": "agent_reference", "name": "synthetic-no-tool", "version": "7"}
        },
    }
    assert len(caller.FIXTURE.encode("ascii")) < 1024


@pytest.mark.parametrize("version", ["", "latest", "0", "-1", "7/8", "7\n"])
def test_exact_version_required(spec, version):
    request = spec
    with pytest.raises(caller.CallerError, match="exact_numeric"):
        caller.Request(**{**request.__dict__, "agent_version": version}).validate()


@pytest.mark.parametrize("endpoint", [
    "http://synthetic-account.services.ai.azure.com/api/projects/synthetic-project",
    "https://synthetic-account.services.ai.azure.com/api/projects/synthetic-project/",
    "https://synthetic-account.services.ai.azure.com/api/projects/synthetic-project?key=forbidden",
    "https://unapproved.example/api/projects/synthetic-project",
])
def test_invalid_endpoint_rejected_before_intent(root, spec, monkeypatch, endpoint):
    create = AsyncMock()
    monkeypatch.setattr(caller, "_sdk_create", create)
    invalid = caller.Request(**{**spec.__dict__, "endpoint": endpoint})
    with pytest.raises(caller.CallerError, match="invalid_project_endpoint"):
        caller.invoke(invalid, allow_live=True)
    create.assert_not_called()
    assert not (root / caller.LEDGER_NAME).exists()


def test_opt_in_precedes_auth_and_ledger(root, spec, monkeypatch):
    request = spec
    create = AsyncMock()
    monkeypatch.setattr(caller, "_sdk_create", create)
    with pytest.raises(caller.CallerError, match="explicit_live_opt_in"):
        caller.invoke(request)
    create.assert_not_called()
    assert not (root / caller.LEDGER_NAME).exists()


def test_actual_usage_and_client_correlation(root, spec, monkeypatch, span_exporter):
    request = spec
    async def create(req, headers):
        intents = list((root / caller.LEDGER_NAME).glob("*.intent.json"))
        assert len(intents) == 1
        intent = json.loads(intents[0].read_text())
        assert intent["status"] == "inflight"
        assert intent["binding"] == request.binding()
        assert headers["x-ms-client-request-id"] == request.run_id
        assert headers["traceparent"].startswith("00-")
        assert req == request
        return response()

    monkeypatch.setattr(caller, "_sdk_create", create)
    with trace.get_tracer(__name__).start_as_current_span("synthetic_parent") as parent:
        result = caller.invoke(request, allow_live=True)
        assert result["client_parent_span_id"] == f"{parent.get_span_context().span_id:016x}"
    assert result["usage"] == {"input_tokens": 17, "output_tokens": 9, "total_tokens": 26}
    assert result["response_id"] == "resp_synthetic_147"
    receipt = json.loads(receipts(root)[0].read_text())
    assert receipt == result
    assert caller.FIXTURE not in receipts(root)[0].read_text()
    assert "Fabricated demo acknowledgement" not in receipts(root)[0].read_text()
    span = next(s for s in span_exporter.get_finished_spans() if s.name == "prompt_agent.responses.create")
    assert span.kind == SpanKind.CLIENT
    assert span.status.status_code == StatusCode.OK
    assert span.attributes["correlation.id"] == request.run_id
    assert span.attributes["llm.token_count.total"] == 26
    assert "input.value" not in span.attributes and "output.value" not in span.attributes


@pytest.mark.parametrize("usage", [
    None,
    SimpleNamespace(input_tokens=1, output_tokens=None, total_tokens=1),
    SimpleNamespace(input_tokens=True, output_tokens=1, total_tokens=2),
    SimpleNamespace(input_tokens=-1, output_tokens=1, total_tokens=0),
    SimpleNamespace(input_tokens=1, output_tokens=1, total_tokens=3),
    SimpleNamespace(input_tokens=1, output_tokens=1025, total_tokens=1026),
])
def test_missing_invalid_or_unbounded_usage_blocks_replay(root, spec, monkeypatch, usage, span_exporter):
    request = spec
    create = AsyncMock(return_value=response(usage=usage))
    monkeypatch.setattr(caller, "_sdk_create", create)
    with pytest.raises(caller.CallerError, match="ambiguous_no_retry"):
        caller.invoke(request, allow_live=True)
    assert json.loads(receipts(root)[0].read_text())["status"] == "ambiguous"
    with pytest.raises(caller.CallerError, match="existing_intent"):
        caller.invoke(request, allow_live=True)
    assert create.await_count == 1
    spans = span_exporter.get_finished_spans()
    assert spans[-1].status.status_code == StatusCode.ERROR
    assert not spans[-1].events


@pytest.mark.parametrize("changes", [
    {"status": "incomplete"}, {"status": "failed"}, {"id": "raw body\nunsafe"},
    {"output_text": ""}, {"output_text": "x" * 16385},
])
def test_provider_result_failure_is_ambiguous(root, spec, monkeypatch, changes):
    request = spec
    monkeypatch.setattr(caller, "_sdk_create", AsyncMock(return_value=response(**changes)))
    with pytest.raises(caller.CallerError, match="ambiguous_no_retry"):
        caller.invoke(request, allow_live=True)
    assert json.loads(receipts(root)[0].read_text())["status"] == "ambiguous"


def test_provider_exception_never_leaks_or_retries(root, spec, monkeypatch, capsys):
    request = spec
    create = AsyncMock(side_effect=RuntimeError("sensitive raw provider body"))
    monkeypatch.setattr(caller, "_sdk_create", create)
    argv = cli_args(request) + ["--allow-live"]
    assert caller.main(argv) == 1
    captured = capsys.readouterr()
    assert captured.err.strip() == "attempt_ambiguous_no_retry"
    assert "sensitive" not in captured.out + captured.err + receipts(root)[0].read_text()
    assert caller.main(argv) == 1
    assert create.await_count == 1


def cli_args(request):
    return [
        "--endpoint", request.endpoint, "--agent-name", request.agent_name,
        "--agent-version", request.agent_version, "--run-id", request.run_id,
        "--authorization-reference", request.authorization_reference,
        "--executor-reference", request.executor_reference,
    ]


def test_help_and_dry_run_are_strictly_offline(root, spec, monkeypatch, capsys):
    request = spec
    monkeypatch.setattr(caller, "_sdk_create", AsyncMock(side_effect=AssertionError("must not run")))
    with pytest.raises(SystemExit) as exc:
        caller.main(["--help"])
    assert exc.value.code == 0
    assert caller.main(cli_args(request) + ["--dry-run", "--allow-live"]) == 0
    assert not (root / caller.LEDGER_NAME).exists()
    assert "offline_dry_run" in capsys.readouterr().out


def test_duplicate_success_run_and_authorization_refused(root, spec, monkeypatch):
    request = spec
    create = AsyncMock(return_value=response())
    monkeypatch.setattr(caller, "_sdk_create", create)
    caller.invoke(request, allow_live=True)
    for changes in ({}, {"run_id": str(uuid.uuid4())}, {"authorization_reference": "different-approval"}):
        replay = caller.Request(**{**request.__dict__, **changes})
        with pytest.raises(caller.CallerError, match="existing_intent"):
            caller.invoke(replay, allow_live=True)
    assert create.await_count == 1


@pytest.mark.parametrize("distinct_run_id", [False, True])
def test_concurrent_attempt_only_one_submission(root, spec, monkeypatch, distinct_run_id):
    request = spec
    entered = threading.Event()
    release = threading.Event()
    calls = []

    async def create(*args):
        calls.append(1)
        entered.set()
        while not release.is_set():
            await asyncio.sleep(0.001)
        return response()

    monkeypatch.setattr(caller, "_sdk_create", create)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(caller.invoke, request, allow_live=True)
        try:
            assert entered.wait(5)
            with pytest.raises(caller.CallerError, match="existing_intent"):
                other = caller.Request(**{
                    **request.__dict__,
                    "run_id": str(uuid.uuid4()) if distinct_run_id else request.run_id,
                })
                caller.invoke(other, allow_live=True)
        finally:
            release.set()
        assert first.result(timeout=5)["status"] == "succeeded"
    assert len(calls) == 1


def test_crashed_inflight_intent_refused(root, spec, monkeypatch):
    request = spec
    with caller.Ledger(root, request):
        pass
    create = AsyncMock()
    monkeypatch.setattr(caller, "_sdk_create", create)
    with pytest.raises(caller.CallerError, match="existing_intent"):
        caller.invoke(request, allow_live=True)
    create.assert_not_called()


def test_preexisting_receipt_alone_refused(root, spec, monkeypatch):
    request = spec
    path = root / caller.LEDGER_NAME
    path.mkdir()
    (path / ("authorization-" + caller.digest(request.authorization_reference) + ".receipt.json")).touch()
    create = AsyncMock()
    monkeypatch.setattr(caller, "_sdk_create", create)
    with pytest.raises(caller.CallerError, match="existing_intent"):
        caller.invoke(request, allow_live=True)
    create.assert_not_called()


def test_intent_fsync_failure_prevents_auth_and_replay(root, spec, monkeypatch):
    request = spec
    create = AsyncMock()
    monkeypatch.setattr(caller, "_sdk_create", create)
    monkeypatch.setattr(caller.os, "fsync", MagicMock(side_effect=OSError("disk unavailable")))
    with pytest.raises(caller.CallerError, match="receipt_or_execution"):
        caller.invoke(request, allow_live=True)
    create.assert_not_called()
    with pytest.raises(caller.CallerError, match="existing_intent"):
        caller.invoke(request, allow_live=True)


def test_receipt_write_failure_after_submission_keeps_intent(root, spec, monkeypatch):
    request = spec
    create = AsyncMock(return_value=response())
    monkeypatch.setattr(caller, "_sdk_create", create)
    monkeypatch.setattr(caller.Ledger, "finish", MagicMock(side_effect=OSError("receipt unavailable")))
    with pytest.raises(caller.CallerError, match="ambiguous_no_retry"):
        caller.invoke(request, allow_live=True)
    with pytest.raises(caller.CallerError, match="existing_intent"):
        caller.invoke(request, allow_live=True)
    assert create.await_count == 1
    assert not receipts(root)


def test_success_receipt_error_records_ambiguous_when_writable(root, spec, monkeypatch, span_exporter):
    monkeypatch.setattr(caller, "_sdk_create", AsyncMock(return_value=response()))
    finish = caller.Ledger.finish
    attempts = []

    def fail_first(self, outcome):
        attempts.append(outcome["status"])
        if len(attempts) == 1:
            raise OSError("synthetic storage error")
        finish(self, outcome)

    monkeypatch.setattr(caller.Ledger, "finish", fail_first)
    with pytest.raises(caller.CallerError, match="ambiguous_no_retry"):
        caller.invoke(spec, allow_live=True)
    assert attempts == ["succeeded", "ambiguous"]
    assert json.loads(receipts(root)[0].read_text())["status"] == "ambiguous"
    assert span_exporter.get_finished_spans()[-1].status.status_code == StatusCode.ERROR


def test_unsafe_ledger_file_refused(root, spec, monkeypatch):
    request = spec
    (root / caller.LEDGER_NAME).touch()
    create = AsyncMock()
    monkeypatch.setattr(caller, "_sdk_create", create)
    with pytest.raises(caller.CallerError, match="unsafe_receipt"):
        caller.invoke(request, allow_live=True)
    create.assert_not_called()


def test_symlink_receipt_directory_refused(root, spec, monkeypatch):
    request = spec
    target = root / "other"
    target.mkdir()
    link = root / caller.LEDGER_NAME
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        import subprocess
        subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(link), str(target)],
            check=True, capture_output=True,
        )
    create = AsyncMock()
    monkeypatch.setattr(caller, "_sdk_create", create)
    try:
        with pytest.raises(caller.CallerError, match="unsafe_receipt"):
            caller.invoke(request, allow_live=True)
        create.assert_not_called()
    finally:
        if link.is_symlink():
            link.unlink()
        else:
            os.rmdir(link)


def test_overall_timeout_cancels_without_retry(root, spec, monkeypatch):
    request = spec
    cancelled = []

    async def create(*args):
        try:
            await asyncio.sleep(30)
        finally:
            cancelled.append(True)

    monkeypatch.setattr(caller, "_sdk_create", create)
    monkeypatch.setattr(caller, "OVERALL_SECONDS", 0.01)
    with pytest.raises(caller.CallerError, match="ambiguous_no_retry"):
        caller.invoke(request, allow_live=True)
    assert cancelled == [True]
    assert json.loads(receipts(root)[0].read_text())["status"] == "ambiguous"


def test_sdk_auth_retries_timeouts_and_submission_mocked(spec, monkeypatch):
    request = spec
    # Exercise the real adapter, replacing all credential/client factories before construction.
    from azure.ai.projects import aio as projects
    from azure.identity import aio as identity
    import httpx

    class Context:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    credential = Context()
    project = Context()
    client = Context()
    client.responses = SimpleNamespace(create=AsyncMock(return_value=response()))
    project.get_openai_client = MagicMock(return_value=client)
    cred_factory = MagicMock(return_value=credential)
    project_factory = MagicMock(return_value=project)
    http_factory = MagicMock(return_value=Context())
    monkeypatch.setattr(identity, "ManagedIdentityCredential", cred_factory)
    monkeypatch.setattr(projects, "AIProjectClient", project_factory)
    monkeypatch.setattr(httpx, "AsyncClient", http_factory)
    monkeypatch.setattr(caller, "version", lambda name: caller.PINS[name])
    monkeypatch.delenv("AZURE_FEDERATED_TOKEN_FILE", raising=False)
    headers = {"x-ms-client-request-id": request.run_id}
    result = asyncio.run(caller._bounded_create(request, headers))
    assert result.usage.total_tokens == 26
    assert cred_factory.call_args.kwargs["client_id"] is None
    args = cred_factory.call_args.kwargs
    assert all(args[key] == 0 for key in ("retry_total", "retry_connect", "retry_read", "retry_status"))
    policy = project_factory.call_args.kwargs["retry_policy"]
    assert policy.total_retries == 0
    assert policy.connect_retries == policy.read_retries == policy.status_retries == 0
    for factory in (cred_factory, project_factory):
        assert factory.call_args.kwargs["connection_timeout"] == 5
        assert factory.call_args.kwargs["read_timeout"] == 20
    assert project_factory.call_args.kwargs["api_version"] == "v1"
    assert project_factory.call_args.kwargs["endpoint"] == request.endpoint
    assert project_factory.call_args.kwargs["credential"] is credential
    args = project.get_openai_client.call_args.kwargs
    assert args["max_retries"] == 0
    assert args["timeout"].connect == 5 and args["timeout"].read == 20
    assert http_factory.call_args.kwargs["trust_env"] is False
    assert http_factory.call_args.kwargs["follow_redirects"] is False
    client.responses.create.assert_awaited_once_with(**request.envelope(), extra_headers=headers)


@pytest.mark.parametrize("failure", ["pin", "federated_file"])
def test_sdk_preflight_rejects_before_credential_construction(spec, monkeypatch, failure):
    from azure.identity import aio as identity
    factory = MagicMock(side_effect=AssertionError("credential must not be constructed"))
    monkeypatch.setattr(identity, "ManagedIdentityCredential", factory)
    monkeypatch.setattr(caller, "version", lambda name: "invalid" if failure == "pin" else caller.PINS[name])
    if failure == "federated_file":
        monkeypatch.setenv("AZURE_FEDERATED_TOKEN_FILE", "must-never-be-opened")
    with pytest.raises(caller.CallerError, match="sdk_pin_mismatch|workload_identity_not_authorized"):
        asyncio.run(caller._sdk_create(spec, {}))
    factory.assert_not_called()


@pytest.mark.parametrize("status", [200, 429, 500])
def test_pinned_sdk_real_wire_envelope_no_retry_and_mock_auth(spec, monkeypatch, status):
    """Real pinned Azure/OpenAI clients, fake credential and in-memory HTTP transport."""
    import httpx
    from azure.identity import aio as identity
    from azure.core.credentials import AccessToken

    sent = []

    class FakeCredential:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get_token(self, *scopes, **kwargs):
            assert scopes == ("https://ai.azure.com/.default",)
            return AccessToken("offline-test-only-not-a-credential", 9999999999)

    def handle(req):
        sent.append(req)
        assert req.method == "POST"
        assert str(req.url) == spec.endpoint + "/openai/v1/responses"
        body = json.loads(req.content)
        envelope = spec.envelope()
        expected = {key: value for key, value in envelope.items() if key != "extra_body"}
        expected.update(envelope["extra_body"])
        assert body == expected
        assert caller.digest(body) == spec.binding()["request_sha256"]
        assert req.headers["x-ms-client-request-id"] == spec.run_id
        if status != 200:
            return httpx.Response(status, json={"error": {"message": "not logged", "type": "test"}})
        return httpx.Response(200, json={
            "id": "resp_synthetic_wire", "object": "response", "created_at": 1,
            "status": "completed", "model": "synthetic-model",
            "output": [{"type": "message", "id": "msg_synthetic", "status": "completed",
                        "role": "assistant", "content": [
                            {"type": "output_text", "text": "Synthetic.", "annotations": []}
                        ]}],
            "parallel_tool_calls": False, "tools": [], "tool_choice": "none",
            "usage": {"input_tokens": 17, "output_tokens": 9, "total_tokens": 26},
        })

    monkeypatch.setattr(identity, "ManagedIdentityCredential", lambda **kwargs: FakeCredential())
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **kwargs: httpx.MockTransport(handle))
    monkeypatch.delenv("AZURE_FEDERATED_TOKEN_FILE", raising=False)
    if status == 200:
        result = asyncio.run(caller._bounded_create(spec, {"x-ms-client-request-id": spec.run_id}))
        assert caller.actual_usage(result) == {"input_tokens": 17, "output_tokens": 9, "total_tokens": 26}
        assert result.output_text == "Synthetic."
    else:
        with pytest.raises(Exception):
            asyncio.run(caller._bounded_create(spec, {"x-ms-client-request-id": spec.run_id}))
    assert len(sent) == 1


def test_windows_directory_rename_blocked_during_intent(root, spec):
    if os.name != "nt":
        pytest.skip("Windows-specific no-delete-sharing handle")
    with caller.Ledger(root, spec):
        with pytest.raises(OSError):
            (root / caller.LEDGER_NAME).rename(root / "replaced-ledger")
