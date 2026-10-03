# foundry-otel-to-arize-demo

A reusable observability demo showing how to instrument a **Microsoft Foundry Prompt Agent**
end-to-end with OpenTelemetry/OpenInference, capture the resulting telemetry in **Application
Insights**, transform and forward it, and visualize/correlate traces, spans, and token usage in
**Arize**.

Built for field engineers to clone, deploy, run, and credibly demo to enterprise healthcare
customers evaluating observability for Foundry Prompt Agents. **All data in this repo — prompts,
responses, screenshots, logs, demo scripts — is synthetic.** See
[`/.github/copilot-instructions.md`](.github/copilot-instructions.md) for full repository
conventions.

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

## Contributing

This repo is maintained using the [Squad](.squad) team framework. See
[`.github/copilot-instructions.md`](.github/copilot-instructions.md) for conventions on
architecture, security, telemetry, testing, and documentation that apply to every contribution.
