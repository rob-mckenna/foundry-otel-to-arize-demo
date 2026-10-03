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
│   └── validate-naming.ps1    # CI/pre-merge lint: fails if a module skips the shared naming/tagging helpers (issue #20)
└── modules/
    ├── naming.bicep           # Shared naming/tagging helpers (issue #20) ✅ - import this from every new module
    ├── foundry-project.bicep  # Azure AI Foundry hub + project (issue #15) ✅
    ├── app-insights.bicep     # Log Analytics + Application Insights (issue #16) ✅
    ├── key-vault.bicep        # Key Vault (RBAC) + managed identity wiring pattern (issue #18) ✅
    ├── networking.bicep       # Optional private endpoint module (issue #21) ✅
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
  Vault/Event Hub namespace identifiers are supplied as parameters. If they
  are not (e.g. deploying this module stand-alone before those resources'
  names are known), grant the roles in a later cross-wiring deployment by
  adding the Function App's `functionAppPrincipalId` output to
  `modules/key-vault.bicep`'s `readerPrincipalIds` and
  `modules/event-hub.bicep`'s `receiverPrincipalIds` - the same two-phase
  pattern used throughout this stack.

**Not yet wired into `main.bicep`.** Issue #17 (Event Hub) was still an
open, unmerged PR when this module was authored; per the lesson recorded
in `.squad/agents/infra/history.md` ("parallel branches editing
`main.bicep`'s structure compounds conflicts"), this PR intentionally adds
only the new, additive `modules/function-app.bicep` file and leaves
`main.bicep`/`main.parameters*.json` wiring (plus cross-wiring
`eventHub`'s `receiverPrincipalIds` and `keyVault`'s `readerPrincipalIds`
to this module's `functionAppPrincipalId` output) as a fast-follow once
both #17 and #19 have merged into `main`, avoiding a structural
add/add conflict on the shared entry-point file.

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
