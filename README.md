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

> This is a minimal placeholder README. A fuller version documenting the complete repository
> structure lands via issue #12 (Repository structure scaffolding and enforcement).
