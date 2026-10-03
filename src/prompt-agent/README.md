# src/prompt-agent

**Status: CURRENT-STATE (validated, implemented)**

This directory holds the Microsoft Foundry Prompt Agent implementation, instrumented with
OpenTelemetry and OpenInference semantic conventions for LLM spans (model name, token usage,
prompt/completion content references, correlation ID).

See `/.github/copilot-instructions.md` §9 for the required OpenTelemetry/OpenInference span and
attribute conventions that code in this directory must follow.

Only validated, implemented code belongs here. Conceptual or proposed changes to how the Prompt
Agent exports telemetry (e.g. direct OTLP export) belong under `/docs/future-state` instead, not
as stubs or partial implementations in this directory.

> This scaffold (#24) ships a placeholder "hello agent" response only. The real
> prompt/response flow, OpenTelemetry instrumentation, and retry logic are
> added incrementally in follow-on issues (#25–#31).

## Requirements

- Python 3.10+

## Setup

```powershell
cd src/prompt-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
```

## Running tests (#31)

```powershell
cd src/prompt-agent
pip install -e ".[test]"
pytest
```

The suite uses OpenTelemetry's `InMemorySpanExporter` (attached alongside
the normal console/Azure Monitor exporter — see `tests/conftest.py`) so
every assertion runs fully in-process, with no console noise or network
calls, asserting:

- spans are created with the expected names, `SpanKind`, and correct
  parent-child linkage (`tests/test_agent_spans.py`)
- OpenInference attributes (`openinference.span.kind`, `input.value`,
  `output.value`, `llm.model_name`, `llm.token_count.*`) are present and
  correct (`tests/test_agent_spans.py`)
- token counts are captured on both the span attributes and
  `AgentResult.response` (`tests/test_agent_spans.py`)
- the correlation ID is generated when absent, honored when the caller
  supplies one, and is attached to **every** span in a request's tree,
  **including every retry attempt span** — both for a retry that
  eventually recovers and one that exhausts all attempts and raises
  (`tests/test_correlation_and_retry.py`)

All 11 tests pass as of this writing.

## Configuration

All configuration is read from environment variables — **never hardcoded**.
In a real deployment these are populated via Azure Key Vault references on
the hosting App Service / Function App; locally they default to obviously-
fake placeholder values so the scaffold runs without any Azure resources.

| Variable | Purpose | Local default |
|---|---|---|
| `FOUNDRY_ENDPOINT` | Foundry project endpoint | `https://synthetic-placeholder.foundry.azure.com` |
| `FOUNDRY_DEPLOYMENT_NAME` | Model deployment name | `synthetic-gpt-demo` |
| `FOUNDRY_API_KEY` | API key (sourced from Key Vault in real deployments) | `REPLACE_ME_SYNTHETIC_KEY` |
| `OTEL_SERVICE_NAME` | OpenTelemetry resource `service.name` | `foundry-prompt-agent` |
| `OTEL_SERVICE_VERSION` | OpenTelemetry resource `service.version` | `0.1.0` |
| `DEPLOYMENT_ENVIRONMENT` | OpenTelemetry resource `deployment.environment` | `dev` |

None of the defaults above are real credentials or endpoints — they are
intentionally obvious placeholders.

## OpenTelemetry / Application Insights export (#26)

| Variable | Purpose | Local default |
|---|---|---|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights connection string (set by Infrastructure's #16 provisioning) | unset → falls back to console exporter |

- If `APPLICATIONINSIGHTS_CONNECTION_STRING` is set, spans export to
  Application Insights via `azure-monitor-opentelemetry-exporter` (install
  with `pip install -e ".[azure]"`).
- If it is unset (e.g. local dev, this sandbox, or CI), spans export to the
  console via `ConsoleSpanExporter` instead — the SDK still runs and is
  fully testable without any live Azure resources.
- `prompt_agent.telemetry.configure_tracing()` is idempotent (safe to call
  more than once) and registers an `atexit` flush/shutdown hook so buffered
  spans are not lost on process exit.

## OpenInference attribute mapping (#28)

Every model/tool span (see "Span instrumentation" below) carries
[OpenInference](https://github.com/Arize-ai/openinference) trace
semantic-convention attributes, using the `openinference-semantic-conventions`
package **pinned to the `0.1.x` spec** (`>=0.1.39,<0.2.0` in `pyproject.toml`)
so attribute key names track the upstream spec rather than being hand-typed
string literals that could drift.

| Span | `openinference.span.kind` | Other attributes |
|---|---|---|
| `prompt_agent.invoke` | `CHAIN` | `input.value` (original user prompt), `output.value` (final response text) |
| `tool.lookup_plan_details` | `TOOL` | `input.value` (plan name), `output.value` (lookup result) |
| `llm.chat_completion` | `LLM` | `input.value` (effective prompt sent to the model), `output.value` (model response text), `llm.model_name`, `llm.token_count.prompt`, `llm.token_count.completion`, `llm.token_count.total` |

Token counts come straight from `ModelResponse` (real API-reported counts
once a real Foundry client is wired in; whitespace-estimated for the current
stub — see `model_client.py`), not re-derived at the span layer. See
`samples/openinference-attribute-validation.md` for captured validation
evidence, including a cross-check that `total == prompt + completion` for
every scenario.

## Correlation ID propagation (#29)

`PromptAgent.invoke()` accepts an optional `correlation_id` argument; if the
caller doesn't supply one (e.g. no upstream request ID to preserve), a new
one is generated (`prompt_agent.correlation.generate_correlation_id()`, a
`uuid4`) at the start of that call. The same correlation ID is then attached
as a `correlation.id` attribute on **every span in that request's tree** —
`prompt_agent.invoke`, `tool.lookup_plan_details`, and `llm.chat_completion`
— and is also returned on `AgentResult.correlation_id` so a calling layer
can log or return it without inspecting span data.

**Telemetry coordination note:** the attribute key is exactly `correlation.id`
(see `correlation.py`) — this is a custom key (OpenTelemetry/OpenInference
have no first-party "correlation ID" semantic convention), distinct from
OTel's own `trace_id`. It exists specifically so a request remains joinable
by one key regardless of how many traces its work happens to span (see
`samples/correlation-id-propagation-validation.md` for why this matters even
in a single-process demo where every request currently shares one
`trace_id`).

## Retry / error-handling with full traceability (#30)

The model call (`llm.chat_completion`) is wrapped in bounded
exponential-backoff retry logic (`prompt_agent/retry.py`,
`call_with_retry`). Configuration (env vars, all optional, see
`config.py`):

| Variable | Purpose | Default |
|---|---|---|
| `RETRY_MAX_ATTEMPTS` | Max attempts before giving up | `3` |
| `RETRY_INITIAL_BACKOFF_SECONDS` | Sleep before the 2nd attempt | `0.1` |
| `RETRY_BACKOFF_MULTIPLIER` | Multiplier applied to the backoff after each failed attempt | `2.0` |

Only exceptions in `RetryConfig.retryable_exceptions` (currently
`TransientModelError` — see `model_client.py`) are retried; anything else
fails immediately. Behavior:

- **Every attempt is its own child span** (`llm.chat_completion.attempt`),
  carrying `retry.attempt` (1-indexed), `retry.max_attempts`, and
  `correlation.id` — so every retry attempt remains traceable back to the
  original request, not just the final outcome.
- A successful attempt returns immediately; **a recovered retry still
  reports the overall call as a success** (`llm.chat_completion` and
  `prompt_agent.invoke` both end up `OK`).
- A failed attempt is explicitly marked `ERROR` with a recorded exception
  event (needed because the exception is caught *inside* the attempt span
  rather than left to propagate — see `retry.py`'s module docstring for why
  OTel's default exception-recording behavior alone isn't enough here).
- If every attempt fails, the final exception propagates up through
  `llm.chat_completion` and `prompt_agent.invoke`, marking both `ERROR` too
  — a terminal failure after exhausting retries is exactly as traceable as
  a single failed call was in #27.

See `samples/retry-validation.md` for captured evidence of both a
recovered-after-2-failures case and an exhausted-all-retries failure case.

## Running locally

```powershell
python -m prompt_agent.main
```

Expected output (placeholder "hello agent" response):

```
Hello from Foundry Prompt Agent 'foundry-prompt-agent' v0.1.0 (dev) — deployment='synthetic-gpt-demo' mode=SYNTHETIC/PLACEHOLDER.
```

To run the synthetic member-services/benefits-lookup scenarios end-to-end
(#25):

```powershell
python -m prompt_agent.main --scenarios
```

This calls `PromptAgent.invoke()` for each fixture in `synthetic/scenarios.py`
against the stub model client (`prompt_agent/model_client.py` —
`# STUB: replace with real Foundry Prompt Agent SDK call`) and prints the
prompt, any tool-lookup output, the response, and token counts for each. See
`samples/scenario-run-2026-10-02.md` for captured sample output.

## Project layout

```
src/prompt-agent/
├── pyproject.toml          # Package metadata + dependencies
├── README.md                # This file
├── prompt_agent/
│   ├── __init__.py
│   ├── main.py               # Entry point (placeholder hello + --scenarios runner)
│   ├── config.py             # Env-var configuration loading (no secrets committed)
│   ├── agent.py               # Core prompt/response flow + span instrumentation + OpenInference/correlation ID attrs + retry wiring (#25, #27, #28, #29, #30)
│   ├── model_client.py        # Model backend interface + stub Foundry client + TransientModelError + demo-only flaky client (#25, #30)
│   ├── correlation.py         # Correlation ID generation + attribute key constant (#29)
│   ├── retry.py                # Bounded exponential-backoff retry-with-tracing helper (#30)
│   └── telemetry.py           # OpenTelemetry SDK bootstrap: TracerProvider, exporter, shutdown hook (#26)
├── synthetic/                # Synthetic fixture data — no real customer data, ever
│   ├── README.md
│   └── scenarios.py           # 5 synthetic member-services demo scenarios (#25)
├── samples/                  # Captured sample prompt/response output (#25)
└── tests/                    # pytest unit tests (#31)
    ├── __init__.py
    ├── conftest.py             # InMemorySpanExporter fixture + span-lookup helpers
    ├── test_agent_spans.py     # Span names/kind/parent-linkage + OpenInference attrs + token counts
    └── test_correlation_and_retry.py  # Correlation ID propagation, incl. across retries
```

## Data policy

Every example, fixture, and test in this project uses **synthetic data
only**. See `synthetic/README.md` for the fixture-naming convention.
