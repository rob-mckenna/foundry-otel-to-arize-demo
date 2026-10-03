"""Token-usage telemetry validation for every LLM-kind span (#34).

Validates the acceptance criteria from issue #34 directly against the span
attributes the agent actually emits (via `InMemorySpanExporter`, no live Azure
resources required — same approach as `test_agent_spans.py`):

  - `llm.token_count.prompt` / `.completion` / `.total` are present on 100% of
    LLM-kind spans in a batch of synthetic invocations.
  - Values are internally consistent (`prompt + completion == total`) across
    20+ synthetic spans.
  - Values are captured with correct numeric typing (`int`, not stringified)
    as OTel span attributes — App Insights only avoids stringifying a
    `customDimensions` value if the attribute is set as a native int/float
    on the span, so the OTel-side type is what this test guards.

Uses `StubFoundryModelClient`'s real (whitespace-based) token estimator
rather than a fixed test double, so token counts vary per synthetic prompt —
this is a more realistic consistency check than asserting against one
canned value repeated 20+ times.
"""
from __future__ import annotations

from prompt_agent.agent import PromptAgent
from prompt_agent.config import load_config
from synthetic.scenarios import SCENARIOS

from .conftest import find_spans

# 5 scenarios x 5 repetitions (with distinct correlation IDs) = 25 LLM spans,
# comfortably over the issue's "20+ synthetic spans" bar, using only
# synthetic/fabricated prompts from synthetic/scenarios.py.
_REPETITIONS = 5


def _run_batch() -> None:
    agent = PromptAgent(config=load_config())
    for rep in range(_REPETITIONS):
        for scenario in SCENARIOS:
            agent.invoke(
                scenario.prompt,
                plan_name=scenario.synthetic_plan_name,
                correlation_id=f"{scenario.scenario_id}-rep{rep}",
            )


def test_every_llm_span_has_all_three_token_count_attributes(span_exporter):
    _run_batch()
    spans = span_exporter.get_finished_spans()
    llm_spans = find_spans(spans, "llm.chat_completion")

    assert len(llm_spans) == len(SCENARIOS) * _REPETITIONS

    required_keys = (
        "llm.token_count.prompt",
        "llm.token_count.completion",
        "llm.token_count.total",
    )
    missing: list[tuple[str, str]] = []
    for span in llm_spans:
        for key in required_keys:
            if key not in span.attributes:
                missing.append((span.context.span_id, key))

    assert not missing, f"LLM spans missing required token-count attributes: {missing}"


def test_token_counts_are_internally_consistent_across_batch(span_exporter):
    _run_batch()
    spans = span_exporter.get_finished_spans()
    llm_spans = find_spans(spans, "llm.chat_completion")

    assert len(llm_spans) >= 20, "need at least 20 synthetic LLM spans for this validation"

    inconsistent = []
    for span in llm_spans:
        prompt_tok = span.attributes["llm.token_count.prompt"]
        completion_tok = span.attributes["llm.token_count.completion"]
        total_tok = span.attributes["llm.token_count.total"]
        if prompt_tok + completion_tok != total_tok:
            inconsistent.append((span.context.span_id, prompt_tok, completion_tok, total_tok))

    assert not inconsistent, f"Inconsistent token counts (prompt + completion != total): {inconsistent}"


def test_token_count_attributes_are_native_int_not_stringified(span_exporter):
    _run_batch()
    spans = span_exporter.get_finished_spans()
    llm_spans = find_spans(spans, "llm.chat_completion")

    wrong_type = []
    for span in llm_spans:
        for key in (
            "llm.token_count.prompt",
            "llm.token_count.completion",
            "llm.token_count.total",
        ):
            value = span.attributes[key]
            # bool is a subclass of int in Python -- explicitly exclude it so
            # a stray boolean attribute wouldn't false-pass this check.
            if not isinstance(value, int) or isinstance(value, bool):
                wrong_type.append((span.context.span_id, key, type(value).__name__))

    assert not wrong_type, f"Token-count attributes not captured as native int: {wrong_type}"
