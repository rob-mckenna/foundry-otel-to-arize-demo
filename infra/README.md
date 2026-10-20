# Modern private infrastructure

**Source implementation for #145 / ADR-0004. No #145 cloud deployment performed.**
Supported fresh architecture:
**Foundry → Application Insights → Log Analytics → Event Hub → Function → Arize**.
No classic ML Hub/Project deployment, public Foundry fallback, legacy opt-in or
executable archive is retained. Git history preserves retired source.

The authoritative boundary is [ADR-0004](../docs/adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md).
Offline compilation/tests do **not** establish fresh deployment, repeat deployment,
provider/policy acceptance, quota, DNS reachability, private agent runtime/state,
agent-version publication or Arize receipt. All remain separately approved gates.
The local Prompt Agent client is still a synthetic stub, not a live SDK backend.

For the next **fresh** environment, use the [QA readiness and acceptance packet
(#147)](../docs/current-state/fresh-foundation-acceptance.md): exact offline results,
owner decision choices, public cost basis and gated provider/private/repeat/E2E
handoffs. It does not authorize cloud execution or certify private agent readiness.

**#147 staged existing-network first allocation:** the exact nonsecret profile
is embedded by `issue147-first-allocation.bicep` (subscription scope, exact fresh
RG). After foundation creation, `issue147-app-insights-bootstrap.bicep` uses an
ARM server-side new-component reference and securestring module parameter to
write only the new routing secret in the existing custody vault. Only immutable
version URI/component ID outputs are exposed; no existing Arize value is copied.
This first-allocation writer is **not** the repeat entrypoint. Metadata-only
collision/ambiguity checks and a later execution lease are mandatory.
[Manifest and safe provider results](../docs/current-state/issue147-existing-network-proposal.md#fresh-tracing-bootstrap--supported-server-side-automation-staged):
Independent evaluated-graph fix passed Provider validate and ResourceIdOnly
what-if at 08:53Z on 2026-10-20: **33 Create / 0 Modify / 0 Delete /
1 Unsupported** future-principal index assignment. All five actual pinned-helper
checks ran through the narrow metadata-only compatibility adapter. The owned
vault reader is isolated in a conditional nested module: a null owned-vault
name never enters ARM's evaluated existing-resource graph. Default freshVault
RBAC GUID inputs, role, scope, principal and all public outputs are unchanged.
Existing-reference mode omits the unused
owned vault and vault PE (four PEs / six expected IP slots); freshVault default
retains both (five PEs / seven expected slots). No deployment or secret operation executed;
official policy/workflow and allocation/runtime acceptance remain incomplete,
not Validated. Run the pinned helper safely (new immutable receipt directory
per analysis) with `scripts\invoke-issue147-official-validation.ps1`; exact
commands and projected receipts are bound in the selected-route manifest.

## Three operations — never substitute one for another

| Operation | Entrypoint / ownership | Scope |
|---|---|---|
| Fresh | `main.bicep` | New, explicitly approved identities in a fresh RG. Owns foundation, private graph and pipeline state/export. Never apply to the mixed live RG. |
| Live tracing adoption | `modern-foundry-tracing.bicep` | Existing account/project, connection-only; `preserveExisting` emits **no connection PUT**. Retain exact manual names. No parent/model/network/IAM writes. |
| Existing durable rollout | `durable-genai-rollout.bicep` | Four writes: existing-account container, additive index role/assignment, existing named export. Preserve complete table union, destination and enabled state. No runtime enablement, replay or checkpoint reset. |
| Retirement | **No executor in this repo** | Separate exact-ID manifest, dependency/governance/recovery review and explicit user approval. Source removal is not Azure deletion. |

`teardown-deployment.ps1` was removed: whole-RG deletion/prefix sweeps are not
cleanup mechanisms. Never use Complete-mode deployment, unmanaged-stack deletion,
vault purge, broad IAM removal or “rollback” that discards state.

Preserve all working modern workload identities, operational agent version/model,
private/shared dependencies, current pipeline/grants, ledger/index/checkpoints,
35 imported ACKs, ambiguous quarantine and retained #138/#139 assets. The
[cleanup register](../docs/current-state/resource-cleanup-plan.md) is as-of evidence,
not permission or proof any resource is unused. #143 release completion stands;
this source work neither replays nor modifies its live state.

## Fresh graph and single-writer ownership

- `modern-foundry-foundation.bicep`: AIServices S0 account and distinct system-MI
  project, API **2025-09-01**; allowProjectManagement, explicit custom subdomain,
  local auth disabled, PNA Disabled, ACL Deny / bypass None.
- Project MI receives published **Foundry User** (`53ca6127-db72-4b80-b1b0-d745d6d5456d`)
  **at account scope**, deterministic assignment. No automatic modern project→KV
  grant, caller grant, Owner/Contributor substitute or permission discovery.
- `modern-foundry-model.bicep`: one account-scoped deployment with exact format,
  catalog name/version, alias, SKU/capacity, upgrade policy; optional existing
  approved RAI policy. No default model, spillover, deprecated scaleSettings,
  alternate-region fallback or quota increase.
- `networking.bicep`: fresh VNet with separate PE and delegated
  `Microsoft.Web/serverFarms` Function integration subnets, seven private DNS
  zones plus registration-disabled VNet links; OR explicit external ownership.
- `private-endpoints.bicep`: actual DNS zone groups, no static A records or IPs.
  Main targets Foundry **account** group `account` with all three Foundry zones,
  and KV group `vault` only in default `keyVaultReferences.mode=freshVault`.
  Existing mode uses four external URI references and null owned-vault name/ID
  outputs, explicit `keyVaultReferenceMode`, and URI-only
  `externalKeyVaultReferences` metadata; no owned vault, vault PE or local reader.
  Function module creates host `blob`/`queue`/`table`
  endpoints and DNS groups **before** creating the integrated Function.
- KV: RBAC, soft delete, purge protection, PNA Disabled, ACL Deny/None.
  Host storage: TLS1.2/HTTPS, no public blobs/shared keys, PNA Disabled, ACL Deny/None.
- Function: Linux Python 3.11 default, **Premium EP1**, capacity/minimum 1,
  explicit plan `maximumElasticWorkerCount=1` and app `functionAppScaleLimit=1`
  via `functionMaximumInstances` (only 1 allowed). Always-ready
  `minimumElasticInstanceCount=1`, prewarmed target `preWarmedInstanceCount=1`;
  the prewarmed buffer stays inside the app maximum, not one extra worker.
  Provider acceptance/readback is still required; no automatic larger fallback.
  These are scale controls, not a monetary cap or deallocation after a test.
  System MI,
  outbound VNet integration with route-all, PNA Disabled, TLS1.2, FTP/SCM basic
  publishing disabled. This timer/EH worker has no public HTTP ingress requirement.
- Function retains Blob/Queue/Table Data Contributor, EH Data Receiver and KV
  Secrets User; adds **Storage Blob Data Owner** required for identity-based
  host storage. All grants are resource-scoped; index actions are container-local.
  This defines new-resource grants, not changes to existing live identities/IAM.
- LAW/AppInsights retain explicit ingestion/query controls; EH retains existing
  API pin **2023-01-01-preview**, Standard, RBAC-only. Auto-inflate is off; explicit
  throughput units bound capacity instead of silently increasing spend.
- `app-insights.bicep` owns one enabled native export rule to namespace **and
  explicit hub `telemetry`**, tables AppDependencies/AppRequests/AppGenAIContent.
  No ML diagnostic coupling or governance diagnostic replacement.
- Function owns private `genai-correlation` and `function-packages` containers.
  `durable-genai-state.bicep` owns the RG-defined two-DataAction index role and
  container-only assignment; GUID derivation matches the narrow rollout.
  **Do not run both entrypoints as concurrent writers of fresh-owned state.**

No Search, Cosmos DB, ACR, capability host, new VM/Bastion/NAT, hosted runtime or
extra evaluation storage is added. A private endpoint only secures account ingress;
it does not prove an agent's private outbound/tool/state path. If selected Prompt
Agent APIs require standard BYO services, VNet injection or another API, stop and
request the exact scoped architecture decision before adding them.

### Monitoring and egress boundary

Foundry PE does **not** privatize Azure Monitor. Preserve service ingestion/query,
LAW→EH export and approved Arize HTTPS `/v1/traces` egress. No AMPLS, EH firewall,
NSG/UDR/NAT redesign is implied. Fresh VNet uses Azure-provided DNS; an approved
private validator must have connectivity to it (none is provisioned).
For existing networks, owners must attest delegation, endpoint network policies,
NSGs, route-all egress and DNS forwarding/links from both Function and validator.
If enterprise policy forbids these service paths, deployment is blocked pending
a separately reviewed design, **not** repaired by enabling public Foundry/KV/storage.

## Inputs: portable, deliberate, non-executable examples

Both `main.parameters*.json` files are **incomplete, non-executable examples**:
no live identities, model tuple or cost approval. They intentionally contain
`REPLACE_ME`, capacity zero and approval false. They are not a deployment command.
The first illustrates a fresh network; `private-endpoint` now illustrates an
externally owned private network, **not** a private-vs-public feature switch.
Replace all placeholders in a separately reviewed secret-free profile.

Required top-level selections:

| Contract | Inputs |
|---|---|
| Naming/tags | `projectToken` (2–10 lowercase alphanumeric), `environment` (dev/demo/prod), `location`, `regionToken`, `ownerTag`, `costCenterTag`; dataClassification is synthetic |
| Modern names | `accountName`, `projectName`, globally unique `customSubDomainName`; optional `projectDisplayName` |
| Model | `modelDeploymentName`, `modelFormat`, `modelName`, **`modelVersion`**, `modelDeploymentSkuName`, positive **`modelDeploymentCapacity`**, **`modelVersionUpgradeOption`**; optional `raiPolicyName` |
| Deployment gates | `modelDeploymentApproved=true` attests owner approval of exact tuple, availability/quota/cost; **`modelDataResidencyApproval`** records processing/residency approval, not a provider setting |
| Function publication | `functionPackageBlobName`: owner-selected immutable ZIP blob name under `function-packages`; separately upload a built package, never a SAS/connection string |
| Function scale | Explicit `functionMaximumInstances=1` in prepared profiles; plan/app ceiling with one always-ready instance and prewarmed target 1. See [proof, lifetime and operator retention plan](../docs/current-state/issue147-bounded-execution.md). |
| Destination | `arizeProjectName`; operator-populated private-vault secret names `arizeEndpointSecretName`, `arizeSpaceIdSecretName`, `arizeApiKeySecretName` |
| Tracing | `appInsightsConnectionName`; `tracingAssociationMode=preserveExisting` by default, explicitly approved `ApiKey` only for fresh main |

Naming helpers define `{project}-{environment}-{type}-{region}` (`foundry`, `fproj`,
`law`, `appi`, `kv`, `ehns`, `func`, `st`, `vnet`, `pe`). Storage drops hyphens.
Explicit Foundry/account/model names are never normalized: keep approved exact
names for adoption. The offline profile validator checks generated name lengths;
operators must choose tokens fitting provider limits and global uniqueness.
No other Azure cloud is certified by the public-cloud endpoint/DNS contract.

Model upgrade choices are `NoAutoUpgrade`, `OnceCurrentVersionExpired`,
`OnceNewDefaultVersionAvailable`. Quota and capacity-unit RPM/TPM are
region/model/deployment-type specific. Existing demo choices are **not defaults**.
No availability/quota queries or cost estimates were run in this source phase.

### Network ownership input

Fresh `network` object (CIDRs are illustrative; obtain owner approval):

```json
{
  "mode": "fresh",
  "virtualNetworkAddressPrefix": "10.40.0.0/24",
  "privateEndpointSubnetAddressPrefix": "10.40.0.0/26",
  "functionIntegrationSubnetAddressPrefix": "10.40.0.64/26"
}
```

Existing `network` requires `mode="existing"`,
`privateEndpointSubnetResourceId`, `functionIntegrationSubnetResourceId`,
`dnsLinksManagedExternally=true`, and `privateDnsZoneIds` with these exact keys:

| Key | Azure public-cloud zone |
|---|---|
| cognitiveServices | privatelink.cognitiveservices.azure.com |
| openAI | privatelink.openai.azure.com |
| servicesAI | privatelink.services.ai.azure.com |
| vault | privatelink.vaultcore.azure.net |
| blob | privatelink.blob.core.windows.net |
| queue | privatelink.queue.core.windows.net |
| table | privatelink.table.core.windows.net |

Use exact full ARM zone IDs (including separately owned DNS RGs); existing zones,
VNet, subnets and links receive **no PUT**. The two approved subnets must be distinct
in the same VNet; integration is predelegated. External owners maintain links/
forwarding, never registration-enabled autogenerated links or truncated subnet lists.
Switching ownership modes after deployment is not an adoption procedure.

## Secrets, tracing and readiness

Fresh main forwards secure `appInsightsConnectionString` through the unchanged
#139 secure module boundary. Active `ApiKey` requires
`appInsightsConnectionPropertiesReviewed=true` plus explicit sharing,
`peRequirement` and `peStatus` review. Supply **only a version-pinned Key Vault
deployment reference**, shaped like the non-executable
`modern-foundry-tracing.secure-reference.parameters.json`, never plaintext
`value`. The offline profile validator rejects plaintext/unpinned references.
The operator must attest the immutable material belongs to the intended component.
`preserveExisting` is no-PUT, **not** “tracing configured.”

Private-vault ARM template resolution is an explicit operator gate: deployer
authorization, deployment-enabled vault and supported private service access must
be established without secret reads or loosening network controls. A fresh vault
cannot implicitly contain the newly created component's secret. Foundation-only
provisioning followed by approved private secret custody and the narrow connection
operation is valid staging, **not a finished tracing deployment**.
`app-insights.bicep` retains optional explicit KV secret-write custody for independently
approved use; main does not enable it or output the connection string.

ProjectManagedIdentity AppInsights ingestion stays a separately approved migration
through the narrow #139 entrypoint (including component-scoped Monitoring Metrics
Publisher and provider-readable metadata security review). It is not coupled to
Foundry local auth, which remains disabled.

### Keyless Premium package and pipeline cutover

Function package is **external private Blob URL + system MI**, not Azure Files:
`WEBSITE_RUN_FROM_PACKAGE` points at the dedicated account's private
`function-packages/<functionPackageBlobName>`, with
`WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID=SystemAssigned`. No Azure Files
share, shared key, content connection string or fake secret is provisioned.
Package upload/build, private package fetch and trigger synchronization are
separate approved gates. Without Azure Files, scaling can be limited; see the
official [no-Azure-Files guidance](https://learn.microsoft.com/azure/azure-functions/storage-considerations#create-an-app-without-azure-files).
The blob name is not evidence of an uploaded/usable package.

Bindings explicitly set `EventHubConnection__fullyQualifiedNamespace`,
`EventHubConnection__credential=managedidentity`,
`EVENT_HUB_CONNECTION_SETTING_PREFIX`, `EVENT_HUB_NAME`,
`EVENT_HUB_CONSUMER_GROUP=function-transform` (or chosen group),
`AzureWebJobsStorage__accountName` and
`AzureWebJobsStorage__credential=managedidentity`.
Function KV references preserve `APPLICATIONINSIGHTS_CONNECTION_STRING`,
`ARIZE_OTLP_ENDPOINT`, `ARIZE_SPACE_ID`, `ARIZE_API_KEY` interfaces. No raw settings/
credential is read or exported by validation.

Fresh main creates desired export/container/index state, but **TelemetryTransform
and DurableGenAIOutbox are explicitly disabled**. It never sets
`DURABLE_GENAI_ENABLED=true`. Before a separately reviewed runtime cutover:
populate/resolve required vault references; publish the reviewed package; verify
Function MI/private DNS/storage/EH/index access; establish exact durable workspace/
component/Arize project destination identity and `DURABLE_*` gates per
[ADR-0003](../docs/adr/0003-opt-in-durable-genai-content-correlation.md);
verify native tables/retention/admission/ACK/outbox and destination behavior.
`arizeProjectName` records intended project only; it does not set runtime durable
scope or prove acceptance. Never enable a fresh consumer before readiness.
Existing demo runtime enablement and all checkpoints remain untouched.

## Outputs

Preserved meanings: LAW/AppInsights/KV/EH/Function names/IDs and MI IDs.
`foundryProjectResourceId`, `foundryProjectPrincipalId`, `foundryProjectEndpoint`
are still named interfaces but now mean **Cognitive Services project** and
`https://<customSubDomainName>.services.ai.azure.com/api/projects/<projectName>`,
never ML discovery. Added account/project/model exact IDs/names/principals;
workspace/component/namespace/Function/storage IDs/names; export/container IDs;
PE subnet, Function integration subnet, seven DNS IDs and five PE IDs.
`privateEndpointsEnabled=true` / `functionAppIsPremiumHostingPlan=true` describe
the desired graph, not reachability. `consumerEnabled=false` is intentional.
No key, token or connection string output.

## Offline verification only

Use an existing standalone Bicep binary (`BICEP_CLI` or PATH), existing Python
test dependencies, and repository-contained dependencies if needed. No automatic
installation, login or Azure query is part of these commands:

```powershell
./infra/scripts/validate-deployment.ps1
./infra/scripts/validate-naming.ps1
python -B -m unittest discover -s infra/scripts -p 'test_modern*.py' -v
python -B -m pytest -q -p no:cacheprovider src/telemetry-pipeline/tests/test_durable_infra.py
```

`validate-deployment.ps1` is now **offline only**: all three entrypoints are compiled
with `--stdout`; JSON is in memory, never generated under `infra`. Removed old
cloud-default parameters (`SkipCreate`, RG creation, what-if/create). A caller using
them fails parameter binding before any operation. Official cloud validation/
deployment needs separate plan approval; it is not exposed as a script mode.

For a completed reviewed ARM parameter file, run
`python -B infra/scripts/validate-modern-foundation.py --parameters <reviewed.parameters.json>`.
Checked-in examples must fail this gate. Passing validates only local shape/
ownership/model-approval/secret-reference contracts, not provider capability,
authorization, quota, unique names, residency compliance or actual private access.
Graph tests require fresh compilation; retained #139 tests exercise secure no-PUT/
exact-name/mutation guards, and durable tests retain the four-resource inventory.

Before **any** cloud phase: update `.azure/deployment-plan.md`, invoke official
azure-validate, obtain exact scope/subscription/RG/resource/cost approval and
review narrow provider validation/what-if. No broad main deployment against the
live group; no automatic repair grants, model calls, fallback or deletion.

## Resource / cost delta (source only)

Classic Hub/ML Project and ML diagnostics are removed from fresh source. Fresh
composition instead defines one S0 AIServices account/project, one explicitly
selected billed model, account-scoped project MI role, Premium EP1 instead of Y1,
one VNet/two subnets/seven DNS zones/seven links in fresh mode, five PEs with DNS
groups, private keyless storage/KV, private package/container/index resources and
one explicit three-table export. Existing-network mode reuses network/DNS without
parent writes. LAW/AppInsights/EH pipeline services remain; no auxiliary AI stores,
VM or hosted compute is added. EP1/PE/DNS/storage, model capacity and telemetry
ingestion/export/egress may incur ongoing charges. No prices or savings are claimed;
cost approval belongs to the chosen fresh model/region/capacity and usage budget.
**No deployed resource, spend, grant, secret, checkpoint or state changed here.**

## Public contract basis

Read 2026-10-19, public documentation only:

- ARM [accounts](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts),
  [projects](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/projects),
  [deployments](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/deployments)
  and [connections](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/projects/connections).
- [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry),
  [published Foundry User role](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles/ai-machine-learning#foundry-user),
  [private isolation and standard-agent BYO prerequisites](https://learn.microsoft.com/azure/foundry/how-to/configure-private-link).
- [Functions host identity roles](https://learn.microsoft.com/azure/azure-functions/manage-connections?tabs=host&pivots=functions-auth-identity),
  [private Blob package MI](https://learn.microsoft.com/azure/azure-functions/deployment-zip-push#fetch-a-package-from-azure-blob-storage-by-using-a-managed-identity),
  [no Azure Files](https://learn.microsoft.com/azure/azure-functions/storage-considerations#create-an-app-without-azure-files).

Provider schemas establish documented shapes, not tenant availability or runtime
success. Agent publication/API/tools/state prerequisites remain **pending**;
standard BYO requirements are a scoped architecture gate, never silently stubbed.
# Issue 147 existing-network preparation profile

`main.issue147-existing-network.parameters.json` is a complete **nonsecret,
offline-validated foundation staging profile**, not an execution authorization
or completed tracing profile. See
[`issue147-existing-network-proposal.md`](../docs/current-state/issue147-existing-network-proposal.md)
for exact subnet/DNS/capacity facts, immutable package custody, the new
`keyVaultReferences` typed URI option, separately leased secret-scoped reader
template, and the one fresh tracing bootstrap custody action.
Existing mode never writes the supplied VNet/subnets/zones/links; new private
endpoint DNS-zone groups still register the new application records.
`freshVault` remains the backward-compatible secret-reference default.
The prepared-profile gate rejects non-vault hosts, query/fragment injection,
missing/duplicate references and malformed versions; run it before provider
validation. Existing-vault mode grants **no** external access automatically.
The fresh private vault/PE remains in the foundation graph without changing
its security controls; this profile does not require populating it.
