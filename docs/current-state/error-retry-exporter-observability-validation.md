# Error/Retry Handling and Exporter Observability — Validation (#58)

**Status: Mixed. (a) Prompt Agent retry: CURRENT-STATE, validated. (b) Export-pipeline outage
handling: BLOCKED (no export pipeline exists). (c) Exporter observability: gap identified, filed
as a new issue — see §4.**

Validation record for
[#58 Validate error/retry handling and exporter observability](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/58),
depends on #30 (Prompt Agent retry implementation) and #36.

## 1. Acceptance criteria under validation

1. A simulated transient failure triggers the Prompt Agent's documented retry behavior (#30), and
   the retry is itself visible as a span event or additional span.
2. A simulated export-pipeline outage results in no silent data loss — either messages queue in
   Event Hub for later processing, or the failure is logged/alerted, not just dropped.
3. Exporter observability: confirm there's a way to see export success/failure counts; document
   what exists and file a gap issue for anything missing.

## 2. (a) Prompt Agent retry behavior — validated

`src/prompt-agent/prompt_agent/retry.py`'s `call_with_retry()` plus
`tests/test_correlation_and_retry.py` directly prove criterion 1, with real (not hypothetical)
assertions:

- `test_correlation_id_propagates_across_a_recovered_retry` uses `_FlakyModelClient` (fails twice,
  then succeeds) and confirms **three separate `llm.chat_completion.attempt` child spans** are
  created (`retry.attempt` = `[1, 2, 3]`), each carrying the same `correlation.id` as the final
  result, with statuses `[ERROR, ERROR, OK]` — the retry is visible as additional spans, exactly
  per criterion 1's wording, not just a log line or a hidden loop.
- `test_retries_exhausted_raises_and_marks_every_span_error` proves the failure-exhausted path:
  every attempt span is marked `ERROR`, `retry.will_retry` is `[True, False]` across the two
  configured attempts, and the exception propagates to mark the enclosing `llm.chat_completion` and
  `prompt_agent.invoke` spans `ERROR` too — so a terminal failure is fully traceable end-to-end,
  not silently swallowed.
- `retry.py`'s own design comments explain *why* this works even though the exception is caught
  inside the span context manager (which would otherwise suppress OTel's automatic
  exception-recording): it explicitly calls `span.record_exception()` +
  `span.set_status(ERROR)` on every failed attempt, retried or not.

**Criterion 1 is fully validated** — by existing, already-written automated tests, reviewed in this
session (not re-executed; no Python interpreter available).

## 3. (b) Export-pipeline outage handling — blocked

This criterion cannot be validated for the same structural reason as #54/#55/#56: there is no
Event Hub, no Azure Function code, and therefore no "temporarily disable the Function" scenario to
simulate. There is nothing downstream of the Prompt Agent's own export (App Insights) to induce an
outage in. This is a genuine implementation gap, not a defect — re-attempt once #19's Function code
and an Event Hub exist.

## 4. (c) Exporter observability — gap identified and filed

**What exists today:** `telemetry.py` uses a standard OTel SDK `BatchSpanProcessor` wrapping
either `AzureMonitorTraceExporter` or `ConsoleSpanExporter`. Direct code review shows:

- The OTel SDK's `BatchSpanProcessor` **does** invoke `on_end`/export internally and will retry
  per the exporter's own policy (Azure Monitor's exporter has built-in retry/backoff), but **this
  repo's own code does not currently expose or log** any count of "spans successfully exported"
  vs. "spans dropped/failed to export" — there is no custom success/failure metric, log line, or
  span-processor wrapper anywhere in `src/prompt-agent`.
- `shutdown_tracing()` calls `force_flush()` on process exit, but does not check or surface
  `force_flush()`'s boolean return value (which indicates whether the flush completed within
  timeout) — a flush that times out or partially fails would be **silently unnoticed** today.
- No Azure Function exists yet to have its own export-side observability (that would be a
  *separate* concern from the Prompt Agent's own export path, and is blocked along with the rest of
  §3).

**This is a real, concrete gap** — not "nothing exists to observe," but specifically that
`force_flush()`'s result is discarded and no export success/failure counter exists. Per this
issue's own acceptance criterion 3 ("document what exists and file a gap issue for anything
missing"), this has been filed as
[#130 "\[Gap\] Prompt Agent exporter observability: force_flush() result discarded, no export success/failure counter"](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/130)
rather than silently left as a doc-only note.

## 5. Sandbox limitation

No Event Hub/Function code and no Python interpreter exist in this session; §2's conclusions are
based on reviewing already-written, already-passing (per prior sessions) test code, not a fresh
execution.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | Retry visible as span/span-event, Prompt Agent | ✅ Validated — existing automated tests (3-attempt recovery + exhausted-retry cases) |
| 2 | Export-pipeline outage, no silent data loss | ❌ Blocked — no export pipeline exists to induce an outage in |
| 3 | Exporter success/failure observability | ⚠️ Gap identified: `force_flush()` return value discarded, no export success/failure counter exists. **Filed as [#130](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/130)** rather than silently noted |

**Overall verdict: Pass (criterion 1) / Blocked (criterion 2) / Gap filed (criterion 3)** — this is
the most "mixed" result in this validation batch, deliberately: Prompt Agent retry is genuinely
solid, export-pipeline resilience is blocked on the same missing infrastructure as everything else
in this batch, and the observability gap is real and actionable today (it doesn't require any new
infrastructure to fix — just a return-value check and a counter — so it was filed as a concrete,
immediately-workable issue rather than deferred indefinitely like §3).
