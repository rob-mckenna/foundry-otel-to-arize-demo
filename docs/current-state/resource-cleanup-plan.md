# Resource cleanup plan: retire classic Foundry without breaking the demo

> **Historical inventory baseline; subsequent execution status is recorded below.**
> This inventory is not a teardown allowlist or blanket deletion authority.
> The original inventory assignment made no cloud changes. Later approvals and
> observed retirement results do not rewrite its as-of evidence or unknowns.

## Current execution status — issue #145

Requester approved the cleanup direction, including repository modernization.
The modern-only private infrastructure source is implemented in `3358374` and
independently Lead-approved with external execution gates. Offline compilation,
naming and 31 focused infrastructure/tracing checks passed. The classic
`foundry-project.bicep` and broad `teardown-deployment.ps1` are removed from
supported source; historical references below describe the inventory baseline.

PR #146 is merged as `46e5ebb`; source issue #145 is closed. Fresh deployment,
provider/private-runtime/idempotence and end-to-end portability validation remain
unperformed under #147. The separate scoped administrative validation below is
not validation of the fresh infrastructure deployment path.

## Live retirement status - issue #148

On 2026-10-19, the requester separately approved the four exact classic workspace
IDs, project-before-hub ordering, owner/governance/consumer clearance and accepted
contained configuration, asset and managed-identity loss. This owner attestation
does not establish that unsupported asset inventory APIs proved empty.

**All four approved classic workspaces are retired.** Each received exactly one
DELETE, projects before hubs; native DELETE/wait commands returned exit 0.
Independent exact-ID checks confirmed HTTP **404 / ResourceNotFound**:

| Workspace | Verified absent, 2026-10-19 UTC |
| --- | --- |
| `fotoa-demo-aiproj-eastus2` | 18:41:58 |
| `fotoa-demo-aihub-eastus2` | 20:12:26 |
| `fotoa-dev-aiproj-eastus2` | 20:31:08 |
| `fotoa-dev-aihub-eastus2` | 20:35:31 |

Execution paused when service-associated effects exceeded the initial protection
conditions. The requester separately accepted automatic removal of four
workspace-contained assignments, the two exact hub-identity RG assignments and
eight hub-GUID A-records in `privatelink.api.azureml.ms`. No explicit IAM/DNS
mutation was issued; service causality is inferred from timing/identity matches,
not independently established by activity logs. Approval and pause history is
retained in #148 and the local execution receipts.

The final aggregate comparison at **20:44:00 UTC** found only the four approved
primary removals and exact accepted automatic effects: **83 -> 79 primary
resources, 25 -> 17 DNS record sets, 91 -> 85 role assignments**. All **79
non-target primary resource IDs/projected metadata**, **48 network IDs**, **8 DNS
zones**, remaining DNS/assignment metadata, modern-project, Event-Hub-consumer
and host/state-container projections were preserved. Both legacy project
Key Vault grants and the existing telemetry sender grant remain; the validation
VM remains deallocated.

These non-atomic management-plane observations do not certify runtime/model
health or inspect stored ledger/checkpoint contents. No agent/model invocation,
replay, force/purge, explicit IAM/DNS cleanup or fresh deployment occurred.
#148 remains open for separately cleared retained classic private endpoints,
provider-owned NICs and other exclusive dependencies; those were not authorized
by the four-workspace approval. Fresh deployment validation remains open in #147.

Metadata-only local execution receipts are
`.azure-sandbox\issue148-exact-workspace-retirement.json` and
`.azure-sandbox\issue148-preservation-comparison.json`, followed by
`.azure-sandbox\issue148-exact-workspace-retirement-continuation.json` and
`.azure-sandbox\issue148-exact-workspace-retirement-aggregate-preservation.json`.
Final completion and aggregate preservation are recorded in
`.azure-sandbox\issue148-exact-workspace-retirement-final.json` and
`.azure-sandbox\issue148-exact-workspace-retirement-final-aggregate-preservation.json`.
Approval and execution outcomes are also tracked in #148. The original
83-resource inventory below is retained as historical evidence, not presented
as the current resource count.

## Accepted direction addendum — issue #145

**2026-10-19T12:38:00.312-04:00 — Lead; requester/approver Rob McKenna.**
[ADR-0004](../adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md)
records the now-accepted **modern-only repository direction** and exact Infra
file/symbol contract. Source implementation is now recorded above; live
verification remains pending.
This supersedes the planning-only architecture status above **only for that
direction**, not the inventory's as-of evidence, unknowns or deletion gates.
The 83 primary rows R01–R83 and their evidence scope are unchanged.

- `infra/main.bicep` becomes the supported modern fresh account/project/model/
  private-network/telemetry composition. Do **not** retain a legacy option or
  executable archived deployment path. Earlier alternatives in the source-work
  table and phase 3 below are superseded on this point. Git history remains.
- Infra is the sole `infra/**` edit owner: new modern foundation/model modules,
  private KV/storage/Function/DNS wiring, removal of classic diagnostic and
  principal coupling, portable profiles/outputs and guarded validation. Agent
  owns caller/config adaptation; Telemetry preserves runtime/correlation behavior;
  QA verifies. See the ADR for exact interfaces and completion gates.
- Fresh deployment, narrow existing-resource adoption and live destructive
  retirement are separate operations/approvals. Connection-only #139 IaC stays
  connection-only. Modern model availability/quota/cost, private runtime/state
  prerequisites and secure-material custody remain execution gates.
- **Release handoff reconciled:** coordinator records #143 hold released,
  merged #144 (`c055795`) and QA acceptance. Released durable-runbook receipts
  record controlled fallback verification and validation VM deallocation at
  `2026-10-19T15:23:04Z`; no grant was created/removed for that fixture and the
  pre-existing sender remained. This replaces the earlier pending-release
  assumption, not the historical inventory observation. Lead made no live query.
- Preserve active pipeline/private access/protected KV/storage/networking,
  ledger/checkpoints/ACKs/quarantine and #138 assets/#139 fixtures/dev stack.
  Operational ambiguous trace `04f49dc16c02643b6a351a499cd4db5a`, span
  `b4cd6555d6c3ea92`, remains delivery-unknown and **must not be resent**.
  Four classic workspaces remain conditional candidates, not unused-certified.
  Consumer, governance, recovery and exact-ID approvals still precede retirement.

No deployment, model call, new grant, replay, teardown, broad IAM cleanup, Complete
RG operation or purge is approved or performed by this addendum.

## Scope, timestamp and recommendation

- Requester: Rob McKenna. Prepared directly by Infra; independent of active #143
  acceptance/release work. Keep this document out of #144.
- Assignment timestamp: **2026-10-19T10:36:45.115-04:00**.
  Live inventory collected approximately **14:37–14:54 UTC on 2026-10-19**.
  This is a sequence of observations, not an atomic snapshot.
- **15:07 UTC verification:** all 83 primary inventory IDs still matched a fresh
  RG-scoped resource list exactly; the protected ledger assignment's canonical
  ID/principal/scope also matched. This did **not** recheck VM power, transient
  fixture grants, runtime settings, agent invocation or release acceptance.
- Subsequent requester context, **2026-10-19 after that inventory; exact update
  time not supplied**: #143 received separate explicit approval for a controlled
  synthetic fixture after two native probes kept content inline. The release
  agent may, only if needed, temporarily assign validation VM MI
  `64c0b8ce-7e6c-4875-a2cb-82552efc0376` **Azure Event Hubs Data Sender only on**
  `fotoa-demo-ehns-eastus2/eventhubs/telemetry`, send two small fixture events,
  remove that temporary grant and deallocate the VM. This is **reported approval,
  not observed completion**. No fixture bodies were read for this plan. Any
  resulting grant/power-state transition is release-owned, not a permanent
  dependency, unused-resource finding or legacy-cleanup authorization. Do not
  remove a transient release grant or change VM power under this plan.
- Only subscription `c81fda52-936e-4f14-8af4-951c0dbb92d2`, resource group
  `fotoa-demo-rg` was inventoried. No subscription-wide resource discovery was done.
- Workspace/repository boundary: `C:\repos\foundry-otel-to-arize-demo`.
  Only this document is an authored deliverable. No branch, staging, commit,
  issue/PR, product/IaC/configuration, shared deployment plan or #143 evidence change.
- All native Azure read processes set
  `AZURE_CONFIG_DIR=C:\repos\foundry-otel-to-arize-demo\.azure-config` and an explicit
  subscription. Existing authentication only; no login, context change, token
  retrieval, secret/key retrieval, appsettings dump or authentication change.

**Recommended direction:** retain the working account/project-based Foundry and the
entire current observability/private-validation path. Prepare to retire **four
classic ML workspaces**, then their **hub-exclusive private endpoints/NICs/DNS
records**, after consumer, policy and recreation gates below. Do **not** conflate
that with deleting shared storage, Key Vault, the demo VNet, or the whole dev
environment. Separately review the retained #139 test project and the continuing
need for #138 operational resources.

### Decision map

| Set | Proposal | Why this is not deletion approval |
|---|---|---|
| Current demo Foundry account, operational project, agent/model, tracing association | **KEEP** | Current intended workload; newer resource type alone is not the evidence—the live project, deployment and connection edges are. |
| Demo AppInsights → LAW → Event Hub → Function → Arize, including durable ledger/host state | **KEEP** | Live enabled export, Function identity/storage grants and recent Event Hub traffic; #143 acceptance still active. |
| Demo/dev classic hub/project pairs | **REMOVE-CANDIDATE** | Empty inspected connection/compute/endpoint collections; still have identities, RBAC, diagnostics, IaC references and unverified asset/consumer use. |
| Hub-only PEs/NICs and `privatelink.api.azureml.ms` artifacts | **REMOVE-CANDIDATE**, after workspace retirement | Exact hub edges observed; DNS zone serves both environments. Remove neither zone nor unrelated shared network early. |
| Complete dev telemetry stack | **UNKNOWN**, retain pending owner decision | Dev Function is Running and has real storage/EH/KV grants. Zero observed EH messages in one window is not proof of abandonment. |
| #139 isolated test project | **REMOVE-CANDIDATE**, separately approved | Runbook explicitly retained it with `temporaryCleanup=false`; it uses the production AppInsights component and has policy diagnostics. |
| Evaluation storage, Windows browser jumpbox/NAT, Linux validation VM/Bastion | **KEEP now** | #138 authorized retained resources; Linux VM was observed Running for #143 acceptance. Subsequent release-owned deallocation is separately approved, not cleanup. Later operational consolidation is a new decision. |
| Legacy-first deployment source | **MIGRATE-FIRST** | `main.bicep` still declares classic resources; shipped modern tracing template does not recreate account/project/model/network foundation. |

`KEEP` means preserve within this cleanup, not proof that every setting or role is
ideal. `REMOVE-CANDIDATE` means eligible for investigation and exact approval only.
`MIGRATE-FIRST` means a dependency/reproducibility change must precede retirement.
`UNKNOWN` means no removal recommendation can yet be defended.

## Evidence and limits

### Evidence register

| Code | Observed or documented evidence |
|---|---|
| E1 | `az resource list` scoped to the approved RG returned **83 rows**. Most application/network parents carry `project=foundry-otel-to-arize-demo`, `owner=infra-team`, environment and synthetic-data tags. Tags are ownership clues, not sole authorization. Test-project owner tag is `Infra`. |
| E2 | ARM `2024-10-01` GET/list for all four ML workspaces: kinds Hub/Project; each project references its matching hub; public network access Disabled. `storageAccount`, `keyVault`, `applicationInsights`, `containerRegistry` and managed-network isolation fields were null in these projected responses. Each workspace's **connections, computes, onlineEndpoints and batchEndpoints** returned empty lists with no nextLink. |
| E3 | Modern account `AIServices`, S0, project management allowed, system MI, public network access Disabled, local auth disabled, ACL Deny/bypass None. Operational project and #139 test project both Succeeded with distinct system MIs. One model deployment observed: `fotoa-demo-gpt5mini-eastus2`, `gpt-5-mini` version `2025-08-07`, GlobalStandard capacity 5. |
| E4 | Operational project lists AAD storage connection `fotoa-demo-eval-storage` and ApiKey AppInsights connection `fotoa-demo-appi-eastus2-2199`, both private sharing. Test project lists `fotoa-demo-appi-139test-eastus2` to the same demo AppInsights. No project capability hosts returned for either project. This is not proof that no service-managed state exists. |
| E5 | Demo AppInsights references demo LAW. Enabled LAW rule `fotoa-demo-e2e-app-spans` exports **AppDependencies, AppRequests, AppGenAIContent** to demo EH namespace, explicit hub `telemetry`. Demo Function Running, integrated with demo VNet `function-integration`, on demo EP1 plan. Dev Function also Running, on dev Y1 plan, no VNet integration reported. Dev AppInsights references dev LAW; dev LAW export list empty. |
| E6 | PE target/subnet/NIC metadata maps demo hub, Foundry, KV and Function/evaluation storage to demo VNet; dev hub/KV to dev VNet. All nine inspected PEs Approved. Demo VNet also carries validation-jumpbox and windows-jumpbox subnets. DNS links are enumerated below. |
| E7 | RG-scoped ARM role-assignment endpoint returned 91 entries including inherited ancestors, no nextLink. Relevant local edges: classic project→matching KV; hub MIs→RG/workspace; demo/dev Function→matching EH/KV/storage; validation VM→demo EH/KV/Foundry project/AppInsights; operational Foundry project→account and evaluation storage. Ancestor assignments returned by that endpoint are **not** repository-owned cleanup targets; no ancestor/other-RG enumeration followed. |
| E8 | ARM container-name metadata: demo Function storage has `azure-webjobs-eventhub`, `azure-webjobs-hosts`, `azure-webjobs-secrets`, **genai-correlation**. Dev and evaluation storage container lists empty at observation. No blob contents, secret contents, prompts or responses accessed. Demo ledger custom-role assignment `c62dca6e-56bf-5821-b41d-9130ede91092` belongs to the Function MI and is preserved. |
| E9 | VM metadata: Linux validation VM **Running**, system MI; Windows jumpbox **deallocated**, no MI reported. Attached disks/NICs remain. Windows subnet references NAT and its NSG; NAT public IP is egress infrastructure, not evidence of public RDP. |
| E10 | Both vaults: private access, RBAC, soft-delete enabled, purge protection enabled, 90-day retention. All three storage accounts: PNA Disabled, shared keys false, blob public access false. Demo/evaluation Blob service delete-retention enabled=false, container retention and versioning unspecified/null: no verified blob recovery safety net. |
| E11 | EH metric totals for **2026-10-12T00:00Z–2026-10-19T14:00Z**, daily buckets: demo IncomingMessages **10,253**, OutgoingMessages **10,265**; dev both **0**, eight returned buckets per metric. Outgoing can include rereads; these are not distinct traces, complete delivery proof or a retirement criterion. |
| E12 | Classic resource-specific activity queries **2026-09-19T00:00Z–2026-10-19T14:45Z**, cap 100 each: demo hub 76, demo project 40, dev hub 28, dev project 10 returned events. Latest returned events were policy/diagnostic operations, not runtime-use evidence. Initial RG activity query capped at 500 and was incomplete; it is not used to establish inactivity. |
| E13 | Both classic hubs, modern account and both modern projects expose `setByPolicy-MCAPSGovernance` diagnostic destinations in **another RG**. Classic projects expose `fotoa-demo-diag-to-law` / `fotoa-dev-diag-to-law` to their corresponding LAW. Destination existence/configuration is metadata, not proof of actual log delivery. |
| E14 | All three storage Event Grid system topics have an event subscription named **StorageAntimalwareSubscription**, destination type WebHook. Endpoint URLs were deliberately not retrieved. They are not established as disposable demo artifacts. |
| E15 | `infra/main.bicep`, classic Foundry/KV/network modules, modern tracing entrypoint/module, durable rollout entrypoint, Infra charter/history and relevant decisions read. Historical decisions describe baseline construction and broad teardown, not current selective cleanup authorization. `docs/current-state/foundry-appinsights-tracing.md` documents #139 retained clean-create test resources and missing modern foundation IaC. |
| E16 | GitHub #138 OPEN is evaluation storage/private Windows access, including user direction to retain resources after validation; **not** a classic-cleanup issue. #139 CLOSED documents tracing adoption/clean-create. Title search found closed #23, broad demo teardown; no matching open cleanup-title issue was found. This is a bounded search, not a claim that no related issue can exist. |
| E17 | Requester-provided preservation constraints: operational agent `fotoa-demo-agent-eastus2` version 1; #143 source `f650fed` deployed, 35 imported ACKs, durable incoming enabled; no new temporary grants; Linux VM needed for acceptance. These were treated as hold requirements, not independently revalidated or edited in this assignment. |

E17 records the **initial** preservation context. The subsequent separately
approved two-event fixture is the narrow exception to its initial no-new-temporary-
grants constraint; it does not expand this assignment. E7/E9 and all role/power
descriptions below are **as observed during the inventory window**, not assertions
about current release-agent activity. Before any later change, obtain a fresh
release-owned state/temporary-grant receipt rather than acting on this snapshot.

### Unknowns deliberately retained

- ARM emptiness for four collections is **not** a complete classic asset audit.
  Jobs, experiments, model/data/environment assets, registries, schedules,
  serverless assets, prompt flows, historical agent/thread/file state, SDK
  endpoints in external callers and service-managed dependencies remain unverified.
  Do not list their data bodies to compensate; obtain allowlisted metadata and
  owner attestations through an approved private path.
- No agent/data-plane GET or invocation was made. Operational agent→model consumer
  mapping is the requester/runbook preservation context plus the observed deployment,
  not a newly verified agent-definition read. Check only name/version/model/tool
  **metadata**, never instructions or synthetic prompt/response bodies, before change.
- Account-level connection listing also returned three **account-path IDs** with the
  same names/targets as project connections; `createdByWorkspaceArmId` was null.
  Whether these are provider projections or independently consumed connections is
  unresolved. Do not deduplicate/delete them merely because their names repeat.
- Log Analytics aggregate query was attempted but native `az monitor
  log-analytics query` was unavailable. No extension was installed and no token,
  alternate config or data-plane workaround used. Per-table recency, Function
  invocation recency, classic data-plane use and billing are therefore incomplete.
- RG locks list was empty. That is neither permission to delete nor proof that
  parent policy, deny assignments or inherited protections are absent.
- No cost-management data, vault secret inventory/values, raw appsettings,
  deployment parameter values, `.env*`, local settings or auth caches were read.
  Secret consumers cannot be exhaustively certified from this review.
- Activated resource-lookup/Foundry skill guidance; local reference access stayed
  within `.azure-sandbox/official-azure-skills-20261016`. That pin contains only
  the Foundry dependency-checker script, not the required reference tree or
  resource-lookup references. Checker inspection showed it can install an azd
  extension, so it was **not executed** under this read-only/no-install assignment.
  No deployment/agent skill workflow was entered. Official public documentation
  was fetched remotely instead; no other host skill directory was inspected.

### Outside-group dependency boundary

Observed diagnostic target, **not inspected**:

`/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/McapsGovernance/providers/Microsoft.OperationalInsights/workspaces/mcaps4f148af4951c0dbb92d2-la`

Recommendation **UNKNOWN / preserve**. The destination and policy are governance
dependencies, not proven repo-owned resources. Governance-owner approval is needed
before retiring monitored source resources or handling their diagnostics. No
cross-RG query, policy change or request for new access is authorized here.
External consumers and inherited identity grants require the same explicit scope
approval if verification would extend beyond this RG.

## Dependency map: old and new are not the same resource

```text
Classic demo project (ML workspace) --> classic demo hub (ML workspace)
    project MI --> demo KV Secrets User; project diagnostic --> demo LAW
    hub MI --> workspace/RG roles; hub PE --> demo VNet + legacy AzureML DNS
Classic dev project/hub --> analogous dev KV, dev LAW, dev VNet/PE/DNS
    (no storage/KV/AppInsights parent association observed in workspace properties)

Modern AIServices account --> operational CognitiveServices project --> Prompt Agent v1
    shared account model deployment: fotoa-demo-gpt5mini-eastus2
    project connection --> demo AppInsights --> demo LAW
        --> enabled native data export --> demo EH/telemetry
        --> demo Function + EP1 plan --> Arize
    Function MI --> demo KV + EH receiver + private/keyless Function storage
        --> host/checkpoint state AND genai-correlation ledger/index role
    operational project MI --> dedicated evaluation storage (AAD connection)
    Foundry/KV/storage PEs --> shared demo VNet, NSGs and private DNS
    Linux validation VM MI + network --> private acceptance/validation dependencies
    Windows browser jumpbox --> own subnet/NSG/NAT/PIP + existing Developer Bastion

Modern #139 test project --> separate AppInsights connection --> SAME demo AppInsights
Policy diagnostics --> outside-RG governance LAW (approval-needed boundary)
Storage system topics --> antimalware webhook subscriptions (security-owner dependency)
```

Null classic dependency fields do not mean the matching KV/storage/LAW is unused:
the current Function has independent grants and use. No in-place conversion from a
`Microsoft.MachineLearningServices/workspaces` project to a
`Microsoft.CognitiveServices/accounts/projects` project is proposed. Any surviving
classic asset/consumer must be explicitly migrated or retained first.

### Identity edges that must survive or be retired deliberately

| Resource / system MI object ID | Disposition / exact prerequisite |
|---|---|
| Demo classic hub `e7f2cd39-0bde-4ea1-a8bc-72225aec1fed` | Candidate only with its workspace; observed RG assignment `104f491f-11d5-4923-b99f-fd1eb9440d54` and workspace assignment `20c52c32-eeec-4f16-b0c3-9bd7f5f286de` need scoped residual-grant review. |
| Demo classic project `c2bd8fe0-3cd9-4548-b0bf-5f17e8f50ee6` | Candidate only after consumer clearance; workspace assignment `ca38726e-c4b8-492d-a519-70f7dfda2b71`, KV Secrets User assignment `9881514f-8952-53b2-94cd-63fbb7ae35cb`. Never delete the KV to remove this grant. |
| Dev classic hub `78945674-70f4-4b7a-924a-81888f6ef34c` | Candidate only with workspace; RG assignment `2758236d-bcda-4761-80be-e297f9bf7bbd`, workspace assignment `3ad17f99-cada-4640-a931-f822a3779bd3`. |
| Dev classic project `031d58a3-0421-4ff1-abaf-1fe76d7c1491` | Candidate only with workspace; workspace assignment `28f70140-8aa4-4a26-8e08-f1f0eac81898`, KV assignment `b72f6eae-6ac5-5d4b-bd65-7798c41d3b1e`. |
| Modern account `0964d49e-0dcb-4119-85a9-0b683d6ea45d` | **KEEP**, identity and model/project ownership preserved. |
| Operational project `650c8a38-543b-4a9b-b497-4d4f2f19c4d2` | **KEEP**, account access and evaluation-storage Blob Contributor observed. |
| Test project `8d8778e9-a60e-4fea-a5e9-5fcb936f736f` | Candidate only after #139 owner release; no direct matching local grant established by this snapshot. Absence is not an external/inherited grant audit. |
| Demo Function `34e9edde-18e4-4cca-b109-7364de41fa76` | **KEEP all current runtime grants**, including EH, KV, Blob/Queue/Table and container-local ledger index role. |
| Dev Function `84fc99cb-f96f-4715-81ab-7a40e17cdd89` | **UNKNOWN / preserve**; actual KV/EH/storage grants prevent treating the whole dev stack as a hub dependency. |
| Linux validation VM `64c0b8ce-7e6c-4875-a2cb-82552efc0376` | **KEEP**; current project/AppInsights/EH/KV validation access remains under #143 owner control. No new temporary grants or role cleanup here. |

Assignment GUIDs identify observed assignments, not deletion commands; ARM-returned
assignment IDs can be extensions at differing scopes. Re-read exact assignment
ID, principal, role and scope before any separately approved removal. Deleting and
recreating a system-assigned identity changes its object ID; same resource name
does not restore these edges.

## Per-resource inventory and disposition

### Reading the inventory

Every ID below is exact **relative to**:

`RG = /subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg`

For each row, the full resource ID is **`RG/providers/` + the ID suffix**.
The suffix explicitly gives provider/type/name, including nested parent/child
segments; it is not a wildcard or a name-based deletion selector. ARM casing is
case-insensitive. Primary rows R01–R83 cover the 83 RG resource-list results.
Separately observed child/extension resources follow the primary inventory.

Owner-evidence codes: **T** = repo/infra-team tags (E1), **I** = live identity/
parent/target edge and/or matching IaC (E2–E8/E15), **V** = requester validation
hold (E17), **H** = explicit retained #138/#139 history (E15–E16), **S** = security/
policy linkage, ownership not independently attested (E13–E14), **U** = owner not
established from tags; name or attachment alone does not prove ownership.

Prerequisites used in rows:

- **P0**: preserve; any change is outside legacy cleanup and requires its own
  approved scope. Current pipeline/validation holds take priority.
- **P1**: Lead/Agent/QA attest no remaining classic consumers/assets; metadata-only
  private-path inventory, source migration/recreation gate, governance approval,
  preservation plan and exact-ID approval complete. Projects before their hub.
- **P2**: P1 complete for the target hub; confirm PE DNS-zone-group/record ownership,
  no other endpoint clients, and approved dependency order. NIC is PE-managed:
  never independently delete a PE's attached NIC.
- **P3**: both classic hubs retired; validate all DNS links/records and external
  clients. Shared legacy zone removed only when no required consumer remains.
- **P4**: dev owner explicitly retires the independent dev environment after a
  representative agreed observation window, retention/secret/network review and
  cross-environment dependency check. No automatic promotion from UNKNOWN.
- **P5**: #139 owner releases intentionally retained test project; check agent/
  evaluation assets and account-level connection semantics, preserve shared
  component, address policy diagnostics, approve exact child/parent IDs.
- **P6**: security/governance owner confirms ownership and lifecycle. Do not remove
  antimalware/policy resources as apparent clutter.
- **P7**: #138 owner and acceptance/release coordinator approve operational
  consolidation after #143 ends; verify human/VM identity, DNS, egress, disk and
  recovery requirements. Deallocation or deletion remains a separate approval.

#### A. Current demo telemetry and shared dependencies

| Row | Resource ID suffix (explicit type/name) | Purpose / owner evidence | Current dependencies | Recommendation | Risk / exact prerequisite |
|---|---|---|---|---|---|
| R01 | `Microsoft.EventHub/namespaces/fotoa-demo-ehns-eastus2` | Telemetry transport; T/I | LAW export, telemetry hub, Function/VM grants; recent traffic | **KEEP** | Critical delivery loss; P0. |
| R04 | `Microsoft.KeyVault/vaults/fotoa-demo-kv-eastus2` | Shared secret custody; T/I/H | Function, classic project and validation identities; tracing/jumpbox history | **KEEP** | Credential/bootstrap/redeployment loss; P0. Remove only obsolete classic grant later. |
| R05 | `Microsoft.OperationalInsights/workspaces/fotoa-demo-law-eastus2` | Current telemetry store; T/I | AppInsights, classic project diagnostics, enabled export | **KEEP** | Retained logs/export loss; P0. Workspace GUID `4658bdb1-b9ca-4f57-a733-6b81f316dc45`. |
| R06 | `Microsoft.Storage/storageAccounts/fotoademosteastus2` | Private/keyless Function host and durable state; T/I/V | Blob/Queue/Table grants and PEs, four named containers, antimalware topic | **KEEP** | Critical checkpoints/ledger/host loss; P0. Not classic-only storage. |
| R07 | `Microsoft.Web/serverFarms/fotoa-demo-plan-eastus2` | EP1 Function hosting; T/I | Demo Function, one site observed | **KEEP** | Outage; P0. Rightsizing is a separate decision. |
| R08 | `Microsoft.Web/sites/fotoa-demo-func-eastus2` | Active Arize transform/export; T/I/V | EP1, VNet, EH, KV, storage, current deployed source | **KEEP** | Critical outage/identity change; P0. |
| R09 | `Microsoft.Insights/components/fotoa-demo-appi-eastus2` | Current trace ingestion; T/I/H | Operational AND test connections, demo LAW | **KEEP** | Breaks both tracing paths; P0. |
| R10 | `microsoft.alertsmanagement/smartDetectorAlertRules/Failure Anomalies - fotoa-demo-appi-eastus2` | AppInsights anomaly alert; U/I | Component-associated name; detailed alert action ownership unverified | **KEEP** | Monitoring regression; P0/P6 before any separate removal. |
| R11 | `Microsoft.EventGrid/systemTopics/fotoademosteastus2-0dc58804-6931-47f3-8d65-518d1cfae662` | Storage event source; U/I/S | Demo storage + StorageAntimalwareSubscription | **KEEP** | Security-control regression; P6, not legacy cleanup. |
| R13 | `Microsoft.Network/privateDnsZones/privatelink.table.core.windows.net` | Function Table private resolution; T/I | Demo VNet link/PE | **KEEP** | Private host access; P0. |
| R14 | `Microsoft.Network/privateDnsZones/privatelink.queue.core.windows.net` | Function Queue private resolution; T/I | Demo VNet link/PE | **KEEP** | Private host access; P0. |
| R15 | `Microsoft.Network/privateDnsZones/privatelink.vaultcore.azure.net` | Shared KV private resolution; T/I | BOTH demo and dev VNet links | **KEEP** | Both vaults affected; P0, never remove zone with classic hub. |
| R16 | `Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net` | Function/evaluation Blob private resolution; T/I | Demo VNet, two Blob PEs | **KEEP** | Host/ledger/evaluation access; P0. |
| R17 | `Microsoft.Network/virtualNetworks/fotoa-demo-vnet-eastus2` | Shared private network; T/I/V/H | Function, hub/Foundry/storage/KV PEs, both jumpboxes | **KEEP** | Broad outage; P0. Hub retirement does not release VNet. |
| R18 | `Microsoft.Network/privateEndpoints/fotoa-demo-pe-kv-eastus2` | Demo vault access; T/I | Demo VNet and KV | **KEEP** | Function/private credential resolution; P0. |
| R19 | `Microsoft.Network/privateEndpoints/fotoa-demo-pe-funcsttable-eastus2` | Table access; T/I | Demo Function storage | **KEEP** | Host-state access; P0. |
| R20 | `Microsoft.Network/privateEndpoints/fotoa-demo-pe-funcstqueue-eastus2` | Queue access; T/I | Demo Function storage | **KEEP** | Host-state access; P0. |
| R21 | `Microsoft.Network/privateEndpoints/fotoa-demo-pe-funcstblob-eastus2` | Blob access; T/I | Function checkpoints/ledger | **KEEP** | Critical state access; P0. |
| R22 | `Microsoft.Network/networkInterfaces/fotoa-demo-pe-kv-eastus2.nic.557b977f-5345-4051-b911-45bbf886f1a5` | PE-managed NIC; T/I | R18 | **KEEP** | Preserve with PE; P0. |
| R23 | `Microsoft.Network/networkInterfaces/fotoa-demo-pe-funcsttable-eastus2.nic.9e843afe-47c5-48cb-bf7b-c7537888f667` | PE-managed NIC; T/I | R19 | **KEEP** | Preserve with PE; P0. |
| R24 | `Microsoft.Network/networkInterfaces/fotoa-demo-pe-funcstblob-eastus2.nic.be30c038-8041-4086-8cbc-8f4de5fe38e1` | PE-managed NIC; T/I | R21 | **KEEP** | Preserve with PE; P0. |
| R25 | `Microsoft.Network/networkInterfaces/fotoa-demo-pe-funcstqueue-eastus2.nic.8a27af63-6a66-4469-90b5-6d6cc92b404e` | PE-managed NIC; T/I | R20 | **KEEP** | Preserve with PE; P0. |
| R27 | `Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net/virtualNetworkLinks/link-fotoa-demo-vnet-eastus2` | Blob zone link; I | Demo VNet, Function/eval PEs | **KEEP** | P0. |
| R28 | `Microsoft.Network/privateDnsZones/privatelink.table.core.windows.net/virtualNetworkLinks/link-fotoa-demo-vnet-eastus2` | Table zone link; I | Demo VNet/Function storage | **KEEP** | P0. |
| R29 | `Microsoft.Network/privateDnsZones/privatelink.queue.core.windows.net/virtualNetworkLinks/link-fotoa-demo-vnet-eastus2` | Queue zone link; I | Demo VNet/Function storage | **KEEP** | P0. |
| R30 | `Microsoft.Network/privateDnsZones/privatelink.vaultcore.azure.net/virtualNetworkLinks/link-fotoa-demo-vnet-eastus2` | KV zone link; I | Demo VNet/vault | **KEEP** | P0. |
| R33 | `Microsoft.Network/networkSecurityGroups/fotoa-demo-vnet-eastus2-function-integration-nsg-eastus2` | Function subnet NSG; T/I | Delegated function-integration subnet | **KEEP** | Network/security regression; P0. |
| R34 | `Microsoft.Network/networkSecurityGroups/fotoa-demo-vnet-eastus2-private-endpoints-nsg-eastus2` | Shared PE subnet NSG; T/I | All demo PEs, not just legacy hub | **KEEP** | P0. |

#### B. Classic Foundry candidates—not shared-resource deletion bundles

| Row | Resource ID suffix (explicit type/name) | Purpose / owner evidence | Current dependencies | Recommendation | Risk / exact prerequisite |
|---|---|---|---|---|---|
| R02 | `Microsoft.MachineLearningServices/workspaces/fotoa-demo-aihub-eastus2` | Classic Hub; T/I | R03, R31/R32, AzureML DNS, system MI/RG grants, governance diagnostic | **REMOVE-CANDIDATE** | High asset/identity/policy risk; P1, then P2/P3; project first. |
| R03 | `Microsoft.MachineLearningServices/workspaces/fotoa-demo-aiproj-eastus2` | Classic Project; T/I | R02, KV grant, project→LAW diagnostic, unverified data-plane assets | **REMOVE-CANDIDATE** | High consumer/asset risk; P1. Empty inspected collections are insufficient alone. |
| R12 | `Microsoft.Network/privateDnsZones/privatelink.api.azureml.ms` | Classic private DNS; T/I | Both hub PEs, two VNet links, eight A recordsets | **REMOVE-CANDIDATE** | Shared zone; P3 only after both environments clear. |
| R26 | `Microsoft.Network/privateDnsZones/privatelink.api.azureml.ms/virtualNetworkLinks/link-fotoa-demo-vnet-eastus2` | Classic DNS link; I | Demo hub resolution | **REMOVE-CANDIDATE** | P2/P3; verify no remaining AzureML clients in demo VNet. |
| R31 | `Microsoft.Network/privateEndpoints/fotoa-demo-pe-aihub-eastus2` | Classic hub PE; T/I | R02 and shared demo PE subnet | **REMOVE-CANDIDATE** | P2; remove only target-specific connection/DNS artifacts. |
| R32 | `Microsoft.Network/networkInterfaces/fotoa-demo-pe-aihub-eastus2.nic.f992623e-9cc8-4bc5-ae48-8c5b618cf5e3` | PE-managed classic NIC; T/I | R31 | **REMOVE-CANDIDATE** | P2; lifecycle through PE, never standalone while attached. |
| R36 | `Microsoft.MachineLearningServices/workspaces/fotoa-dev-aihub-eastus2` | Classic Hub; T/I | R37/R46/R48, legacy DNS, RG/workspace grants, governance diagnostic | **REMOVE-CANDIDATE** | P1; independent of whether dev telemetry is retained. |
| R37 | `Microsoft.MachineLearningServices/workspaces/fotoa-dev-aiproj-eastus2` | Classic Project; T/I | R36, dev KV grant, dev LAW diagnostic | **REMOVE-CANDIDATE** | P1; do not cascade to dev KV/LAW/storage. |
| R46 | `Microsoft.Network/privateEndpoints/fotoa-dev-pe-aihub-eastus2` | Dev classic hub PE; T/I | R36 + dev VNet | **REMOVE-CANDIDATE** | P2. |
| R48 | `Microsoft.Network/networkInterfaces/fotoa-dev-pe-aihub-eastus2.nic.c1b8719d-2dcc-476e-a541-7dfd4a11bd43` | PE-managed dev classic NIC; T/I | R46 | **REMOVE-CANDIDATE** | P2; PE lifecycle only. |
| R50 | `Microsoft.Network/privateDnsZones/privatelink.api.azureml.ms/virtualNetworkLinks/link-fotoa-dev-vnet-eastus2` | Classic dev DNS link; I | Dev hub/private clients | **REMOVE-CANDIDATE** | P2/P3; retaining dev KV does not require this AzureML zone. |

#### C. Independent dev stack: not proven obsolete

| Row | Resource ID suffix (explicit type/name) | Purpose / owner evidence | Current dependencies | Recommendation | Risk / exact prerequisite |
|---|---|---|---|---|---|
| R35 | `Microsoft.EventHub/namespaces/fotoa-dev-ehns-eastus2` | Dev telemetry transport; T/I | Dev telemetry hub, dev Function receiver grant | **UNKNOWN** | P4; zero seven-day-window traffic alone insufficient. |
| R38 | `Microsoft.KeyVault/vaults/fotoa-dev-kv-eastus2` | Dev secrets; T/I | Dev Function/project grants, private PE | **UNKNOWN** | P4; protected secrets/names and unverified consumers. |
| R39 | `Microsoft.OperationalInsights/workspaces/fotoa-dev-law-eastus2` | Dev log store; T/I | Dev AppInsights and classic project diagnostic; no exports observed | **UNKNOWN** | P4; log retention and non-export consumers unknown. |
| R40 | `Microsoft.Storage/storageAccounts/fotoadevsteastus2` | Dev Function state; T/I | Dev Function Blob/Queue/Table grants, security topic | **UNKNOWN** | P4/P6; empty container list is not whole-account emptiness. |
| R41 | `Microsoft.Web/serverFarms/fotoa-dev-plan-eastus2` | Dev Y1 plan; T/I | One dev Function site | **UNKNOWN** | P4, retire consumers before hosting. |
| R42 | `Microsoft.Insights/components/fotoa-dev-appi-eastus2` | Dev ingestion; T/I | Dev LAW, possible client exporters | **UNKNOWN** | P4; exporter/ingestion recency incomplete. |
| R43 | `Microsoft.Web/sites/fotoa-dev-func-eastus2` | Dev Function, observed Running; T/I | Dev plan, EH/KV/storage grants | **UNKNOWN** | P4; Running neither proves useful work nor abandonment. |
| R44 | `Microsoft.Network/virtualNetworks/fotoa-dev-vnet-eastus2` | Dev private network; T/I | KV and hub PEs, private subnet NSG | **UNKNOWN** | P4; remains relevant if dev vault retained. |
| R45 | `Microsoft.Network/privateEndpoints/fotoa-dev-pe-kv-eastus2` | Dev private KV; T/I | Dev vault/VNet | **UNKNOWN** | P4, not removed with hub PE. |
| R47 | `Microsoft.Network/networkInterfaces/fotoa-dev-pe-kv-eastus2.nic.a53b9ad9-ad9c-4640-824b-e5cc35c30306` | PE-managed KV NIC; T/I | R45 | **UNKNOWN** | P4; follow PE lifecycle only. |
| R49 | `Microsoft.Network/privateDnsZones/privatelink.vaultcore.azure.net/virtualNetworkLinks/link-fotoa-dev-vnet-eastus2` | Dev KV DNS link; I | Dev VNet; zone shared with demo | **UNKNOWN** | P4; never delete shared parent zone for dev cleanup. |
| R51 | `microsoft.alertsmanagement/smartDetectorAlertRules/Failure Anomalies - fotoa-dev-appi-eastus2` | Dev anomaly alert; U/I | Dev component, action ownership unverified | **UNKNOWN** | P4/P6. |
| R52 | `Microsoft.Network/networkSecurityGroups/fotoa-dev-vnet-eastus2-private-endpoints-nsg-eastus2` | Dev PE subnet NSG; T/I | Dev KV/hub PEs | **UNKNOWN** | P4; still attached after hub-only retirement. |
| R53 | `Microsoft.EventGrid/systemTopics/fotoadevsteastus2-03d207a0-753e-4b87-8949-1af65457a7bf` | Dev storage security events; U/I/S | Dev storage + antimalware subscription | **UNKNOWN** | P4/P6, security-owner decision before retirement. |

#### D. Modern Foundry and private validation

| Row | Resource ID suffix (explicit type/name) | Purpose / owner evidence | Current dependencies | Recommendation | Risk / exact prerequisite |
|---|---|---|---|---|---|
| R54 | `Microsoft.Network/networkSecurityGroups/fotoa-validation-nsg-eastus2` | Linux validation subnet security; U/I/V | validation-jumpbox subnet | **KEEP** | P0/P7; pending #143 acceptance. |
| R55 | `Microsoft.Network/bastionHosts/fotoa-validation-bastion-eastus2` | Private operator access; U/H/V | Existing Developer Bastion access design; exact ongoing clients not audited | **KEEP** | P0/P7; do not remove as VM-adjacent clutter. |
| R56 | `Microsoft.Network/networkInterfaces/fotoa-validation-vm-eastus2VMNic` | Linux VM private NIC; U/I/V | R57, validation subnet | **KEEP** | P0/P7. |
| R57 | `Microsoft.Compute/virtualMachines/fotoa-validation-vm-eastus2` | Private validation, Running as observed; U/I/V | System MI roles, NIC, disk, acceptance at inventory time | **KEEP** | P0/P7; no cleanup-owned power action. Subsequent separately approved release-owned deallocation is not resource retirement. |
| R58 | `Microsoft.Compute/disks/fotoa-validation-vm-eastus2_disk1_0c7fac1ec1534584afb765f038feb50a` | Attached Linux OS disk; U/I/V | R57 managedBy | **KEEP** | P0/P7; attachment disproves orphan assumption. |
| R59 | `Microsoft.Compute/virtualMachines/fotoa-validation-vm-eastus2/extensions/MDE.Linux` | VM security extension; U/I/S/V | R57 | **KEEP** | P0/P6/P7. |
| R60 | `Microsoft.Network/privateDnsZones/privatelink.cognitiveservices.azure.com` | Modern Foundry private DNS; T/I | Modern PE/demo VNet | **KEEP** | P0; not legacy AzureML DNS. |
| R61 | `Microsoft.Network/privateDnsZones/privatelink.openai.azure.com` | Model endpoint private DNS; T/I | Modern PE/demo VNet | **KEEP** | P0. |
| R62 | `Microsoft.Network/privateDnsZones/privatelink.services.ai.azure.com` | Foundry project private DNS; T/I | Modern PE/demo VNet | **KEEP** | P0. |
| R63 | `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2` | Working modern account; T/I/V | Operational/test projects, deployment, MI, PE, policy diagnostics | **KEEP** | P0; never delete parent to retire test child. |
| R64 | `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-eastus2` | Working project; T/I/V | Agent v1, model, AppInsights/eval connections, MI | **KEEP** | P0. |
| R65 | `Microsoft.Network/privateDnsZones/privatelink.cognitiveservices.azure.com/virtualNetworkLinks/fotoa-demo-link-foundry-eastus2` | Modern private DNS link; T/I | Demo VNet | **KEEP** | P0. |
| R66 | `Microsoft.Network/privateDnsZones/privatelink.services.ai.azure.com/virtualNetworkLinks/fotoa-demo-link-foundry-eastus2` | Modern private DNS link; T/I | Demo VNet | **KEEP** | P0. |
| R67 | `Microsoft.Network/privateDnsZones/privatelink.openai.azure.com/virtualNetworkLinks/fotoa-demo-link-foundry-eastus2` | Modern private DNS link; T/I | Demo VNet | **KEEP** | P0. |
| R68 | `Microsoft.Network/privateEndpoints/fotoa-demo-pe-foundry-eastus2` | Modern account PE, group account; T/I | Demo VNet and R63 | **KEEP** | P0; replacing legacy PE is not removing this PE. |
| R69 | `Microsoft.Network/networkInterfaces/fotoa-demo-pe-foundry-eastus2.nic.22e64155-f7ce-4366-9e71-528c8c7a4260` | PE-managed modern NIC; T/I | R68 | **KEEP** | P0. |
| R83 | `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-139test-eastus2` | Retained clean-create test project; T(Infra)/H/I | Own MI, test AppInsights connection, governance diagnostics, shared account | **REMOVE-CANDIDATE** | P5; intentional retention cannot be reversed by age/name inference. |

#### E. #138 operational resources: keep until separately released

| Row | Resource ID suffix (explicit type/name) | Purpose / owner evidence | Current dependencies | Recommendation | Risk / exact prerequisite |
|---|---|---|---|---|---|
| R70 | `Microsoft.Storage/storageAccounts/fotoademoevalstc81fda52` | Dedicated keyless eval storage; T/H/I | Operational project AAD connection + Blob role, Blob PE, security topic | **KEEP** | P0/P7; no current containers does not cancel #138 scope. |
| R71 | `Microsoft.Network/privateEndpoints/fotoa-demo-pe-evalblob-eastus2` | Eval storage Blob PE; T/H/I | Demo VNet/eval storage/shared Blob DNS | **KEEP** | P0/P7. |
| R72 | `Microsoft.Network/networkInterfaces/fotoa-demo-pe-evalblob-eastus2.nic.ccb5f37c-aa0a-454e-8c8b-240b4ae36e1e` | Eval PE-managed NIC; T/I | R71 | **KEEP** | P0/P7. |
| R73 | `Microsoft.EventGrid/systemTopics/fotoademoevalstc81fda52-9cfd76fd-9d3f-4b33-bfb7-8d4015b28e26` | Eval storage security events; T/I/S | Eval storage + antimalware subscription | **KEEP** | P0/P6/P7. |
| R74 | `Microsoft.Network/networkSecurityGroups/fotoa-demo-nsg-wjump-eastus2` | Windows subnet security; T/H/I | windows-jumpbox subnet | **KEEP** | P7; private access posture. |
| R75 | `Microsoft.Network/publicIPAddresses/fotoa-demo-pip-wjump-egress-eastus2` | Windows NAT egress IP; T/H/I | NAT R76, not VM public ingress | **KEEP** | P7; removing egress can break browser/setup access. |
| R76 | `Microsoft.Network/natGateways/fotoa-demo-nat-wjump-eastus2` | Windows egress; T/H/I | windows-jumpbox subnet, R75 | **KEEP** | P7; no assumption that deallocated VM makes NAT unnecessary. |
| R77 | `Microsoft.Network/networkInterfaces/fotoa-demo-nic-wjump-eastus2` | Private Windows NIC; T/H/I | R78 and windows-jumpbox subnet | **KEEP** | P7. |
| R78 | `Microsoft.Compute/virtualMachines/fotoa-demo-wjump-eastus2` | Private browser VM, deallocated; T/H/I | Disk/NIC, human credentials, #138 retained-use intent | **KEEP** | P7; deallocated is not abandoned. |
| R79 | `Microsoft.Compute/disks/fotoa-demo-osdisk-wjump-eastus2` | Attached Windows OS disk; U/I/H | R78 managedBy | **KEEP** | P7; data/state and ongoing disk cost. |
| R80 | `Microsoft.DevTestLab/schedules/shutdown-computevm-fotoa-demo-wjump-eastus2` | Windows shutdown cost control; T/H | Named VM; full schedule target not separately read | **KEEP** | P7; validate exact target before any later change. |
| R81 | `Microsoft.Compute/virtualMachines/fotoa-demo-wjump-eastus2/extensions/enablevmAccess` | Windows access extension; U/I/H | R78, human-access recovery | **KEEP** | P7; no extension settings/protected settings read. |
| R82 | `Microsoft.Compute/virtualMachines/fotoa-demo-wjump-eastus2/extensions/MDE.Windows` | Windows security extension; U/I/S | R78 | **KEEP** | P6/P7. |

### Important child/extension resources not fully covered by `az resource list`

The following also use `RG/providers/` unless the row says otherwise. These are
separate dependencies, not evidence that the 83-row listing was exhaustive.

| Exact ID suffix / identity | Purpose, ownership and evidence | Recommendation / risk / prerequisite |
|---|---|---|
| `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/deployments/fotoa-demo-gpt5mini-eastus2` | Shared observed model deployment; I/V, E3/E17 | **KEEP**, P0; no quota/model/sku change. |
| Data-plane identity `fotoa-demo-agent-eastus2`, version `1`, within R64 (not asserted to be an ARM child ID) | Current Prompt Agent; requester evidence E17; not re-read | **KEEP**, P0; verify model/tool metadata later without invocation/body access. |
| `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-eastus2/connections/fotoa-demo-appi-eastus2-2199` | Operational project tracing link; I/H, E4 | **KEEP**, P0; preserve name, target, private sharing and ApiKey mode. Do not force MI migration as cleanup. |
| `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-eastus2/connections/fotoa-demo-eval-storage` | Operational AAD storage link; I/H | **KEEP**, P0/P7; current project MI storage dependency. |
| `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-139test-eastus2/connections/fotoa-demo-appi-139test-eastus2` | Test project tracing link to shared R09; I/H | **REMOVE-CANDIDATE**, P5; not the component, account or operational connection. |
| `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/connections/fotoa-demo-appi-eastus2-2199` | Account-path listing, same operational target; I, E4/account-origin check | **UNKNOWN / preserve**, P0; provider semantics/consumers unresolved. |
| `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/connections/fotoa-demo-eval-storage` | Account-path listing, same eval target; I | **UNKNOWN / preserve**, P7 plus connection-origin verification. |
| `Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/connections/fotoa-demo-appi-139test-eastus2` | Account-path listing, same test target; I | **UNKNOWN / preserve**, P5; do not assume independent duplicate or safe delete. |
| `Microsoft.OperationalInsights/workspaces/fotoa-demo-law-eastus2/dataExports/fotoa-demo-e2e-app-spans` | Enabled export of all three current tables; I/V, E5 | **KEEP**, P0; exact table set, enabled state and destination preserved. |
| `Microsoft.EventHub/namespaces/fotoa-demo-ehns-eastus2/eventhubs/telemetry` | Live transport, 2 partitions, 1-day retention; I | **KEEP**, P0; backlog loss/replay-window risk. |
| `Microsoft.EventHub/namespaces/fotoa-demo-ehns-eastus2/eventhubs/telemetry/consumerGroups/$Default` | Observed group; I | **KEEP**, P0; actual consumers not exhaustively mapped. |
| `Microsoft.EventHub/namespaces/fotoa-demo-ehns-eastus2/eventhubs/telemetry/consumerGroups/function-transform` | Observed transform group; I | **KEEP**, P0; do not reset offsets/checkpoints. |
| `Microsoft.EventHub/namespaces/fotoa-dev-ehns-eastus2/eventhubs/telemetry` | Dev transport, 2 partitions/1-day retention; I | **UNKNOWN**, P4; dev groups/consumers need exact readback before retirement. |
| `Microsoft.Storage/storageAccounts/fotoademosteastus2/blobServices/default/containers/genai-correlation` | Current application ledger; I/V | **KEEP**, P0; logical expiry is not permission to delete durable records. |
| `Microsoft.Storage/storageAccounts/fotoademosteastus2/blobServices/default/containers/azure-webjobs-eventhub` | EH checkpoints; I/V | **KEEP**, P0; deletion can cause replay/gaps. |
| `Microsoft.Storage/storageAccounts/fotoademosteastus2/blobServices/default/containers/azure-webjobs-hosts` | Function host state; I/V | **KEEP**, P0. |
| `Microsoft.Storage/storageAccounts/fotoademosteastus2/blobServices/default/containers/azure-webjobs-secrets` | Function runtime secret-state container; I/V; names only inspected | **KEEP**, P0; no content retrieval. |
| Full ID `/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/providers/Microsoft.Authorization/roleDefinitions/c0ddffa6-6772-585e-89e1-28c7b882ee37` | Live role `fotoademosteastus2-genai-correlation-index`, assignable scope only this RG; I/V | **KEEP**, P0; ARM canonical ID is subscription-shaped, not an extra subscription scan. |
| `Microsoft.Storage/storageAccounts/fotoademosteastus2/blobServices/default/containers/genai-correlation/providers/Microsoft.Authorization/roleAssignments/c62dca6e-56bf-5821-b41d-9130ede91092` | Ledger index role→Function MI observed; I/V | **KEEP**, P0; retain existing host grants too. Re-read canonical assignment ID before any future action. |
| `Microsoft.EventGrid/systemTopics/fotoademosteastus2-0dc58804-6931-47f3-8d65-518d1cfae662/eventSubscriptions/StorageAntimalwareSubscription` | Demo antimalware webhook subscription; I/S | **KEEP**, P6; destination credentials/URL deliberately not read. |
| `Microsoft.EventGrid/systemTopics/fotoadevsteastus2-03d207a0-753e-4b87-8949-1af65457a7bf/eventSubscriptions/StorageAntimalwareSubscription` | Dev antimalware subscription; I/S | **UNKNOWN / preserve**, P4/P6. |
| `Microsoft.EventGrid/systemTopics/fotoademoevalstc81fda52-9cfd76fd-9d3f-4b33-bfb7-8d4015b28e26/eventSubscriptions/StorageAntimalwareSubscription` | Evaluation antimalware subscription; I/S | **KEEP**, P6/P7. |
| `Microsoft.MachineLearningServices/workspaces/fotoa-demo-aiproj-eastus2/providers/Microsoft.Insights/diagnosticSettings/fotoa-demo-diag-to-law` | Classic project→demo LAW; I | **REMOVE-CANDIDATE** only with source project, P1; destination retained. |
| `Microsoft.MachineLearningServices/workspaces/fotoa-dev-aiproj-eastus2/providers/Microsoft.Insights/diagnosticSettings/fotoa-dev-diag-to-law` | Classic project→dev LAW; I | **REMOVE-CANDIDATE** only with source project, P1; not authorization to remove LAW. |

Policy diagnostic extensions named `setByPolicy-MCAPSGovernance` were observed on
**R02, R36, R63, R64 and R83**. For each, its exact ID is that primary row's full
ID plus `/providers/Microsoft.Insights/diagnosticSettings/setByPolicy-MCAPSGovernance`.
Purpose: governance telemetry; owner evidence S/E13. Disposition **UNKNOWN /
preserve**; P6 and source-specific P1/P5 apply. Do not remove the policy/destination
or suppress its recreation.

Legacy DNS A recordsets were observed under R12 with exact names:

| Hub/workspace GUID | Recordset names, each type `Microsoft.Network/privateDnsZones/A` | Disposition |
|---|---|---|
| Demo `a09b60ce-d588-4d31-9711-18dd90827f1b` | `a09b60ce-d588-4d31-9711-18dd90827f1b.workspace.eastus2.cert`; `a09b60ce-d588-4d31-9711-18dd90827f1b.workspace.eastus2`; `*.a09b60ce-d588-4d31-9711-18dd90827f1b.inference.eastus2`; `*.a09b60ce-d588-4d31-9711-18dd90827f1b.models.eastus2` | **REMOVE-CANDIDATE**, I/E2/E6, P2/P3. |
| Dev `1d369da0-678d-495e-9aee-dd6b30129b42` | `1d369da0-678d-495e-9aee-dd6b30129b42.workspace.eastus2.cert`; `1d369da0-678d-495e-9aee-dd6b30129b42.workspace.eastus2`; `*.1d369da0-678d-495e-9aee-dd6b30129b42.inference.eastus2`; `*.1d369da0-678d-495e-9aee-dd6b30129b42.models.eastus2` | **REMOVE-CANDIDATE**, I/E2/E6, P2/P3. |

Full recordset ID = R12 full ID + `/A/` + exact recordset name.
The wildcard is literally part of the DNS recordset name, **not a delete glob**.
Zone SOA `@` is platform DNS state; **KEEP while zone exists**. PE DNS-zone-group
IDs and record-IP membership were not enumerated; P2 requires them before change.
Other zones' complete recordsets, subnets, storage services/tables/queues, LAW
tables, remaining roles, model policy children and provider-managed state are not
exhaustively inventoried. Preserve them unless independently assessed and approved.

## Required source/IaC/documentation work (future changes, not performed)

| Artifact | Required change before retirement | Preservation rule |
|---|---|---|
| `infra/main.bicep`, `infra/modules/foundry-project.bicep` | **MIGRATE-FIRST**: establish an explicit reviewed modern account/project foundation path and intentional legacy opt-in/deprecation. Main still creates Hub/Project ML workspaces and emits classic discovery/principal outputs. Decide whether this entrypoint becomes modern or is archived as clearly non-live reference. | Do not broad-redeploy main against this RG. Existing classic module writes PNA Enabled and cannot reproduce the observed modern private environment. |
| `infra/modules/key-vault.bicep` and main cross-wiring | Remove only obsolete classic principal wiring once retired; document actual Function/validation/tracing/Windows secret consumers. | Preserve vault, Function MI, protected secret versions and all nonclassic grants. No blanket principal cleanup. |
| `infra/modules/networking.bicep`, main network target list | Model modern Foundry account PE/private DNS and existing shared network ownership. Main currently targets classic project `amlworkspace`; live PEs target hubs, showing drift. | Preserve Function storage PEs, both required KV paths, modern Foundry PE, shared subnets/NSGs and DNS. |
| `infra/modern-foundry-tracing.bicep`, `infra/modules/modern-foundry-app-insights.bicep` | Retain connection-only contract; explicitly distinguish it from a complete modern foundation. Resolve account-path/project-path connection semantics before deduplication. | Keep working ApiKey/project-private link and secure deployment-reference workflow; MI ingestion migration is optional, separate approval, not cleanup. |
| `infra/modules/app-insights.bicep`, `event-hub.bicep`, `function-app.bicep`, `infra/durable-genai-rollout.bicep` | Future owner-reconciled documentation/outputs should show live three-table LAW export, identity-based bindings, ledger/container role and checkpoint dependencies. | No #143 source/configuration change in this assignment; reconcile only after release coordinator handoff. |
| `infra/main*.parameters*.json`, modern profiles, deployment/validation scripts | Later maintainers must review names/IDs through approved secret-safe tooling; update classic assumptions and validation target types. **Parameter values were not read here.** | Do not retrieve secrets or silently resolve secure references for planning. No new `.azure/deployment-plan.md` edits here. |
| `infra/scripts/teardown-deployment.ps1` | Existing #23 utility supports whole-RG/target teardown and optional vault purge; it is **not** the selective cleanup plan. Future change should require an exact reviewed dependency-aware manifest and protected-resource denylist. | Never run whole-RG teardown, prefix/tag sweep, Complete-mode deployment, vault purge or broad orphan-RBAC removal on this mixed live RG. No destructive script is supplied here. |
| Agent deployment/configuration and tests under `src/prompt-agent` | Agent owner verifies caller endpoint interfaces and model/tool metadata use modern project, removes stale classic assumptions only where found. `FOUNDRY_ENDPOINT` remains a runtime config interface; source interface alone does not reveal live consumer configuration. | Do not read `.env*` or raw runtime settings; no invocation or prompt-body inspection to prove this. |
| `README.md`, `infra/README.md`, current-state architecture/runbooks, validation guides and ADR | Lead records proposed→accepted modernization decision, dependency ownership, deploy/recover/retire separation and retained operational resources. Mark historical claims as historical without rewriting acceptance evidence. | Current-state AppInsights→LAW→EH→Function→Arize stays current; direct OTLP/future-state is not substituted. #138 remains ancillary, #139 fixture release explicit. |

The missing modern foundation is a **recreation gap**, not evidence the live
account is unneeded. Recreating a model at the same name/capacity can be blocked
by quota, model availability or policy. IaC compilation alone does not establish
provider acceptance, private data-plane readiness or preserved agent state.

## Ordered cleanup phases and exact approval checkpoints

1. **Freeze and architecture review — no cloud changes.**
   Lead reviews this proposal with Infra/Agent/Telemetry/QA and the resource owner.
   Confirm the intended minimal target: one modern operational account/project/model,
   full existing telemetry chain and required private validation dependencies.
   Separate decisions: classic retirement; #139 fixture release; eventual dev-stack
   retirement; optional #138 jumpbox consolidation.
   **Checkpoint A:** user accepts the target and investigation scope, not deletion.
   Release coordinator explicitly releases the #143 acceptance hold before any
   cleanup mutation. Preserve `f650fed`, ledger and imported-ACK evidence meanwhile.
   Any intervening approved release fixture/grant removal/VM deallocation must be
   reconciled from the release owner's receipt; this plan neither executes nor
   blocks that independently authorized work.

2. **Close consumer/ownership gaps with metadata only.**
   For each classic project/hub, Agent/QA attest current callers and scheduled work;
   Infra inventories remaining asset/job/endpoint/datastore/flow metadata through
   existing authorized private access. Establish a representative owner-agreed
   observation window, not an invented “30 days means unused” threshold.
   Obtain governance confirmation for source diagnostics and security confirmation
   for any affected managed artifacts. Verify any external consumer only after
   explicit scope approval; do not scan the subscription.
   Test-project owner separately confirms retained fixture no longer needed.
   **Checkpoint B:** each candidate has an owner, positive retirement rationale,
   full dependency checklist, no unresolved required consumer and no UNKNOWN edge.
   Otherwise downgrade it to UNKNOWN or MIGRATE-FIRST and stop that candidate.

3. **Resolve source ownership and recovery gaps.**
   Implement/review modern foundation/deprecation changes separately, with focused
   tests and explicit private/network/identity invariants. Remove classic references
   from future deployment defaults only after deciding retained legacy support.
   Design narrow change scope; any future provider validation/what-if/deployment
   must have its own authorization—none was run for this assignment.
   **Checkpoint C:** Lead accepts the architecture/ADR and reviewed source changes;
   no plan can delete live dependencies just to make old IaC agree with reality.

4. **Preservation and pre-change baseline.**
   Resource owners approve asset retention, secret custody, configuration
   reconstruction and recovery responsibilities. Record sanitized IDs, identity
   object IDs, required role scopes, PE/DNS mappings and deployment provenance;
   securely preserve non-recreatable state through a separately authorized workflow.
   Capture metadata-only current health baseline and approved trace evidence.
   No blob/secret/model-state export is authorized by this document.
   **Checkpoint D:** backup coverage and explicit loss/recreate limits accepted;
   baseline succeeds; no release/validation task is using the candidate.

5. **Approve and retire the smallest classic slice, then verify.**
   Proposed ordering: one classic **project**, then its **hub** only after no
   projects/consumers remain; corresponding obsolete MI grants are reviewed at
   their exact scopes, not removed by display-name sweep.
   Inspect/delete only separately approved hub PE artifacts in the provider-supported
   order; let PE-managed NIC lifecycle follow its PE. DNS-zone-group/record
   ownership determines whether DNS cleanup is automatic or needs an exact follow-up.
   Preserve shared KV/storage/LAW/VNet/NSGs. Repeat the separately approved process
   for the other environment only after the first slice passes verification.
   **Checkpoint E:** user approves the **exact full IDs**, child/extension effects,
   execution window, operator, abort conditions and accepted irreversible loss.
   No approval is inferred from the term REMOVE-CANDIDATE.

6. **Retire remaining classic-only DNS last.**
   After both hub paths are gone, verify eight legacy A records, two links and
   all remaining private clients/zone-group ownership; remove only explicitly
   approved residual classic artifacts. Keep modern/storage/KV DNS untouched.
   **Checkpoint F:** both environments and network owner sign off. If any AzureML
   consumer survives, retain the zone/link/records it needs.

7. **Optional, independently scoped follow-ons.**
   #139 test project/connection can be retired only under P5, leaving shared account,
   model, demo AppInsights and operational connection intact. Resolve account-level
   listing ambiguity before any account-path connection action.
   Dev stack P4 is a separate whole-environment decision, not a consequence of hub
   retirement. #138 consolidation P7 may reduce duplicate access infrastructure,
   but Linux acceptance VM and Windows browser use are not interchangeable without
   private routing, identity, browser/OS, egress and recovery evidence.
   **Checkpoint G:** fresh exact-scope user approval per follow-on. No stop,
   deallocation, RBAC change or resource deletion is preauthorized.

8. **Close out after post-change verification and retention signoff.**
   Re-inventory exact intended absences, retained resources, role scopes and DNS
   references; update architecture/runbooks and cost comparison. Do not erase
   deployment/audit/acceptance history as “cleanup.” Lead owns review/routing;
   this assignment stops at the plan.

## Verification gates: preserve invocation and the full telemetry path

These are **future acceptance checks**, not tests performed or permission to invoke.
Metadata can support readiness but cannot prove invocation or end-to-end Arize
delivery. Use a separately authorized bounded synthetic canary, only after the
current acceptance owner releases the environment and approves call budget.

| Gate | Required verification | Abort condition |
|---|---|---|
| Private posture | Approved validator confirms operational Foundry/storage/KV PEs/DNS, required VNet/subnet/NSG routes, system MI identity stability, local auth disabled/keyless storage and current ACLs unchanged. | Any public fallback, lost private resolution, credential extraction or need for new grant. Stop; do not repair by weakening controls. |
| Foundry | Existing agent version 1 metadata still targets intended model/tools. Authorized private-path canary invokes the same intended agent/model and records only permitted IDs/status, no body in cleanup evidence. | Endpoint/agent/model identity drift, invocation failure or quota/policy error. Preserve remaining candidates and hand off to owner. |
| AppInsights → LAW | Canary trace/span IDs and allowed aggregate counts appear in intended tables, including content-event presence where authorized; preserve privacy controls. | Missing expected records, broken trace/parent relationships, changed component/workspace routing. |
| LAW → EH | Exact export still enabled with AppDependencies/AppRequests/AppGenAIContent and explicit `telemetry` destination; message metrics move within agreed latency. | Missing table/destination drift or growing unprocessed backlog. |
| EH → Function | Intended consumer group and identity bindings unchanged; Function runs without auth/DNS failures; checkpoint progress and durable correlation/replay semantics preserved. | Offset reset, replay storm, ledger/index access failure, missing host/secret state. |
| Function → Arize | Approved reviewer verifies new canary trace graph/IDs, token mapping, content visibility permitted by policy and imported/ACK evidence; no synthetic bodies copied into this plan. | Missing Arize acceptance or graph/token/content regression, even if Azure metrics look healthy. |
| Isolation | #143 deployment/evidence and every protected resource remain unchanged except the later explicitly approved cleanup manifest. | Concurrent acceptance or drift makes baseline incomparable. Stop and reschedule. |

Recent EH traffic and the requester-reported 35 imported ACKs are evidence to
preserve, **not a new end-to-end pass**. The current assignment did not invoke a
model, run a VM command, read trace bodies or independently reaccept #143.

## Preservation, backup, recreation and irreversible risks

- **Workspaces/projects/agents:** deletion can lose project assets, files,
  conversation/thread/evaluation/flow state and references. This review neither
  established a complete export nor verified a supported restoration path.
  Same-name recreation is not restoration; capture owner-approved metadata and
  use separately authorized secure asset preservation before retirement.
- **Identity/RBAC:** system MI object IDs change on recreation; role assignments
  at surviving scopes can remain as stale grants. Preserve working identities and
  review only obsolete principal-specific residuals after approved retirement.
  Inherited/global/governance assignments are not part of this plan.
- **Storage:** do not delete the demo account, ledger or any host/checkpoint/secret
  container. Demo/evaluation Blob delete retention was disabled and versioning
  unverified. Recovery is not assumed; ledger/checkpoint deletion can create
  unrecoverable gaps, duplicates or wrong correlations even if the Function restarts.
- **Event Hub/LAW/AppInsights:** EH retention is one day; replay is bounded and
  source retention/backfill cannot be assumed. Deleting/replacing LAW/AppInsights
  loses or severs retained telemetry and connection identity. No purge is proposed.
- **Key Vault:** both vaults have 90-day retention/purge protection. Do not purge,
  delete, rotate, enumerate secret contents or assume a new vault restores existing
  version-pinned deployment references. Human credential/secret custody remains
  with approved operators; metadata backups do not contain secret recovery material.
- **Private network:** PE IPs/NICs, DNS-zone-group behavior and clients must be
  reconciled before changes. Recreating the same resource names can yield new IPs.
  Never remove shared VNet/NSGs/Blob/KV/modern DNS to retire a legacy endpoint.
- **VMs:** deallocation does not delete attached disks or imply permission to
  delete them. Neither OS disk was orphaned. Linux MI/current session and Windows
  access/bootstrap state require separate operational recovery acceptance.
- **Policy/security:** source deletion may affect mandated diagnostics; policy can
  recreate settings. Storage antimalware subscriptions and MDE extensions require
  security ownership, not name/age heuristics.
- **Rollback limits:** before an approved irreversible action, abort and retain
  the candidate on any doubt. After deletion, recreation may need separate
  deployment/RBAC/model authorization, new IDs, quota and restored state. No
  blanket rollback promise, restore command, secret export or destructive script
  is provided.

## Cost impact: likely direction, not a savings quote

No billing/price dataset was queried. Classic hub/project control-plane removal
may save little directly; measure associated billable PEs and any genuinely
allocated compute/storage first. Empty inspected compute lists do not establish
zero service-managed or historical costs.

Potential separately approved savings: the two classic hub PEs and eventual
legacy DNS zone/links; unnecessary dev EH/storage/log ingestion after P4; retained
test-related usage after P5; operational NAT/PIP/VM-disk costs after P7.
The current EP1 plan is an obvious persistent cost surface **but is required by
the working Function/private topology in this plan**, not a cleanup candidate.
Deallocated Windows VM still leaves disk/NAT/PIP charges; Running Linux validation
VM costs cannot be cut during acceptance.
The later requester-approved release-agent deallocation is separately authorized;
this plan does not execute it or treat the VM/MI/network as disposable afterward.

#138 records an **historical approved ceiling**, USD 53.42/month persistent if NAT
was necessary plus USD 0.188 per running VM hour. That is not a fresh price quote,
bill, or projected cleanup saving. Obtain resource-ID-attributed costs, pricing,
retention/security charges and a comparable before/after window under separately
approved billing scope before committing to a savings figure.

## Review requested and blockers

1. **Lead:** review modern-only target and the MIGRATE-FIRST IaC/recreation gap.
2. **Agent/QA owners:** provide positive classic consumer/asset clearance and
   approved metadata-only agent/model mapping verification; no calls authorized.
3. **Governance/security owners:** approve handling of source diagnostics and
   clarify any affected provider-managed artifacts; outside-RG destination remains
   uninspected and preserved.
4. **Release coordinator:** release #143 validation hold before any eventual
   operational change; keep this document out of #144.
5. **Resource owner:** separately decide #139 fixture retention, dev-stack purpose
   and #138 operational consolidation; approve only exact fully resolved IDs later.

Until those gates close: **keep all resources as they are**.

### Sources

- Repository: `infra/main.bicep`, `infra/modules/foundry-project.bicep`,
  `infra/modules/key-vault.bicep`, `infra/modules/networking.bicep`,
  `infra/modern-foundry-tracing.bicep`,
  `infra/modules/modern-foundry-app-insights.bicep`,
  `infra/durable-genai-rollout.bicep`, `infra/README.md`,
  `infra/scripts/teardown-deployment.ps1` (read only, never executed),
  `docs/current-state/foundry-appinsights-tracing.md`,
  `.squad/team.md`, `.squad/routing.md`, `.squad/agents/infra/charter.md`,
  scoped Infra history and relevant `.squad/decisions.md` entries.
- GitHub: [#138](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/138),
  [#139](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/139),
  [#23](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/23).
- Live: native RG resource list; ARM allowlisted workspace/account/project/
  connection/compute/endpoint/container/role/diagnostic metadata; PE/VNet/DNS
  metadata; VM power/identity/attachment metadata; vault/storage protection;
  EH/consumer-group/export metadata; bounded activity and message metrics.
  The evidence register distinguishes failed queries and unverified areas.
- Public official references fetched 2026-10-19:
  [Microsoft Foundry overview](https://learn.microsoft.com/en-us/azure/foundry/what-is-foundry)
  states hub-based projects remain in classic and new investment focuses on
  Foundry projects;
  [Create a Foundry project](https://learn.microsoft.com/en-us/azure/foundry/how-to/create-projects)
  describes current project organization. These support the direction, **not**
  a declaration that this repository's classic resources are unused.

## Lead planning review — approved with gates

**Reviewer:** Lead, requested by Rob McKenna.

**Review context timestamp:** 2026-10-19T11:10:12.473-04:00.
**Verdict: APPROVED WITH GATES for the planning structure only. No deletion,
migration, deployment, invocation, IAM or VM power action is approved.**

The 83 primary rows are present once each (R01–R83). Their recommendations are
appropriately conditional on the reported inventory, not an independent Lead
certification of live IDs or non-use. No blocking architecture contradiction was
found in this bounded repository review. Old type, age, null associations, empty
collections and quiet traffic windows do not establish that a resource is unused.

### Repository checks supporting this verdict

- **Recreation gap confirmed:** `infra/main.bicep:123` invokes the classic module;
  `infra/modules/foundry-project.bicep:74–112` declares both ML workspace kinds,
  their hub dependency and PNA Enabled. Main still wires the classic project
  principal into KV and targets the project for `amlworkspace` private access
  (`infra/main.bicep:172–174,281–291`). Treat the reported live hub-target PEs as
  drift to reconcile, not permission to redeploy this baseline.
- **Modern tracing is not foundation IaC:** the account/project declarations are
  `existing`; the writable resource is their connection
  (`infra/modules/modern-foundry-app-insights.bicep:43–50,84–90`).
  `infra/README.md:93–108` explicitly preserves this connection-only boundary.
  Reviewed modern foundation/source ownership and recovery readiness must precede
  classic retirement; compilation alone cannot close that gate.
- **State and retained-test dependencies confirmed:** the durable rollout owns
  the ledger container, additive index role/assignment and three-table export
  (`infra/durable-genai-rollout.bicep:45–110`), not a replacement foundation.
  The #139 runbook explicitly records `temporaryCleanup=false` and the test
  connection's shared component (`foundry-appinsights-tracing.md:301–345`).
  Neither ledger/checkpoint loss nor removal of that shared component is cleanup.

### Mandatory interpretation and outstanding gates

1. Keep the modern account/project/agent v1/model and full
   AppInsights → LAW → EH → Function → Arize path, current runtime identities,
   ledger/checkpoints, shared KV/storage/VNet/DNS/PEs and private validation path.
   The four classic workspaces remain candidates only: positive asset/consumer
   clearance, governance approval and Checkpoints A–E precede project-then-hub
   retirement; exclusive PE/NIC/DNS retirement follows P2/P3, never a shared sweep.
2. Dev retirement remains UNKNOWN; #139 release and #138 consolidation remain
   separate owner decisions. Preserve unresolved account-path connections,
   governance diagnostics/destination and antimalware subscriptions. Any required
   investigation of the exact outside-RG governance LAW above, ancestor grants or
   external consumers needs separate explicit scope approval; none was queried.
3. Preserve unresolved quarantined work and its provenance without deleting,
   resetting or blindly resending it (`durable-genai-correlation.md:34–39`).
   Requester handoff reports deployed `f650fed`, documentation update `17a45be`,
   and two native attempts (one success, one HTTP 429); native content-table
   transport is verified, but live fallback remains unproven. The separately
   approved two-event, tiny explicitly synthetic fixture is release-owned, not a
   cleanup test or acceptance result. Obtain its completion/temporary Data Sender
   grant-removal/VM-deallocation receipt before establishing a cleanup baseline;
   inventory IAM and power state are as-of observations, not current assertions.
4. Preserve Checkpoints A–G, exact-ID approvals, synthetic-only authorized
   validation, accepted irreversibility/recovery limits and abort-on-UNKNOWN
   behavior. No broad RG teardown, secret/cache inspection, public fallback or
   implicit repair grant is permitted. Keep this separate plan out of #144.

**Remaining execution blockers:** consumer/asset and connection-semantic gaps,
modern source/recreation readiness, governance/security/retention signoff, release
handoff and fresh exact-resource user approval. All resources remain retained
under this plan until the applicable gates close. Review used repository sources
and supplied handoff only; no Azure inventory, mutation or runtime test was run.
