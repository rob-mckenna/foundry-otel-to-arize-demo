# #153 — Function-health isolation and exact existing-demo cutover

**Source implementation; NOT DEPLOYED or live-validated.** This fixes the existing
Foundry → App Insights → LAW → Event Hub → Function → Arize pipeline; it is not
direct OTLP or a fresh-foundation proposal. Only bounded metadata reads were
performed on 2026-10-20. No cloud configuration/resource/IAM changes, package
publication, VM start, model call, replay or live KQL query was performed.

## One owner decision before any creation

Rob McKenna must explicitly approve **one dedicated Function-health component and
non-exported workspace**, same existing `fotoa-demo-rg`, `eastus2`, with the names,
tags and cost choice below. Existing dev resources are **not approved substitutes**.
Approval of source changes is not approval to deploy. The coordinator must finalize
the exact commit, source hashes, package digest and nonsecret rollback identifiers
before authorizing the commands below.

### Resource/cost/cutover manifest

All ARM IDs below expand from this exact prefix:

```text
R = /subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg
```

| Exact target | Necessity and allowed change |
|---|---|
| **NEW** `R/providers/Microsoft.OperationalInsights/workspaces/fotoa-demo-funclaw-eastus2` | Dedicated health store; **no data export, diagnostic forwarding, DCR or Event Hub route**. `PerGB2018`, retention **30 days**, daily cap **1 GB**. |
| **NEW** `R/providers/Microsoft.Insights/components/fotoa-demo-funcappi-eastus2` | Workspace-based Function host/worker requests, dependencies, exceptions, logs, guard/drain diagnostics. Points only to the new health LAW. Standard workspace-based ingestion, no separate fixed component SKU charge assumed. |
| **NEW secret** `R/providers/Microsoft.KeyVault/vaults/fotoa-demo-kv-eastus2/secrets/function-health-connection-string` | ARM directly transfers component `ConnectionString` into vault. No plaintext parameter/output/file/CLI retrieval. Capture the resulting **versioned secret URI only**. |
| Existing `R/providers/Microsoft.Web/sites/fotoa-demo-func-eastus2` | Publish one reviewed guard-enabled immutable package, exact exclusion settings, then change only monitoring reference/obsolete key and temporary trigger gates. No Function parent PUT. |
| Existing `R/providers/Microsoft.Storage/storageAccounts/fotoademosteastus2/blobServices/default/containers/function-packages` | One private immutable ZIP blob, published using approved existing identity/private connectivity. Do not create storage, SAS, keys or a public endpoint. Container existence/publication authorization must be verified. |
| Existing `R/providers/Microsoft.Insights/components/fotoa-demo-appi-eastus2` and `R/providers/Microsoft.OperationalInsights/workspaces/fotoa-demo-law-eastus2` | **NO CHANGE**. Agent native tracing, source allowlist, durable namespace and active table export stay here. Never exclude this component wholesale. |
| Existing Event Hub, consumer group, host checkpoints, `genai-correlation` ledger/index, imported ACKs and quarantine | **NO CHANGE**: no reset, deletion, namespace switch, auto-replay or lease-policy change. |

New pair tags exactly match the observed demo convention:
`environment=demo`, `owner=infra-team`, `project=foundry-otel-to-arize-demo`,
`costCenter=demo-engineering`, `dataClassification=synthetic`.
The owner approves these tag values as part of the single choice.

**Incremental cost selection:** consumption-based Analytics ingestion, no commitment
tier, 30-day retention, 1-GB/day workspace cap. The official Azure Retail Prices
API returned the following applicable PAYG Analytics ingestion meter on
**2026-10-20T15:09:12.6822059Z**:

| Field | Exact public retail result |
|---|---|
| Region / product / SKU | `eastus2` / `Log Analytics` / `Analytics Logs` |
| Meter | `Analytics Logs Data Ingestion`, ID `ec00a25a-ab14-4b7b-a94f-66581f123295` |
| Type / primary meter region | `Consumption` / `true` |
| Unit / currency | `1 GB` / `USD` |
| Retail price and unit price | **2.76** at `tierMinimumUnits=5`; **0** at `tierMinimumUnits=0` |
| Effective start (both tier rows) | `2018-02-01T00:00:00Z` |
| Source | [Official API, exact meter/region/Consumption filter](https://prices.azure.com/api/retail/prices?currencyCode=USD&$filter=armRegionName%20eq%20%27eastus2%27%20and%20meterId%20eq%20%27ec00a25a-ab14-4b7b-a94f-66581f123295%27%20and%20priceType%20eq%20%27Consumption%27) |

This is a retrieved **public retail rate**, not the subscription's negotiated
contract price or proof of unused free allowance. For ingested `G` GB/day at
retail rate `P=2.76` USD/GB, gross 30-day ingestion before allowances is
`30 × G × P`: **$8.28** at 0.1 GB/day, **$82.80** at 1 GB/day.
The API also reports the zero-price starting tier; do not assume its 5-GB
allowance remains available to this workspace or subtract it again from an
already-discounted contract bill. Confirm actual billing eligibility with the
owner as part of this **same pair/cost decision**, not another resource option.
There is no extra fixed compute/VM/Event Hub SKU in this change.
KV secret operations and package Blob storage/transactions are incremental;
network egress, taxes, negotiated discounts/free allowances and Azure Monitor
table-specific included retention affect the bill. Do not double-charge App
Insights ingestion plus its backing LAW for the same data. The daily cap is
**not a hard spend ceiling**, can overshoot, and can interrupt health ingestion.
Watch ingestion/guard counts and cap notifications; reaching the cap is a health
incident, not permission to suppress health or silently raise it.

### Evidence from bounded read-only metadata (2026-10-20)

- RG inventory found the existing demo **and dev** App Insights/LAW pairs; no
  `fotoa-demo-funcappi-eastus2` or `fotoa-demo-funclaw-eastus2`. Dev ownership,
  effective export and dependency suitability were not established: no reuse.
- Demo agent component points to demo LAW, customer/workspace ID
  `4658bdb1-b9ca-4f57-a733-6b81f316dc45`. Its SKU is `PerGB2018`, retention 30,
  cap 1 GB/day.
- Enabled export `fotoa-demo-e2e-app-spans` sends **AppDependencies, AppRequests,
  AppGenAIContent** to `fotoa-demo-ehns-eastus2`, explicit hub `telemetry`.
  A second component in this LAW would therefore still feed the same pipeline.
- Function is Running with system identity
  `34e9edde-18e4-4cca-b109-7364de41fa76`; the parent PNA field was null, not proof
  of a private deployment. Do not apply fresh-template network/hosting settings.
- Function setting names include `APPLICATIONINSIGHTS_CONNECTION_STRING`,
  legacy `APPINSIGHTS_INSTRUMENTATIONKEY`, and `OTEL_RESOURCE_ATTRIBUTES`.
  The instrumentation key/resource-attribute/connection-string values were
  **not read**. No alternate OTEL exporter setting name appeared in this query.
- Safe-reference-only filters returned **no KV reference** for the existing
  monitoring connection and **no unsigned private Blob package URL**.
  **Old secret URI and old package URL are NOT established:** the safe-reference
  filters yielded zero matching rows, not a denied read or proof of absence of
  monitoring/package configuration. Required custody evidence is the prior
  package's immutable unsigned private URL + SHA256 and an existing versioned
  monitoring secret URI, **if one exists**. If legacy monitoring was never
  vaulted, its custodian must attest that no old URI exists; do not demand the
  old credential value or invent a URI. A historical ZIP below is not proof of
  today's active package. Record this baseline gap before cutover; it blocks a
  claim of reversible legacy restoration, not source readiness.
- Incoming trigger disabled flag was `false`; `DURABLE_GENAI_ENABLED=true`;
  durable source workspace/component were the existing **agent** pair. The
  outbox disabled key was absent from the selected settings (preserve absence,
  not a newly invented disabled state).
- No diagnostic settings were returned on the agent component or demo LAW.
  Function diagnostic metadata showed a **policy-owned external governance
  destination**, not demo LAW/Event Hub. **Do not access or change that external
  resource or policy.** This metadata does not prove its downstream routes are
  isolated. A successful bounded Function diagnostic GET during cycle 2 returned
  exactly one setting: `setByPolicy-MCAPSGovernance`, at
  `R/providers/Microsoft.Web/sites/fotoa-demo-func-eastus2/providers/Microsoft.Insights/diagnosticSettings/setByPolicy-MCAPSGovernance`.
  Its workspace ID is
  `/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/McapsGovernance/providers/Microsoft.OperationalInsights/workspaces/mcaps4f148af4951c0dbb92d2-la`;
  Event Hub/rule/storage destination fields were null. **Only the Function's own
  metadata was read; that workspace was not accessed.** The setting name is
  not a verified policy assignment ID. An authorized custodian must supply
  the governing policy assignment ID and attest for these exact identifiers
  that neither direct nor downstream forwarding from Function health reaches
  `fotoa-demo-law-eastus2`, `fotoa-demo-ehns-eastus2`/`telemetry`, or an equivalent
  input route, with scope and UTC observation time. No new governance route,
  external-resource query or policy change is authorized. Without that bounded
  attestation, live acceptance remains blocked.
- Existing Function MI grants observed at their individual resource scopes:
  **Key Vault Secrets User** on demo KV; **Storage Blob/Queue/Table Data
  Contributor** on demo host storage; **Azure Event Hubs Data Receiver** on demo
  namespace. This read did not inventory container-local index grants. Preserve
  existing durable index grants; no IAM writes are part of this rollout.
- KV metadata: RBAC enabled, PNA Disabled, template-deployment flag true.
  The flag is **not proof ARM secret writes or Function resolution will work**
  through the existing private boundary. Do not enable public access to fix it.

### Repo-contained packaging finding (cycle 2; no build/install/publication)

Metadata-only inspection found historical Linux Function ZIPs in repository-root
`.azure-sandbox`, not an approved extracted dependency tree at either the root
or this worktree's `.release\dependencies` (both `.release` directories absent).
The two relevant existing candidates are:

| Repository-root-relative path | Exact SHA256 | Bounded metadata finding |
|---|---|---|
| `.azure-sandbox\genai-e2c557f-20261016-active-87eef08fd92b88c55117a4d67395a7553066526decdc3a0b2619ca88b4b2da14.zip` | `87eef08fd92b88c55117a4d67395a7553066526decdc3a0b2619ca88b4b2da14` | 1,808 members, 19 wheel metadata entries, no `.pyd`, no guard module. Historical package prior art, not today's verified running bytes. |
| `.azure-sandbox\issue143-f650fed-built.zip` | `c1a276b62af37da8810c0c120b9cbe8cdff913fc76f43e51399f50db61d540f7` | 2,852 members, 29 wheel metadata entries, no `.pyd`, no guard module. Additional dependency candidate, not an approved #153 release. |

`WHEEL` metadata shows CPython 3.11 manylinux x86_64, compatible ABI3 and pure
Python tags, including `manylinux_2_28_x86_64`; tags alone do **not** prove the
target runtime/glibc compatibility, completeness against current requirements,
or approval to reuse. No source, settings or dependency payload was extracted.
CLI extension wheels are not Function dependencies. Cancelled #147/PR151
artifacts are not candidates and remain unmodified.

The concrete missing input is an **approved complete Linux/Python 3.11 runtime
dependency tree for the finalized #153 requirements**, with version/hash
provenance. The historical ZIPs above may be assessed by the existing artifact
custodian, not blindly deployed or treated as a current rollback package.
The current builder accepts an extracted dependency tree, not ZIP input, and
deliberately confines inputs/outputs to this worktree. No approved root dependency
tree was found, so it was not widened merely to consume an unapproved archive.
After approval, stage only the approved dependency members into this worktree's
`.release\dependencies`, rejecting links/reparse points and configuration
members before traversal; do not pass a repository-root archive to the builder.
This keeps output local without a new root-cache interface. **No final source
HEAD, #153 package hash or deployable #153 ZIP exists yet**; the coordinator
finalizes the commit and receipt after concurrent work concludes. Source
validation can pass while this packaging input and live acceptance remain blocked.

## Source topology and permissions

`infra/modules/function-health.bicep` owns only the pair and ARM-custodied secret.
It deliberately does **not** reuse `app-insights.bicep` (which unconditionally
exports the agent tables). The fresh Function module composes the same health
module and refers to `functionHealthConnectionStringSecretName`; permitted extra
KV settings are Arize settings only, so they cannot override health routing.
Host and any SDK using the common `APPLICATIONINSIGHTS_CONNECTION_STRING` inherit
the health sink. No health categories are disabled. Independent SDK hardcoded
exporters, legacy keys, portal auto-instrumentation overrides and external
diagnostic policies require explicit live readback; source compilation cannot
prove their absence.

For this **existing** demo use only `infra/pipeline-health-rollout.bicep`.
It writes the new pair plus secret (and an incremental nested deployment record).
**Do not deploy `main.bicep`, `function-app.bicep`, foundation, tracing or durable
rollout templates to accomplish this cutover.** They are not configuration
snapshots of this live app.

No new Function IAM grant is expected: existing KV Secrets User covers the new
secret in that vault, with existing MI/private resolution. The approving deployment
principal needs pair create/update at this RG and secret-write permission for
this exact new vault secret through the approved ARM custody path; the package
publisher needs Blob Data Contributor at the existing **package container**, if
not already authorized. An authorized verifier needs Reader on the pair and Log
Analytics Reader for count-only queries. These are **required effective scopes,
not permission to assign roles**. Do not grant subscription Contributor/Owner,
RG-wide data access, new runtime identities or Monitor publisher roles just to
make this work. If absent, stop for an explicitly scoped permission decision.

## Exact sequence — NOT EXECUTED; approval-gated commands

All commands run from this assigned worktree. Each Azure CLI process must inherit
the following config and include the explicit subscription, including offline
`az bicep` if used. Prefer the existing standalone compiler instead. Do not login,
account-set, register providers, install extensions, dump caches or print raw
provider errors. Run approved commands with bounded sanitized failure handling;
any nonzero exit stops the sequence.

```powershell
$ErrorActionPreference = 'Stop'
. .\infra\scripts\invoke-health-command.ps1
$env:AZURE_CONFIG_DIR = 'C:\repos\foundry-otel-to-arize-demo\.azure-config'
$env:AZURE_EXTENSION_USE_DYNAMIC_INSTALL = 'no'
$Subscription = 'c81fda52-936e-4f14-8af4-951c0dbb92d2'
$RG = 'fotoa-demo-rg'
$Function = 'fotoa-demo-func-eastus2'
$R = "/subscriptions/$Subscription/resourceGroups/$RG"
$HealthId = "$R/providers/Microsoft.Insights/components/fotoa-demo-funcappi-eastus2"
$FunctionId = "$R/providers/Microsoft.Web/sites/$Function"
```

Every native process below runs **alone** in `Invoke-HealthCommand`. The helper
consumes stderr in memory instead of discarding it: failure retains only the
fixed operation label, numeric exit status, up to four allowlisted Azure/Bicep
codes and four allowlisted HTTP statuses. Unknown failures become
`Unclassified`; invocation failures never print exception bodies. No raw
provider responses, arguments, setting/payload bodies or stderr are emitted on
failure. Successful stdout is limited to 64 KiB and only the explicit safe
queries below may return it; `-DiscardOutput` consumes compiler stdout without
printing a template. Output-limit and missing-exit failures also terminate.
No raw diagnostic log is written. A denied/unsupported read is a stop, never an
empty result. If a useful code is absent, report `Unclassified` and obtain
separately authorized diagnostics rather than dumping the provider response.

1. **Freeze exact rollback/cutover inputs first.** Coordinator records finalized
   source HEAD, member SHA256s, private package URL + SHA256, old monitoring
   **secret URI only**, trigger key presence/effective values and safe selected
   source flags. Resolve the baseline custody gap and containment-only recovery
   approval above before execution; do not present an old-package rollback as
   available. Do not dump
   the full settings list or retrieve values merely to produce rollback evidence.
   Refresh safe references without values using:

   ```powershell
   Invoke-HealthCommand -Operation ReadReferences -Command {
   az functionapp config appsettings list --resource-group $RG --name $Function --subscription $Subscription `
     --query "[?(name=='APPLICATIONINSIGHTS_CONNECTION_STRING' && starts_with(value, '@Microsoft.KeyVault(')) || (name=='WEBSITE_RUN_FROM_PACKAGE' && starts_with(value, 'https://fotoademosteastus2.blob.core.windows.net/') && !contains(value, '?')) || name=='AzureWebJobs.TelemetryTransform.Disabled' || name=='AzureWebJobs.DurableGenAIOutbox.Disabled' || name=='DURABLE_GENAI_ENABLED' || name=='DURABLE_ALLOWED_WORKSPACE_ID' || name=='DURABLE_ALLOWED_COMPONENT_RESOURCE_ID'].{name:name,value:value}" `
     --output json --only-show-errors
   }
   ```

2. **Build the guard package before touching routing.** Use the coordinator's
   finalized commit, not dirty worktree bytes. The builder invokes
   `git -c core.autocrlf=false -c core.eol=lf archive` with **binary stdout captured
   as bytes**, strips only the repository prefix, and packages runtime members at
   ZIP root. No PowerShell stdout redirection, CRLF normalization or text hashing.
   `host.json`, `function_app.py`, `requirements.txt`, and every runtime module
   must match git bytes, not “match after normalization.”

   Reuse an approved, repo-contained **Linux/Python 3.11 compatible** dependency
   artifact under `.release\dependencies`; do not search outside this repo, use a
   Windows venv as deployable dependencies, resolve new unpinned dependencies
   silently or copy any secret/local settings. Requirements contain ranges, not
   a locked environment. If the approved dependency artifact is unavailable,
   obtain a separately approved Linux build using this repo's requirements and
   record versions/hashes; do not install dependencies in this source-only task.

   ```powershell
   # Replace only after coordinator finalizes all concurrent source work.
   $SourceHead = '<FINAL_40_HEX_COMMIT>'
   Invoke-HealthCommand -Operation BuildPackage -Command {
   python .\infra\scripts\build-pipeline-health-package.py --source-head $SourceHead `
     --dependencies .\.release\dependencies --output ".\.release\pipeline-health-$SourceHead.zip"
   }
   ```

   The receipt records exact source-member SHA256s, all dependency hashes,
   member count and package SHA256. Ordered ZIP members, fixed timestamps/modes
   preserve reproducibility for the **same dependency bytes**; this does not
   claim that re-resolving requirement ranges is reproducible. Record Python/zlib
   build versions. Name the blob with full source HEAD and full package SHA256.
   Neither this script nor tests publish, install dependencies or read settings.

3. **Private publication + guard first.** From an already-authorized running
   private publisher with existing network/identity access (no VM start, new
   grant, package-key/SAS/public fallback), set the finalized receipt values:

   ```powershell
   $PackageSha256 = '<FINAL_64_HEX_SHA256>'
   $Blob = "pipeline-health-$SourceHead-$PackageSha256.zip"
   $PackageURL = "https://fotoademosteastus2.blob.core.windows.net/function-packages/$Blob"
   Invoke-HealthCommand -Operation PublishPackage -Command {
   az storage blob upload --account-name fotoademosteastus2 --container-name function-packages `
     --name $Blob --file ".\.release\pipeline-health-$SourceHead.zip" --auth-mode login --overwrite false `
     --metadata "sourceHead=$SourceHead" "sha256=$PackageSha256" --subscription $Subscription `
     --output none --only-show-errors
   }
   ```

   Obtain independent private readback SHA256 of the blob; metadata alone is
   not byte verification. Pause **both** existing triggers with a small
   secret-free settings file, not a Function parent/template PUT:

   ```powershell
   @{
     'AzureWebJobs.TelemetryTransform.Disabled' = 'true'
     'AzureWebJobs.DurableGenAIOutbox.Disabled' = 'true'
   } | ConvertTo-Json | Set-Content .\.release\pause-settings.json -Encoding utf8
   Invoke-HealthCommand -Operation PauseTriggers -Command {
   az functionapp config appsettings set --resource-group $RG --name $Function --subscription $Subscription `
     --settings '@.release\pause-settings.json' --output none --only-show-errors
   }
   ```

   Allow the existing 120-second claim boundary plus a bounded observation
   interval (at least 150 seconds); verify in-flight execution has ceased using
   content-free health counts. Do not clear a sending claim or assume a timeout
   means no acceptance. Preserve sending/ambiguous/rejected quarantine.

   ```powershell
   @{
     'WEBSITE_RUN_FROM_PACKAGE' = $PackageURL
     'WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID' = 'SystemAssigned'
     'PIPELINE_EXCLUDED_SERVICE_NAMES' = (ConvertTo-Json -InputObject @($Function) -Compress)
     'PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS' = (ConvertTo-Json -InputObject @($HealthId) -Compress)
   } | ConvertTo-Json | Set-Content .\.release\guard-settings.json -Encoding utf8
   Invoke-HealthCommand -Operation SetGuard -Command {
   az functionapp config appsettings set --resource-group $RG --name $Function --subscription $Subscription `
     --settings '@.release\guard-settings.json' --output none --only-show-errors
   }
   ```

   These are JSON **exact-identity arrays**, not CSV, prefixes, trace-wide or
   LLM-only filters. The shared agent component is not an exclusion.
   Before continuing, independently hash all active source files and dependency
   tree at the **running Function's script root** against the receipt using the
   approved private runtime diagnostic channel. Verify package resolution and
   trigger indexing, not just the settings URL, blob metadata or deployment
   “success.” No SCM/basic-auth secrets or new public SCM ingress. A stopped
   private validation VM is not permission to start it; absent an authorized
   running runtime-check channel, stop here.

4. **After the one pair/cost approval, provision only health resources.**
   Refresh the demo LAW export/diagnostic metadata, verify no new pair names
   preexist with another owner, and obtain the external diagnostic no-feedback
   attestation. Do not modify policy. The following is the entire resource
   deployment; review its exact compiled writable-resource inventory first:

   ```powershell
   Invoke-HealthCommand -Operation CreateHealth -Command {
   az deployment group create --resource-group $RG --name issue153-function-health --subscription $Subscription `
     --template-file .\infra\pipeline-health-rollout.bicep `
     --parameters projectToken=fotoa environment=demo location=eastus2 regionToken=eastus2 `
       ownerTag=infra-team costCenterTag=demo-engineering keyVaultName=fotoa-demo-kv-eastus2 `
       functionHealthConnectionStringSecretName=function-health-connection-string `
       workspaceSkuName=PerGB2018 retentionInDays=30 dailyQuotaGb=1 `
     --query properties.outputs --output json --only-show-errors
   }
   ```

   Output is identifiers only. Save `functionHealthSecretUri.value` as the exact
   versioned `$HealthSecretUri`, not its value. If private KV secret write fails,
   stop; do not fall back to a public vault or plaintext settings.

5. **Verify non-exported topology before the route change.** The commands must
   return the new component→new LAW, empty health exports and no health
   diagnostic forwarding. Review any unexpected policy-created route with its
   owner; no automatic deletion or export disabling.

   ```powershell
   Invoke-HealthCommand -Operation ReadTopology -Command {
   az rest --method get --subscription $Subscription `
     --url "https://management.azure.com/$($HealthId.TrimStart('/'))?api-version=2020-02-02" `
     --query "{id:id,workspace:properties.WorkspaceResourceId}" --output json --only-show-errors
   }
   $HealthLAW = "$R/providers/Microsoft.OperationalInsights/workspaces/fotoa-demo-funclaw-eastus2"
   Invoke-HealthCommand -Operation ReadTopology -Command {
   az rest --method get --subscription $Subscription `
     --url "https://management.azure.com/$($HealthLAW.TrimStart('/'))/dataExports?api-version=2023-09-01" `
     --query "value[].{name:name,enabled:properties.enable,tables:properties.tableNames,destination:properties.destination.resourceId}" `
     --output json --only-show-errors
   }
   foreach ($Id in @($HealthLAW, $HealthId, $FunctionId)) {
     Invoke-HealthCommand -Operation ReadTopology -Command {
     az rest --method get --subscription $Subscription `
       --url "https://management.azure.com/$($Id.TrimStart('/'))/providers/Microsoft.Insights/diagnosticSettings?api-version=2021-05-01-preview" `
       --query "value[].{name:name,workspace:properties.workspaceId,eventHubRule:properties.eventHubAuthorizationRuleId,eventHub:properties.eventHubName,storage:properties.storageAccountId}" `
       --output json --only-show-errors
     }
     Invoke-HealthCommand -Operation ReadTopology -Command {
     az rest --method get --subscription $Subscription `
       --url "https://management.azure.com/$($Id.TrimStart('/'))/providers/Microsoft.Insights/dataCollectionRuleAssociations?api-version=2022-06-01" `
       --query "value[].{name:name,rule:properties.dataCollectionRuleId,endpoint:properties.dataCollectionEndpointId}" `
       --output json --only-show-errors
     }
   }
   ```

   Health DCR associations must also be empty, or have separately reviewed
   destinations proving no agent-LAW/Event Hub feedback. Do not follow a rule
   into an external governance scope under this authorization. An unsupported,
   failed or denied association read is not an empty collection.

6. **Route host + worker monitoring to health, keep guards active.**

   ```powershell
   # $HealthSecretUri is the exact new versioned URI, NEVER a connection string.
   @{ 'APPLICATIONINSIGHTS_CONNECTION_STRING' = "@Microsoft.KeyVault(SecretUri=$HealthSecretUri)" } |
     ConvertTo-Json | Set-Content .\.release\health-settings.json -Encoding utf8
   Invoke-HealthCommand -Operation SetHealth -Command {
   az functionapp config appsettings set --resource-group $RG --name $Function --subscription $Subscription `
     --settings '@.release\health-settings.json' --output none --only-show-errors
   }
   Invoke-HealthCommand -Operation RemoveLegacyKey -Command {
   az functionapp config appsettings delete --resource-group $RG --name $Function --subscription $Subscription `
     --setting-names APPINSIGHTS_INSTRUMENTATIONKEY --output none --only-show-errors
   }
   ```

   Verify KV reference **resolution status without values**, worker SDK/common
   connection usage, host role and component identities; audit alternate
   monitoring setting **names** again. Do not remove operational logging or
   change `OTEL_RESOURCE_ATTRIBUTES` blindly. If an independent worker exporter
   exists, reconcile that exact route before resuming either trigger.

7. **Restore only captured trigger gates**, leaving durable mode and agent
   workspace/component/destination unchanged. For the observed baseline,
   restore absent outbox key, then incoming `false` (if a refreshed snapshot
   differs, use that exact approved snapshot instead):

   ```powershell
   Invoke-HealthCommand -Operation RestoreOutbox -Command {
   az functionapp config appsettings delete --resource-group $RG --name $Function --subscription $Subscription `
     --setting-names AzureWebJobs.DurableGenAIOutbox.Disabled --output none --only-show-errors
   }
   @{ 'AzureWebJobs.TelemetryTransform.Disabled' = 'false' } |
     ConvertTo-Json | Set-Content .\.release\resume-settings.json -Encoding utf8
   Invoke-HealthCommand -Operation ResumeIncoming -Command {
   az functionapp config appsettings set --resource-group $RG --name $Function --subscription $Subscription `
     --settings '@.release\resume-settings.json' --output none --only-show-errors
   }
   ```

   Resume outbox first only after guard-enabled active bytes and health routing
   are independently verified. Verify passive executions, exclusion outcomes and
   preserved quarantine; do not replay pending input to generate evidence.

## Passive verification — counts only, no new model invocation

Separately authorize query/readback access. Use a fixed 15-minute post-resume
window, then allow 15 minutes for ingestion/export latency and repeat **once**.
Record UTC `Start`/`End`, returned counts and query success. Azure Monitor timing,
sampling/cap, inactivity or source retention can make results inconclusive.
Do not keep polling or generate synthetic model calls to fill a quiet window.

Run in the **new health LAW** first; use its customer ID read from safe workspace
metadata (not the shared source UUID):

```kusto
let Start = datetime(<APPROVED_UTC_START>);
let End = datetime(<APPROVED_UTC_END>);
union withsource=Table isfuzzy=true AppRequests, AppDependencies, AppTraces, AppExceptions
| where TimeGenerated between (Start .. End)
| where AppRoleName == "fotoa-demo-func-eastus2"
| summarize Rows=count() by Table, _ResourceId
```

Expected: nonzero host/timer/drain health with the new component ID; exceptions
can legitimately be zero. Guard/drain logs must remain queryable; use count-only
aggregation of the documented `durable outcome=`/exclusion reason prefix, never
return log bodies or hashed ledger keys. These are health counters, not proof
of Arize delivery.

In the **existing agent LAW**, count newly ingested Function contamination:

```kusto
let Start = datetime(<APPROVED_UTC_START>);
let End = datetime(<APPROVED_UTC_END>);
union withsource=Table isfuzzy=true AppRequests, AppDependencies, AppGenAIContent
| where TimeGenerated between (Start .. End) and ingestion_time() >= Start
| where AppRoleName == "fotoa-demo-func-eastus2"
    or _ResourceId =~ "<EXACT_NEW_HEALTH_COMPONENT_ARM_ID>"
| summarize PipelineRows=count() by Table
```

Expected zero new pipeline-role/component rows after the latency boundary;
empty groups count as zero only on a successful query. Historical shared-source
rows can still be draining and are blocked by exact Function role. A query
failure is not zero. Missing role is not automatically pipeline/excluded.

Count genuine agent non-LLM children in the same passive window:

```kusto
let Start = datetime(<APPROVED_UTC_START>);
let End = datetime(<APPROVED_UTC_END>);
union withsource=Table AppRequests, AppDependencies
| where TimeGenerated between (Start .. End)
| where _ResourceId =~ "<EXACT_EXISTING_AGENT_COMPONENT_ARM_ID>"
| where AppRoleName != "fotoa-demo-func-eastus2"
| where isnotempty(ParentId)
| extend Kind=tostring(Properties["openinference.span.kind"])
| summarize Children=count(), NonLLMChildren=countif(Kind !in ("LLM", "AGENT"))
```

Use approved existing Arize metadata-only readback to compare counts and
trace/span/parent identities for naturally arriving legitimate children
(tool/chain/error spans included). Do not expose prompt/content bodies or
claim kind absence proves a span is non-LLM. If no legitimate children arrive,
live preservation is **inconclusive**; offline mixed-batch tests establish the
code behavior, not new live traffic. No whole-trace completeness, historical
cleanup or exactly-once guarantee follows.

For CLI query execution, populate `$WorkspaceId`, `$CountOnlyKql` and `$Timespan`
with the approved exact health/source customer ID, count-only query and fixed
`START/END` window respectively, then use:

```powershell
Invoke-HealthCommand -Operation QueryCounts -Command {
  az monitor log-analytics query --workspace $WorkspaceId --analytics-query $CountOnlyKql `
    --timespan $Timespan --subscription $Subscription --output json --only-show-errors
}
```

Do not dynamically install its extension; absent tooling, use the authorized
Azure Monitor query interface. No raw errors or payload dumps.

## Rollback safety floor

- Record the baseline custody gap above, any established **old secret URI and
  old package URL + digest**, and the **new versioned health secret URI and
  guard package URL + digest**. Old identifiers remain unestablished; do not
  claim reversible legacy rollback. An owner-authorized containment-only
  cutover can use the new verified guard + isolated health sink while paused;
  this is not permission to skip artifact, topology or route-attestation gates.
- **Never roll back monitoring to the exported shared agent LAW while export
  is active.** Never restore the legacy instrumentation key as a shortcut.
- If source/routing verification fails, pause both triggers using the exact
  pause-settings command above. Keep the guard package and new health sink
  active; restore only a previously verified **isolated-health** secret version
  if one exists. With no known-safe isolated reference, keep paused and escalate.
  Pausing stops new trigger intake/drains after in-flight work is verified
  quiescent; the guard rejects residual self-telemetry and isolated health keeps
  diagnosis observable without feeding the agent export. This is safe failure
  containment, **not restored service** or proof of exactly-once delivery.
- A package rollback requires an explicitly verified guard-capable package
  compatible with the current durable `excluded` tombstones. The pre-fix
  package is **not** a safe fallback while workspace export is active.
  Apply its exact approved private URL using the same guard-settings mechanism;
  do not change ledger/source/destination scope.
- Preserve checkpoints, imported ACKs, excluded tombstones, pending unsent work,
  retries and sending/ambiguous/rejected quarantine. No automatic resend,
  ledger deletion or namespace switch. Do not disable durable mode or start a
  second exporter. Owner chooses any later remediation/replay explicitly.
- Do not delete the new pair/secret until monitoring has a separately approved
  non-exported replacement and required health retention has elapsed.

## Offline checks

From the worktree, using the existing repository-contained standalone compiler:

```powershell
$ErrorActionPreference = 'Stop'
. .\infra\scripts\invoke-health-command.ps1
$env:BICEP_CLI = 'C:\repos\foundry-otel-to-arize-demo\.azure-config\bin\bicep.exe'
Invoke-HealthCommand -Operation Compile -DiscardOutput -Command {
  & $env:BICEP_CLI build .\infra\pipeline-health-rollout.bicep --stdout
}
Invoke-HealthCommand -Operation Compile -DiscardOutput -Command {
  & $env:BICEP_CLI build .\infra\modules\function-app.bicep --stdout
}
Invoke-HealthCommand -Operation Compile -DiscardOutput -Command {
  & $env:BICEP_CLI build .\infra\main.bicep --stdout
}
Invoke-HealthCommand -Operation Test -DiscardOutput -Command {
  python -B -m unittest discover -s .\infra\scripts -p 'test_pipeline_health*.py' -v
}
Invoke-HealthCommand -Operation Test -DiscardOutput -Command {
  python -B -m unittest discover -s .\infra\scripts -p 'test_modern_*.py' -v
}
.\infra\scripts\test-health-command.ps1
.\infra\scripts\validate-naming.ps1
if (-not $?) { throw 'Naming validation failed' }
Invoke-HealthCommand -Operation Diff -Command { git --no-pager diff --check }
```

Compilation checks source only, not Azure policy, effective permissions, external
routes, KV resolution, private package reachability or delivery. No what-if or
deployment was run. Telemetry owns the runtime exclusion/mapping/export test
evidence; coordinator assembles that evidence before any cutover decision.

### Local validation receipt (2026-10-20)

- `bicep build .\infra\pipeline-health-rollout.bicep --stdout`: **PASS**,
  no compiler/linter warnings (stdout discarded, existing standalone compiler).
- `bicep build .\infra\modules\function-app.bicep --stdout`: **PASS**,
  no compiler/linter warnings.
- `bicep build .\infra\main.bicep --stdout`: **PASS**, no compiler/linter warnings;
  compile only, no foundation deployment or source change to `main.bicep`.
- `python -B -m unittest discover -s .\infra\scripts -p 'test_pipeline_health*.py' -v`:
  **7 tests, OK** (four topology/custody tests, three byte-exact package tests).
- `python -B -m unittest discover -s .\infra\scripts -p 'test_modern_*.py' -v`:
  **26 tests, OK**.
- `.\infra\scripts\validate-naming.ps1`: **PASSED for 9 modules**.
- `.\infra\scripts\test-health-command.ps1`: **PASS** — synthetic success,
  allowlisted `AuthorizationFailed`/403 with exit 7, raw stdout/stderr redaction,
  64-KiB output bound, immediate sequence stop on exit 9, unknown-error
  classification, and unavailable-command redaction/stale-exit protection.
  No Azure write command was exercised.
- All **12** PowerShell command blocks parsed without executing their cutover
  commands.
- `git --no-pager diff --check`: **PASS**.

No dependencies were installed. Package tests use only synthetic project-local
fixtures and remove their scratch files. No real release ZIP was built because
the coordinator has not finalized the source commit/dependency artifact.
