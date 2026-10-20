"""Exact source identities excluded from agent export, independent of span kind."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Mapping

from .mapping import MalformedRecordError, source_service_name


def _identities(environment: Mapping[str, str], name: str) -> frozenset[str]:
    try:
        values = json.loads(environment.get(name, "[]"))
    except (ValueError, TypeError, RecursionError):
        raise ValueError(f"{name} requires a JSON array of nonempty strings") from None
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value.strip() or value != value.strip()
        for value in values
    ):
        raise ValueError(f"{name} requires a JSON array of nonempty strings")
    return frozenset(values)


@dataclass(frozen=True)
class SourcePolicy:
    services: frozenset[str] = frozenset()
    components: frozenset[str] = frozenset()

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> SourcePolicy:
        environment = os.environ if environment is None else environment
        return cls(
            _identities(environment, "PIPELINE_EXCLUDED_SERVICE_NAMES"),
            frozenset(value.lower() for value in _identities(
                environment, "PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS",
            )),
        )

    def exclusion_reason(self, record: Mapping) -> str:
        service = source_service_name(record)
        component = record.get("_ResourceId")
        if component is not None and not isinstance(component, str):
            raise MalformedRecordError("_ResourceId must be a string")
        if service in self.services:
            return "service_identity"
        if component is not None and component.lower() in self.components:
            return "component_identity"
        return ""
