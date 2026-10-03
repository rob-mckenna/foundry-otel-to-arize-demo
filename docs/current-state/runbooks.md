# Demo Environment Runbooks: Setup, Teardown, and Troubleshooting

**Status: MIXED.** The setup and teardown runbooks below (§1, §2) cover infrastructure and
Prompt Agent steps that are merged and validated today. The troubleshooting section (§3) covers
the 4 most likely failure points named in issue #61; two of them (Event Hub throughput, Arize
ingestion rejections) describe failure modes for components whose transform/export code is not
yet implemented (see `docs/validation/demo-validation-plan.md` capabilities #9/#10) — those entries
are written as **anticipated** guidance based on the documented design, not confirmed live
incidents, and are labeled as such below.

This runbook is written so that **a customer's own engineers, or a different squad member, can run
the demo without QA or Infrastructure being in the room.** It is the deeper operational companion
to [`/demo/runbook.md`](../../demo/runbook.md) (#45), which is the shorter demo-day
setup→run→teardown script read during a live presentation. Use this document when standing up a
fresh environment, tearing one down for good, or diagnosing a failure outside of demo time.

## 1. Setup runbook: standing up the demo environment from scratch

Prerequisites: see the root [`README.md`](../../README.md#prerequisites) — Azure subscription,
`az` CLI + Bicep extension, Python 3.10+, PowerShell 7+.

| Step | Command | Expected result | Notes |
|---|---|---|---|
| 1 | `az login` | Browser/device-code auth succeeds | Confirm `az account show` returns the intended subscription before continuing |
| 2 | `az group create -n <resource-group> -l <region>` | Resource group created | Pick a region matching `infra/main.parameters.json`'s region token |
| 3 | `pwsh ./infra/scripts/validate-naming.ps1` (from `infra/`) | Exits 0, no naming/tagging violations reported | Static check, no Azure calls — safe to run before `az login` even completes |
| 4 | `az deployment group what-if -g <resource-group> -f main.bicep -p main.parameters.json` | Shows planned creates for Foundry project, App Insights/Log Analytics, Key Vault, Event Hub, Function App shell — no unexpected deletes | If this is a re-run against an existing group, idempotency means no unexpected changes to already-matching resources |
| 5 | `az deployment group create -g <resource-group> -f main.bicep -p main.parameters.json` | `provisioningState: Succeeded` | Full module list and RBAC wiring detail: `infra/README.md` |
| 6 | Confirm managed-identity RBAC wiring | `az role assignment list --scope <key-vault-resource-id>` shows the Function App's and/or Foundry project's managed identity with `Key Vault Secrets User` | No connection strings/keys should appear anywhere in deployment output |
| 7 | Set up the Prompt Agent locally (`python -m venv .venv`, `pip install -e ".[test]"`, optionally `".[azure]"`) | `pytest` passes (11 tests as of this writing) | See `src/prompt-agent/README.md` |
| 8 | Point the agent at the deployed App Insights resource (`APPLICATIONINSIGHTS_CONNECTION_STRING`, sourced from Key Vault — never hardcoded) | `python -m prompt_agent.main --scenarios` runs and prints 5 scenario results | Omit this variable to run against the console exporter only (no live Azure needed) |

**Acceptance for a successful setup:** step 5 reports `Succeeded`, step 7's test suite passes, and
step 8 produces a correlation ID that is subsequently queryable in Application Insights (see
`demo/narrative.md` §3 for the exact KQL).

## 2. Teardown runbook: leaving zero orphaned resources

```powershell
az group delete -g <resource-group> --yes --no-wait
```

Wait for completion, then verify:

```powershell
az resource list -g <resource-group> --output table
az group show -g <resource-group>   # should error "ResourceGroupNotFound" once fully deleted
```

**Acceptance for a clean teardown:** `az resource list` returns an empty table and
`az group show` errors with `ResourceGroupNotFound`. If either command still shows resources after
a few minutes, re-run `az group delete` (idempotent) rather than deleting resources individually —
individual deletion risks leaving RBAC role assignments or soft-deleted Key Vault instances behind
(Key Vault soft-delete in particular: confirm with
`az keyvault list-deleted --query "[?properties.vaultId.contains(@, '<resource-group>')]"` and
purge with `az keyvault purge --name <vault-name>` if the demo environment will not be reused with
the same name).

> ⚠️ A dedicated, scripted teardown tool (issue #23, "Cleanup / teardown script for demo
> resources") is tracked but not yet merged as of this writing. Until it lands, the commands above
> — delete by resource group plus explicit `az resource list` / Key Vault soft-delete verification
> — are the validated teardown path, since this repo's Bicep modules provision everything into a
> single resource group with no cross-resource-group dependencies. Update this section once #23
> merges, per the doc-drift checklist (#62).

## 3. Troubleshooting: the 4 most likely failure points

### 3.1 Foundry authentication failures

**Symptom:** Prompt Agent calls fail with an auth/401-style error when `FOUNDRY_API_KEY` or a
managed-identity token is rejected.

**Likely cause:** expired/incorrect API key placeholder still set from `src/prompt-agent/README.md`'s
local-dev defaults (`REPLACE_ME_SYNTHETIC_KEY` is a placeholder, not a real credential — it will
never authenticate against a real Foundry endpoint), or a managed identity missing the expected
role assignment.

**Fix:** confirm `FOUNDRY_ENDPOINT`/`FOUNDRY_DEPLOYMENT_NAME`/`FOUNDRY_API_KEY` are sourced from
Key Vault (never the local placeholder) when targeting a real deployment; confirm the calling
identity has the Foundry project's required data-plane role via
`az role assignment list --scope <foundry-project-resource-id>`.

### 3.2 Event Hub throughput / ingestion lag

**Status: anticipated guidance — not yet confirmed against a live incident**, since no component
in this repo streams live traffic into the Event Hub yet (the Log Analytics → Event Hub export
wiring is a documented baseline design per `docs/telemetry/log-analytics-export-baseline.md`, not
a deployed/validated data flow).

**Symptom (anticipated):** Event Hub throttling errors (`ServerBusyException`) or growing consumer
lag once the export pipeline is live, under demo-scale but bursty traffic.

**Likely cause:** `infra/modules/event-hub.bicep` provisions at demo scale (1 throughput unit,
auto-inflate to 2, per `infra/README.md`) — sufficient for scripted demo scenarios, not sized for
production-volume ingestion.

**Fix (anticipated):** raise `eventHubThroughputUnits`/the auto-inflate ceiling in
`main.parameters.json` and redeploy (idempotent); confirm the Function's consumer group
(`functionConsumerGroupName`, default `function-transform`) isn't competing with another consumer
reading `$Default`.

### 3.3 Azure Function cold start

**Symptom:** The first Function invocation after a period of inactivity takes several seconds
longer than subsequent ones.

**Likely cause:** `infra/modules/function-app.bicep` defaults to a Consumption (Y1) hosting plan —
an intentional cost/latency trade-off documented in `infra/README.md`, not a defect.

**Fix:** for a POC that needs to eliminate cold start, set `hostingPlanTier: 'Premium'` in the
Bicep parameters (single-parameter upgrade to Elastic Premium EP1, no template rewrite) and
redeploy. For a one-off live demo, a warm-up invocation a few minutes before presenting avoids the
issue without any infrastructure change.

### 3.4 Arize ingestion rejections

**Status: anticipated guidance — not yet confirmed against a live incident**, since no Function
transform code exists yet to emit OTLP spans toward Arize (`src/telemetry-pipeline/` is
infrastructure-only as of this writing — see `docs/validation/demo-validation-plan.md` capability
#9).

**Symptom (anticipated):** Arize's OTLP ingestion endpoint rejects a batch (e.g. malformed span
schema, a non-numeric value in a field documented as requiring type coercion).

**Likely cause:** per `docs/telemetry/field-mapping.md`'s "transform-wide rule" — Application
Insights exports every `customDimensions` value as a JSON string regardless of the OTel SDK's
original type. Token counts, span-status booleans, and retry-attempt counters all require an
explicit type cast in the Function; a raw string passthrough for any of these is the single most
likely cause of an Arize-side schema rejection once that transform exists.

**Fix (anticipated):** cross-check the Function's actual output against the field-by-field
mapping table in `docs/telemetry/field-mapping.md` before investigating Arize-side configuration —
this is a transform-code bug class, not typically an Arize configuration issue.

## 4. When this runbook needs updating

Per the doc-drift checklist (#62): any PR that changes `infra/modules/*.bicep`, adds
`src/telemetry-pipeline/` transform code, or merges issues #22/#23/#41 must update the relevant
section of this runbook in the same PR — do not leave §3.2/§3.4's "anticipated guidance" labels in
place once those components are actually implemented and a live incident/validation can replace
the anticipated guidance with a confirmed one.

## Related

- [`/demo/runbook.md`](../../demo/runbook.md) (#45) — the shorter demo-day setup→run→teardown script
- [`/docs/current-state/architecture.md`](../current-state/architecture.md) — the authoritative current-state diagram this runbook assumes
- [`/docs/validation/demo-validation-plan.md`](../validation/demo-validation-plan.md) — capability validation status
- [`/infra/README.md`](../../infra/README.md) — full infrastructure module detail
