"""Shared fixtures/synthetic record builders for the telemetry_pipeline tests.

Follows `src/prompt-agent/tests/conftest.py`'s conventions: small, focused
fixtures plus a couple of plain helper functions (not fixtures) used across
multiple test modules.
"""
from __future__ import annotations

from typing import Any

import pytest


def make_record(**overrides: Any) -> dict:
    """Build one synthetic Azure Monitor `AppDependencies`-style record.

    Defaults describe a root `prompt_agent.invoke` CHAIN span (no parent),
    matching the shape used throughout
    `docs/current-state/mapping-and-limitations.md` identity contract.
    Override any field (including nested `customDimensions` keys via the
    `custom_dimensions` kwarg) to build a child/LLM/retry-attempt span.
    """
    custom_dimensions = {
        "correlation.id": "synthetic-correlation-id-123",
        "openinference.span.kind": "CHAIN",
        "input.value": "What is my synthetic deductible?",
        "output.value": "Your synthetic deductible is $500.",
    }
    custom_dimensions.update(overrides.pop("custom_dimensions", {}) or {})

    record = {
        "operation_Id": "0af7651916cd43dd8448eb211c80319c",
        "operation_ParentId": "",
        "id": "b7ad6b7169203331",
        "Name": "prompt_agent.invoke",
        "Success": True,
        "timestamp": "2026-10-03T12:00:00.000Z",
        "duration": 123.456,
        "customDimensions": custom_dimensions,
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="session")
def registered_pipeline_functions():
    from telemetry_pipeline import function_app

    # Azure Functions' metadata builder must be materialized only once.
    return function_app.app.get_functions()
