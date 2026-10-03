# Project Context

- **Owner:** Rob McKenna
- **Project:** foundry-otel-to-arize-demo — a reusable observability demo repository showing how to instrument Microsoft Foundry Prompt Agents with OpenTelemetry/OpenInference, capture telemetry in Application Insights, export it through a transformation pipeline, and visualize/correlate traces and token usage in Arize. Built to be reused across enterprise healthcare customers (UnitedHealth Group, CVS Health, Elevance Health, etc.) evaluating observability for Foundry Prompt Agents.
- **Stack:** Azure (Foundry, Application Insights, Log Analytics, Event Hub, Azure Functions, Key Vault, managed identities), Infrastructure-as-Code (Bicep/Terraform), OpenTelemetry + OpenInference semantic conventions, Arize OTLP ingestion
- **Created:** 2026-10-02

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->
- Telemetry Mapping issues require the full chain: App Insights source record → Azure Monitor field → OTel field → OpenInference attribute → Arize destination field → transformation logic → correlation requirements → validation query.
- Current-state pipeline (App Insights → Event Hub → Function → Arize OTLP) must stay documented separately from the future-state direct-OTLP design.
- Milestone 2 first pass (#32–#37): this sandbox has no Python interpreter and no live Azure resources — every "validated" claim had to be split into (a) what in-memory `InMemorySpanExporter` + direct source inspection actually proved, vs. (b) what's "documented, pending live instance/infra merge." Never claim a test passed without actually running it; say plainly when an environment can't execute what it wrote, and let a human/CI re-run it.
- App Insights `operation_Id`/`operation_ParentId`/`id` are already the exact same byte-width as OTel `trace_id`/`parent_span_id`/`span_id` — no hex-padding/conversion is needed between them, only "does the value survive each hop unchanged." The real correlation risk is entirely in Event Hub partition-key choice and Function batch-checkpointing strategy, not format translation — flagged to Infra before #17/#19 are implemented rather than discovered as a bug after.
- `customDimensions` values are exported from App Insights as strings regardless of the OTel SDK's original attribute type (int/bool) — every downstream Azure Function field mapping must explicitly re-cast, or numeric/boolean fields silently become quoted strings in Arize. This is the single highest-risk correctness bug class in the whole transform step.
- Issues referencing attributes the agent doesn't actually emit (e.g. #32 listed `llm.input_messages`/`llm.output_messages`, but the agent only sets `input.value`/`output.value`) should be documented as an explicit current-state gap against real source, never silently assumed into existence to match the issue text.
- Grouped near-duplicate `telemetry-mapping.yml` issues by shared transformation logic (identity/correlation, token, LLM I/O, span-kind/status — 4 issues instead of 11+ one-per-attribute) and recorded the rationale directly in the mapping doc so a reviewer doesn't wonder why there aren't more issues.
