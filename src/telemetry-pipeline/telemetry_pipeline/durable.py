"""Opt-in cross-batch content correlation and conservative durable outbox.

All clocks are durable receipt clocks, never content capture/span event times.
The store's compare-and-swap, not process memory, owns admission and sending.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Callable, Iterable

from .batch import _extract_records, _message_body_to_text
from .durable_store import AdmissionError, BlobLedger, json_bytes
from .mapping import (
    MalformedRecordError, _message_json, _parse_time_ns, normalize_dependency_record,
    parse_custom_dimensions, parse_parent_span_id, parse_span_id, parse_trace_id,
    record_to_span,
)
from .strict_sender import Delivery, MAX_WIRE_BYTES, freeze_record
from .source_policy import SourcePolicy

logger = logging.getLogger(__name__)
MAX_RECORD_BYTES = 128 * 1024
MAX_MESSAGE_BYTES = 1024 * 1024
MAX_RECORDS_PER_MESSAGE = 256
MAX_BATCH_RECORDS = 1024
MAX_CANDIDATES_PER_SIDE = 4
MAX_CAS_ATTEMPTS = 8
SCAN_LIMIT = 16
MAX_SENDS_PER_DRAIN = 4
JOIN_SECONDS = 300
ORPHAN_SECONDS = 24 * 3600
ACK_SECONDS = 48 * 3600
CLAIM_SECONDS = 120
MAX_SEND_ATTEMPTS = 5


def _digest(value) -> str:
    return hashlib.sha256(json_bytes(value)).hexdigest()


def _event(reason: str, key: str = "", detail: str = "") -> None:
    safe_key = hashlib.sha256(key.encode("utf-8")).hexdigest() if key else ""
    logger.info("durable outcome=%s key=%s count=1 reason=%s", reason, safe_key, detail)


@dataclass(frozen=True)
class Scope:
    workspace: str
    component: str
    project: str
    destination: str

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip() or len(value) > 1024
            for value in (self.workspace, self.component, self.project, self.destination)
        ):
            raise AdmissionError("scope_required_or_limit")

    @property
    def namespace(self) -> str:
        return _digest([
            self.workspace.lower(), self.component.lower(), self.project, self.destination,
        ])

    def validate(self, record: dict) -> None:
        if (
            not isinstance(record.get("TenantId"), str)
            or record["TenantId"].lower() != self.workspace.lower()
            or not isinstance(record.get("_ResourceId"), str)
            or record["_ResourceId"].lower() != self.component.lower()
        ):
            raise AdmissionError("source_not_allowed")


class _SendBudget:
    def __init__(self, sender):
        self.sender = sender
        self.count = 0

    def send(self, payload):
        self.count += 1
        return self.sender.send(payload)


class Correlator:
    def __init__(
        self, store: BlobLedger, scope: Scope, clock: Callable[[], float] = time.time,
        freeze: Callable[[dict, str], bytes] = freeze_record,
        policy: SourcePolicy | None = None,
    ):
        self.store = store
        self.scope = scope
        self.clock = clock
        self.freeze = freeze
        self.policy = SourcePolicy.from_environment() if policy is None else policy
        self.prefix = f"ledger/{scope.namespace}/"

    def admit_batch(self, messages: Iterable) -> int:
        count = 0
        admitted = 0
        try:
            for message in messages:
                # Check bytes before decoding/parsing. No unbounded JSON reads.
                get_body = getattr(message, "get_body", None)
                body = get_body() if callable(get_body) else message
                if not isinstance(body, (str, bytes, bytearray)):
                    raise AdmissionError("message_shape")
                if len(body) > MAX_MESSAGE_BYTES:
                    raise AdmissionError("message_limit")
                text = _message_body_to_text(body)
                if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
                    raise AdmissionError("message_limit")
                records = _extract_records(text)
                if len(records) > MAX_RECORDS_PER_MESSAGE:
                    raise AdmissionError("message_record_limit")
                for record in records:
                    count += 1
                    if count > MAX_BATCH_RECORDS:
                        raise AdmissionError("batch_record_limit")
                    if self.admit(record):
                        admitted += 1
        except AdmissionError as exc:
            # AdmissionError messages are fixed internal reason codes, unlike
            # mapper/parser exceptions which may include source values.
            _event("admission_failure", detail=str(exc))
            raise AdmissionError("durable_admission_failure") from None
        except (MalformedRecordError, ValueError, UnicodeError, RecursionError):
            _event("admission_failure", detail="invalid_record_or_envelope")
            raise AdmissionError("durable_admission_failure") from None
        return admitted

    def admit(self, record: dict) -> str:
        json_bytes(record, MAX_RECORD_BYTES)
        if not isinstance(record, dict):
            raise AdmissionError("record_shape")
        try:
            excluded = self.policy.exclusion_reason(record)
        except MalformedRecordError:
            _event("malformed_source_identity")
            return ""
        content = record.get("Type") == "AppGenAIContent"
        if content:
            try:
                self.scope.validate(record)
                trace = parse_trace_id(record.get("TraceId"))
                span = parse_span_id(record.get("SpanId"), trace)
                timestamp = record.get("TimeGenerated")
                if (
                    not isinstance(timestamp, str)
                    or re.search(r"(?:Z|[+-]00(?::?00){0,2})$", timestamp) is None
                    or _parse_time_ns(timestamp) is None
                ):
                    raise MalformedRecordError("content_capture_time_requires_utc")
                parent_present = record.get("ParentSpanId") not in (None, "")
                parent = parse_parent_span_id(record.get("ParentSpanId"), trace)
            except (AdmissionError, ValueError):
                _event("malformed_or_disallowed_content")
                return ""
            candidates = {}
            for side in (() if excluded else ("input", "output")):
                value = _message_json(record.get(f"{side.title()}Messages"), side)
                if value is not None:
                    # Canonicalize object-key order to deduplicate equivalent arrays.
                    value = json_bytes(json.loads(value), MAX_RECORD_BYTES).decode("utf-8")
                    candidates[side] = {
                        "value": value, "parent": parent, "check_parent": parent_present,
                    }
            if not candidates and not excluded:
                _event("malformed_content")
                return ""
            original = None
        else:
            try:
                self.scope.validate(record)
            except AdmissionError:
                if not excluded:
                    raise
                # Excluded foreign sources cannot create entries in this namespace.
                _event("excluded_source", detail=excluded)
                return ""
            mapped = record_to_span(record)
            trace, span = mapped.context.trace_id, mapped.context.span_id
            original = record
            candidates = {}
        key = f"{self.prefix}{trace:032x}-{span:016x}"
        for _ in range(MAX_CAS_ATTEMPTS):
            current = self.store.read(key)
            now = self.clock()
            ledger = copy.deepcopy(current.value) if current else {
                "state": "pending", "created": now, "original": None,
                "candidates": {"input": {}, "output": {}},
                "scan_after": now + ORPHAN_SECONDS,
            }
            if ledger["state"] == "pending" and original is not None and ledger["original"] is not None:
                if ledger["original_hash"] != _digest(original):
                    raise AdmissionError("original_identity_conflict")
            reason = (
                self._exclusion_reason(ledger) if ledger.get("original") is not None else excluded
            )
            if reason and ledger["state"] in ("pending", "retry"):
                if self.store.cas(key, current.etag if current else None, self._excluded(now, reason)):
                    _event("excluded", key, reason)
                    return key
                continue
            if excluded and content:
                _event("excluded_content", key, excluded)
                return key
            if ledger["state"] != "pending":
                _event("late" if content else "replay_suppressed", key)
                return key
            if original is not None:
                if ledger["original"] is not None:
                    if ledger["original_hash"] != _digest(original):
                        raise AdmissionError("original_identity_conflict")
                    return key
                ledger["original"] = original
                ledger["original_hash"] = _digest(original)
                ledger["admitted"] = now
                ledger["deadline"] = now + JOIN_SECONDS
                ledger["scan_after"] = now
            for side, candidate in candidates.items():
                candidate_hash = _digest(candidate)
                existing = ledger["candidates"][side]
                if candidate_hash not in existing:
                    if len(existing) >= MAX_CANDIDATES_PER_SIDE:
                        raise AdmissionError("candidate_limit")
                    existing[candidate_hash] = candidate
                    if ledger["original"] is not None:
                        ledger["scan_after"] = now
            # Validate the *whole* next document before any write.
            json_bytes(ledger)
            if self.store.cas(key, current.etag if current else None, ledger):
                _event("admitted_content" if content else "admitted", key)
                return key
        raise AdmissionError("admission_contention")

    def _exclusion_reason(self, ledger: dict) -> str:
        if ledger["state"] not in ("pending", "retry") or ledger.get("original") is None:
            return ""
        return self.policy.exclusion_reason(ledger["original"])

    @staticmethod
    def _excluded(now: float, reason: str) -> dict:
        return {
            "state": "excluded", "excluded": now, "reason": reason,
            "expires": now + ACK_SECONDS,
        }

    def _enriched(self, ledger: dict, key: str) -> tuple[dict, bool]:
        record = copy.deepcopy(ledger["original"])
        mapped = record_to_span(record)
        attrs = mapped.attributes or {}
        dimensions = parse_custom_dimensions(normalize_dependency_record(record))
        parent = mapped.parent.span_id if mapped.parent else None
        for side in ("input", "output"):
            eligible = {}
            for candidate in ledger["candidates"][side].values():
                if candidate["check_parent"] and candidate["parent"] != parent:
                    _event("parent_mismatch", key)
                    continue
                eligible[candidate["value"]] = candidate
            if len(eligible) > 1:
                _event("conflict", key)
            if f"{side}.value" in attrs:
                continue
            if len(eligible) == 1:
                dimensions[f"gen_ai.{side}.messages"] = next(iter(eligible))
        record["customDimensions"] = dimensions
        # Native Properties must remain consistent with the normalized alias.
        if "Properties" in record:
            record["Properties"] = dimensions
        enriched_attrs = record_to_span(record).attributes or {}
        relevant = (
            attrs.get("openinference.span.kind") in ("LLM", "AGENT")
            or bool(attrs.get("gen_ai.operation.name"))
        )
        ready = not relevant or all(f"{side}.value" in enriched_attrs for side in ("input", "output"))
        return record, ready

    def drain_key(self, key: str, sender, allow_send: bool = True) -> bool:
        if re.fullmatch(re.escape(self.prefix) + r"[0-9a-f]{32}-[0-9a-f]{16}", key) is None:
            raise AdmissionError("ledger_key_shape")
        for _ in range(MAX_CAS_ATTEMPTS):
            current = self.store.read(key)
            now = self.clock()
            if current is None:
                return False
            ledger = copy.deepcopy(current.value)
            state = ledger["state"]
            if state in ("acknowledged", "excluded"):
                if now >= ledger["expires"]:
                    self.store.delete(key, current.etag)
                return False
            if state == "sending":
                if now - ledger["claimed"] < CLAIM_SECONDS:
                    return False
                ledger["state"] = "ambiguous"
                if self.store.cas(key, current.etag, ledger):
                    _event("ambiguous", key)
                    return False
                continue
            if state in ("ambiguous", "rejected"):
                _event(f"recovery_{state}", key)
                return False
            reason = self._exclusion_reason(ledger)
            if reason:
                if self.store.cas(key, current.etag, self._excluded(now, reason)):
                    _event("excluded", key, reason)
                    return False
                continue
            if state == "pending":
                if ledger["original"] is None:
                    if now - ledger["created"] >= ORPHAN_SECONDS:
                        if self.store.delete(key, current.etag):
                            _event("orphan_expired", key)
                    return False
                if not allow_send:
                    return False
                record, ready = self._enriched(ledger, key)
                if not ready and now < ledger["deadline"]:
                    ledger["scan_after"] = ledger["deadline"]
                    if not self.store.cas(key, current.etag, ledger):
                        continue
                    _event("pending", key)
                    return False
                payload = self.freeze(record, self.scope.project)
                if len(payload) > MAX_WIRE_BYTES:
                    raise AdmissionError("wire_payload_limit")
                ledger["wire"] = base64.b64encode(payload).decode("ascii")
                ledger["wire_hash"] = hashlib.sha256(payload).hexdigest()
                ledger["finalized"] = now
                ledger["completion"] = "matched" if ready else "deadline_missing"
                ledger["attempts"] = 0
            elif state == "retry":
                if now < ledger["due"] or not allow_send:
                    return False
            else:
                raise AdmissionError("unknown_ledger_state")
            ledger["state"] = "sending"
            ledger["claimed"] = now
            ledger["scan_after"] = now + CLAIM_SECONDS
            ledger["attempts"] += 1
            if self.store.cas(key, current.etag, ledger):
                if ledger["attempts"] == 1:
                    _event(ledger["completion"], key)
                self._send_claim(key, ledger, sender)
                return True
        raise AdmissionError("drain_contention")

    def _send_claim(self, key: str, ledger: dict, sender) -> None:
        # A crash anywhere from this point leaves `sending`, recovered as ambiguous.
        payload = base64.b64decode(ledger["wire"], validate=True)
        if hashlib.sha256(payload).hexdigest() != ledger["wire_hash"]:
            raise AdmissionError("frozen_payload_integrity")
        outcome = sender.send(payload)
        current = self.store.read(key)
        if current is None or current.value != ledger:
            _event("ambiguous", key)
            raise AdmissionError("send_claim_lost")
        now = self.clock()
        if outcome == Delivery.CONFIRMED:
            updated = {
                "state": "acknowledged", "acknowledged": now, "expires": now + ACK_SECONDS,
            }
            reason = "acknowledged"
        else:
            updated = copy.deepcopy(ledger)
            if outcome == Delivery.RETRYABLE_REJECTION and ledger["attempts"] < MAX_SEND_ATTEMPTS:
                updated["state"] = "retry"
                updated["due"] = now + min(30 * 2 ** (ledger["attempts"] - 1), 900)
                updated["scan_after"] = updated["due"]
            elif outcome in (Delivery.REJECTED, Delivery.RETRYABLE_REJECTION):
                updated["state"] = "rejected"
            else:
                updated["state"] = "ambiguous"
            reason = updated["state"]
        if not self.store.cas(key, current.etag, updated):
            _event("ambiguous", key)
            raise AdmissionError("send_ack_contention")
        _event(reason, key)

    def drain(self, sender, limit: int = SCAN_LIMIT) -> int:
        if not 1 <= limit <= SCAN_LIMIT:
            raise AdmissionError("scan_limit")
        cursor_key = f"control/{self.scope.namespace}/scan"
        current = self.store.read(cursor_key)
        cursor = current.value.get("cursor") if current else None
        cutoff = current.value["cutoff"] if cursor else self.clock()
        keys, following = self.store.page(self.prefix, cursor, limit, cutoff)
        budget = _SendBudget(sender)
        failed = False
        for key in keys:
            try:
                self.drain_key(key, budget, allow_send=budget.count < MAX_SENDS_PER_DRAIN)
            except AdmissionError as exc:
                # Retain failed entries, but advance past poison work so later
                # pages can progress on the next timer invocation.
                _event("drain_failure", key, detail=str(exc))
                failed = True
        if not self.store.cas(
            cursor_key, current.etag if current else None,
            {"cursor": following, "cutoff": cutoff},
        ):
            _event("scan_contention")
        if failed:
            raise AdmissionError("durable_drain_failure")
        return len(keys)
