"""Synthetic restart/race/fault tests through the actual Blob adapter."""
from __future__ import annotations

import copy
import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from azure.core import MatchConditions
from azure.core.exceptions import (
    AzureError, ResourceExistsError, ResourceModifiedError, ResourceNotFoundError,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

from telemetry_pipeline.durable import (
    ACK_SECONDS, CLAIM_SECONDS, JOIN_SECONDS, MAX_CANDIDATES_PER_SIDE,
    MAX_MESSAGE_BYTES, MAX_RECORD_BYTES, MAX_RECORDS_PER_MESSAGE,
    MAX_SEND_ATTEMPTS, MAX_SENDS_PER_DRAIN, ORPHAN_SECONDS,
    AdmissionError, Correlator, Scope,
)
from telemetry_pipeline.durable_store import BlobLedger, MAX_LEDGER_BYTES
from telemetry_pipeline.strict_sender import Delivery

from .conftest import make_record

SCOPE = Scope("synthetic-workspace", "/synthetic/component", "synthetic-project", "synthetic-space")
TRACE = "0af7651916cd43dd8448eb211c80319c"
SPAN = "b7ad6b7169203331"


def messages(text="synthetic message"):
    return [{"role": "user", "parts": [{"type": "text", "content": text}]}]


def original(**overrides):
    record = make_record(customDimensions={"openinference.span.kind": "LLM"})
    record.update(TenantId=SCOPE.workspace, _ResourceId=SCOPE.component)
    record.update(overrides)
    return record


def content(**overrides):
    record = {
        "Type": "AppGenAIContent", "TenantId": SCOPE.workspace,
        "_ResourceId": SCOPE.component, "TraceId": TRACE, "SpanId": SPAN,
        "Id": "synthetic-content-id-not-a-span", "TimeGenerated": "2020-01-01T00:00:00.123456789Z",
        "InputMessages": json.dumps(messages()), "OutputMessages": json.dumps(messages("synthetic answer")),
    }
    record.update(overrides)
    return record


class FakeContainer:
    """Implements conditional Blob calls, not a second correlation algorithm."""

    def __init__(self):
        self.data = {}
        self.tags = {}
        self.lock = threading.RLock()
        self.sequence = 0
        self.fail_write = False
        self.fail_ack = False
        self.fail_after_commit = False
        self.fail_reads = set()
        self.forced_conflicts = 0
        self.downloads = []
        self.scans = []

    def get_blob_client(self, key):
        return FakeBlob(self, key)

    def find_blobs_by_tags(self, *, filter_expression, results_per_page, **kwargs):
        container = self
        scope, cutoff = re.fullmatch(
            r"""["]scope["] = '([0-9a-f]{64})' AND ["]due["] <= '([0-9]+)'""",
            filter_expression,
        ).groups()

        def eligible(key):
            tags = container.tags.get(key, {})
            return tags.get("scope") == scope and "due" in tags and tags["due"] <= cutoff

        class Listing:
            def by_page(self, continuation_token=None):
                with container.lock:
                    keys = sorted(key for key in container.data if eligible(key))
                keys = [key for key in keys if continuation_token is None or key > continuation_token]
                page = keys[:results_per_page]
                self.continuation_token = page[-1] if len(keys) > len(page) else None
                container.scans.append((continuation_token, len(page)))
                return self

            def __next__(self):
                with container.lock:
                    keys = sorted(key for key in container.data if eligible(key))
                cursor = container.scans[-1][0]
                keys = [key for key in keys if cursor is None or key > cursor]
                return iter(SimpleNamespace(name=key) for key in keys[:results_per_page])

        return Listing()


class FakeBlob:
    def __init__(self, container, key):
        self.c = container
        self.key = key

    def get_blob_properties(self, **kwargs):
        with self.c.lock:
            if self.key in self.c.fail_reads:
                raise AzureError("synthetic read fault")
            if self.key not in self.c.data:
                raise ResourceNotFoundError()
            payload, etag = self.c.data[self.key]
            return SimpleNamespace(size=len(payload), etag=etag)

    def download_blob(self, *, etag, match_condition, length, **kwargs):
        assert match_condition == MatchConditions.IfNotModified
        with self.c.lock:
            payload, actual = self.c.data[self.key]
            if actual != etag:
                raise ResourceModifiedError()
            self.c.downloads.append(length)
            return SimpleNamespace(readall=lambda: payload[:length])

    def upload_blob(self, payload, *, overwrite, **kwargs):
        with self.c.lock:
            if self.c.fail_write:
                raise AzureError("synthetic write fault")
            if self.c.fail_ack and json.loads(payload).get("state") == "acknowledged":
                raise AzureError("synthetic ack fault")
            if self.c.forced_conflicts:
                self.c.forced_conflicts -= 1
                raise ResourceModifiedError()
            existing = self.c.data.get(self.key)
            if not overwrite and existing:
                raise ResourceExistsError()
            if overwrite:
                assert kwargs["match_condition"] == MatchConditions.IfNotModified
                if existing is None or kwargs["etag"] != existing[1]:
                    raise ResourceModifiedError()
            self.c.sequence += 1
            self.c.data[self.key] = (payload, str(self.c.sequence))
            self.c.tags[self.key] = kwargs["tags"]
            if self.c.fail_after_commit:
                self.c.fail_after_commit = False
                raise AzureError("synthetic uncertain admission commit")

    def delete_blob(self, *, etag, match_condition, **kwargs):
        assert match_condition == MatchConditions.IfNotModified
        with self.c.lock:
            existing = self.c.data.get(self.key)
            if existing is None:
                raise ResourceNotFoundError()
            if existing[1] != etag:
                raise ResourceModifiedError()
            del self.c.data[self.key]
            self.c.tags.pop(self.key, None)


class Sender:
    def __init__(self, result=Delivery.CONFIRMED, callback=None):
        self.payloads = []
        self.result = result
        self.callback = callback

    def send(self, payload):
        self.payloads.append(payload)
        if self.callback:
            self.callback()
        return self.result


def decoded(payload):
    request = ExportTraceServiceRequest()
    request.ParseFromString(payload)
    resource = request.resource_spans[0]
    span = resource.scope_spans[0].spans[0]
    attrs = {attr.key: attr.value for attr in span.attributes}
    return span, attrs, resource.resource


@pytest.fixture
def rig():
    container = FakeContainer()
    now = [1000.0]
    store = BlobLedger(container)
    engine = Correlator(store, SCOPE, clock=lambda: now[0])
    return engine, store, container, now


@pytest.mark.parametrize("content_first", [True, False])
def test_cross_batch_restart_join_and_original_fidelity(rig, content_first):
    engine, store, container, now = rig
    source = original(customDimensions={
        "openinference.span.kind": "LLM", "correlation.id": "synthetic-request",
        "llm.token_count.prompt": "7", "llm.token_count.completion": "3",
    })
    first, second = (content(), source) if content_first else (source, content())
    engine.admit_batch([json.dumps(first)])
    sender = Sender()
    engine.drain(sender)
    assert sender.payloads == []
    restarted = Correlator(BlobLedger(container), SCOPE, clock=lambda: now[0])
    restarted.admit_batch([json.dumps({"records": [second]})])
    restarted.drain(sender)
    assert len(sender.payloads) == 1
    span, attrs, resource = decoded(sender.payloads[0])
    assert span.trace_id.hex() == TRACE and span.span_id.hex() == SPAN
    assert span.parent_span_id == b""
    assert span.start_time_unix_nano == 1791028800000000000
    assert span.end_time_unix_nano - span.start_time_unix_nano == 123456000
    assert attrs["correlation.id"].string_value == "synthetic-request"
    assert attrs["llm.token_count.prompt"].int_value == 7
    assert attrs["llm.token_count.completion"].int_value == 3
    assert "llm.token_count.total" not in attrs
    assert json.loads(attrs["input.value"].string_value) == messages()
    assert json.loads(attrs["output.value"].string_value) == messages("synthetic answer")
    assert {a.key: a.value.string_value for a in resource.attributes}["openinference.project.name"] == SCOPE.project


@pytest.mark.parametrize("table", ["AppDependencies", "AppRequests"])
def test_native_root_aliases_and_nanoseconds_survive_durable_enrichment(rig, table):
    engine, _, _, _ = rig
    source = {
        "Type": table, "OperationId": TRACE, "Id": SPAN,
        "ParentId": TRACE if table == "AppDependencies" else "",
        "Name": "synthetic.native.invoke", "Success": True,
        "TimeGenerated": "2026-10-03T12:00:00.123456789Z", "DurationMs": 2.5,
        "Properties": json.dumps({
            "gen_ai.operation.name": "chat", "gen_ai.usage.input_tokens": "7",
        }),
        "TenantId": SCOPE.workspace, "_ResourceId": SCOPE.component,
        "AppRoleName": "synthetic-agent",
    }
    engine.admit(content())
    key = engine.admit(source)
    sender = Sender()
    engine.drain_key(key, sender)
    span, attrs, resource = decoded(sender.payloads[0])
    assert span.parent_span_id == b""
    assert span.start_time_unix_nano == 1791028800123456789
    assert span.end_time_unix_nano - span.start_time_unix_nano == 2500000
    assert attrs["llm.token_count.prompt"].int_value == 7
    assert json.loads(attrs["input.value"].string_value) == messages()
    assert {a.key: a.value.string_value for a in resource.attributes}["service.name"] == "synthetic-agent"


def test_per_side_precedence_empty_explicit_and_invalid_inline_fallback(rig):
    engine, store, container, now = rig
    engine.admit(content())
    key = engine.admit(original(customDimensions={
        "openinference.span.kind": "LLM", "input.value": "", "input.mime_type": "text/plain",
        "gen_ai.input.messages": messages("unused inline"),
        "gen_ai.output.messages": "{truncated", "output.mime_type": "stale/mime",
    }))
    sender = Sender()
    engine.drain_key(key, sender)
    _, attrs, _ = decoded(sender.payloads[0])
    assert attrs["input.value"].string_value == ""
    assert attrs["input.mime_type"].string_value == "text/plain"
    assert json.loads(attrs["output.value"].string_value) == messages("synthetic answer")
    assert attrs["output.mime_type"].string_value == "application/json"


@pytest.mark.parametrize("dimensions", [
    {"openinference.span.kind": "AGENT", "gen_ai.input.messages": [], "gen_ai.output.messages": []},
    {"openinference.span.kind": "LLM", "input.value": "", "output.value": ""},
    {"openinference.span.kind": "TOOL"},
    {"openinference.span.kind": "CHAIN"},
    {},
])
def test_complete_inline_or_non_genai_bypasses_join_wait(rig, dimensions):
    engine, _, _, _ = rig
    key = engine.admit(original(customDimensions=dimensions))
    sender = Sender()
    engine.drain_key(key, sender)
    assert len(sender.payloads) == 1


def test_inline_messages_win_over_different_content(rig):
    engine, _, _, _ = rig
    engine.admit(content())
    key = engine.admit(original(customDimensions={
        "gen_ai.operation.name": "chat", "gen_ai.input.messages": messages("inline"),
        "gen_ai.output.messages": [],
    }))
    sender = Sender()
    engine.drain_key(key, sender)
    _, attrs, _ = decoded(sender.payloads[0])
    assert json.loads(attrs["input.value"].string_value) == messages("inline")
    assert json.loads(attrs["output.value"].string_value) == []


def test_receipt_deadline_not_event_time_or_duplicate_and_partial_content(rig, caplog):
    engine, store, _, now = rig
    engine.admit(content(OutputMessages=None))
    now[0] += 200
    key = engine.admit(original())
    deadline = store.read(key).value["deadline"]
    assert deadline == now[0] + JOIN_SECONDS
    now[0] += JOIN_SECONDS - 1
    engine.admit(original())
    assert store.read(key).value["deadline"] == deadline
    sender = Sender()
    engine.drain_key(key, sender)
    assert not sender.payloads
    now[0] += 1
    with caplog.at_level(logging.INFO):
        engine.drain_key(key, sender)
    assert "deadline_missing" in caplog.text
    _, attrs, _ = decoded(sender.payloads[0])
    assert "input.value" in attrs and "output.value" not in attrs


def test_cas_contention_uses_successful_admission_clock_not_initial_attempt(rig, monkeypatch):
    engine, store, _, now = rig
    cas = store.cas
    failures = [2]

    def contended(key, etag, value):
        if failures[0]:
            failures[0] -= 1
            now[0] += 10
            return False
        return cas(key, etag, value)

    monkeypatch.setattr(store, "cas", contended)
    key = engine.admit(original())
    assert store.read(key).value["admitted"] == 1020
    assert store.read(key).value["deadline"] == 1020 + JOIN_SECONDS


def test_content_identity_never_uses_id_parent_and_trace_are_isolated(rig, caplog):
    engine, store, _, now = rig
    key = engine.admit(original(operation_ParentId="1234567890abcdef"))
    engine.admit(content(ParentSpanId="fedcba0987654321"))
    other = engine.admit(content(TraceId="1" * 32))
    assert other != key
    now[0] += JOIN_SECONDS
    sender = Sender()
    with caplog.at_level(logging.INFO):
        engine.drain_key(key, sender)
    span, attrs, _ = decoded(sender.payloads[0])
    assert span.parent_span_id.hex() == "1234567890abcdef"
    assert "input.value" not in attrs and "output.value" not in attrs
    assert "parent_mismatch" in caplog.text
    assert store.read(other).value["original"] is None


@pytest.mark.parametrize("changes", [
    {"SpanId": None, "Id": SPAN},
    {"TraceId": "0" * 32},
    {"ParentSpanId": "bad-parent"},
    {"TimeGenerated": "2026-01-01T00:00:00"},
    {"TimeGenerated": "invalid"},
    {"_ResourceId": "/wrong/source"},
    {"TenantId": "wrong-workspace"},
])
def test_invalid_content_does_not_suppress_valid_original(rig, changes, caplog):
    engine, _, _, _ = rig
    with caplog.at_level(logging.INFO):
        count = engine.admit_batch([json.dumps([
            content(**changes), original(customDimensions={"openinference.span.kind": "TOOL"}),
        ])])
    sender = Sender()
    engine.drain(sender)
    assert count == 1 and len(sender.payloads) == 1
    assert "malformed_or_disallowed_content" in caplog.text


def test_namespace_includes_source_and_destination(rig):
    engine, store, _, now = rig
    first = engine.admit(original())
    for field, value in (("workspace", "another-workspace"), ("component", "/another-component"),
                         ("project", "another-project"), ("destination", "another-space")):
        scope = Scope(**{**SCOPE.__dict__, field: value})
        other = Correlator(store, scope, clock=lambda: now[0])
        source = original(TenantId=scope.workspace, _ResourceId=scope.component)
        assert other.admit(source) != first
    with pytest.raises(AdmissionError, match="source_not_allowed"):
        engine.admit(original(TenantId="another-workspace"))


def test_duplicates_canonical_arrays_conflict_per_side_and_cap_atomicity(rig, caplog):
    engine, store, _, now = rig
    first = content()
    key = engine.admit(first)
    reordered = [{"parts": [{"content": "synthetic message", "type": "text"}], "role": "user"}]
    engine.admit(content(Id="another-id", InputMessages=reordered))
    assert len(store.read(key).value["candidates"]["input"]) == 1
    engine.admit(content(InputMessages=messages("different")))
    engine.admit(original())
    now[0] += JOIN_SECONDS
    sender = Sender()
    with caplog.at_level(logging.INFO):
        engine.drain_key(key, sender)
    _, attrs, _ = decoded(sender.payloads[0])
    assert "input.value" not in attrs and "output.value" in attrs
    assert "conflict" in caplog.text
    # A separate pending key demonstrates all-or-nothing candidate admission.
    for index in range(MAX_CANDIDATES_PER_SIDE):
        capped = content(SpanId="1" * 16, InputMessages=messages(str(index)))
        cap_key = engine.admit(capped)
    before = store.read(cap_key)
    with pytest.raises(AdmissionError, match="candidate_limit"):
        engine.admit(content(SpanId="1" * 16, InputMessages=messages("overflow")))
    assert store.read(cap_key) == before


def test_ack_removes_all_content_and_suppresses_late_and_replay_for_48h(rig, caplog):
    engine, store, _, now = rig
    engine.admit(content())
    key = engine.admit(original())
    sender = Sender()
    engine.drain_key(key, sender)
    assert set(store.read(key).value) == {"state", "acknowledged", "expires"}
    with caplog.at_level(logging.INFO):
        engine.admit(content(InputMessages=messages("late synthetic")))
        engine.admit(original())
    now[0] += ACK_SECONDS - 1
    engine.drain_key(key, sender)
    assert store.read(key).value["state"] == "acknowledged"
    assert len(sender.payloads) == 1 and "late" in caplog.text
    now[0] += 1
    engine.drain_key(key, sender)
    assert store.read(key) is None


def test_orphan_expires_without_sending_and_duplicate_does_not_reset_age(rig, caplog):
    engine, store, _, now = rig
    key = engine.admit(content())
    now[0] += ORPHAN_SECONDS - 1
    engine.admit(content())
    sender = Sender()
    engine.drain_key(key, sender)
    assert store.read(key) is not None
    now[0] += 1
    with caplog.at_level(logging.INFO):
        engine.drain_key(key, sender)
    assert store.read(key) is None and sender.payloads == []
    assert "orphan_expired" in caplog.text


@pytest.mark.parametrize("outcome", [Delivery.AMBIGUOUS, Delivery.REJECTED])
def test_uncertain_or_definitively_rejected_work_retained_without_ttl_resend(rig, outcome):
    engine, store, _, now = rig
    key = engine.admit(original(customDimensions={"input.value": "", "output.value": ""}))
    sender = Sender(outcome)
    engine.drain_key(key, sender)
    frozen = copy.deepcopy(store.read(key).value)
    now[0] += ACK_SECONDS * 100
    engine.admit(content())
    engine.drain_key(key, sender)
    assert store.read(key).value == frozen and len(sender.payloads) == 1
    assert frozen["state"] == ("ambiguous" if outcome == Delivery.AMBIGUOUS else "rejected")
    assert frozen["wire"] and frozen["original"] is not None


def test_definitive_throttling_retries_frozen_payload_with_finite_backoff(rig):
    engine, store, _, now = rig
    key = engine.admit(original(customDimensions={"input.value": "", "output.value": ""}))
    sender = Sender(Delivery.RETRYABLE_REJECTION)
    engine.drain_key(key, sender)
    first = store.read(key).value
    engine.admit(content())
    engine.drain_key(key, sender)
    assert len(sender.payloads) == 1
    for attempt in range(1, MAX_SEND_ATTEMPTS):
        now[0] = store.read(key).value["due"]
        engine.drain_key(key, sender)
    assert store.read(key).value["state"] == "rejected"
    assert len(sender.payloads) == MAX_SEND_ATTEMPTS
    assert len(set(sender.payloads)) == 1
    assert store.read(key).value["wire_hash"] == first["wire_hash"]


def test_ack_write_failure_and_stale_sending_quarantine_on_restart(rig):
    engine, store, container, now = rig
    key = engine.admit(original(customDimensions={"input.value": "", "output.value": ""}))
    container.fail_ack = True
    sender = Sender()
    with pytest.raises(AdmissionError, match="storage_write_failure"):
        engine.drain_key(key, sender)
    assert store.read(key).value["state"] == "sending"
    container.fail_ack = False
    restarted = Correlator(store, SCOPE, clock=lambda: now[0])
    restarted.drain_key(key, sender)
    now[0] += CLAIM_SECONDS
    restarted.drain_key(key, sender)
    assert store.read(key).value["state"] == "ambiguous"
    assert len(sender.payloads) == 1


def test_stale_worker_cannot_ack_after_another_worker_quarantines_its_claim(rig):
    engine, store, _, now = rig
    key = engine.admit(original(customDimensions={"input.value": "", "output.value": ""}))
    second = Correlator(store, SCOPE, clock=lambda: now[0])

    def stale_during_send():
        now[0] += CLAIM_SECONDS
        second.drain_key(key, Sender())

    sender = Sender(callback=stale_during_send)
    with pytest.raises(AdmissionError, match="send_claim_lost"):
        engine.drain_key(key, sender)
    assert store.read(key).value["state"] == "ambiguous"
    assert len(sender.payloads) == 1


def test_concurrent_admission_and_claims_do_not_lose_sides_or_send_twice(rig):
    engine, store, container, now = rig
    second = Correlator(BlobLedger(container), SCOPE, clock=lambda: now[0])
    key = engine.admit(original())
    container.forced_conflicts = 2
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(engine.admit, content(OutputMessages=None))
        b = pool.submit(second.admit, content(InputMessages=None))
        assert a.result() == key and b.result() == key
    entered, release = threading.Event(), threading.Event()

    def block():
        entered.set()
        assert release.wait(5)

    sender = Sender(callback=block)
    with ThreadPoolExecutor(max_workers=2) as pool:
        sending = pool.submit(engine.drain_key, key, sender)
        assert entered.wait(5)
        assert second.drain_key(key, sender) is False
        engine.admit(content(InputMessages=messages("late while sending")))
        release.set()
        sending.result()
    assert len(sender.payloads) == 1
    _, attrs, _ = decoded(sender.payloads[0])
    assert json.loads(attrs["input.value"].string_value) == messages()


def test_admission_failure_and_uncertain_commit_are_safe_to_replay(rig):
    engine, store, container, now = rig
    source = original()
    container.fail_write = True
    with pytest.raises(AdmissionError, match="durable_admission_failure"):
        engine.admit_batch([json.dumps(source)])
    assert not container.data
    container.fail_write = False
    container.fail_after_commit = True
    with pytest.raises(AdmissionError):
        engine.admit_batch([json.dumps(source)])
    now[0] += 100
    key = engine.admit(source)
    assert store.read(key).value["admitted"] == 1000
    container.forced_conflicts = 100
    with pytest.raises(AdmissionError, match="admission_contention"):
        engine.admit(content())


def test_record_and_blob_bounds_before_write_and_before_download(rig):
    engine, store, container, _ = rig
    with pytest.raises(AdmissionError, match="payload_limit"):
        engine.admit(original(extra="x" * MAX_RECORD_BYTES))
    assert not container.data
    container.data["oversized"] = (b"x" * (MAX_LEDGER_BYTES + 1), "1")
    with pytest.raises(AdmissionError, match="stored_payload_limit"):
        store.read("oversized")
    assert container.downloads == []
    key = engine.admit(original())
    engine.admit(content())
    assert all(length == MAX_LEDGER_BYTES + 1 for length in container.downloads)


def test_oversized_actual_wire_is_retained_pending_without_truncation_or_send(rig):
    engine, store, _, _ = rig
    key = engine.admit(original(Name="synthetic-" + "n" * 100000))
    engine.admit(content(InputMessages=messages("i" * 100000), OutputMessages=None))
    engine.admit(content(InputMessages=None, OutputMessages=messages("o" * 100000)))
    sender = Sender()
    with pytest.raises(AdmissionError, match="wire_payload_limit"):
        engine.drain_key(key, sender)
    assert store.read(key).value["state"] == "pending" and not sender.payloads


@pytest.mark.parametrize("oversized_message", [
    b"x" * (MAX_MESSAGE_BYTES + 1),
    json.dumps([{}] * (MAX_RECORDS_PER_MESSAGE + 1)),
], ids=["message-bytes", "message-record-count"])
def test_message_limits_fail_before_any_record_admission(rig, oversized_message, caplog):
    engine, _, container, _ = rig
    with caplog.at_level(logging.INFO), pytest.raises(AdmissionError, match="durable_admission_failure"):
        engine.admit_batch([oversized_message])
    assert not container.data
    assert "reason=message_" in caplog.text


def test_original_identity_conflict_does_not_replace_authoritative_span(rig):
    engine, store, _, _ = rig
    key = engine.admit(original())
    before = store.read(key)
    with pytest.raises(AdmissionError, match="original_identity_conflict"):
        engine.admit(original(Name="synthetic-different-operation"))
    assert store.read(key) == before


def test_blob_adapter_enforces_create_replace_delete_etags_and_read_races(rig, monkeypatch):
    _, store, container, _ = rig
    assert store.read("synthetic-key") is None
    assert store.cas("synthetic-key", None, {"value": 1})
    first = store.read("synthetic-key")
    assert not store.cas("synthetic-key", None, {"value": 2})
    assert store.cas("synthetic-key", first.etag, {"value": 2})
    second = store.read("synthetic-key")
    assert not store.cas("synthetic-key", first.etag, {"value": 3})
    assert not store.delete("synthetic-key", first.etag)
    download = FakeBlob.download_blob

    def raced_download(blob, **kwargs):
        store.cas(blob.key, second.etag, {"value": 3})
        return download(blob, **kwargs)

    monkeypatch.setattr(FakeBlob, "download_blob", raced_download)
    with pytest.raises(AdmissionError, match="read_contention"):
        store.read("synthetic-key")
    monkeypatch.setattr(FakeBlob, "download_blob", download)
    third = store.read("synthetic-key")
    assert store.delete("synthetic-key", third.etag)
    assert store.read("synthetic-key") is None


def test_partial_batch_failure_replays_without_resetting_successful_admission(rig, monkeypatch):
    engine, store, container, now = rig
    first, second = original(), original(id="1" * 16)
    cas = store.cas

    def fail_second(key, etag, value):
        if key.endswith("1" * 16):
            raise AdmissionError("synthetic_second_record_failure")
        return cas(key, etag, value)

    monkeypatch.setattr(store, "cas", fail_second)
    with pytest.raises(AdmissionError):
        engine.admit_batch([json.dumps([first, second])])
    now[0] += 50
    monkeypatch.setattr(store, "cas", cas)
    assert engine.admit_batch([json.dumps([first, second])]) == 2
    key = engine.admit(first)
    assert store.read(key).value["admitted"] == 1000
    assert len(container.data) == 2


def test_scan_cursor_fairness_caps_and_poison_work_progress(rig):
    engine, store, container, now = rig
    keys = []
    for index in range(1, 26):
        keys.append(engine.admit(original(id=f"{index:016x}")))
    # First page stays pending; a later page must still be scanned.
    sender = Sender()
    assert engine.drain(sender, limit=8) == 8
    ready = keys[9]
    engine.admit(content(SpanId=f"{10:016x}"))
    assert engine.drain(sender, limit=8) == 8
    assert store.read(ready).value["state"] == "acknowledged"
    container.fail_reads.add(keys[16])
    with pytest.raises(AdmissionError, match="durable_drain_failure"):
        engine.drain(sender, limit=8)
    # Poisoned third page did not pin the persisted cursor.
    assert engine.drain(sender, limit=8) == 1
    assert all(size <= 8 for _, size in container.scans)
    container.fail_reads.clear()
    now[0] += JOIN_SECONDS
    before = len(sender.payloads)
    engine.drain(sender)
    assert len(sender.payloads) - before == MAX_SENDS_PER_DRAIN
    with pytest.raises(AdmissionError, match="scan_limit"):
        engine.drain(sender, limit=10000)


def test_scan_send_budget_counts_failed_acknowledgments_and_still_advances(rig):
    engine, store, container, _ = rig
    keys = [
        engine.admit(original(
            id=f"{index:016x}", customDimensions={"input.value": "", "output.value": ""},
        ))
        for index in range(1, 26)
    ]
    container.fail_ack = True
    sender = Sender()
    with pytest.raises(AdmissionError, match="durable_drain_failure"):
        engine.drain(sender)
    assert len(sender.payloads) == MAX_SENDS_PER_DRAIN
    assert sum(store.read(key).value["state"] == "sending" for key in keys) == MAX_SENDS_PER_DRAIN
    with pytest.raises(AdmissionError):
        engine.drain(sender)
    assert len(sender.payloads) == 2 * MAX_SENDS_PER_DRAIN
    assert container.scans[1][0] is not None


def test_due_index_excludes_retained_tombstones_orphans_and_recovery_work(rig):
    engine, store, container, now = rig
    sender = Sender()
    for index in range(1, 81):
        key = engine.admit(original(
            id=f"{index:016x}", customDimensions={"input.value": "", "output.value": ""},
        ))
        engine.drain_key(key, sender)
    orphan = engine.admit(content(SpanId=f"{81:016x}"))
    waiting = engine.admit(original(id=f"{82:016x}"))
    engine.drain_key(waiting, sender)
    recovery = engine.admit(original(
        id=f"{83:016x}", customDimensions={"input.value": "", "output.value": ""},
    ))
    engine.drain_key(recovery, Sender(Delivery.AMBIGUOUS))
    ready = engine.admit(original(
        id=f"{84:016x}", customDimensions={"input.value": "", "output.value": ""},
    ))
    before = len(sender.payloads)
    assert engine.drain(sender) == 1
    assert len(sender.payloads) == before + 1
    assert store.read(ready).value["state"] == "acknowledged"
    assert store.read(orphan).value["original"] is None
    assert store.read(waiting).value["state"] == "pending"
    assert store.read(recovery).value["state"] == "ambiguous"
    now[0] += JOIN_SECONDS
    assert engine.drain(sender) == 1
    assert store.read(waiting).value["state"] == "acknowledged"
    assert all(size <= 16 for _, size in container.scans)


def test_content_arrival_reschedules_waiting_entry_and_stale_index_cannot_resend(rig):
    engine, store, container, now = rig
    key = engine.admit(original())
    sender = Sender()
    engine.drain(sender)
    assert not sender.payloads
    assert store.read(key).value["scan_after"] == now[0] + JOIN_SECONDS
    engine.admit(content())
    engine.drain(sender)
    assert len(sender.payloads) == 1
    # Index visibility may lag; the conditional ledger remains authoritative.
    container.tags[key]["due"] = "00000000000000000000"
    engine.drain(sender)
    assert len(sender.payloads) == 1


def test_logs_do_not_include_content_even_for_invalid_payloads(rig, caplog):
    engine, _, _, now = rig
    marker = "synthetic-private-log-marker"
    with caplog.at_level(logging.INFO):
        engine.admit(content(InputMessages=marker, OutputMessages=marker))
        key = engine.admit(original(customDimensions={
            "openinference.span.kind": "LLM", "gen_ai.input.messages": marker,
        }))
        now[0] += JOIN_SECONDS
        engine.drain_key(key, Sender(Delivery.AMBIGUOUS))
    assert marker not in caplog.text
    assert "ambiguous" in caplog.text
