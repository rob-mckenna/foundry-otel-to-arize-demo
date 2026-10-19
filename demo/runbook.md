# Demo Runbook: Choose an Evidence-Bounded Path

**CURRENT ROUTING (2026-10-19); fresh private provider/runtime/end-to-end
validation PENDING.** The old classic/public setup and RG teardown script is
superseded by [ADR-0004](../docs/adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md).
Do not use old milestone recipes as a live deployment or deletion instruction.

## 1. Offline synthetic walkthrough

Use the [root README](../README.md) and
[Prompt Agent README](../src/prompt-agent/README.md) for the supported local stub
walkthrough. Synthetic output and instrumentation tests are not a live model
call, published Foundry agent or AppInsights/Arize delivery evidence.
Keep cloud exporters and model calls out of an offline walkthrough.

## 2. Fresh private environment

Use [current operations](../docs/current-state/runbooks.md) and the
[Infra implementation guide](../infra/README.md) for the **one modern-only
private fresh contract**. Infra reports source and offline checks complete;
**Ready for Validation** is not Validated, and no #145 cloud workflow ran.
No fresh deployment command is supplied here. Model/version/region/SKU/capacity/upgrade/residency,
quota, Premium cost, network ownership and secure vault resolution need operator
approval. Account/project/model provisioning does not publish an agent version
or establish private agent runtime/state readiness.

Do not substitute a classic Hub profile, public fallback or broad `main.bicep`
deployment over the live mixed RG. Stop on unmet runtime/network requirements;
no automatic Search/Cosmos/ACR/VM, extra storage or permissions.

## 3. Existing demo and evidence

The [#139 tracing runbook](../docs/current-state/foundry-appinsights-tracing.md)
records narrow existing-project connection adoption and dated source/export
evidence. It is not a fresh foundation recipe.

The [#143 durable runbook](../docs/current-state/durable-genai-correlation.md)
records accepted native transport/inline precedence and independently verified
**generated-fixture** missing-inline fallback. Do not call it native
missing-inline verification, exactly-once delivery or full graph/resource parity.
The unrelated operational ambiguous send stays quarantined; no retry/replay.
Only demonstrate existing live assets under separately approved exact scope.

The [architecture](../docs/current-state/architecture.md) and
[mapping/export contract](../docs/current-state/telemetry-mapping-export-contract.md)
separate implementation, historical receipts and destination-evidence limits.
Do not present a captured run as a fresh live result.

## 4. End the demo without retiring resources

Ending a presentation is not teardown authorization. Keep private controls,
agent v1, retained tests/evaluation assets, identities, vaults, ledger/ACKs and
checkpoints. Use the separately gated
[retirement plan](../docs/current-state/resource-cleanup-plan.md) only after
consumer/governance/recovery review and new exact-ID approval; never an RG-wide
delete, purge or prefix/IAM sweep.

## Archived presentation assets

[Narrative](narrative.md), [fallback notes](fallback.md) and
[one-pager](one-pager.md) retain earlier milestone scripts as **archive**.
Their inline status labels/recipes are not current guidance or proof.
If live readiness is unavailable, use explicitly labeled historical captures
or the offline walkthrough, not improvised deployment or invocation.
