# Fresh modern foundation — readiness and acceptance packet (#147)

**2026-10-20 existing-network correction:** the
[concrete fresh-application proposal](issue147-existing-network-proposal.md)
supersedes the disconnected-new-VNet blocker and missing-name/profile gaps.
ADR-0004 explicitly supports reusing the existing network. The complete
nonsecret profile and tested existing-secret URI contract are now implemented.
This is **fresh application / existing networking**, not standalone full-fresh-
network proof; QA must preserve that distinction in eventual acceptance.
Fresh tracing still requires the exact new-component secure bootstrap described
there; no fresh execution or closure is claimed.

**2026-10-19 · QA owner (`squad:qa`) · BOUNDED OFFLINE CHECKS PASS;
FRESH-READINESS HOLD / NOT READY FOR EXECUTION APPROVAL.
PROVIDER / FRESH PRIVATE RUNTIME / REPEAT DEPLOYMENT / E2E NOT RUN.**

**2026-10-20 Infra followup:** owner approved the minimal no-tool Basic/private
CLIENT ingress + Microsoft-managed runtime/state direction. No repeated scope
choice is needed. [Bounded source/execution record](issue147-bounded-execution.md)
supersedes the old choice inventory where applicable: EP1 plan/app maximum **1**,
minimum **1**, prewarmed target **1** inside the ceiling; explicit 24h validation
lifetime and finite day-7/day-30 retained-state disposition obligations, no
automatic destructive teardown. Approved direction has no numeric ceiling.
One security-plan metadata GET succeeded; exact G/L/R entitlement/custody/
private-runner/provider exceptions remain. QA owns acceptance; #147 stays OPEN
and PR #151 unmerged. No fresh deployment or live acceptance is claimed.

This is the bounded readiness slice and same-issue pricing/workflow followup of [#147](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/147),
not deployment, invocation, spending, grant, or retirement approval. Source baseline:
`main` `2219075`, including #146/#145 and #149. [ADR-0004](../adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md)
and [infra/README](../../infra/README.md) define the supported graph:
Foundry → Application Insights → LAW → Event Hub → Function → Arize.
Earlier #143/#144 receipts do not validate a fresh environment or exactly-once delivery.

## 1. What this slice actually establishes

- Three supported entrypoints compile; modern graph, private/keyless controls,
  scoped identities, explicit consumer binding, three-table export and fresh
  disabled incoming/outbox gates pass existing offline contracts.
- Both reusable `main.parameters*.json` examples reject incomplete/unapproved
  input. Neither is an executable deployment profile. Fresh/existing **network
  ownership** is not a public/private Foundry switch.
- Pipeline mapping/export/durable regressions and local correlation/token tests
  pass. The local Prompt Agent CLI **always uses an OFFLINE STUB**, even with an
  endpoint/key. Its estimated tokens and synthetic fixtures are not live usage.
- Narrow East US 2 model/quota metadata was read; no resource/model was created,
  invoked, modified or deleted. Public official documentation and public retail
  prices were fetched directly, not sent to a research service.

The issue-specific worktree `.azure/deployment-plan.md` was created **before**
refreshing `azure-prepare`. It remains preparation-only, not Ready for Validation.
The refreshed skill's reference tree is outside the repository and was **not
read**. The followup reconciled existing official references and fetched only
needed public official equivalents, pinned and hashed in the repository.
[Exact workflow gates](issue147-workflow-gates.md) replace the earlier
“missing/unreconciled references” blocker: public references are now available,
but approval, technical prerequisites and official workflow execution are not.
Public prose/offline tests do not confer `Validated`. The closed root
plan/receipts remain immutable.

## 2. Historical consolidated decision packet (see approved-direction update above)

### Technical go/no-go — distinguish scope choice from fresh readiness

The integrated [Agent prerequisite assessment](issue147-private-agent-prerequisites.md)
resolves the runtime contract; it does **not** clear fresh acceptance:

| Boundary | What existing evidence proves | Fresh technical gap / consequence |
|---|---|---|
| Source / historical runtime | ARM account/project/model modules pin **2025-09-01**. Historical existing agent version `"1"` is a new Foundry `PromptAgentDefinition`, zero tools, bound to the existing **GlobalStandard capacity 5** deployment. Bounded metadata and prior runtime evidence are not fresh deployment proof. | Fresh Bicep does not publish an agent. The shipped local client remains an offline stub. Fresh publication/readback, immutable runner/dependency lock, validator identity/network and actual usage/correlation evidence are missing. |
| Exact data plane | `azure-ai-projects==2.0.0`, `azure-identity==1.26.0`, `openai==2.26.0`; `AIProjectClient(api_version="v1").agents.get_version(...)` returns `AgentVersionDetails` / `PromptAgentDefinition`. Invoke HTTPS **POST `<project-endpoint>/openai/v1/responses`** through `project.get_openai_client().responses.create(...)`, with versioned `extra_body.agent_reference` and deployment alias in the definition. Entra scope **`https://ai.azure.com/.default`**, private validator `ManagedIdentityCredential`. | API/SDK selection is **resolved**, not an owner guess or missing research. Full request timeout/budget/once-only intent/error controls and resolved dependency hashes still need a reviewed live runner. Classic threads/runs, account chat completions and hosted `/invoke` are not substitutes. |
| Privacy / state | Basic supports **private inbound** account access with **Microsoft-managed agent state**. Account PE/PNA Disabled does not establish private outbound service execution, customer-owned state or state residency. Existing metadata is consistent with Basic, not certification of hidden runtime placement. | A is compatible with the current foundation; record its explicit ADR ingress clarification. **Only if B is selected**, source is technically incomplete: Standard needs Storage **and Search and Cosmos**, dedicated agent-subnet injection, supported capability provisioning, dependency PEs/DNS and distinct provisioning/runtime permissions. A no-tool waiver from B is not established or needed for A. Scope changes require accepted review, not silent isolation weakening or expansion. |
| Model / provider | AIServices advertises `OpenAI/gpt-5-mini/2025-08-07/eastus2/DataZoneStandard`, `agentsV2=true`, `responses=true`; quota snapshot is 0/300 Count. | **Capacity 1 remains provider-unproven**: minimum/step/allowedValues null, default 10 is not a minimum. Exact tuple/policy/name validation, allocatable capacity, provisioning and later bounded runtime success remain separate gates; no automatic capacity increase or GlobalStandard fallback. |

**2026-10-20 correction:** the earlier blanket technical NO-GO must **not** be
read as a Standard dependency mandate for ADR-0004's no-tool/private-client-
ingress foundation. Its promise is “its private reachability and the existing
telemetry pipeline's infrastructure”; §4 expressly excludes adding Search/Cosmos
merely for this foundation. It does not promise customer-VNet runtime isolation.
The [Agent scope analysis and exact choices](issue147-private-agent-prerequisites.md#1a-correction-adr-promise-authoritative-distinction-and-bounded-choices)
quote ADR-0004 and pinned official sources:
**A**, Basic private client ingress with Microsoft-service-managed runtime/state,
is compatible with the source and documented product contract; **B**, fully
isolated Standard/BYO runtime, is absent and needs an accepted ADR amendment;
**C**, US-zone model processing/residency, is independent and not a blanket
every-service residency warranty. Historical private-VM v1 invocation supports
only the existing path, never fresh readiness.

At the earlier snapshot, Lead/QA and the owner had not selected the real
acceptance boundary; the 2026-10-20 receipt now selects A as recorded above.
No silent selection or weakening is authorized. A requires an explicit
ADR scope clarification, not unrelated Standard resources. A separately accepted
stronger promise would require amendment before choosing A. Standard remains
conditionally blocked pending supported provisioning API/roles/state/cost design.
The documented `2026-07-15-preview` path does not replace ARM **2025-09-01**.
The **fresh-readiness hold remains** for package/runner/identity/network,
capacity/provider, publication, telemetry, repeat and official workflow evidence.
These are technical gates, not facts an owner can approve into existence.

The following are **proposals for explicit approval, not defaults or permission**.
They are a deferred owner-choice inventory, **not an approval-ready request**.
Do not copy approval=true into a profile until technical preparation is complete
and the owner accepts the complete row.

| Choice | Concrete recommendation / evidence | Exact outstanding decision |
|---|---|---|
| Fresh scope | Subscription `c81fda52-936e-4f14-8af4-951c0dbb92d2`; propose new RG `fotoa-demo-rg147-eastus2`, token `fotoa147`, environment `demo`, region/regionToken `eastus2`. Propose account/subdomain `fotoa147-demo-foundry-eastus2`, project `fotoa147-demo-fproj-eastus2`, model alias `qa147-synthetic`. | Owner confirms **new** RG/name availability, ownerTag, costCenterTag and new-resource executor principal ID. No existing RG is an alternative. Naming checks do not prove global uniqueness. |
| Model + processing | Propose `OpenAI / gpt-5-mini / 2025-08-07 / DataZoneStandard / capacity 1 / NoAutoUpgrade`, in `eastus2`, US data-zone processing. Catalog lists this version; Agent Service supports East US 2 private VNet; scoped model metadata lists DataZoneStandard. No PTU, batch, instant-model path, spillover, alternate model or automatic upgrade. | Accept exact tuple and **US-zone processing, not East-US-2-only inference**; accept no-auto-upgrade and pre-retirement review. Capacity **1 is a proposal**, not a documented minimum: returned minimum/step were null; provider validation must accept it. Do not silently take returned default 10. Model SKU metadata reported deprecation `2027-02-09`; recheck lifecycle before execution. |
| Residency alternative | GlobalStandard is public-documented and present in metadata, but allows global inference. Geography-based Standard is not listed in this scoped model result. | If US-zone is unacceptable, stop for a newly approved tuple/design; no automatic GlobalStandard fallback. Storage residency, agent-state location and Arize destination processing/retention also need approval. A private endpoint is not a residency control. |
| Quota | Read-only `eastus2` result: DataZoneStandard gpt-5-mini current **0**, limit **300**, unit **Count**; GlobalStandard current **605**, limit **1000**, unit **Count**. Thus headroom snapshots are 300 / 395 capacity-count units respectively. | Quota discovery is **not missing**; fresh reservation/availability at execution is. Recheck exact selected SKU; require provider acceptance. Do not equate capacity counts to TPM/RPM without the selected model contract, reallocate existing capacity, request an increase or call inference to test quota. |
| Network / validator | Prefer fresh network ownership to avoid writes to shared DNS/VNet. Propose the example `/24`, PE `/26`, Function `/26` only after network-owner nonoverlap review. Same-region Foundry/VNet, five PEs, seven DNS zones/links; preserve Monitor ingestion/query, LAW→EH and Arize HTTPS egress. | Network owner confirms CIDRs, egress and DNS authority; supplies already-approved private validator identity/path. **No VM start/new VM/VPN/NAT/AMPLS is authorized.** Function integration subnet is not an Agent Service injection subnet. |
| Private Agent prerequisites | One synthetic text-only new Foundry Prompt Agent, **no tools**, no evaluation or hosted compute. Exact v1 Responses API/SDK pins are resolved above and in the [Agent assessment](issue147-private-agent-prerequisites.md). | Choose explicit A/B acceptance boundary per Agent §1a: Basic private client ingress/service-managed state is compatible with ADR-0004's foundation, subject to recorded clarification; Standard BYO/injection needs an accepted amendment. No Standard resource mandate for A. Fresh agent/version, consumer/author identities, publication/readback, applicable state/recovery limitations, private validator and immutable runner remain technical gates. No Search/Cosmos/ACR/capability additions are authorized. |
| Tracing custody | Stage with `preserveExisting` (no connection PUT); then use the narrow tracing entrypoint with explicitly approved ApiKey association, reviewed sharing/PE fields and version-pinned KV deployment reference. Foundry account local auth remains disabled. | Name responsible secret custodian and deployer; record immutable secret **reference** version, component binding attestation, deployment-enabled vault/private ARM resolution and connection name. A newly created vault does not contain the new component's secret automatically. No plaintext, secret reads, broad grants or network relaxation. |
| Package custody | Dedicated private `function-packages`; immutable reviewed ZIP name such as `telemetry-<commit>-<sha256>.zip`, package hash/build provenance, Python 3.11/Linux compatible dependencies; system-MI Blob fetch. | Name build/publisher and private uploader principal IDs, approved blob path/hash, Function MI fetch readiness and trigger-sync executor. No SAS, shared keys, raw app-settings export, public SCM bootstrap or overwriting a package URL. Release artifacts are not checked into this doc. |
| Durable / destination | Fresh `genai-correlation`, explicit `function-transform` consumer and `telemetry` hub, AppDependencies/AppRequests/AppGenAIContent export. Keep `TelemetryTransform` and `DurableGenAIOutbox` disabled until cutover. | Exact workspace UUID, component ARM ID, destination endpoint/project/space identity attestations and KV secret-reference custodians. Telemetry records all ADR-0003 runtime gates, native schema/retention and ledger/index/ACK/outbox readiness before a separately approved enablement. `arizeProjectName` alone does not configure durable scope. |
| Cost / lifetime | **24h validation lifetime** from first allocation; source EP1 floor/plan/app maximum **1**, minimum/prewarmed target 1. Five PEs/seven zones. Conditional priced subtotal **$15.504880 at N=1**, **plus unresolved security/Arize/runtime/overages/tail**. N=20 is historical sensitivity, not selectable. | [Bounded followup](issue147-bounded-execution.md) fixes the source limit and operator tail plan. **USD25/USD60 are not approved caps**. Exact entitlement/custody/provider gates remain; no automatic teardown. |
| Invocation envelope | Propose **one** live synthetic request, scenario `benefits-deductible-lookup`, new run/correlation IDs, input ≤1,024 tokens, `max_output_tokens=1024` including reasoning, **zero client retries**, no tools/evaluation, one-at-a-time. | Agent confirms API enforces envelope; owner accepts request/token/dollar bounds. No second call on timeout/ambiguous delivery. Poll evidence at most three times over 20 minutes, then stop/reconcile. Limits are proposals, not fabricated usage figures. |

**Consolidated decision packet, not a demand to approve missing discovery:**
Infra/Agent/Telemetry must finish the technical gates in the linked
Agent/cost/workflow ledgers first. The Agent artifact is now integrated into
this same-issue packet and PR #151. Provider-only validation/admission unknowns
are explicitly retained, not recast as owner choices or prerequisites already
passed. Coordinator can then present actual scope/privacy/model/residency,
complete spending/lifetime and named custody decisions together, with any
separately gated provider checks clearly identified. Approval cannot certify
capacity, private networking or missing implementation. Execution handoffs
remain later and separately authorized.

## 3. Full source cost ledger — conditional estimate, not an approved quote

The followup [itemized estimate](issue147-cost-estimate.md) accounts for every
source resource and potential meter: EP1 min/max/buffers, EH TU/ingress/retention,
Blob/Queue/Table capacity/operations and retained state, PE/DNS/network/egress,
LAW ingestion/retention/export, KV/keyless package custody, DataZone model tokens,
Defender/malware/governance and Arize/external-license unknowns.
The [machine-readable evidence](issue147-planning-evidence.json) preserves
39 selected public meters from six complete response sets with source URLs,
effective dates, retrieval times, immutable workflow commit and file hashes.

For the explicitly conditional 24h quantities, priced subtotals are
**$15.504880 (N=1), $116.919280 (N=20)**; N=100 sensitivity is $543.927280.
Full cost additionally includes unresolved security/entitlements **G**, Arize/
license **L**, Agent/private-runner/build/state **R**, overages and retained
lifetime. No unconditional all-inclusive ceiling exists. Twenty-instance
maximum is now historical sensitivity, not the permitted source configuration
(explicit plan/app maximum 1) or provider proof.
Thirty additional idle retained days illustrate **$235.0028** more under stated
security/capacity/rounding/connection assumptions, before continuing usage and
those unresolved addends.

**USD25 is an unapproved historical proposal, not an approved cap.
$185.93/month below remains historical partial-baseline math, not the quote.**

### Earlier public partial baseline (superseded for decision-making)

Direct official [Retail Prices API](https://prices.azure.com/api/retail/prices)
read 2026-10-19 (USD retail, no customer pricing or secrets):

| Meter / quantity | Returned rate | Planning subtotal |
|---|---|---|
| East US 2 Premium vCPU Duration, 1 core | $0.16 / hour | $0.16/hour |
| East US 2 Premium Memory Duration, EP1 3.5 GB sizing | $0.0114 / GiB-hour | approximately $0.0399/hour |
| Global `Virtual Network Private Link / Standard Private Endpoint`, 5 PEs | $0.01 / endpoint-hour | $0.05/hour |
| Azure DNS Private Zone, first 25 tier, 7 zones | $0.50 / zone-month | $3.50/month (daily prorating applies) |
| Azure DNS Private Queries | $0.40 / million | usage-dependent |

EP1 + five PEs is approximately **$0.2499/hour**, **$6.00/24 hours**,
or **$182.43/730 hours**; adding seven full-month DNS zones gives about
**$185.93/month**. This is a **partial baseline, not a ceiling or quote**.
It excludes Event Hub Standard throughput/ingress, LAW/AppInsights ingestion/
retention/export, storage capacity/operations, KV operations, Private Link data
processing, network transfer, Arize charges and inference. EP1 capacity=1 is
not proof of a hard maximum burst limit. Infra must reconcile maximum scale
and price all omitted meters before owner spending approval.

Reproduce public prices without Azure authentication (PowerShell):

```powershell
$filters = @(
  "serviceName eq 'Functions' and armRegionName eq 'eastus2' and priceType eq 'Consumption'",
  "meterName eq 'Standard Private Endpoint' and priceType eq 'Consumption'",
  "serviceName eq 'Azure DNS' and priceType eq 'Consumption'"
)
foreach ($filter in $filters) {
  $url = 'https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&$filter=' + [uri]::EscapeDataString($filter)
  $page = Invoke-RestMethod -Uri $url -TimeoutSec 45
  $page.Items | Where-Object {
    ($_.productName -eq 'Premium Functions') -or
    ($_.meterName -eq 'Standard Private Endpoint' -and $_.armRegionName -eq 'Global') -or
    ($_.meterName -in @('Private Zone','Private Queries') -and $_.armRegionName -eq '')
  } | Select-Object productName,meterName,retailPrice,unitOfMeasure,currencyCode,tierMinimumUnits
  if ($page.NextPageLink) { throw 'Incomplete price page; review pagination before quoting.' }
}
```

The first combined price request was throttled (429); one later bounded
Functions request succeeded. Region-only Private Link filters found no rows:
the matched meter is **Global**, not an East US 2 meter. Pricing HTML rendered
`$-`, not numeric quotes. Do not convert missing prices to zero.

## 4. Reproducible existing offline acceptance

Run from the issue worktree, not the team root. Python 3.11.9; standalone Bicep
is repo-contained. No Azure command is invoked by the following checks:

```powershell
Set-Location C:\repos\foundry-otel-to-arize-demo\.worktrees\issue147-readiness
$env:BICEP_CLI = 'C:\repos\foundry-otel-to-arize-demo\.azure-config\bin\bicep.exe'
.\infra\scripts\validate-deployment.ps1
.\infra\scripts\validate-naming.ps1
python -B -m unittest discover -s infra\scripts -p 'test_modern*.py' -v
python -B -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests\test_durable_infra.py
python -B -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests tests\telemetry-mapping tests\export\test_otlp_export_conformance.py
python -B infra\scripts\validate-modern-foundation.py --parameters infra\main.parameters.json
python -B infra\scripts\validate-modern-foundation.py --parameters infra\main.parameters.private-endpoint.json
```

| Exact command above | Actual result, 2026-10-19 |
|---|---|
| `.\infra\scripts\validate-deployment.ps1` | PASS; main, tracing and durable entrypoints compile; modern outputs checked. Two existing BCP334 warnings at durable rollout lines 87/92 (minimum string length); no provider claim. |
| `.\infra\scripts\validate-naming.ps1` | PASS; 8 modules. |
| `python -B -m unittest discover -s infra\scripts -p 'test_modern*.py' -v` | PASS; 26 tests, 10.197s; no skips. |
| `python -B -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests\test_durable_infra.py` | PASS; 5 tests, 7.84s; no skips. |
| `python -B -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests tests\telemetry-mapping tests\export\test_otlp_export_conformance.py` | PASS; 260 tests, 34.32s; no skips. Includes production pipeline tests; the standalone export conformance file is a reference transform, not live endpoint evidence. |
| `python -B infra\scripts\validate-modern-foundation.py --parameters infra\main.parameters.json` | EXPECTED REJECTION, exit 1: incomplete/unapproved profile. |
| `python -B infra\scripts\validate-modern-foundation.py --parameters infra\main.parameters.private-endpoint.json` | EXPECTED REJECTION, exit 1: incomplete/unapproved existing-network profile. |

Focused Prompt Agent check (offline only):

```powershell
Remove-Item Env:APPLICATIONINSIGHTS_CONNECTION_STRING -ErrorAction SilentlyContinue
$env:PYTHONPATH = "$PWD\src\prompt-agent;$PWD\.azure-sandbox\issue147-test-deps"
python -B -m pytest -q -p no:cacheprovider src\prompt-agent\tests\test_correlation_and_retry.py src\prompt-agent\tests\test_token_usage_validation.py
```

**PASS: 8 tests, 0.57s, exit 0.** An existing console-exporter shutdown warning
(`ValueError: I/O operation on closed file`) occurred after pytest capture closed;
recorded, not interpreted as a live exporter result. Initial selector including
nonexistent `test_config.py` returned exit 4/no tests. Corrected selectors initially
failed collection because `openinference` was missing, including a failed attempt
to reuse existing repo-contained export dependencies. Only then was test-only
`openinference-semantic-conventions==0.1.39` restored locally:

```powershell
New-Item -ItemType Directory -Force .azure-sandbox\issue147-scratch | Out-Null
$env:TEMP = "$PWD\.azure-sandbox\issue147-scratch"
$env:TMP = $env:TEMP
$env:PIP_USER = '0'
python -B -m pip install --quiet --no-cache-dir --no-deps --target .azure-sandbox\issue147-test-deps 'openinference-semantic-conventions==0.1.39'
```

Restoration passed; no manifest change or global install. An initial pip attempt
without `PIP_USER=0` failed (`--user`/`--target` conflict). Installed test dependency
is local-only, not a release dependency or tracked evidence.
Documentation checks also passed: `git diff --check`; all ten PowerShell fenced
examples parsed through the PowerShell AST parser with zero syntax errors; both
local links from this artifact resolved. Parsing is not execution. Checking the
installed CLI help rejected `az functionapp sync-function-triggers`; the later
handoff below instead uses the official documented `az rest` trigger-sync API.

## 5. Minimum provider and repeat-deployment handoff — NOT EXECUTED

**Stop before this section until plan approval, repo-contained official workflow
references and `azure-prepare` → `azure-validate` → `azure-deploy` evidence exist.**
Only Infra's approved workflow may execute the mutations below. A validation
request is not a substitute for a cloud mutation lease. Commands are deliberately
not wrapped into a new deploy script and never create/reuse an RG implicitly.

Use these process settings for **every** Azure CLI process, including later
private validator commands; never login/account-set, inspect auth caches or use
an unqualified subscription:

```powershell
$env:AZURE_CONFIG_DIR = 'C:\repos\foundry-otel-to-arize-demo\.azure-config'
$sub = 'c81fda52-936e-4f14-8af4-951c0dbb92d2'
$rg = 'REPLACE_WITH_APPROVED_NEW_RG'
$profile = '.\infra\issue147.approved.parameters.json'
if ($rg -like 'REPLACE*' -or -not (Test-Path $profile)) { throw 'Approval/profile missing.' }
python -B infra\scripts\validate-modern-foundation.py --parameters $profile
if ($LASTEXITCODE) { throw 'Offline profile gate failed.' }
$profileHash = (Get-FileHash $profile -Algorithm SHA256).Hash
az deployment group validate --subscription $sub --resource-group $rg --name qa147-provider --template-file .\infra\main.bicep --parameters "@$profile" --validation-level Provider --query '{state:properties.provisioningState}' --output json --only-show-errors
if ($LASTEXITCODE) { throw 'Provider validation failed.' }
az deployment group what-if --subscription $sub --resource-group $rg --name qa147-initial --template-file .\infra\main.bicep --parameters "@$profile" --result-format ResourceIdOnly --output json --only-show-errors
if ($LASTEXITCODE) { throw 'Initial what-if failed.' }
```

Record each exit code. Provider failure/deny/quota/name errors stop the step:
no grant repair, `/codes` diagnostics, public fallback or automatic reattempt.
Review all predicted creates and exact IDs against the approved fresh manifest;
any existing workload/shared-resource mutation is a failure. ResourceIdOnly is
not sufficient property review: Infra must additionally inspect a securely held,
allowlisted property diff without exposing parameter/secret material.

Within **azure-deploy**, after reviewed what-if and explicit approval:

```powershell
az deployment group create --subscription $sub --resource-group $rg --name qa147-first --mode Incremental --template-file .\infra\main.bicep --parameters "@$profile" --query '{state:properties.provisioningState,correlationId:properties.correlationId}' --output json --only-show-errors
if ($LASTEXITCODE) { throw 'Fresh deployment failed; do not repeat.' }
if ((Get-FileHash $profile -Algorithm SHA256).Hash -ne $profileHash) { throw 'Parameters changed.' }
az deployment group what-if --subscription $sub --resource-group $rg --name qa147-repeat-review --template-file .\infra\main.bicep --parameters "@$profile" --result-format ResourceIdOnly --output json --only-show-errors
if ($LASTEXITCODE) { throw 'Repeat what-if failed.' }
# STOP for review: no unexplained changes, replacement, grant churn or destination change.
# Only after the identical repeat is separately approved:
az deployment group create --subscription $sub --resource-group $rg --name qa147-repeat --mode Incremental --template-file .\infra\main.bicep --parameters "@$profile" --query '{state:properties.provisioningState,correlationId:properties.correlationId}' --output json --only-show-errors
if ($LASTEXITCODE) { throw 'Repeat deployment failed.' }
```

Hold source commit, compiled-template SHA256 (compile stdout in memory), profile
SHA256, immutable secure-reference versions, package hash and resource-ID manifest
constant. Record first/repeat deployment IDs, timestamps, statuses and identities.
No-changes what-if is not actual repeat deployment proof; two successful deploys
without identity/state comparison are not idempotence proof. Compare MI principal
IDs, model tuple, PE/DNS IDs, export destination/table union, consumer and disabled
flags before/after. Securely review property noise; do not accept all Modify
operations as harmless. No Complete mode, deletes, replay or checkpoint changes.

### Candidate model/quota READ-ONLY reproduction (already executed)

```powershell
az cognitiveservices model list --location eastus2 --subscription $sub --query "[?model.name=='gpt-5-mini' && model.version=='2025-08-07'].model.{format:format,name:name,version:version,lifecycleStatus:lifecycleStatus,skus:skus}" --output json --only-show-errors
$usage = az cognitiveservices usage list --location eastus2 --subscription $sub --query "[].{name:name.value,current:currentValue,limit:limit,unit:unit}" --output json --only-show-errors
if ($LASTEXITCODE) { throw 'Quota metadata unavailable; no grant change.' }
$usage | ConvertFrom-Json | Where-Object { $_.name -like '*gpt-5-mini*' }
```

Both succeeded; model metadata returned two matching catalog rows, not two
deployments. Initial projection looked for top-level `skus` and returned null;
corrected to `model.skus`. Initial usage `contains(...)` query hit Windows
`az.cmd` parsing (exit 255); the projection plus in-memory filter above succeeded.
No credentials, resource settings, raw prompts/responses or telemetry were read.

## 6. Private/package/tracing/runtime acceptance — NOT EXECUTED

From the **approved already-connected** validator, using only fresh names:

```powershell
$accountHost = 'REPLACE_APPROVED_SUBDOMAIN.services.ai.azure.com'
$vaultHost = 'REPLACE_APPROVED_VAULT.vault.azure.net'
$storage = 'REPLACE_APPROVED_STORAGE'
foreach ($hostName in @($accountHost,$vaultHost,"$storage.blob.core.windows.net","$storage.queue.core.windows.net","$storage.table.core.windows.net")) {
  Resolve-DnsName -Name $hostName -Type A
  Test-NetConnection -ComputerName $hostName -Port 443 -InformationLevel Detailed
}
# Each approved fresh PE ID comes from the allowlisted deployment outputs.
az network private-endpoint show --ids $approvedPeId --subscription $sub --query '{id:id,groups:privateLinkServiceConnections[].groupIds,status:privateLinkServiceConnections[].privateLinkServiceConnectionState.status}' --output json --only-show-errors
python -B infra\scripts\validate-modern-foundry-tracing.py --project-resource-id $approvedProjectId --connection-name $approvedConnection --app-insights-resource-id $approvedComponentId --expected-auth-type ApiKey --expected-sharing private
```

Require **all five** PE approvals; compare actual A records with the corresponding
fresh PE NIC metadata, not merely any RFC1918 address. Verify the three Foundry
DNS zones and KV/blob/queue/table zone groups/links. TCP443 success does not prove
project authorization, Function private access or agent outbound state/tool access.
Function host has a separate network vantage point: require content-free MI/KV
resolution, private host storage/EH/index readiness and package-hash/trigger-sync
receipts from Infra, not this Windows validator's DNS alone. No `/codes` probes.

Later approved publisher's minimum package operations (not run here):

```powershell
Get-FileHash $approvedPackagePath -Algorithm SHA256
az storage blob upload --subscription $sub --auth-mode login --account-name $storage --container-name function-packages --name $approvedImmutableBlobName --file $approvedPackagePath --overwrite false --query '{etag:etag}' --output json --only-show-errors
if ($LASTEXITCODE) { throw 'Package upload failed; no trigger sync.' }
az rest --method post --subscription $sub --url "https://management.azure.com/subscriptions/$sub/resourceGroups/$rg/providers/Microsoft.Web/sites/$approvedFunctionName/syncfunctiontriggers?api-version=2016-08-01" --only-show-errors
if ($LASTEXITCODE) { throw 'Trigger sync failed.' }
```

Use only a reviewed ready-to-run Linux package and authorized private upload path;
verify Function MI fetches that exact package. These commands do not build an
artifact, set durable gates, create tracing, grant roles or authorize cutover.
Connection creation must have its own approved narrow tracing profile/workflow;
do not rerun broad main to adopt a live association. A successful association
readback still needs capture evidence. Keep both triggers disabled until all
private/runtime/destination readiness gates have signed receipts.

## 7. Minimum bounded E2E evidence handoff — NOT EXECUTED

1. Agent supplies a **reviewed, pinned live runner command** for the approved
   agent/version/identity, the resolved **v1 Responses** API/three SDK pins above,
   and the §2 one-request envelope. **No repository
   live command exists today**: `python -m prompt_agent.main --scenarios` is
   explicitly excluded. Do not invent a runnable SDK command or claim this
   packet has cleared the private runtime gate.
2. Infra/Telemetry perform separately approved secure configuration/cutover for
   fresh-only source/destination identities; record a new UTC window, run ID,
   trace/span/parent/correlation IDs and SDK-reported numeric token usage.
3. After the single authorized request, query metadata only with exact fresh
   workspace/component and time bounds; never dump prompts or full rows:

```powershell
# Requires approved post-run values; no placeholders may be sent.
if ($traceId -notmatch '^[0-9a-f]{32}$') { throw 'Fresh trace ID required.' }
if ($traceId -eq '04f49dc16c02643b6a351a499cd4db5a') { throw 'Protected historical identity.' }
$kql = @"
union withsource=SourceTable AppDependencies, AppRequests
| where TimeGenerated between (datetime($startUtc) .. datetime($endUtc))
| where _ResourceId =~ '$approvedComponentId' and OperationId == '$traceId'
| project SourceTable, OperationId, Id, ParentId,
    correlation=tostring(Properties['correlation.id']),
    prompt=Properties['llm.token_count.prompt'],
    completion=Properties['llm.token_count.completion'],
    total=Properties['llm.token_count.total'],
    nativeInput=Properties['gen_ai.usage.input_tokens'],
    nativeOutput=Properties['gen_ai.usage.output_tokens']
"@
az monitor log-analytics query --subscription $sub --workspace $approvedWorkspaceUuid --analytics-query $kql --timespan "$startUtc/$endUtc" --output json --only-show-errors
$contentKql = @"
AppGenAIContent
| where TimeGenerated between (datetime($startUtc) .. datetime($endUtc))
| where _ResourceId =~ '$approvedComponentId' and OperationId == '$traceId'
| summarize rows=count() by OperationId, SpanId
"@
az monitor log-analytics query --subscription $sub --workspace $approvedWorkspaceUuid --analytics-query $contentKql --timespan "$startUtc/$endUtc" --output json --only-show-errors
```

Schema/table absence or query error is a **failed/missing evidence gate**, never
permission for a broad query fallback. Numeric fields may be absent; preserve
absence and do not synthesize totals. If actual source uses another documented
correlation key, record that mapping rather than silently changing it.

4. Telemetry captures content-free EH partition/sequence/checkpoint and Function
   admission/outbox/ACK counts for only the fresh scope; protect ledger evidence.
   QA independently verifies exact destination project/space/trace/span identity,
   parent/correlation and numeric tokens. HTTP200 or a local ACK alone is not
   independent Arize visibility.
5. Native I/O acceptance requires **independent source/destination SHA256
   receipts**, side presence/MIME, canonicalization/version and identity join.
   Custodians calculate hashes inside their approved boundary and release only
   metadata; QA does not retrieve raw native content. Plain KQL `tostring` hashes
   are not automatically comparable to Python JSON serialization. Telemetry must
   pin the same reviewed canonicalization and precedence rules (explicit
   OpenInference → inline GenAI → unique valid native content) at both ends.
   Record inline precedence, source-missing parents/resources, missing sides and
   conflicting content; do not invent parity for fields the source never emits.
6. Poll at most three times across the proposed 20-minute evidence window. The
   durable 300-second join deadline is **not** a delivery SLA. Stop on ambiguity,
   retain state, and reconcile; never resend/replay to improve a screenshot.

### Evidence checklist / sign-off record

Every receipt records UTC time, exact command/version, scope, exit/status,
content-free result, reviewer and limitations; store restricted operational
metadata under the issue's own local receipts and link only approved summaries.

| Gate | Required persistent evidence | Current result / next owner |
|---|---|---|
| Offline | §4 exact commands/results, baseline commit, tool versions | PASS as bounded above — QA |
| Decisions | Completed §2 choices, conditional cost technical gates/contract addends and custody identities | Technical discovery first; complete spending/lifetime/custody decision afterward — Infra/Agent/coordinator/resource owner |
| Official workflow | Public refs reconciled/pinned; approved plan → official validate → separately authorized deploy receipts | References RECONCILED; execution BLOCKED at unapproved planning prerequisites/helper compatibility — Infra |
| Provider | Scoped validation + reviewed what-if, policy/quota/unique names | NOT RUN — Infra |
| Fresh + repeat | Two deployment receipts; identical source/profile/secure versions; IDs/MI/state comparison | NOT RUN — Infra |
| Private/package | Five PEs/seven zones, two network vantages, MI/KV/package hash/trigger sync | NOT RUN — Infra |
| Agent/runtime/tracing | v1 Responses/SDK contract resolved in Agent assessment; approved immutable live runner, fresh version/state/tool proof, association readback + actual capture | Contract RESOLVED; fresh private/runtime acceptance BLOCKED / NOT RUN — Agent + Infra |
| Bridge/durable | Explicit consumer, three-table export, exact allowed source/destination, fresh-only cutover, ledger/ACK/quarantine evidence | NOT RUN — Telemetry |
| E2E independent | Single fresh invocation receipt, source/export/destination identity/parent/correlation/tokens, comparable I/O hash receipts | NOT RUN — Telemetry + QA |
| Closeout | Exceptions named, cost/lifecycle decision, reusable instructions updated | PENDING — QA; **#147 remains open** |

Followup gate clarification: official public references are **RECONCILED**, not
blocked on external profile access. Official prepare/validate **execution still
stops at unapproved planning prerequisites**. The [workflow ledger](issue147-workflow-gates.md)
lists full inventory/quota/policy, build/static-role/proof and explicit-subscription
helper compatibility gates; prior retirement completion is not fresh acceptance.
Cost math/provenance/link regression checks passed via
`python -B -m unittest discover -s tests\readiness -p 'test_issue147_planning.py' -v`
(4 tests). Initial test incorrectly assumed meter IDs uniquely identify operation
display names; corrected to full identity after public evidence showed write/list
aliases. No price or usage was silently removed to make the test pass.
`.\tests\readiness\check-issue147-docs.ps1` also passed: 11 documentation
PowerShell examples and two pinned official scripts parse; none executed.

Same-issue Agent integration reran both readiness commands: **4 tests PASS**,
including all four packet documents' local links and both Agent Python examples
(AST only); **14 PowerShell examples + 2 pinned official scripts parse**, none
executed. `git diff --check` passed after staging the new Agent document.
No new provider discovery, model invocation or official workflow step was run.

## 8. Official public references fetched directly in this slice

Read 2026-10-19; public contracts are not tenant/provider/runtime certification:

- [ARM model deployment 2025-09-01](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/deployments):
  explicit version/sku capacity/upgrade values; source pin retained.
- [Model catalog](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure)
  and [regional availability](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability):
  gpt-5-mini 2025-08-07; model/SKU/region availability must be rechecked.
- [Deployment types](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/deployment-types):
  Global vs US data-zone vs geography processing and pay-per-token vs PTU.
- [Quota](https://learn.microsoft.com/azure/foundry/openai/how-to/quota):
  subscription/region/model/SKU scope; model-specific capacity/RPM/TPM;
  quota read permission is not a reason to add grants here.
- [Agent limits/regions](https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions)
  and [network isolation](https://learn.microsoft.com/azure/foundry/how-to/configure-private-link):
  East US 2 private support, same-region account/VNet, distinct inbound/outbound/
  injection and standard BYO prerequisites.
- [Premium plan](https://learn.microsoft.com/azure/azure-functions/functions-premium-plan),
  [Functions pricing](https://azure.microsoft.com/pricing/details/functions/),
  [Private Link pricing](https://azure.microsoft.com/pricing/details/private-link/),
  [DNS pricing](https://azure.microsoft.com/pricing/details/dns/):
  at least one billed EP1, sizing, PE hour/data-transfer and DNS zone/query billing.
- [Package + MI](https://learn.microsoft.com/azure/azure-functions/deployment-zip-push#fetch-a-package-from-azure-blob-storage-by-using-a-managed-identity):
  private Blob URL/system MI, external package trigger sync and retained artifacts.
- [Trigger syncing](https://learn.microsoft.com/azure/azure-functions/functions-deployment-technologies#trigger-syncing):
  explicit `syncfunctiontriggers` POST for external package URLs; no SCM/basic-auth
  or undocumented CLI subcommand substitution.

No retirement operation is part of this packet. Preserve all existing resources,
governance/antimalware, ledger/index/checkpoints/ACKs/quarantine and sender
`27c683e5-b400-4b1e-9234-89e40fde2198`. Never resend protected trace
`04f49dc16c02643b6a351a499cd4db5a` / span `b4cd6555d6c3ea92` (delivery unknown).
The four deleted classic workspaces are not candidates for another DELETE.
