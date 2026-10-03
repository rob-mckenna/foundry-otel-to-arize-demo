# Token-Usage Metrics — Capture & Validation

**Status: CURRENT-STATE.** Validates the acceptance criteria of issue #34 against the Prompt
Agent's existing instrumentation (`src/prompt-agent/prompt_agent/agent.py`, `model_client.py`) —
no code changes to the agent were needed; this issue is verification + test coverage.

## 1. What's captured, and where

Every `llm.chat_completion` span (the only `LLM`-kind span the agent emits — see
[`custom-dimensions-schema.md`](./custom-dimensions-schema.md)) unconditionally sets three
attributes, straight from `agent.py`:

```python
model_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, response.prompt_tokens)
model_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, response.completion_tokens)
model_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, response.total_tokens)
```

`SpanAttributes.LLM_TOKEN_COUNT_PROMPT` / `.LLM_TOKEN_COUNT_COMPLETION` / `.LLM_TOKEN_COUNT_TOTAL`
resolve to the OpenInference attribute keys `llm.token_count.prompt`, `llm.token_count.completion`,
and `llm.token_count.total` respectively. `response.total_tokens` is a computed property
(`prompt_tokens + completion_tokens`, see `model_client.py`'s `ModelResponse`) — **not** an
independently-reported number from the model backend — so internal consistency
(`prompt + completion == total`) is structurally guaranteed by the dataclass today, not just
empirically likely. This test suite validates that guarantee holds all the way through to the
actual span attribute values (not just the dataclass), since it's the span attributes — not the
dataclass — that flow downstream to App Insights/Arize.

Both `prompt_tokens`/`completion_tokens` are set via `set_attribute(..., response.prompt_tokens)`,
i.e. native Python `int` values, not `str(...)`-coerced — the OpenTelemetry SDK stores them as
`int`-typed span attributes. This matters because the Azure Monitor exporter preserves the OTel
attribute's native type into `customDimensions` (see `app-insights-custom-dimensions.md` §1) —
setting an `int` attribute here is what keeps the value as a queryable number downstream rather
than a quoted string a KQL `toint()` cast would otherwise be needed to work around every time.

## 2. Validation performed in this pass

Added `src/prompt-agent/tests/test_token_usage_validation.py` — three tests, run against a batch of
25 synthetic LLM invocations (all 5 entries from `synthetic/scenarios.py`, repeated 5 times each
with distinct correlation IDs, comfortably over the issue's "20+ synthetic spans" bar):

1. `test_every_llm_span_has_all_three_token_count_attributes` — asserts
   `llm.token_count.prompt`/`.completion`/`.total` are present on **100%** of the 25 LLM spans.
2. `test_token_counts_are_internally_consistent_across_batch` — asserts `prompt + completion ==
   total` for every one of the 25 spans (zero inconsistent rows).
3. `test_token_count_attributes_are_native_int_not_stringified` — asserts every token-count
   attribute value is a native Python `int` (explicitly excluding `bool`, which is a subclass of
   `int` in Python and would otherwise false-pass an `isinstance(..., int)` check).

**Execution note:** no Python interpreter is available in this validation environment (`python`/`py`
both report no installed interpreter found), so this test file could not actually be executed here.
It was written to the same conventions as the existing, already-passing
`src/prompt-agent/tests/test_agent_spans.py` suite (same `span_exporter`/`find_spans` fixtures, same
`StubFoundryModelClient`-based invocation pattern) and manually traced against `agent.py`/
`model_client.py` source to confirm the assertions are correct given that code. **This must be
re-run with a working Python 3.10+ environment (`pip install -e ".[test]"` then `pytest tests`
under `src/prompt-agent`) before being relied on as passing CI evidence** — flagging this
explicitly rather than claiming an untested result as validated, per charter ("every claim about
telemetry is backed by a validation query or test" — the test exists and is reasoned through, but
has not been executed in this pass).

## 3. Validation KQL (once a live App Insights instance exists)

```kql
AppDependencies
| where customDimensions["openinference.span.kind"] == "LLM"
| extend promptTok = toint(customDimensions["llm.token_count.prompt"])
| extend compTok = toint(customDimensions["llm.token_count.completion"])
| extend totalTok = toint(customDimensions["llm.token_count.total"])
| extend consistent = (promptTok + compTok == totalTok)
| summarize count(), countif(consistent == false)
```

Expected result once run against ≥20 synthetic LLM spans: `count_` ≥ 20, `countif_` (inconsistent
count) == 0 — matching issue #34's acceptance criteria and expected evidence exactly.

## 4. Telemetry-mapping issues

Per issue #34's acceptance criterion ("telemetry-mapping issue filed for each of the three token
fields"), these three fields are covered as the "token fields" group in #36's field-mapping doc
(`field-mapping.md`) rather than as three standalone issues, since all three share identical source
(`agent.py`), transformation logic, and correlation requirements — see that doc's grouping
rationale.

## Related

- [`app-insights-custom-dimensions.md`](./app-insights-custom-dimensions.md) (#32)
- [`custom-dimensions-schema.md`](./custom-dimensions-schema.md) (#33)
- [`field-mapping.md`](./field-mapping.md) (#36, not yet merged at time of writing)
