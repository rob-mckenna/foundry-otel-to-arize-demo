# Infrastructure (`/infra`)

Bicep is the preferred Infrastructure-as-Code tool for this repo (see
`/.github/copilot-instructions.md` sections 5-7). This directory contains the
current-state infrastructure for `foundry-otel-to-arize-demo` - the resources
needed to run the demo pipeline described in the repo root README.

## Layout

```
infra/
├── bicepconfig.json            # Enables Bicep compile-time imports (needed by naming.bicep)
├── main.bicep                 # Deployment entry point, wires modules together
├── main.parameters.json       # Example/default parameter values - public-access baseline (no secrets)
├── main.parameters.private-endpoint.json  # Example parameters with the private-endpoint variant enabled (no secrets)
├── scripts/
│   ├── validate-naming.ps1     # CI/pre-merge lint: fails if a module skips the shared naming/tagging helpers (issue #20)
│   ├── validate-deployment.ps1 # End-to-end what-if/deploy/verify validation against a scratch resource group (issue #22)
│   └── teardown-deployment.ps1 # Safely tears down demo resources with confirmation safeguards (issue #23)
└── modules/
    ├── naming.bicep           # Shared naming/tagging helpers (issue #20) ✅ - import this from every new module
    ├── foundry-project.bicep  # Azure AI Foundry hub + project (issue #15) ✅
    ├── app-insights.bicep     # Log Analytics + Application Insights (issue #16) ✅
    ├── key-vault.bicep        # Key Vault (RBAC) + managed identity wiring pattern (issue #18) ✅
    ├── networking.bicep       # Optional private endpoint module (issue #21) ✅
    ├── event-hub.bicep        # Event Hub namespace + hub for telemetry streaming (issue #17) ✅
    └── function-app.bicep     # Azure Function App shell for telemetry transform pipeline (issue #19) ✅
```

Each module is independently parameterized (no hardcoded names, regions, or
environment-specific values) and idempotent - re-running a deployment with
the same parameters must not fail or duplicate resources.

## Naming convention

Resource names follow: `{project}-{env}-{resourceType}-{region}`

Example: `fotoa-demo-aiproj-eastus2`, `fotoa-dev-kv-eastus2`.

- `{project}`: short project token (`fotoa` for foundry-otel-to-arize-demo)
- `{env}`: `dev`, `demo`, or `prod`
- `{resourceType}`: abbreviated resource type (e.g. `aihub`, `aiproj`, `appi`, `law`, `kv`, `func`)
- `{region}`: short Azure region token (e.g. `eastus2`)

See `modules/naming.bicep` (issue #20) for the shared Bicep implementation of
this pattern, and `/.github/copilot-instructions.md` section 7 for the
authoritative definition. Every module **must** `import { buildResourceName,
buildRequiredTags, resourceTypeTokens } from 'naming.bicep'` and use those
functions to build its resource name(s) and `tags:` object - do not re-derive
the pattern or the tag keys locally. `infra/bicepconfig.json` enables Bicep's
`compileTimeImports` experimental feature flag that some Bicep CLI versions
still require for cross-file `import { ... } from '...'` statements.

### Enforcing the convention (issue #20)

`infra/scripts/validate-naming.ps1` is a lightweight static check (no Azure
or Bicep-compiler dependency) that fails if any module under `infra/modules`
(other than `naming.bicep` itself) does not import and call
`buildResourceName`/`buildRequiredTags`. Run it locally:

```
pwsh ./infra/scripts/validate-naming.ps1
```

**CI wiring status:** a `.github/workflows/infra-validate.yml` workflow
(running this script plus `az bicep build` on every PR touching `infra/**`)
was authored and verified locally, but could not be pushed in this pass -
the `gh`/git credential in this automated environment lacks the `workflow`
OAuth scope required to create or update workflow files
(`refusing to allow an OAuth App to create or update workflow ... without
'workflow' scope`). **Manual pre-merge step until that workflow is added:**
run `pwsh ./infra/scripts/validate-naming.ps1` and `az bicep build`/
`az deployment group what-if` locally before merging any `infra/**` PR. A
team member with `workflow` scope should add the CI workflow as a fast
follow-up (the script itself is already committed and ready to wire in).

## Required tags

Every provisioned resource must carry:

| Tag | Purpose |
|---|---|
| `environment` | dev / demo / prod |
| `owner` | responsible team/individual |
| `project` | `foundry-otel-to-arize-demo` |
| `costCenter` | cost allocation tag |
| `dataClassification` | must be `synthetic` for every resource in this repo |

## Secrets and managed identity pattern

- **No secrets are ever passed as Bicep parameters or stored in source.** Every
  secret-capable resource (Foundry project, Function App, any future compute)
  is wired with a **system-assigned managed identity** and granted
  least-privilege RBAC access to Key Vault (`Key Vault Secrets User` for
  readers) rather than embedding keys/connection strings.
- Application Insights connection strings are stored in Key Vault as a secret
  by the `app-insights.bicep` module's wiring step - never emitted as a plain
  Bicep output.
- Actual third-party secrets (e.g. the Arize API key) are entered into Key
  Vault manually post-deploy by an operator and are never committed to this
  repository.

### Granting a compute resource access to Key Vault

Pattern used by every module that needs to read secrets (see
`modules/key-vault.bicep` for the reusable role-assignment resource):

1. Provision the compute resource with `identity: { type: 'SystemAssigned' }`.
2. Capture its `identity.principalId` as a module output.
3. In the Key Vault module (or a cross-wiring deployment that runs after both
   resources exist), create a `Microsoft.Authorization/roleAssignments`
   resource scoped to the Key Vault, assigning the
   `Key Vault Secrets User` role (`4633458b-17de-408a-b874-0445c86b69e6`) to
   that principal ID.
4. The compute resource reads secrets via `https://<vault-name>.vault.azure.net/secrets/<name>`
   using its managed identity token - no key material is ever configured in
   app settings or source.

This is a **two-phase deploy**: provision resource shells independently, then
run a follow-up wiring deployment (or a second `module` block in `main.bicep`)
that cross-references principal IDs once both sides exist. See
`.squad/decisions.md` ("Function App ↔ Key Vault sequencing") for the
reasoning behind this split.

## Network posture

### Decision: public access + RBAC is the demo default

**Default (demo) posture: public network access, secured by Azure AD/RBAC
auth** - no private endpoints are deployed by default. Every resource in
this stack (Foundry project, Application Insights/Log Analytics, Key Vault)
authenticates and authorizes via Azure AD/RBAC (managed identity + role
assignments, never shared keys where avoidable); "public network access" in
this repo means reachable over the internet with that auth still enforced,
not open/anonymous access.

**Rationale:** this is a sales-engineering demo, not a production
deployment. Healthcare prospects evaluating the pipeline need to go from
clone to working demo quickly; requiring a VNet, private DNS zones, and
VPN/ExpressRoute/bastion connectivity just to view synthetic trace data
would add setup friction with no corresponding benefit for a demo using
only synthetic data (see `/.github/copilot-instructions.md` section 1).
Network isolation is a legitimate requirement for a real POC/pilot using a
customer's own data, which is exactly the scenario the optional upgrade
path below exists for.

### Optional upgrade path: private endpoints

`modules/networking.bicep` (issue #21) is an **optional, parameterized**
module, disabled by default (`enablePrivateEndpoints: false` in
`main.bicep`/`main.parameters.json`). When a prospect needs network
isolation during a POC, set `enablePrivateEndpoints: true` (see
`main.parameters.private-endpoint.json` for a ready-made example) to
additionally:

- Provision a small scratch VNet + subnet with
  `privateEndpointNetworkPolicies: 'Disabled'` (required by Azure for
  private endpoints), or reuse an existing subnet via
  `networkExistingSubnetResourceId` / `networkCreateVirtualNetwork: false`.
- Create a `Microsoft.Network/privateEndpoints` resource for the Key Vault
  (`groupId: 'vault'`) and the Foundry project
  (`groupId: 'amlworkspace'`), without rewriting either module - the
  private-endpoint wiring lives entirely in `networking.bicep` and is
  parameterized from `main.bicep`.
- No template changes are required to toggle between the two postures -
  it is a single boolean parameter plus (optionally) an existing-subnet
  resource ID.

Adding private endpoints for a given resource does **not** automatically
disable its public network access flag in this module set - for a true
network-isolated POC, also set that resource's own
`publicNetworkAccess`/`networkAcls` parameter to deny public traffic (left
as an explicit, separate choice so the default demo path is never
accidentally broken by this module existing).

**Validation performed:** the private-endpoint variant (`enablePrivateEndpoints:
true`, `networkCreateVirtualNetwork: true`) was reviewed for Bicep syntax
correctness (conditional resource/module deployment, `for` loop over
`privateEndpointTargets`, DNS-free connection wiring). It was **not**
deployed+torn-down against a live/scratch Azure subscription from this
automated environment - see the `az` CLI limitation noted below. A team
member with Azure access should run the deploy/teardown validation steps
from issue #21 before treating this variant as demo-ready, and record the
result in `.squad/decisions/inbox/infra-network-posture.md` (already filed
with this PR) or a follow-up decision entry.

This decision is also recorded in
`.squad/decisions/inbox/infra-network-posture.md` for the Scribe to merge.

## Event Hub telemetry streaming (issue #17)

`modules/event-hub.bicep` provisions a Standard-tier Event Hub namespace +
hub sitting between Application Insights/Log Analytics (export source) and
the Azure Function transform pipeline (issue #19, Milestone 2). Throughput
units (`eventHubThroughputUnits`, default 1, auto-inflate to 2) and
partition count (`eventHubPartitionCount`, default 2) are parameterized at
demo scale - not sized for production ingestion volume.

**Auth model: RBAC-only by default, no connection strings.** The namespace
is provisioned with `disableLocalAuth: true` (SAS keys disabled). Producers
and consumers are granted least-privilege data-plane roles instead:

- `senderPrincipalIds` -> **Azure Event Hubs Data Sender**
- `receiverPrincipalIds` -> **Azure Event Hubs Data Receiver**

As of the Function App module (issue #19) being wired into `main.bicep`,
the Function App's system-assigned managed identity is passed into
`receiverPrincipalIds` automatically - no manual cross-wiring step is
required for a fresh deployment.

An **optional** connection-string fallback (`storeConnectionStringInKeyVault:
true` + `keyVaultName`) is available for tooling that cannot use
identity-based Event Hub bindings - it requires explicitly re-enabling local
auth (`disableLocalAuth: false`) and writes the connection string only into
an existing Key Vault secret, never as a plaintext Bicep output. RBAC is the
recommended and default posture per `/.github/copilot-instructions.md`
section 8; this fallback is off by default and not wired in `main.bicep`.

A dedicated consumer group (`functionConsumerGroupName`, default
`function-transform`) is provisioned alongside `$Default` for the Function
App to read from without competing with other consumers.

## Function App telemetry transform pipeline (issue #19)

`modules/function-app.bicep` provisions the Function App "shell" for the
Event Hub -> OTLP transform pipeline: a dedicated storage account, an App
Service plan, and the Function App itself, ready for Telemetry to deploy
the actual transform code (Milestone 2).

**Hosting plan: Consumption (Y1) by default.** This demo pipeline runs
against bursty, low-volume manual/scripted demo traffic, not a
latency-sensitive production workload - a few seconds of cold start after
idle is an acceptable trade-off for near-zero idle cost, and reinforces the
"low operational overhead" pitch in issue #19. Set `hostingPlanTier:
'Premium'` for a single-parameter upgrade to an Elastic Premium (EP1) plan
when a POC needs no cold start and/or VNet integration - no template
rewrite required, same pattern as the private-endpoint upgrade path.

**No inline secrets, no shared keys:**

- System-assigned managed identity is enabled on the Function App.
- `AzureWebJobsStorage` uses the identity-based connection
  (`AzureWebJobsStorage__accountName` / `__credential: managedidentity`)
  instead of a storage connection-string app setting. The identity is
  granted least-privilege Storage Blob/Queue/Table Data Contributor roles
  on the dedicated storage account.
- The Event Hub (issue #17) trigger binding uses the identity-based
  `<prefix>__fullyQualifiedNamespace` / `__credential: managedidentity`
  pattern (the namespace host name is not a secret) when
  `eventHubNamespaceFqdn` is supplied; the identity is granted "Azure Event
  Hubs Data Receiver" when `eventHubNamespaceResourceId` is also supplied.
  A Key-Vault-backed connection-string fallback is available via
  `eventHubConnectionSecretName` for tooling that cannot use identity-based
  bindings.
- `APPLICATIONINSIGHTS_CONNECTION_STRING` is wired as a Key Vault reference
  (`@Microsoft.KeyVault(SecretUri=...)`) against the secret
  `app-insights.bicep` already writes (issue #16) - never a plaintext app
  setting. `extraKeyVaultReferenceAppSettings` supports additional secrets
  (e.g. a future Arize API key) the same way.
- The module grants itself the necessary "Key Vault Secrets User" /
  "Azure Event Hubs Data Receiver" roles when the corresponding Key
  Vault/Event Hub namespace identifiers are supplied as parameters - which
  `main.bicep` now does for both automatically.

**Now wired into `main.bicep`.** `main.bicep` passes
`eventHub.outputs.eventHubNamespaceFqdn` /
`eventHub.outputs.eventHubNamespaceResourceId` into this module's
`eventHubNamespaceFqdn`/`eventHubNamespaceResourceId` parameters, and this
module's `functionAppPrincipalId` output into both
`keyVault`'s `readerPrincipalIds` and `eventHub`'s `receiverPrincipalIds` -
a single deployment now provisions the whole chain with RBAC fully
cross-wired, no manual follow-up deployment required.

## Validating a deployment

```
az deployment group what-if -g <resource-group> -f infra/main.bicep -p infra/main.parameters.json
az deployment group create  -g <resource-group> -f infra/main.bicep -p infra/main.parameters.json
```

> **Note:** `what-if`/`az bicep build` validation for the modules in this
> directory could not be executed from the automated environment that
> authored them (no Azure subscription context / `az` CLI profile access
> available in that sandbox). Templates were manually reviewed for Bicep
> syntax correctness. Run `az bicep build` and `az deployment group what-if`
> against a real/scratch resource group before merging or demoing.

### End-to-end deployment validation script (issue #22)

`infra/scripts/validate-deployment.ps1` is the one-command pre-demo
confidence check: it runs `what-if`, deploys the full stack to a scratch
resource group, confirms every module's resource(s) reached provisioning
state `Succeeded`, spot-checks the managed-identity RBAC wiring documented
above (Function App -> Key Vault Secrets User, Function App -> Event Hub
Data Receiver, Foundry project -> Key Vault Secrets User), and prints a
pass/fail summary table with timestamps.

```powershell
# Fast sanity check - what-if only, no resources created/modified:
pwsh ./infra/scripts/validate-deployment.ps1 -ResourceGroupName fotoa-validate-demo -SkipCreate

# Full validation - creates the scratch resource group if missing, deploys,
# and verifies every resource + RBAC spot check:
pwsh ./infra/scripts/validate-deployment.ps1 `
  -ResourceGroupName fotoa-validate-demo `
  -CreateResourceGroupIfMissing
```

Requires the `az` CLI installed and authenticated (`az login`) against a
real subscription. Expected duration for a full run: roughly 10-20 minutes
end-to-end (Foundry project and Key Vault purge-protection-enabled create
are the slowest steps) - plan for that lead time before a demo, not a
same-minute check.

To exercise the induced-failure path (issue #22 validation step 2), pass a
parameters file with a deliberately invalid value (e.g. set
`eventHubPartitionCount` above its `@maxValue(32)` bound in a copy of
`main.parameters.json`) and confirm the script reports the `what-if`/deploy
failure clearly instead of a false pass.

**Sandbox limitation:** this script could not be executed end-to-end from
the automated environment that authored it - the same `az` CLI
unavailability documented above and in
`.squad/agents/infra/history.md` applies. It was validated by: (1) static
PowerShell parse-checking
(`[System.Management.Automation.Language.Parser]::ParseFile`, zero errors),
and (2) a logic smoke test of the `az`-missing/not-logged-in failure paths
(temporarily run under Windows PowerShell 5.1 with a 2-arg `Join-Path`
substitution, since this script - like `validate-naming.ps1` - targets
`pwsh`/PowerShell 7, which is only present in this sandbox as an
unprovisioned Windows Store execution alias). A team member with `az` CLI
access should run both example commands above against a real scratch
resource group before treating this script as demo-ready.

### Teardown / cleanup script (issue #23)

`infra/scripts/teardown-deployment.ps1` safely deletes the demo resource
group (or a targeted set of resource IDs) provisioned by `main.bicep`,
with explicit confirmation safeguards since this is a destructive,
hard-to-reverse operation - it removes everything the validation script
above provisions.

```
# Delete an entire demo resource group (prompts for confirmation):
pwsh ./infra/scripts/teardown-deployment.ps1 -ResourceGroupName rg-fotoa-demo-eastus2

# Delete a targeted set of resources instead of the whole group:
pwsh ./infra/scripts/teardown-deployment.ps1 -ResourceGroupName rg-fotoa-demo-eastus2 `
  -ResourceIds @('/subscriptions/.../resourceGroups/.../providers/Microsoft.KeyVault/vaults/fotoa-demo-kv-eastus2')

# Also purge the Key Vault's soft-deleted record (separate, irreversible,
# separately confirmed):
pwsh ./infra/scripts/teardown-deployment.ps1 -ResourceGroupName rg-fotoa-demo-eastus2 -PurgeKeyVault

# Non-interactive (CI/scripted) teardown - skips both confirmation prompts:
pwsh ./infra/scripts/teardown-deployment.ps1 -ResourceGroupName rg-fotoa-demo-eastus2 -PurgeKeyVault -Force
```

What it does:

1. Checks `az` CLI presence and login/auth state before doing anything else.
2. Prompts for an explicit "yes" confirmation (unless `-Force`) before
   deleting the resource group or targeted resources - this is the
   irreversible step, so it is never skipped silently.
3. Deletes the resource group (`--no-wait`) or the specific resource IDs
   supplied via `-ResourceIds`, then polls `az group show`/`az resource
   show` until the target(s) are confirmed absent (or a timeout is hit,
   in which case it tells you how to check manually).
4. If `-PurgeKeyVault` is set, asks for a **second, separate** explicit
   confirmation before permanently purging the Key Vault's soft-deleted
   record (`az keyvault purge`) - soft-delete and purge are independent,
   differently-risky operations and are never bundled behind one prompt.
5. Checks for orphaned role assignments still scoped to the deleted
   resource(s)/group (Azure normally cleans these up, but this is a
   documented edge case worth confirming rather than assuming).
6. Prints a pass/fail summary table and exits non-zero if any check
   failed, so it can be wired into a CI "demo cleanup" job.

> **Sandbox limitation:** `az` CLI is present in the automated environment
> that authored this script, but every invocation fails with a Python
> traceback (`PermissionError` reading the cached profile at
> `~/.azure/azureProfile.json`) - the script was validated via
> `[System.Management.Automation.Language.Parser]::ParseFile` (0 errors)
> and a smoke test of its "az present but not authenticated" failure path
> (clean `[FAIL]` reporting, correct summary counts, exit code 1) rather
> than a live deploy+teardown. **A team member with real Azure access must
> run this script end-to-end against a scratch resource group before
> relying on it for demo cleanup**, confirming: resource-group deletion,
> targeted-resource deletion, Key Vault purge, and the orphaned-role-
> assignment check all behave as documented. During this work, a reusable
> PowerShell gotcha was found and fixed: under `$ErrorActionPreference =
> 'Stop'`, piping a native command's stderr into the success stream via
> `2>&1` throws a terminating error instead of letting the script's own
> fail-handling logic run - fixed via `Invoke-AzJson`/`Invoke-AzCommand`
> helper functions that scope `$ErrorActionPreference = 'Continue'` around
> each individual `az` call. See
> `.squad/decisions/inbox/infra-teardown-script.md` for the full design
> rationale.
