# Bicep entrypoints

The supported templates are in [`../`](../README.md), not this directory.
`main.bicep` is the ADR-0004 **modern-only private fresh composition**.
Compilation is offline source evidence, not a live-deployment, idempotence,
agent-publication, private-runtime or end-to-end validation claim.

Existing environments use only separately reviewed narrow operations:
`modern-foundry-tracing.bicep` and `durable-genai-rollout.bicep`. Never deploy
fresh main over the mixed live resource group. Source removal grants no live
retirement permission.
