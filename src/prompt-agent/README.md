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
│   ├── agent.py               # Core prompt/response flow + synthetic tool call (#25)
│   └── model_client.py        # Model backend interface + stub Foundry client (#25)
├── synthetic/                # Synthetic fixture data — no real customer data, ever
│   ├── README.md
│   └── scenarios.py           # 5 synthetic member-services demo scenarios (#25)
├── samples/                  # Captured sample prompt/response output (#25)
└── tests/                    # pytest unit tests
```

## Data policy

Every example, fixture, and test in this project uses **synthetic data
only**. See `synthetic/README.md` for the fixture-naming convention.
