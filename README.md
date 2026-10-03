# foundry-otel-to-arize-demo

A reusable observability demo showing how to instrument a **Microsoft Foundry Prompt Agent**
end-to-end with OpenTelemetry/OpenInference, capture the resulting telemetry in **Application
Insights**, transform and forward it, and visualize/correlate traces, spans, and token usage in
**Arize**.

## Overview and customer scenario

This repository exists so a Microsoft field engineer can **clone it, deploy the current-state
pipeline, run a demo end-to-end, and credibly explain — to a customer's own engineers — both what
is validated today and what is still a proposal**, without guessing or overstating readiness.

The intended audience is **enterprise healthcare customers evaluating observability for Foundry
Prompt Agents** (e.g., UnitedHealth Group, CVS Health, Elevance Health). The content is written to
be credible and reusable across any healthcare enterprise — it is not tied to one named customer's
real environment, and it must never be. **All data in this repo — prompts, responses, screenshots,
logs, demo scripts — is synthetic**: no real patient, member, claims, or other PII/PHI data is ever
used, in code, docs, tests, issues, or commit history. See
[`/.github/copilot-instructions.md`](.github/copilot-instructions.md) for the full repository
conventions this project follows, including the data policy quoted above.

## Table of contents

- [Overview and customer scenario](#overview-and-customer-scenario)
- [What this demo proves](#what-this-demo-proves)
- [Quick start](#quick-start)
- [Prerequisites](#prerequisites)
- [Setup and configuration](#setup-and-configuration)
- [Architecture](#architecture)
- [Documentation map](#documentation-map)
- [Repository structure](#repository-structure)
- [Known limitations and open gaps](#known-limitations-and-open-gaps)
- [Contributing](#contributing)

## What this demo proves

This demo exists to let a field engineer credibly show — and a customer's own engineers
independently re-verify, using only synthetic data — the following capabilities. Status reflects
what is actually validated in this repository today; see
[`docs/validation/demo-validation-plan.md`](docs/validation/demo-validation-plan.md) for the full
evidence trail behind every row.

| # | Capability | Status |
|---|---|---|
| 1 | Prompt Agent execution (invoke + response) | ✅ Validated |
| 2 | Application Insights capture of spans/traces | ✅ Validated |
| 3 | OpenInference attribute mapping (model, prompt/response, token counts) | ✅ Validated |
| 4 | Token-usage telemetry (prompt/completion/total) | ✅ Validated at source; ⚠️ not yet confirmed through Arize |
| 5 | Trace/span/parent-span-ID preservation | ⚠️ Validated at source; Event Hub/Function hops not yet built |
| 6 | Export-pipeline execution (Event Hub → Azure Function) | 🔴 Infrastructure provisioned; transform code not yet implemented |
| 7 | Telemetry schema transformation (App Insights → OTLP) | 🔴 Fully specified; not yet implemented |
| 8 | Arize OTLP ingestion | 🔴 Not yet implemented (depends on #6/#7) |
| 9 | Arize trace visualization | 🔴 Not yet implemented (depends on #8) |
| 10 | Error/retry handling with full traceability | ✅ Validated |
| 11 | Exporter observability (console/Azure Monitor dual export) | ✅ Validated |

**In short: the Prompt Agent half of this pipeline (capabilities 1-5, 10-11) is built, tested, and
demoable today. The telemetry-export half into Arize (6-9) is fully designed — infrastructure is
provisioned and the schema mapping is specified field-by-field — but the transform code itself has
not been written yet.** Do not demo capabilities 6-9 as working; see
[`demo/narrative.md`](demo/narrative.md) and [`demo/fallback.md`](demo/fallback.md) for how to
talk about this honestly if asked.

## Quick start

This is the fast path for a field engineer who just wants to see the demo run. It is **honest
about what works without any live Azure/Arize environment versus what a real demo requires** — see
[What this demo proves](#what-this-demo-proves) for the full capability-by-capability breakdown.

| Step | Command(s) | Requires a live Azure/Arize environment? |
|---|---|---|
| 1. Clone | `git clone https://github.com/rob-mckenna/foundry-otel-to-arize-demo.git` | No |
| 2. Configure env (no secrets committed) | Set env vars per [`src/prompt-agent/README.md#configuration`](src/prompt-agent/README.md#configuration); every local default is an obviously-fake placeholder | No — only required to export to a *real* App Insights resource |
| 3. Deploy infra | `az deployment group create -g <rg> -f infra/main.bicep -p infra/main.parameters.json` | **Yes** — Azure subscription with deployment permissions |
| 4. Run the Prompt Agent | `pip install -e ".[test]"` then `python -m prompt_agent.main --scenarios` from `src/prompt-agent/` | No — runs today against a stub model client and prints spans to console by default |
| 5. Observe telemetry | Look up the printed correlation ID in Application Insights (if step 3 ran) or read the console span output directly | Console output: no. App Insights lookup: yes |

**What you can demo with zero Azure/Arize access:** steps 1, 2, and 4 — the Prompt Agent invoking
synthetic scenarios, emitting OpenTelemetry/OpenInference spans, and printing token counts and a
correlation ID to the console (and passing its own test suite via `pytest`).

**What requires a live environment:** confirming those same spans land in a real Application
Insights resource (step 3/5), and — not yet possible at all today, regardless of environment —
seeing them flow through Event Hub → Azure Function → Arize, because that transform code has not
been written yet (see the capability table below and
[`src/telemetry-pipeline/README.md`](src/telemetry-pipeline/README.md)).

Never commit secrets (connection strings, API keys) — configuration is environment-variable only,
and real values are pulled from Key Vault, never hardcoded or checked in.

## Prerequisites

- An **Azure subscription** with permission to create resource groups, Bicep deployments, and RBAC
  role assignments.
- **Azure CLI** (`az`) installed and authenticated (`az login`), with the Bicep extension
  (`az bicep install` / `az bicep upgrade`).
- **Microsoft Foundry access** (a Foundry project/hub you can deploy into, or use
  `infra/modules/foundry-project.bicep` to provision one). The Prompt Agent code in this repo runs
  today against a stub model client by default — a real Foundry project is only required once you
  wire in a live model deployment.
- **Python 3.10+** and **PowerShell 7+**.
- An **Arize account/API key** — **not required to run today's demo** (see the capability table
  above); only needed once the Event Hub → Function → Arize export pipeline is implemented.

No step in this README requires a real patient, member, or claims record — every example uses the
synthetic fixtures in [`src/prompt-agent/synthetic/scenarios.py`](src/prompt-agent/synthetic/scenarios.py).

## Setup and configuration

### 1. Clone and deploy infrastructure

```powershell
git clone https://github.com/rob-mckenna/foundry-otel-to-arize-demo.git
cd foundry-otel-to-arize-demo/infra
az deployment group what-if -g <resource-group> -f main.bicep -p main.parameters.json
az deployment group create  -g <resource-group> -f main.bicep -p main.parameters.json
```

See [`infra/README.md`](infra/README.md) for the full module list, naming convention, and the
RBAC/managed-identity model (no secrets are ever passed as Bicep parameters).

### 2. Set up the Prompt Agent

```powershell
cd src/prompt-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
```

Configuration is environment-variable only — **never hardcoded** — and every local default is an
obviously-fake placeholder (see the full table in
[`src/prompt-agent/README.md`](src/prompt-agent/README.md#configuration)). To export spans to a
real Application Insights resource instead of the console, set
`APPLICATIONINSIGHTS_CONNECTION_STRING` (pulled from Key Vault — never committed) and install the
optional Azure extra: `pip install -e ".[azure]"`.

Confirm the agent is healthy:

```powershell
pytest
```

### 3. Run the demo walkthrough (synthetic prompts)

```powershell
python -m prompt_agent.main --scenarios
```

This runs all 5 synthetic member-services scenarios from
`src/prompt-agent/synthetic/scenarios.py` (fabricated member IDs, fabricated plan names — see that
file's docstring) end-to-end, printing the prompt, any tool lookup, the response, and token counts
for each, and generating a fresh correlation ID per run that you can look up in Application
Insights. For the full narrated version of this walkthrough — including exactly what to show and
say — see [`demo/narrative.md`](demo/narrative.md); for setup → run → teardown operational detail,
see [`demo/runbook.md`](demo/runbook.md).

### 4. Tear down

```powershell
az group delete -g <resource-group> --yes --no-wait
az resource list -g <resource-group> --output table   # confirm empty once deletion completes
```

## Architecture

- **Current-state (validated, implemented):** [`/docs/current-state/architecture.md`](docs/current-state/architecture.md)
- **Future-state (conceptual, not implemented):** [`/docs/future-state`](docs/future-state)
- **Architecture Decision Records:** [`/docs/adr`](docs/adr)
- **Demo Validation Plan (capability-by-capability evidence):** [`/docs/validation/demo-validation-plan.md`](docs/validation/demo-validation-plan.md)

## Documentation map

Use this table to jump straight to the doc you need instead of hunting through directories.

| Doc | What it's for |
|---|---|
| [`docs/current-state/`](docs/current-state/) | Architecture, runbooks, and validation notes for what is **implemented today** |
| [`docs/future-state/`](docs/future-state/) | **CONCEPTUAL — NOT IMPLEMENTED** direct-OTLP design proposal and dependencies |
| [`docs/telemetry/mapping/`](docs/telemetry/mapping/) | Field-by-field schema mapping specs (identity/correlation fields, LLM I/O fields, span-kind/status fields, token fields) that the telemetry-pipeline transform must implement |
| [`docs/telemetry/kql/`](docs/telemetry/kql/) | KQL validation query pack for a live Application Insights instance (span-kind coverage, token-count consistency, correlation-ID completeness, export latency, schema drift) |
| [`docs/validation/demo-validation-plan.md`](docs/validation/demo-validation-plan.md) | The authoritative, capability-by-capability demo validation plan and shared synthetic prompt set |
| [`demo/narrative.md`](demo/narrative.md) | The narrated walkthrough — exactly what to show and say during a customer demo |
| [`demo/runbook.md`](demo/runbook.md) | Setup → run → teardown operational detail for running the demo |
| [`demo/one-pager.md`](demo/one-pager.md) | A one-page leave-behind summary for customer stakeholders |
| [`demo/fallback.md`](demo/fallback.md) | How to talk honestly about capabilities that aren't demoable yet if a customer asks |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | The doc-drift checklist to run through before opening a PR that changes architecture or behavior |
| [`src/telemetry-pipeline/README.md`](src/telemetry-pipeline/README.md) | Status and scope of the (not-yet-implemented) Event Hub → Azure Function → Arize transform code |

## Repository Structure

```
/
├── .github/                      # Issue templates, PR template, workflows, copilot-instructions.md
├── .squad/                       # Squad team framework (charters, routing, decisions) — not product code
├── src/
│   ├── prompt-agent/              # Foundry Prompt Agent implementation + OTel/OpenInference instrumentation (CURRENT-STATE)
│   └── telemetry-pipeline/        # Azure Function transform/mapping code, Event Hub consumers (CURRENT-STATE)
├── infra/
│   ├── bicep/                     # Bicep modules (preferred IaC) — App Insights, Log Analytics, Event Hub, Function, Key Vault (CURRENT-STATE)
│   └── terraform/                 # Optional Terraform alternative, mirrors bicep/ module boundaries (CURRENT-STATE)
├── docs/
│   ├── current-state/             # Architecture docs, runbooks, diagrams for what is implemented and validated
│   ├── future-state/              # Conceptual direct-OTLP design docs, diagrams, proposals — NEVER implementation code
│   └── adr/                       # Architecture Decision Records (process, template, and recorded decisions)
├── tests/
│   ├── telemetry-mapping/         # Tests validating Event Hub → Function → Arize schema mapping
│   └── export/                    # Tests validating OTLP export behavior
├── demo/                          # Demo scripts, synthetic prompts/transcripts, narrated walkthrough assets
└── README.md                      # This file
```

Each directory above contains its own `README.md` stating its purpose and current-state/future-state
status. Current-state (validated) code lives only under `/src` and `/infra`; future-state
(conceptual) design work lives only under `/docs/future-state` — the two are never mixed (see
[`/.github/copilot-instructions.md`](.github/copilot-instructions.md) §4).

## Known limitations and open gaps

Being explicit about what's not yet solid is part of this repo's demo-honesty convention (see
[`/.github/copilot-instructions.md`](.github/copilot-instructions.md) §16). Current known open
items:

- **[#37 — Trace/span/parent-span/correlation-ID preservation across Event Hub and Function
  hops](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/37)** (reopened). The
  Prompt Agent side preserves these identifiers at the source (validated), but preservation across
  the Event Hub → Azure Function hops cannot be confirmed until the transform code in
  [`src/telemetry-pipeline/`](src/telemetry-pipeline/) exists and is exercised against real traffic
  — this issue tracks that evidence gap and remains open pending it.
- **[#130 — Prompt Agent exporter observability gap](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/130)**:
  `force_flush()`'s result is currently discarded and there is no export success/failure counter,
  so a silent exporter failure would not currently surface as an operator-visible signal.
- **The Event Hub → Azure Function → Arize transform has no implementation code yet** — see
  [`src/telemetry-pipeline/README.md`](src/telemetry-pipeline/README.md). The schema mapping is
  fully specified and reviewed ([`docs/telemetry/field-mapping.md`](docs/telemetry/field-mapping.md),
  [`docs/telemetry/mapping/`](docs/telemetry/mapping/)) and infrastructure is provisioned, but
  capabilities 6-9 in the table above are not demoable as working today.
- **The KQL validation query pack** ([`docs/telemetry/kql/`](docs/telemetry/kql/)) is written and
  reasoned through against the documented schema but has not been executed against a live
  Application Insights instance in this pass — treat it as validated-via-review, not
  live-validated, until re-run against a real workspace with synthetic demo traffic.

If you find an additional gap while using this repo, file it as a `bug-report.yml` issue rather
than silently working around it — see [Contributing](#contributing).

## Contributing

This repo is maintained using the [Squad](.squad) team framework. See
[`.github/copilot-instructions.md`](.github/copilot-instructions.md) for conventions on
architecture, security, telemetry, testing, and documentation that apply to every contribution,
and [`CONTRIBUTING.md`](CONTRIBUTING.md) for the short doc-drift checklist to run through before
opening a PR that changes architecture or behavior.
