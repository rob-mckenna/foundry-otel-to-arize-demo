# Existing-resource telemetry bridge attachment

**Preparation only; not an allocation, deployment approval, or live validation.**
There is one path: `main.bicep`, with one synthetic `main.parameters.json`
example. It attaches the durable bridge to an **existing** Foundry
account/project/model deployment and exact numbered Prompt Agent version.
It does not create Foundry, models, agents, a landing zone, or a new bridge host.
If the prerequisites below are unavailable, preparation is blocked. Have the
resource owners supply them under a separate approval; do not enable public
access, shared keys, broader roles, or remote-build/SCM fallbacks.

## Exact write boundary

Run only in the existing bridge resource group, in incremental mode:

| Written resource | Effect |
| --- | --- |
| Existing Function's `config/appsettings` child | Full PUT of the supplied complete baseline plus the runtime settings below; both triggers disabled |
| Existing agent LAW's named `dataExports` child | Same reviewed namespace/hub destination and enabled state; union all existing tables with `AppRequests`, `AppDependencies`, `AppGenAIContent` |
| Existing storage's `default/genai-correlation` container | Private (`publicAccess: None`); no account properties modified |
| Custom durable index role + container-scoped assignment | Only blob-tag write and container-local blob filter data actions for the existing Function system identity |

The custom role uses the retained `durable-genai-index-v1` GUID derivation.
Existing assignments with another name/GUID need owner review, not replacement.
The custom definition's assignable scope is the resource group; its **assignment**
is only the correlation container. All other access must already exist.

No base Function/plan/identity, storage, Event Hub, Key Vault, App Insights,
workspace, Foundry, model, subnet, DNS, private endpoint, firewall, publishing
policy, or other RBAC resource is redeployed. Existing resource tags and network
posture are untouched. The removed Function module imported DNS types from the
removed networking module; neither is imported by this attachment.

## Blocking prerequisites

The owner must independently attest every item; offline validation cannot:

1. **Invocation target:** existing Foundry account/project, model deployment,
   agent name and exact positive numbered version (not `latest`). `existingAgent`
   records this target in the deployment outputs only. This bridge scopes records
   to an agent component/workspace, **not to an individual agent version**.
   The invocation client must select that exact version. Multiple agents sharing
   that component can still be exported.
2. **Agent sink:** existing agent Application Insights component linked to the
   named LAW. The three export tables must be supported/available in that LAW;
   the agent's native content-tracing configuration must already be in place.
   This attachment neither enables tracing on Foundry nor changes its connections.
3. **Bridge host:** existing Linux Python 3.11 Functions v4 Elastic Premium
   Function with **system-assigned** identity. Public Function/SCM access,
   FTP/SCM basic auth disabled; HTTPS/TLS 1.2 required. Existing VNet integration,
   private endpoints and DNS must already work. This is not a migration from
   consumption, public SCM, Azure Files, connection-string auth or another MI.
4. **Storage/package:** existing HTTPS/TLS 1.2 StorageV2 account, public network,
   anonymous blobs and shared-key access disabled; private Blob/Queue/Table
   endpoints and DNS reachable by host and authorized package publisher.
   Existing `function-packages` container and SHA-256-named immutable ZIP.
   No SAS. Set `WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID=SystemAssigned`.
   The ZIP contents, Linux dependencies, package SHA, and **deployed** exact runtime
   function set (`TelemetryTransform`, `DurableGenAIOutbox`) need separate
   attestation; a URL or successful Bicep build proves none of these.
5. **Event Hub:** existing namespace, exact hub and dedicated consumer group;
   identity-based Function receiver access and native LAW-export sender access
   must work with the **existing approved** service-ingestion/firewall posture.
   Native LAW export may require its supported public service-ingestion path:
   do not convert it to private-only or open its firewall here. Stop if the
   current posture cannot support export. No namespace/SAS/local-auth changes.
6. **Key Vault:** existing RBAC vault and live, unexpired secrets for the Arize
   endpoint/space/API key and Function-health connection string, resolving via
   the Function system identity. Private vault endpoint/DNS/routes and private
   publication must preexist. No vault shell, secret writing or access widening.
   Arize API-key authentication is the non-MI exception; key stays in Key Vault.
7. **Separate health sink:** existing Function-health Application Insights and
   its own LAW, both different from the agent sinks. Its connection-string
   secret must point there, and **no export path** may send that LAW's health
   telemetry to the agent bridge. Its current approved ingestion path must
   already be reachable. Do not add an export to this workspace.
8. **Existing access:** Function identity has the host's required Blob Data
   Owner, Queue Data Contributor and Table Data Contributor roles on host
   storage, plus application Blob Contributor access for the durable ledger,
   Event Hubs Data Receiver on the hub/namespace and Key Vault Secrets User
   for references. This attachment does not create these grants. Its only
   additive grant is the container-scoped index permission described above.
9. **Reviewed baseline:** supply the complete current nonsecret Function settings
   map and complete export table list, exact destination and enabled state.
   Do not pass raw connection strings or keys; sensitive settings must already
   be Key Vault references. Preserve required custom settings/host identity.
   Do not attach during concurrent settings/export updates. If completeness,
   destination, identity principal ID, resource-group scope, or package readiness
   cannot be independently confirmed, stop rather than send a destructive PUT.

All bridge references are in the deployment subscription/resource group
(the existing Foundry target can be elsewhere). The example uses fabricated
names, zero subscription ID and a synthetic principal: **never deploy it**.

## Preparation interface

From the repository root, with Python 3.11+ and the standalone Bicep CLI:

```powershell
python infra\scripts\prepare-bridge.py --parameters infra\main.parameters.json
bicep build infra\main.bicep --stdout > $null
python -m unittest discover -s infra\scripts -p "test_*.py" -v
```

The checker is read-only/offline, uses only worktree-contained input paths,
rejects legacy auth/mode settings, mismatched storage URIs, nonimmutable package
URLs, shared agent/health sinks and unversioned agent targets. It prints a
canonical `parametersSha256` and the required confirmation names.
`contract: PASS` is **not readiness**, especially for synthetic example values.

For a separately approved real preparation, create an **uncommitted** local
parameter copy containing reference values only and owner evidence with:

```text
{
  "parametersSha256": "the canonical digest printed for the exact local parameters",
  "confirmations": {
    "exactAgentVersionExists": true,
    "agentComponentWorkspaceLink": true,
    "completeSettingsAndExportSnapshot": true,
    "privatePremiumFunctionAndSystemIdentity": true,
    "privateHostStorageAndPackageAccess": true,
    "privateKeyVaultReferencesResolved": true,
    "eventHubIdentityAndExportAccess": true,
    "separateHealthSinkWithoutExport": true,
    "scopedRbacReady": true,
    "privatePublicationAndDnsReady": true,
    "linuxPackageAndRuntimeSetAttested": true
  }
}
```

These booleans record the owner's independent checks, not checks performed by
the script. Keep the underlying evidence in the approved operational system,
not raw telemetry, credentials or production captures in this repository.
Changing any parameter invalidates the digest. Example **future operator**
commands (not authorization to run them):

```powershell
python infra\scripts\prepare-bridge.py --parameters .local\bridge.parameters.json --attestation .local\bridge-attestation.json
# Only after separate Azure review/approval; this contacts Azure:
az deployment group what-if --resource-group $ResourceGroup --template-file infra\main.bicep --parameters "@.local\bridge.parameters.json"
# Only after separately approved what-if:
az deployment group create --mode Incremental --resource-group $ResourceGroup --template-file infra\main.bicep --parameters "@.local\bridge.parameters.json"
```

Review must show only the write set above. Base resources, unexpected grants,
changed export destinations, absent prerequisite private access or unresolved
Key Vault references are blockers, not opportunities for fallback.
ARM can be invoked without this checker; it does not enforce owner attestation.

## Runtime settings and activation boundary

`main.bicep` preserves unrelated baseline settings and configures:

- `FUNCTIONS_EXTENSION_VERSION=~4`, `FUNCTIONS_WORKER_RUNTIME=python`.
- `AzureWebJobsStorage__accountName`, `AzureWebJobsStorage__credential=managedidentity`;
  optional existing service URIs must name that same storage account.
- `EventHubConnection__fullyQualifiedNamespace`,
  `EventHubConnection__credential=managedidentity`,
  `EVENT_HUB_CONNECTION_SETTING_PREFIX=EventHubConnection`,
  `EVENT_HUB_NAME`, `EVENT_HUB_CONSUMER_GROUP`.
- `DURABLE_ALLOWED_WORKSPACE_ID`, `DURABLE_ALLOWED_COMPONENT_RESOURCE_ID`,
  `DURABLE_ARIZE_PROJECT`.
- Key Vault references for `ARIZE_OTLP_ENDPOINT`, `ARIZE_SPACE_ID`,
  `ARIZE_API_KEY`, `APPLICATIONINSIGHTS_CONNECTION_STRING` (health only).
- `PIPELINE_EXCLUDED_SERVICE_NAMES` / `PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS`:
  JSON arrays; preserve existing exclusions and add the Function service name
  and health component ID. These are the runtime **SourcePolicy** guard.
- `AzureWebJobs.TelemetryTransform.Disabled=true` and
  `AzureWebJobs.DurableGenAIOutbox.Disabled=true`. Every preparation pauses both.

There is no console/direct mode or `DURABLE_GENAI_ENABLED` switch. The only
runtime is durable Blob state in `genai-correlation`, with a **300-second**
join horizon and **30-second** outbox sweep. These constants belong to the
runtime, not a choice of deployment profile.

Package publication/trigger synchronization, Key Vault resolution, exact
runtime indexing, and a bounded synthetic end-to-end acceptance are separate
approved operations on the private host. After those checks, an authorized
operator must explicitly enable **both** named triggers together. This repo
contains no activation, replay, incident-cutover or SCM mutation tool.
Do not interpret preparation success as guard-release deployment or proof that
an existing Function is running the source in this checkout.

## Minimal immutable packaging

Use a clean finalized source commit and a separately approved, worktree-local
Linux Python 3.11 dependency tree built from
`src\telemetry-pipeline\requirements.txt`. Do not reuse incident archives or host
dependencies. Dependency installation is not part of attachment.

```powershell
python infra\scripts\build-function-package.py --source-head $FinalizedCommit --dependencies .release\dependencies --output .release\bridge.zip
```

The builder archives committed runtime source bytes (not working-tree edits),
packages local dependency bytes reproducibly, rejects Windows binaries/secret
configuration and escaping paths, requires the retained durable-only module set
and exactly the two named function registrations, and emits `.receipt.json` source/dependency/
ZIP hashes. Publish the ZIP under `<packageSha256>.zip` in the existing private
`function-packages` container using an approved private publisher; updating the
baseline URL requires renewed attestation. No upload or deployment is performed.
Receipts establish byte provenance only, **not dependency compatibility or live
runtime readiness**.

## Validation and removal

Offline Bicep compilation and `infra\scripts` tests cover the retained write
boundary, settings/export preservation, scoped index permissions, preparation
blockers and package mechanics. Telemetry's runtime tests cover actual durable
mapping/export; infrastructure tests do not replace them.

No Azure operation was run as part of this reduction. Fresh allocation (#147),
live guard-release activation (#153), and existing-resource package/function
attestation remain outside this change. Existing POC resources are untouched.
There is no teardown script: removal needs independent approval to pause both
triggers, assess unsent durable state and export ownership, then remove only
approved attachment-owned children/assignments. Never delete existing base
resources or the exported workspace to clean up this attachment.
