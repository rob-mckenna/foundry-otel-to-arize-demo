"""Bounded, optimistic Blob ledger storage; no host checkpoint container reuse."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

from azure.core import MatchConditions
from azure.core.exceptions import (
    AzureError,
    ResourceExistsError,
    ResourceModifiedError,
    ResourceNotFoundError,
)

MAX_LEDGER_BYTES = 1024 * 1024


def _due_tag(timestamp: float) -> str:
    return f"{math.ceil(timestamp):020d}"


def _index_tags(key: str, value: dict) -> dict[str, str]:
    match = re.fullmatch(r"ledger/([0-9a-f]{64})/[0-9a-f]{32}-[0-9a-f]{16}", key)
    if match is None:
        return {}
    tags = {"scope": match[1]}
    if value["state"] in ("acknowledged", "excluded"):
        tags["due"] = _due_tag(value["expires"])
    elif value["state"] in ("pending", "retry", "sending"):
        tags["due"] = _due_tag(value["scan_after"])
    return tags


class AdmissionError(RuntimeError):
    """Safe, content-free failure that must prevent successful admission."""


def json_bytes(value: Any, limit: int = MAX_LEDGER_BYTES) -> bytes:
    try:
        payload = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (ValueError, TypeError, RecursionError):
        raise AdmissionError("non_json_payload") from None
    if len(payload) > limit:
        raise AdmissionError("payload_limit")
    return payload


@dataclass(frozen=True)
class Versioned:
    value: dict
    etag: str


class BlobLedger:
    """A container client is injected to make real ETag behavior testable.

    CAS is also the send claim: only the worker that commits `sending` may send.
    Azure SDK exceptions are deliberately not propagated with response details.
    """

    def __init__(self, container):
        self.container = container

    def read(self, key: str) -> Versioned | None:
        blob = self.container.get_blob_client(key)
        try:
            properties = blob.get_blob_properties(logging_enable=False)
            if properties.size > MAX_LEDGER_BYTES:
                raise AdmissionError("stored_payload_limit")
            payload = blob.download_blob(
                etag=properties.etag,
                match_condition=MatchConditions.IfNotModified,
                offset=0,
                length=MAX_LEDGER_BYTES + 1,
                logging_enable=False,
            ).readall()
            if len(payload) > MAX_LEDGER_BYTES:
                raise AdmissionError("stored_payload_limit")
            value = json.loads(payload)
            if not isinstance(value, dict):
                raise AdmissionError("stored_payload_shape")
            return Versioned(value, properties.etag)
        except ResourceNotFoundError:
            return None
        except ResourceModifiedError:
            raise AdmissionError("read_contention") from None
        except (AzureError, ValueError, RecursionError):
            raise AdmissionError("storage_read_failure") from None

    def cas(self, key: str, etag: str | None, value: dict) -> bool:
        payload = json_bytes(value)
        tags = _index_tags(key, value)
        blob = self.container.get_blob_client(key)
        try:
            if etag is None:
                blob.upload_blob(payload, overwrite=False, tags=tags, logging_enable=False)
            else:
                blob.upload_blob(
                    payload, overwrite=True, etag=etag,
                    match_condition=MatchConditions.IfNotModified,
                    tags=tags,
                    logging_enable=False,
                )
            return True
        except (ResourceExistsError, ResourceModifiedError, ResourceNotFoundError):
            return False
        except AzureError:
            raise AdmissionError("storage_write_failure") from None

    def delete(self, key: str, etag: str) -> bool:
        try:
            self.container.get_blob_client(key).delete_blob(
                etag=etag, match_condition=MatchConditions.IfNotModified,
                logging_enable=False,
            )
            return True
        except (ResourceNotFoundError, ResourceModifiedError):
            return False
        except AzureError:
            raise AdmissionError("storage_delete_failure") from None

    def page(
        self, prefix: str, cursor: str | None, limit: int, cutoff: float,
    ) -> tuple[list[str], str | None]:
        match = re.fullmatch(r"ledger/([0-9a-f]{64})/", prefix)
        if match is None:
            raise AdmissionError("scan_scope")
        query = f'"scope" = \'{match[1]}\' AND "due" <= \'{_due_tag(cutoff)}\''
        try:
            pages = self.container.find_blobs_by_tags(
                filter_expression=query, results_per_page=limit,
                logging_enable=False,
            ).by_page(continuation_token=cursor)
            page = next(pages, ())
            keys = []
            for item in page:
                if len(keys) >= limit:
                    raise AdmissionError("scan_page_limit")
                keys.append(item.name)
            return keys, pages.continuation_token
        except AzureError:
            raise AdmissionError("storage_scan_failure") from None
