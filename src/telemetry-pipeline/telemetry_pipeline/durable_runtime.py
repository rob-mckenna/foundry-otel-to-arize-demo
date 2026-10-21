"""Required source/destination configuration and managed-identity Blob wiring."""
from __future__ import annotations

import os
import re
from contextlib import ExitStack
from urllib.parse import urlsplit

from azure.identity import ManagedIdentityCredential
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient

from .durable import Correlator, Scope
from .durable_store import AdmissionError, BlobLedger
from .strict_sender import StrictSender
from .source_policy import SourcePolicy

CONTAINER = "genai-correlation"


class DurableRuntime:
    def __init__(self):
        policy = SourcePolicy.from_environment()
        required = (
            "DURABLE_ALLOWED_WORKSPACE_ID", "DURABLE_ALLOWED_COMPONENT_RESOURCE_ID",
            "DURABLE_ARIZE_PROJECT", "ARIZE_OTLP_ENDPOINT", "ARIZE_SPACE_ID", "ARIZE_API_KEY",
        )
        values = {name: os.environ.get(name, "") for name in required}
        if not all(value.strip() for value in values.values()):
            raise AdmissionError("durable_source_destination_configuration_required")
        if not re.fullmatch(
            r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
            values["DURABLE_ALLOWED_WORKSPACE_ID"],
        ):
            raise AdmissionError("durable_workspace_id_requires_uuid")
        if not re.fullmatch(
            r"/subscriptions/[0-9a-fA-F-]{36}/resourceGroups/[^/]+"
            r"/providers/Microsoft\.Insights/components/[^/]+",
            values["DURABLE_ALLOWED_COMPONENT_RESOURCE_ID"], re.IGNORECASE,
        ):
            raise AdmissionError("durable_component_resource_id_required")
        uri = os.environ.get("AzureWebJobsStorage__blobServiceUri", "")
        if not uri:
            account = os.environ.get("AzureWebJobsStorage__accountName", "")
            if not re.fullmatch(r"[a-z0-9]{3,24}", account):
                raise AdmissionError("durable_identity_blob_storage_required")
            uri = f"https://{account}.blob.core.windows.net"
        try:
            parsed = urlsplit(uri)
            port = parsed.port
        except ValueError:
            raise AdmissionError("durable_storage_requires_public_azure_blob_uri") from None
        if (
            parsed.scheme != "https" or not parsed.hostname
            or not re.fullmatch(r"[a-z0-9]{3,24}\.blob\.core\.windows\.net", parsed.hostname)
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/") or port not in (None, 443)
        ):
            raise AdmissionError("durable_storage_requires_public_azure_blob_uri")
        self.sender = StrictSender(
            values["ARIZE_OTLP_ENDPOINT"], values["ARIZE_SPACE_ID"],
            values["ARIZE_API_KEY"],
        )
        scope = Scope(
            values["DURABLE_ALLOWED_WORKSPACE_ID"],
            values["DURABLE_ALLOWED_COMPONENT_RESOURCE_ID"],
            values["DURABLE_ARIZE_PROJECT"],
            values["ARIZE_OTLP_ENDPOINT"] + "|" + values["ARIZE_SPACE_ID"],
        )
        self._stack = ExitStack()
        try:
            credential = self._stack.enter_context(ManagedIdentityCredential())
            service = self._stack.enter_context(BlobServiceClient(
                uri, credential=credential, logging_enable=False,
                connection_timeout=10, read_timeout=10, retry_total=2,
            ))
            self.correlator = Correlator(
                BlobLedger(service.get_container_client(CONTAINER)), scope, policy=policy,
            )
        except (ValueError, AdmissionError, AzureError):
            self._stack.close()
            raise AdmissionError("durable_initialization_failure") from None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._stack.close()
