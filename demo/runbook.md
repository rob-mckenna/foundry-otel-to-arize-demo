# Demo Runbook: Setup → Run → Teardown

**Status: MIXED.** Steps marked ✅ use commands/scripts that exist in this repo today and have been
reviewed against the merged infrastructure/code. Steps marked ⚠️ reference work tracked in open
issues that has **not yet merged** — follow the linked issue for current status rather than
assuming the step is ready. This runbook will be updated in the same PR that merges each
pending piece, per the doc-drift checklist (#62) — do not let it silently drift from reality.

This is the operational companion to [`/demo/narrative.md`](narrative.md) (the talking-point
script) and indexes into [`docs/validation/demo-validation-plan.md`](../docs/validation/demo-validation-plan.md)
for proof of each capability. For what to do if something breaks mid-demo, see
[`/demo/fallback.md`](fallback.md).

## 0. Prerequisites

- Azure subscription with permission to create resource groups and assign RBAC roles.
- Azure CLI (`az`) installed and logged in (`az login`), with the Bicep CLI extension
  (`az bicep install` / `az bicep upgrade`).
- Python 3.10+ (for the Prompt Agent — see `src/prompt-agent/README.md`).
- PowerShell 7+ (for `infra/scripts/validate-naming.ps1` and the commands below).
- An Arize account/API key — **not yet required for the current-state demo**, since the
  Function→Arize export leg is not implemented yet (see §4). Provision one ahead of time if you
  plan to demo the designed end-state narrative, but do not block today's setup on it.

## 1. Setup — Infrastructure (✅ current-state)

From the repo root:

```powershell
cd infra
pwsh ./scripts/validate-naming.ps1
az deployment group what-if -g <resource-group> -f main.bicep -p main.parameters.json
az deployment group create  -g <resource-group> -f main.bicep -p main.parameters.json
```

This provisions, per `infra/README.md`:

- Azure AI Foundry hub + project
- Application Insights + its backing Log Analytics workspace
- Key Vault (RBAC) with managed-identity wiring
- Event Hub namespace + hub for telemetry streaming
- Azure Function App shell (infrastructure only — see §4 for its current code status)

Confirm the deployment succeeded:

```powershell
az deployment group show -g <resource-group> -n main --query properties.provisioningState
```

Expected: `"Succeeded"`.

> ⚠️ A dedicated, scripted **deployment validation script** (issue #22) is tracked but not yet
> merged. Until it lands, the `what-if`/`show` commands above are the validated way to confirm a
> deployment, exactly as documented in `infra/README.md`'s own "Validating a deployment" section.

## 2. Setup — Prompt Agent (✅ current-state)

```powershell
cd src/prompt-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
pip install -e ".[azure]"   # only needed if exporting to a live Application Insights resource
```

Set the environment variables documented in `src/prompt-agent/README.md`'s configuration table —
at minimum `APPLICATIONINSIGHTS_CONNECTION_STRING` (pull the value from Key Vault, never hardcode
it) if you want spans to land in the deployed Application Insights resource rather than the local
console exporter.

Run the test suite to confirm the agent is healthy before a live demo:

```powershell
pytest
```

Expected: all tests pass (11 as of this writing — see `src/prompt-agent/README.md`).

## 3. Run — the synthetic scenario (✅ current-state)

```powershell
cd src/prompt-agent
python -m prompt_agent.main --scenarios
```

This is also the exact command narrated in `demo/narrative.md` §2. Note the correlation ID printed
for each scenario — you'll use it to look up the trace in the next step.

**Where to look during the live demo:**

- **Application Insights** (✅ current-state): Transaction Search or Logs, querying
  `AppDependencies` filtered by `customDimensions["correlation.id"]` — see the exact KQL in
  `demo/narrative.md` §3.
  > ⚠️ A curated **KQL validation query pack** (issue #41) is tracked but not yet merged; until it
  > lands, use the ad hoc query in `demo/narrative.md` §3 or
  > `docs/telemetry/trace-correlation-preservation.md` §5.
- **Arize** (🔴 not current-state yet): there is no live Arize screen to show today — the
  Event Hub → Azure Function transform that would forward telemetry to Arize has not been
  implemented yet (`src/telemetry-pipeline/` is infrastructure-only; see
  `docs/validation/demo-validation-plan.md` capabilities #9/#10). Do not open an Arize dashboard
  during a live demo implying this is working end-to-end — narrate it as "designed and the
  infrastructure is ready; the transform code is the next deliverable," per `demo/narrative.md` §3.

## 4. Teardown (⚠️ partially scripted)

```powershell
az group delete -g <resource-group> --yes --no-wait
```

Confirm no orphaned resources remain once the deletion completes:

```powershell
az resource list -g <resource-group> --output table
```

Expected: empty output (resource group itself will also disappear from
`az group list` once deletion finishes).

> ⚠️ A dedicated **cleanup/teardown script** (issue #23) is tracked but not yet merged. Until it
> lands, `az group delete` against the single resource group used for the demo (per the
> naming/tagging convention in `infra/README.md`) is the validated teardown path, since every
> resource in this repo's Bicep modules is provisioned into one resource group with no
> cross-resource-group dependencies as of this writing. Re-run `az resource list` after the delete
> completes to confirm zero orphaned resources before considering teardown done.

## 5. Known gaps in this runbook

- Steps flagged ⚠️ above depend on issues #22, #23, and #41, none of which are merged as of this
  writing. This runbook uses the best validated current alternative for each and will be updated
  to reference the dedicated scripts once they land — see §1 header for the drift policy.
- The Function transform / Arize ingestion leg (§3) is not runnable end-to-end yet; do not promise
  it live. Track its status via `docs/validation/demo-validation-plan.md`.

## Related

- [`/demo/narrative.md`](narrative.md) — the talking-point script this runbook supports
- [`/demo/fallback.md`](fallback.md) — what to do if a step above fails mid-demo
- [`docs/validation/demo-validation-plan.md`](../docs/validation/demo-validation-plan.md) — capability-by-capability validation status
- [`infra/README.md`](../infra/README.md) — full infrastructure deployment detail
