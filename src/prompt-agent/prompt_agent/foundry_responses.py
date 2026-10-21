"""Minimal real Foundry Responses caller with an explicitly offline dry-run."""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
import logging
import os
from pathlib import Path
import re
import stat
import sys
import threading
import uuid

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

PINS = {
    "azure-ai-projects": "2.0.0", "azure-identity": "1.26.0",
    "openai": "2.26.0", "azure-core": "1.41.0",
}
FIXTURE = "SYNTHETIC DEMO ONLY. Reply with one short sentence: this is a fabricated benefits enquiry."
MAX_OUTPUT_TOKENS = 1024
OVERALL_SECONDS = 60
LEDGER_NAME = ".foundry-live-receipts"
SAFE_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
ENDPOINT = re.compile(
    r"https://[a-z0-9-]+\.services\.ai\.azure\.com/api/projects/[A-Za-z0-9_-]+\Z"
)
_logging_lock = threading.Lock()
_logging_users = 0
_logging_previous = 0


class CallerError(Exception):
    """Only fixed, content-free error codes may cross the CLI boundary."""


@contextmanager
def _quiet_dependency_logs():
    global _logging_users, _logging_previous
    with _logging_lock:
        if _logging_users == 0:
            _logging_previous = logging.root.manager.disable
            logging.disable(sys.maxsize)
        _logging_users += 1
    try:
        yield
    finally:
        with _logging_lock:
            _logging_users -= 1
            if _logging_users == 0:
                logging.disable(_logging_previous)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


@dataclass(frozen=True)
class Request:
    endpoint: str
    agent_name: str
    agent_version: str
    run_id: str
    authorization_reference: str
    executor_reference: str
    managed_identity_client_id: str | None = None

    def validate(self) -> None:
        if not ENDPOINT.fullmatch(self.endpoint):
            raise CallerError("invalid_project_endpoint")
        for label in (self.agent_name, self.authorization_reference, self.executor_reference):
            if not SAFE_LABEL.fullmatch(label):
                raise CallerError("invalid_nonsecret_reference")
        if not re.fullmatch(r"[1-9][0-9]{0,9}", self.agent_version):
            raise CallerError("exact_numeric_agent_version_required")
        try:
            if str(uuid.UUID(self.run_id)) != self.run_id:
                raise ValueError()
            if self.managed_identity_client_id:
                uuid.UUID(self.managed_identity_client_id)
        except ValueError:
            raise CallerError("invalid_identity") from None

    def envelope(self) -> dict:
        return {
            "input": FIXTURE,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "stream": False,
            "background": False,
            "tools": [],
            "tool_choice": "none",
            "extra_body": {
                "agent_reference": {
                    "type": "agent_reference",
                    "name": self.agent_name,
                    "version": self.agent_version,
                }
            },
        }

    def binding(self) -> dict:
        envelope = self.envelope()
        wire_body = {key: value for key, value in envelope.items() if key != "extra_body"}
        wire_body.update(envelope["extra_body"])
        return {
            "schema": 1,
            "endpoint": self.endpoint,
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "run_id": self.run_id,
            "authorization_reference": self.authorization_reference,
            "executor_reference": self.executor_reference,
            "managed_identity_client_id": self.managed_identity_client_id,
            "fixture_sha256": hashlib.sha256(FIXTURE.encode("ascii")).hexdigest(),
            "request_sha256": digest(wire_body),
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "overall_timeout_seconds": OVERALL_SECONDS,
            "client_retries": 0,
        }


def repository_root() -> Path:
    # Source and editable installs only: never put receipts in a user profile/site-packages.
    root = Path(__file__).absolute().parents[3]
    if not (root / "src" / "prompt-agent" / "pyproject.toml").is_file() or not (root / ".git").exists():
        raise CallerError("repository_source_checkout_required")
    return root


def _plain_directory(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or path.is_symlink() or (
        getattr(info, "st_file_attributes", 0) & 0x400
    ):
        raise CallerError("unsafe_receipt_directory")


@contextmanager
def _pin_directory(path: Path):
    """On Windows, deny directory deletion/rename while the ledger is in use."""
    _plain_directory(path)
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            yield fd
        finally:
            os.close(fd)
        return
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    handle = create(str(path), 0x80000000, 0x3, None, 3, 0x02200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise CallerError("receipt_directory_lock_failed")
    try:
        _plain_directory(path)
        yield None
    finally:
        close(handle)


class Ledger:
    """Immutable exclusive intent + exclusive outcome; neither is ever replaced/deleted."""

    def __init__(self, root: Path, request: Request):
        self.root = root.absolute()
        self.path = self.root / LEDGER_NAME
        self.request = request
        self.stack = ExitStack()
        self.dir_fd = None

    def __enter__(self):
        try:
            # The supplied checkout root is trusted; never inspect or pin host ancestors.
            self.stack.enter_context(_pin_directory(self.root))
            try:
                self.path.mkdir(mode=0o700)
            except FileExistsError:
                pass
            self.dir_fd = self.stack.enter_context(_pin_directory(self.path))
            self.key = digest(self.request.authorization_reference)
            if os.path.lexists(self.path / ("authorization-" + self.key + ".receipt.json")):
                raise CallerError("existing_intent_or_receipt_refused")
            binding = self.request.binding()
            intent = {"status": "inflight", "binding": binding, "binding_sha256": digest(binding)}
            # Run ID and authorization are separately single-use. A partial claim is a tombstone.
            self.write("run-" + self.request.run_id + ".json", intent)
            self.write("authorization-" + self.key + ".intent.json", intent)
            if os.path.lexists(self.path / ("authorization-" + self.key + ".receipt.json")):
                raise CallerError("existing_intent_or_receipt_refused")
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *args):
        self.stack.close()

    def write(self, name: str, data: dict) -> None:
        _plain_directory(self.path)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        kwargs = {"dir_fd": self.dir_fd} if self.dir_fd is not None else {}
        target = name if kwargs else self.path / name
        try:
            fd = os.open(target, flags, 0o600, **kwargs)
        except FileExistsError:
            raise CallerError("existing_intent_or_receipt_refused") from None
        try:
            with os.fdopen(fd, "wb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise CallerError("unsafe_receipt_file")
                stream.write(canonical(data) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            if self.dir_fd is not None:
                os.fsync(self.dir_fd)
        except BaseException:
            # Never remove an empty/partial intent: persistence uncertainty blocks replay.
            raise

    def finish(self, data: dict) -> None:
        self.write("authorization-" + self.key + ".receipt.json", data)


def actual_usage(response) -> dict:
    usage = response.usage
    if usage is None:
        raise CallerError("missing_or_invalid_actual_usage")
    counts = {key: getattr(usage, key, None) for key in ("input_tokens", "output_tokens", "total_tokens")}
    if any(type(value) is not int or value < 0 for value in counts.values()):
        raise CallerError("missing_or_invalid_actual_usage")
    if counts["total_tokens"] != counts["input_tokens"] + counts["output_tokens"]:
        raise CallerError("missing_or_invalid_actual_usage")
    if counts["output_tokens"] > MAX_OUTPUT_TOKENS or counts["input_tokens"] > 1024:
        raise CallerError("actual_usage_exceeds_approved_bound")
    return counts


async def _sdk_create(request: Request, headers: dict):
    # Imports and all credential construction happen only after durable intent.
    import httpx
    from azure.ai.projects.aio import AIProjectClient
    from azure.core.pipeline.policies import AsyncRetryPolicy
    from azure.identity.aio import ManagedIdentityCredential

    for package, expected in PINS.items():
        if version(package) != expected:
            raise CallerError("sdk_pin_mismatch")
    if os.environ.get("AZURE_FEDERATED_TOKEN_FILE"):
        raise CallerError("workload_identity_not_authorized")
    timeout = httpx.Timeout(20, connect=5, read=20, write=10, pool=5)
    retry = dict(retry_total=0, retry_connect=0, retry_read=0, retry_status=0)
    async with (
        ManagedIdentityCredential(
            client_id=request.managed_identity_client_id,
            **retry,
            connection_timeout=5, read_timeout=20,
        ) as credential,
        AIProjectClient(
            endpoint=request.endpoint, credential=credential, api_version="v1",
            retry_policy=AsyncRetryPolicy(**retry),
            connection_timeout=5, read_timeout=20, logging_enable=False,
        ) as project,
        httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(retries=0),
            timeout=timeout, trust_env=False, follow_redirects=False,
        ) as http_client,
        project.get_openai_client(
            max_retries=0, timeout=timeout, http_client=http_client,
        ) as client,
    ):
        return await client.responses.create(**request.envelope(), extra_headers=headers)


async def _bounded_create(request: Request, headers: dict):
    return await asyncio.wait_for(_sdk_create(request, headers), timeout=OVERALL_SECONDS)


def invoke(request: Request, *, allow_live: bool = False) -> dict:
    if not allow_live:
        raise CallerError("explicit_live_opt_in_required")
    request.validate()
    root = repository_root()
    try:
        # SDK error messages/debug logging can contain raw service bodies.
        with _quiet_dependency_logs(), Ledger(root, request) as ledger:
            binding_sha = digest(request.binding())
            outcome = {"status": "ambiguous", "binding_sha256": binding_sha, "run_id": request.run_id}
            try:
                tracer = trace.get_tracer(__name__)
                parent = trace.get_current_span().get_span_context()
                if parent.is_valid:
                    outcome["client_parent_span_id"] = f"{parent.span_id:016x}"
                with tracer.start_as_current_span(
                    "prompt_agent.responses.create", kind=SpanKind.CLIENT,
                    record_exception=False, set_status_on_exception=False,
                    attributes={
                        "correlation.id": request.run_id,
                        "foundry.agent.name": request.agent_name,
                        "foundry.agent.version": request.agent_version,
                        "demo.telemetry.source": "local_client_not_native_agent",
                    },
                ) as span:
                    context = span.get_span_context()
                    headers = {"x-ms-client-request-id": request.run_id}
                    if context.is_valid:
                        # W3C client context only; provider propagation is not asserted.
                        headers["traceparent"] = (
                            f"00-{context.trace_id:032x}-{context.span_id:016x}-{int(context.trace_flags):02x}"
                        )
                        outcome["client_trace_id"] = f"{context.trace_id:032x}"
                        outcome["client_span_id"] = f"{context.span_id:016x}"
                    try:
                        response = asyncio.run(_bounded_create(request, headers))
                        usage = actual_usage(response)
                        if response.status != "completed":
                            raise CallerError("response_not_completed")
                        if not isinstance(response.id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", response.id):
                            raise CallerError("invalid_response_identifier")
                        text = response.output_text
                        if not isinstance(text, str) or not text or len(text.encode("utf-8")) > 16384:
                            raise CallerError("missing_or_unbounded_synthetic_output")
                        outcome.update(status="succeeded", response_id=response.id, usage=usage)
                        for attr, field in (
                            ("prompt", "input_tokens"), ("completion", "output_tokens"), ("total", "total_tokens")
                        ):
                            span.set_attribute("llm.token_count." + attr, usage[field])
                        ledger.finish(outcome)
                        span.set_status(Status(StatusCode.OK))
                    except BaseException:
                        span.set_status(Status(StatusCode.ERROR, "once_only_request_failed"))
                        raise
                return outcome
            except BaseException:
                # Includes timeout, cancellation, auth/provider/usage and success-receipt errors.
                # If this write also fails, the immutable inflight intent still blocks replay.
                try:
                    ledger.finish({
                        "status": "ambiguous", "binding_sha256": binding_sha, "run_id": request.run_id,
                    })
                except BaseException:
                    pass
                raise CallerError("attempt_ambiguous_no_retry") from None
    except CallerError:
        raise
    except BaseException:
        raise CallerError("receipt_or_execution_failed_no_retry") from None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Once-only no-tool Foundry Responses caller; --dry-run is strictly offline")
    parser.add_argument("--endpoint", required=True, help="Nonsecret project endpoint; no trailing slash")
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--agent-version", required=True, help="Exact positive numeric version, never latest")
    parser.add_argument("--run-id", required=True, help="Fresh lowercase UUID; correlation/request ID")
    parser.add_argument("--authorization-reference", required=True, help="Fresh approved nonsecret receipt reference")
    parser.add_argument("--executor-reference", required=True, help="Approved private runner/MI custody reference, nonsecret")
    parser.add_argument("--managed-identity-client-id", help="Approved user-assigned MI client UUID; omit for system MI")
    parser.add_argument("--allow-live", action="store_true", help="Explicitly permit ONE paid create; never retry")
    parser.add_argument("--dry-run", action="store_true", help="Offline validation/hash only; no auth, SDK client or ledger")
    args = parser.parse_args(argv)
    request = Request(
        args.endpoint, args.agent_name, args.agent_version, args.run_id,
        args.authorization_reference, args.executor_reference, args.managed_identity_client_id,
    )
    try:
        request.validate()
        if args.dry_run:
            print(json.dumps({"status": "offline_dry_run", "binding_sha256": digest(request.binding())}))
            return 0
        result = invoke(request, allow_live=args.allow_live)
        print(json.dumps(result, sort_keys=True))
        return 0
    except CallerError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
