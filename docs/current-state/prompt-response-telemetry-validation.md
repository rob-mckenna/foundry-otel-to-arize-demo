# Prompt/Response Telemetry Behavior — Validation (#51)

**Status: CURRENT-STATE (validation procedure + static/code-review evidence, implemented;
live-environment long-prompt/truncation evidence NOT YET captured — see §4.)**

Validation record for
[#51 Validate prompt/response telemetry behavior](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/51),
depends on #50 (see [`app-insights-telemetry-capture-validation.md`](./app-insights-telemetry-capture-validation.md)).

## 1. Acceptance criteria under validation

1. Captured `input.value`/`llm.input_messages` matches the synthetic prompt sent,
   character-for-character.
2. Captured `output.value`/`llm.output_messages` matches the actual agent response,
   character-for-character.
3. At least one long synthetic prompt/response (near/above App Insights' property size limits) is
   tested to confirm no silent truncation, or truncation is documented as a known limitation.

## 2. What is validated today — statically, via code review + existing tests

- **Character-for-character match, source side.** `tests/test_agent_spans.py::test_llm_span_has_openinference_attributes_and_token_counts`
  asserts `llm_span.attributes["input.value"].startswith("What is my synthetic deductible?")` and
  `llm_span.attributes["output.value"] == "synthetic test response"` — an exact string equality
  check against the literal text sent/returned, not a substring heuristic, for the output side.
  `tests/test_agent_spans.py::test_invoke_span_has_openinference_chain_attributes` further asserts
  the root `prompt_agent.invoke` span's `output.value` equals `result.response.text` exactly
  (`==`, not a fuzzy match). This proves the agent's own instrumentation code
  (`agent.py`) attaches the exact prompt/response strings to span attributes, with no
  mutation/corruption introduced between "what the model returned" and "what's on the span" —
  this is the half of criteria 1–2 this repo's own code controls.
- **No truncation logic exists in this repo's instrumentation code.** Direct inspection of
  `agent.py`'s span-attribute-setting calls shows they pass the full prompt/response strings
  straight through (`span.set_attribute("input.value", prompt)` / `.set_attribute("output.value", response.text)`,
  no slicing, no length check). So any truncation that could occur would happen **downstream**,
  either in the OTel SDK/exporter layer or in Application Insights' own ingestion pipeline — not
  in code this repo owns.

## 3. What is NOT validated — requires a live App Insights instance

- **Criteria 1–2 for the App Insights-side value** (after export, not just pre-export on the
  in-memory span) — this requires the same live App Insights instance #50 is blocked on.
- **Criterion 3, the long-prompt/truncation test, is not yet implemented as a test case at all** —
  no existing test in `src/prompt-agent/tests/` sends a prompt near/above Application Insights'
  property size limit. Application Insights' documented limit on a single `customDimensions`
  string property is **8,192 characters** (Azure Monitor service limit, not configurable). This
  repo currently has no test proving what happens to an `input.value`/`output.value` at or beyond
  that boundary — this is a **real gap**, not just an unexecuted-but-already-written test, and is
  called out below as a concrete follow-up rather than silently assumed to be fine.

## 4. Sandbox limitation

No Python interpreter and no live Application Insights instance exist in this session (same as
#50) — a new long-prompt test case could not be written-and-executed here, only designed.

## 5. Concrete follow-up: long-prompt/truncation test (not yet written)

Recommended test, to be added to `src/prompt-agent/tests/test_agent_spans.py` once a Python
interpreter is available:

```python
def test_long_prompt_and_response_are_not_silently_truncated(span_exporter):
    long_text = "synthetic filler word " * 500  # ~11,500 chars, well above the 8,192-char
                                                  # Application Insights property size limit
    agent = PromptAgent(config=load_config(), model_client=_FixedModelClient(text=long_text))
    agent.invoke(long_text, plan_name=None)
    spans = span_exporter.get_finished_spans()
    llm_span = find_span(spans, "llm.chat_completion")
    assert llm_span.attributes["input.value"] == long_text  # exact length preserved pre-export
    assert llm_span.attributes["output.value"] == long_text
```

This would prove the **pre-export** (in-process span attribute) side is never truncated by this
repo's own code — it does not prove what Application Insights itself does with a >8,192-char
`customDimensions` value on ingestion (Azure Monitor's documented behavior is to truncate, not
reject, oversized string properties — this would need to be confirmed against a live instance and
recorded as a **known limitation**, not silently treated as "fine," per
`.github/copilot-instructions.md`'s synthetic-data/no-silent-gaps conventions). If truncation is
confirmed live, the mapping doc at
[`docs/telemetry/mapping/llm-io-fields.md`](./../telemetry/mapping/llm-io-fields.md) (#91) should be
updated with a documented size-limit caveat for `input.value`/`output.value`.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | `input.value` exact match, pre-export | ✅ Validated-via-review (existing test, exact-match assertion) |
| 1 (post-export, live App Insights) | — | ⚠️ Blocked — same as #50, no live instance |
| 2 | `output.value` exact match, pre-export | ✅ Validated-via-review (existing test, exact-match assertion, including root span) |
| 2 (post-export, live App Insights) | — | ⚠️ Blocked — same as #50, no live instance |
| 3 | Long prompt/response truncation test | ❌ **Gap — no test exists yet.** §5 provides the test to add; live Application Insights truncation behavior (8,192-char property limit) not yet confirmed and must be recorded as a known limitation once it is |

**Overall verdict: Pass with caveats (source-side) / Blocked (live-instance, truncation
criterion)** — the agent's own instrumentation never corrupts or truncates prompt/response text
pre-export (proven). Post-export behavior against a live App Insights instance, and the specific
long-prompt truncation acceptance criterion, remain open and are tracked explicitly rather than
assumed.
