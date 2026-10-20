# src/prompt-agent

**Status: existing CLI is an offline synthetic scaffold. A separate once-only
Foundry Responses caller is implemented and offline-tested, NOT live-accepted.**

This directory holds the local synthetic Prompt Agent scaffold, instrumented with
OpenTelemetry and OpenInference semantic conventions for LLM spans (model name, token usage,
prompt/completion content references, correlation ID).

See `/.github/copilot-instructions.md` §9 for the required OpenTelemetry/OpenInference span and
attribute conventions that code in this directory must follow.

Only validated, implemented code belongs here. Conceptual or proposed changes to how the Prompt
Agent exports telemetry (e.g. direct OTLP export) belong under `/docs/future-state` instead, not
as stubs or partial implementations in this directory.

The CLI includes synthetic scenario responses, instrumentation and bounded retries.
It always uses the stub client; setting endpoint or credential variables does not
turn it into the independently deployed Foundry Prompt Agent.

## Separate no-tool Foundry Responses caller (#147)

`prompt-agent` and `python -m prompt_agent.main` remain unchanged/offline.
`foundry-responses-once` / `python -m prompt_agent.foundry_responses` is a
**different**, explicit live entrypoint. It never registers an agent, creates a
conversation, chooses a model, falls back, streams, polls or retries.
It uses the pinned SDK contract in
[Agent prerequisites](../../docs/current-state/issue147-private-agent-prerequisites.md):
project API **v1**, HTTPS POST `<project-endpoint>/openai/v1/responses`,
exact `agent_reference` **name + numeric version**, no tools. ARM **2025-09-01**
is a separate provisioning boundary.

From the repository/worktree root, install in your approved environment:

```powershell
python -m pip install -e "src\prompt-agent[foundry,test]"
python -m prompt_agent.foundry_responses --help
python -m prompt_agent.foundry_responses --endpoint https://synthetic-account.services.ai.azure.com/api/projects/synthetic-project --agent-name synthetic-no-tool --agent-version 7 --run-id 7580d28b-7bdf-4ada-afdd-dcaea1ca0147 --authorization-reference synthetic-unapproved-example --executor-reference synthetic-private-runner-mi --dry-run
python -B -m pytest -q -p no:cacheprovider src\prompt-agent\tests
```

The dry run is genuinely offline: no credential/client construction, ledger or
network. These names/UUIDs are synthetic examples, **not live authorization**.
Pinned opt-in dependencies are `azure-ai-projects==2.0.0`,
`azure-identity==1.26.0`, `openai==2.26.0`, `azure-core[aio]==1.41.0`
(async HTTP transport required). This is not a complete transitive wheel lock.
The `test` extra includes these same pins so standard `.[test]` installs and CI
exercise the mocked SDK contract tests without authentication.

**Future live command, DO NOT run under this checkpoint:** use the same module
command with the approved fresh private endpoint/name/version, fresh lowercase
UUID and fresh nonsecret authorization reference, replace `--dry-run` with
`--allow-live`, and optionally add `--managed-identity-client-id <approved-MI-client-UUID>`.
`--executor-reference` must identify the approved private runner/MI custody
attestation; it is bound into the intent, not independently verified by this CLI.
Missing `--allow-live` exits 1 before authentication. Only
`ManagedIdentityCredential` is used; no DefaultAzureCredential, CLI cache,
dotenv, keys or automatic authentication fallback. Federated-token-file
configuration is refused. The MI must already be authorized; this code grants
nothing.

**Once-only custody is mandatory:** `.foundry-live-receipts` at this source
checkout's root holds exclusive immutable run-ID and authorization intents,
fsynced **before** auth/submission, and a separate exclusive outcome. Reuse of
either identifier, any existing receipt, incomplete write, crash/inflight intent,
failed or ambiguous outcome is refused. No reset/delete/resume facility exists.
Do not remove/move receipts, change checkout/host to evade a stop, or reuse the
authorization elsewhere. Preserve the operator-owned durable ledger with the
approved executor; this is a local filesystem guard, not a distributed/global
idempotency service or a guarantee against administrator tampering, storage
rollback or power-loss metadata loss. Reparse/symlink directories are rejected;
Windows directory handles deny rename/deletion during execution; POSIX uses
directory-relative exclusive creation. Existing files are never read or followed.
Only one custodian/executor/checkout may hold a given authorization.

The one built-in ASCII fixture is under 1 KiB and explicitly synthetic; no
arbitrary input is accepted. `max_output_tokens=1024` includes reasoning;
returned text is required and checked at ≤16 KiB but never logged/printed/stored.
Actual input/output/total usage is mandatory, integer/nonnegative/additive and
within 1,024 input/output tokens; missing/invalid usage is failure, not estimated
zero. The approved published definition must separately establish the total
input bound, exact model deployment and no tools; this caller does not attest it.

All relevant client retries are zero, including MI HTTP retry policy.
Connect/read/write/pool timeouts are 5/20/10/5 seconds for Responses,
MI connect/read are 5/20 seconds, and the async auth/create/close operation has a
60-second overall cancellation deadline. Timeout/auth/429/5xx/parse/usage/output/
receipt failure exits 1, leaves an immutable intent and records **ambiguous**
where writable: STOP, reconcile out-of-band, **never rerun**. An outcome write
failure cannot turn a request into a reported success. Dependency logging and
raw exception recording are suppressed during execution.

The optional local OTel span is explicitly **CLIENT**, not a native Agent span.
It preserves the current parent/trace context, adds `correlation.id`, sends W3C
`traceparent` when available and `x-ms-client-request-id`, and records returned
numeric usage/response ID only. No exporter is configured by this entrypoint.
Header transmission is tested; native service propagation/ingestion and
App Insights → LAW → Event Hub → Function → Arize acceptance remain unproven.
There is no direct Arize/OTLP path.

Live prerequisites remain QA's fresh exact-envelope approval, approved private
runner/MI/DNS, provider/capacity gates, published no-tool version/readback and
definition hash, immutable dependency/package custody, preserved ledger and
cost/retained-state gates. Historical VM success and these mocks are **not**
fresh live acceptance. #147 remains open; PR #151 remains unmerged.

## Requirements

- Python 3.10+

## Setup

```powershell
Set-Location .\src\prompt-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
```

## Running tests (#31)

```powershell
Set-Location .\src\prompt-agent
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
- every scenario in the #48 shared synthetic prompt library (`synthetic/scenarios.py`) produces
  a response with no unhandled error, a root span with a valid trace ID, and sane/relevant
  response content (`tests/test_scenario_validation.py`, #49)

Run the commands above for the current result. Historical execution evidence is
separate from live model or destination validation.

## Configuration

All configuration is read from environment variables — **never hardcoded**.
Local defaults are obviously fake, so the scaffold runs without Azure resources.
The supported modern infrastructure uses an Entra-authenticated, local-auth-disabled
Foundry account. Its project endpoint has the form
`https://<custom-subdomain>.services.ai.azure.com/api/projects/<project-name>`;
it is not an ML workspace discovery URL. The deployment name is the configured
model deployment alias, not its catalog model name or version.

| Variable | Purpose | Local default |
|---|---|---|
| `FOUNDRY_ENDPOINT` | Foundry project endpoint | `https://synthetic-placeholder.foundry.azure.com` |
| `FOUNDRY_DEPLOYMENT_NAME` | Model deployment name | `synthetic-gpt-demo` |
| `FOUNDRY_API_KEY` | Legacy scaffold field used only for the configuration label; not modern Foundry authentication | `REPLACE_ME_SYNTHETIC_KEY` |
| `OTEL_SERVICE_NAME` | OpenTelemetry resource `service.name` | `foundry-prompt-agent` |
| `OTEL_SERVICE_VERSION` | OpenTelemetry resource `service.version` | `0.1.0` |
| `DEPLOYMENT_ENVIRONMENT` | OpenTelemetry resource `deployment.environment` | `dev` |

None of the defaults above are real credentials or endpoints — they are
intentionally obvious placeholders.

No API key is needed for the offline demo. A live caller requires its own approved
Entra identity and project permissions; the project's managed identity is not the
caller identity. Foundation provisioning does not publish an agent version,
restore agent/thread/file state or prove private agent runtime readiness.
See [ADR-0004](../../docs/adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md)
and the [infrastructure guide](../../infra/README.md) for the modern foundation
and separate runtime prerequisites. The separate once-only Responses entrypoint above is opt-in and not live-accepted;
the offline CLI has no automatic public/authentication fallback.

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

## Validating Prompt Agent execution against the shared scenario library (#49)

`tests/test_scenario_validation.py` parametrizes over every scenario in `synthetic/scenarios.py`
(the #48 shared synthetic prompt library) and asserts, per scenario: no unhandled error, a root
`prompt_agent.invoke` span with a valid (non-zero) trace ID, and a non-empty response containing
an expected keyword relevant to that prompt. Run it with:

```powershell
pytest tests/test_scenario_validation.py -v
```

See `/docs/current-state/prompt-agent-execution-validation.md` for the full validation procedure,
checklist, evidence table, and an explicit breakdown of what's proven by this static test suite
versus what still requires a live Foundry deployment (this repo's default `StubFoundryModelClient`
is not a live model backend).

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
    ├── test_correlation_and_retry.py  # Correlation ID propagation, incl. across retries
    └── test_scenario_validation.py    # #49: every shared-library scenario succeeds + has a valid root-span trace ID + a sane response
```

## Data policy

Every example, fixture, and test in this project uses **synthetic data
only**. See `synthetic/README.md` for the fixture-naming convention.
