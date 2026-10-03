"""Static, automated validation of PromptAgent against every synthetic
scenario in the shared prompt library (#49 — "Validate Prompt Agent
execution"; scenarios sourced from `synthetic/scenarios.py`, see #48).

This module is `pytest`-executable proof that `PromptAgent.invoke()`
handles every scenario currently defined in the shared synthetic prompt
library without raising, and that each invocation's root span and response
satisfy #49's three acceptance criteria:

  1. Every synthetic prompt produces a successful response (no unhandled
     error).
  2. A root span (`prompt_agent.invoke`) is emitted with a valid trace ID.
  3. Response content is sane (non-empty, relevant to the prompt).

**STUB vs. LIVE caveat — read before treating a pass here as "the demo
works against a live Foundry agent":** `PromptAgent` defaults to
`StubFoundryModelClient` (`prompt_agent/model_client.py`); no live Foundry
Prompt Agent deployment exists in this sandbox (#25's dependency on Infra's
#15/#16/#18 is unresolved here). This suite validates the agent's
*orchestration and instrumentation* logic — span creation, parent/child
linkage, trace-ID propagation, response wiring — which is exactly the
current-state code owned by this directory. It does NOT exercise a live
model backend. See `/docs/current-state/prompt-agent-execution-validation.md`
for the full static-vs-live validation split and the procedure to re-run
this suite (and capture live evidence) once a real Foundry client/
environment is available.
"""
from __future__ import annotations

import pytest

from prompt_agent.agent import PromptAgent
from prompt_agent.config import load_config
from synthetic.scenarios import SCENARIOS

from .conftest import find_span

# One keyword that MUST appear (case-insensitive) in a scenario's response
# text for that response to count as "relevant" (acceptance criterion #3),
# not merely "non-empty". Chosen to match the keyword-routing table in
# `model_client.py`'s `StubFoundryModelClient._synthetic_answer()`, so a
# genuine routing regression there is caught here too.
_EXPECTED_RESPONSE_KEYWORD: dict[str, str] = {
    "benefits-deductible-lookup": "deductible",
    "benefits-copay-lookup": "copay",
    "member-id-confirmation": "member id",
    "network-coverage-lookup": "network",
    "claim-status-lookup": "claim",
}


def _is_valid_trace_id(trace_id: int) -> bool:
    """OpenTelemetry represents an invalid/unset trace ID as all-zero bits
    (`opentelemetry.trace.INVALID_TRACE_ID`). A real, usable trace ID is any
    non-zero 128-bit integer.
    """
    return isinstance(trace_id, int) and trace_id != 0


def test_shared_library_keyword_map_is_complete():
    """Guard against silent scenario-library drift: fails loudly if a new
    scenario is added to `synthetic/scenarios.py` (#48) without a matching
    expected-keyword entry above, so this suite's relevance check can't
    quietly go stale and start rubber-stamping new scenarios.
    """
    missing = {s.scenario_id for s in SCENARIOS} - set(_EXPECTED_RESPONSE_KEYWORD)
    assert not missing, f"Missing expected-keyword mapping for scenarios: {sorted(missing)}"


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.scenario_id)
def test_scenario_produces_successful_response_and_root_span(scenario, span_exporter):
    """Exercises every synthetic prompt in the shared library (#48) through
    `PromptAgent.invoke()` and asserts #49's three acceptance criteria.
    """
    assert scenario.synthetic is True, "shared prompt library must only contain synthetic scenarios"

    agent = PromptAgent(config=load_config())

    # Criterion 1: invoking the agent with this prompt must not raise.
    result = agent.invoke(scenario.prompt, plan_name=scenario.synthetic_plan_name)

    spans = span_exporter.get_finished_spans()
    root_span = find_span(spans, "prompt_agent.invoke")

    # Criterion 2: the root span has no parent (it really is the root of
    # this request's span tree) and carries a valid, non-zero trace ID.
    assert root_span.parent is None
    assert _is_valid_trace_id(root_span.context.trace_id)

    # Criterion 3: response content is sane - non-empty and relevant to the
    # prompt (keyword check), not just "no exception thrown".
    response_text = result.response.text.strip()
    assert response_text != ""
    expected_keyword = _EXPECTED_RESPONSE_KEYWORD[scenario.scenario_id]
    assert expected_keyword in response_text.lower(), (
        f"scenario {scenario.scenario_id!r} response did not contain expected "
        f"keyword {expected_keyword!r}: {response_text!r}"
    )

    # Root span itself must also report success (OK), not just "didn't
    # raise" — consistent with #27's span-status instrumentation.
    from opentelemetry.trace import StatusCode

    assert root_span.status.status_code == StatusCode.OK
