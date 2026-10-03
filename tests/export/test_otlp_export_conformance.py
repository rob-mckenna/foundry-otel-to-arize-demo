"""Conformance test scaffold for issue #38 (OTLP export conformance, Azure Function -> Arize).

**Execution note:** no Python interpreter is available in this validation environment, so this
file could not actually be executed in this pass (consistent with Telemetry's Milestone 2 history
entry on the same sandbox limitation). It is written to the same conventions as the existing,
already-reasoned `src/prompt-agent/tests/test_agent_spans.py` /
`test_token_usage_validation.py` suites and manually traced against
`docs/telemetry/otlp-export-conformance.md` / the four field-mapping specs (#89-#92) to confirm the
assertions are correct given that spec. **This must be re-run with a working Python 3.10+
environment (e.g. `pip install pytest` then `pytest tests/export`) before being relied on as passing
CI evidence.**

This test does NOT exercise the production Azure Function (no such code exists in this repo yet -
see `src/telemetry-pipeline/README.md`) or a live Arize OTLP endpoint. It exercises a minimal
*reference transform* defined in this file, which implements the field-mapping specs
(docs/telemetry/mapping/*.md) closely enough to prove the specs are internally consistent and
implementable. Treat this as a spec-conformance scaffold, not production-equivalent coverage.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Synthetic input: Log Analytics / Event Hub envelope rows (one per span)
# ---------------------------------------------------------------------------

def _hex(n: int) -> str:
    """Deterministic n-hex-char synthetic identifier (never a real trace/span ID)."""
    return uuid.uuid4().hex[:n]


def build_synthetic_batch(trace_count: int = 10) -> list[dict]:
    """Builds a synthetic batch of Log Analytics rows shaped like AppDependencies export records.

    Each trace contributes 5 spans: prompt_agent.invoke (root) -> tool.lookup_plan_details and
    llm.chat_completion (children) -> llm.chat_completion.attempt x2 (grandchildren of the LLM
    span), mirroring the span tree already validated in
    src/prompt-agent/tests/test_agent_spans.py. Defaults to 10 traces x 5 spans = 50 spans, meeting
    issue #38's "50+ span synthetic batch" acceptance bar.
    """
    rows: list[dict] = []
    for _ in range(trace_count):
        trace_id = _hex(32)
        root_id = _hex(16)
        tool_id = _hex(16)
        llm_id = _hex(16)
        attempt_ids = [_hex(16), _hex(16)]

        rows.append(_row(trace_id, root_id, None, "prompt_agent.invoke", True, {}))
        rows.append(
            _row(
                trace_id,
                tool_id,
                root_id,
                "tool.lookup_plan_details",
                True,
                {"openinference.span.kind": "TOOL", "input.value": "synthetic-input",
                 "output.value": "synthetic-output"},
            )
        )
        rows.append(
            _row(
                trace_id,
                llm_id,
                root_id,
                "llm.chat_completion",
                True,
                {
                    "openinference.span.kind": "LLM",
                    "llm.model_name": "synthetic-model-v1",
                    "llm.token_count.prompt": "42",
                    "llm.token_count.completion": "18",
                    "llm.token_count.total": "60",
                    "correlation.id": f"SYN-{trace_id[:8]}",
                },
            )
        )
        for i, attempt_id in enumerate(attempt_ids):
            rows.append(
                _row(
                    trace_id,
                    attempt_id,
                    llm_id,
                    "llm.chat_completion.attempt",
                    i == len(attempt_ids) - 1,
                    {"retry.attempt": str(i + 1), "retry.max_attempts": "2",
                     "retry.will_retry": "false" if i == len(attempt_ids) - 1 else "true"},
                )
            )
    return rows


def _row(trace_id, span_id, parent_id, name, success, custom_dims):
    return {
        "operation_Id": trace_id,
        "operation_ParentId": parent_id or "",
        "id": span_id,
        "Name": name,
        "Success": success,
        "customDimensions": custom_dims,
    }


# ---------------------------------------------------------------------------
# Reference transform: Log Analytics row -> OTLP-shaped span (spec conformance only)
# ---------------------------------------------------------------------------

RESOURCE_SERVICE_NAME = "foundry-prompt-agent-demo"
RESOURCE_DEPLOYMENT_ENVIRONMENT = "demo"


@dataclass
class ReferenceSpan:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    status_code: str
    attributes: dict = field(default_factory=dict)


def transform_row_to_span(row: dict) -> ReferenceSpan:
    """Reference implementation of the field-mapping specs (#89-#92). Not the production Function."""
    attrs: dict = {}
    for key, value in row["customDimensions"].items():
        if key in ("llm.token_count.prompt", "llm.token_count.completion",
                   "llm.token_count.total", "retry.attempt", "retry.max_attempts"):
            attrs[key] = int(value)
        elif key == "retry.will_retry":
            attrs[key] = value == "true"
        else:
            attrs[key] = value

    return ReferenceSpan(
        trace_id=row["operation_Id"],
        span_id=row["id"],
        parent_span_id=row["operation_ParentId"] or None,
        name=row["Name"],
        status_code="STATUS_CODE_OK" if row["Success"] else "STATUS_CODE_ERROR",
        attributes=attrs,
    )


def build_resource_spans(rows: list[dict]) -> dict:
    """Groups transformed spans under one ResourceSpans message, per docs/telemetry/otlp-export-conformance.md §2."""
    return {
        "resource": {
            "attributes": {
                "service.name": RESOURCE_SERVICE_NAME,
                "deployment.environment": RESOURCE_DEPLOYMENT_ENVIRONMENT,
            }
        },
        "spans": [transform_row_to_span(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_span_count_in_equals_span_count_out_for_50_plus_batch():
    rows = build_synthetic_batch(trace_count=10)
    assert len(rows) >= 50, "fixture must meet issue #38's 50+ span acceptance bar"

    resource_spans = build_resource_spans(rows)

    assert len(resource_spans["spans"]) == len(rows), (
        "no span may be silently dropped by the transform (issue #38 acceptance criterion)"
    )


def test_resource_attributes_set_correctly():
    rows = build_synthetic_batch(trace_count=2)
    resource_spans = build_resource_spans(rows)

    assert resource_spans["resource"]["attributes"]["service.name"] == "foundry-prompt-agent-demo"
    assert resource_spans["resource"]["attributes"]["deployment.environment"]


def test_trace_and_span_ids_round_trip_unchanged():
    rows = build_synthetic_batch(trace_count=3)
    resource_spans = build_resource_spans(rows)

    for row, span in zip(rows, resource_spans["spans"]):
        assert span.trace_id == row["operation_Id"]
        assert span.span_id == row["id"]
        expected_parent = row["operation_ParentId"] or None
        assert span.parent_span_id == expected_parent


def test_root_spans_have_no_parent_span_id():
    rows = build_synthetic_batch(trace_count=1)
    resource_spans = build_resource_spans(rows)

    root_spans = [s for s in resource_spans["spans"] if s.name == "prompt_agent.invoke"]
    assert len(root_spans) == 1
    assert root_spans[0].parent_span_id is None, (
        "a root span's missing operation_ParentId must map to 'no parent', never a zero-filled ID"
    )


def test_token_count_attributes_are_native_int_on_llm_spans():
    rows = build_synthetic_batch(trace_count=1)
    resource_spans = build_resource_spans(rows)

    llm_spans = [s for s in resource_spans["spans"] if s.name == "llm.chat_completion"]
    assert len(llm_spans) == 1
    attrs = llm_spans[0].attributes
    assert isinstance(attrs["llm.token_count.prompt"], int)
    assert isinstance(attrs["llm.token_count.completion"], int)
    assert isinstance(attrs["llm.token_count.total"], int)
    assert attrs["llm.token_count.prompt"] + attrs["llm.token_count.completion"] == (
        attrs["llm.token_count.total"]
    )
