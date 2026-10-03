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

## Architecture

- **Current-state (validated, implemented):** [`/docs/current-state/architecture.md`](docs/current-state/architecture.md)
- **Future-state (conceptual, not implemented):** [`/docs/future-state`](docs/future-state)
- **Architecture Decision Records:** [`/docs/adr`](docs/adr)

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
architecture, security, telemetry, testing, and documentation that apply to every contribution,
and [`CONTRIBUTING.md`](CONTRIBUTING.md) for the short doc-drift checklist to run through before
opening a PR that changes architecture or behavior.
