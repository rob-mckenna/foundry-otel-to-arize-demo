# ADR-0004: Modern-only Foundry foundation and gated classic retirement

## Status

**Accepted direction, 2026-10-19. Implementation and live verification pending.**
Requester/approver: **Rob McKenna**, who approved “Go ahead with cleanup, approved.”
at 2026-10-19T12:35:55.792-04:00 for
[#145](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/145).
Approval covers modernization and focused repository
cleanup with a modern-only supported deployment path; it does **not** approve
deployment, model invocation, IAM changes or deletion of any live resource.
This ADR records that approval, not a claim of separate cross-track acceptance.

Reviewed source baseline: released `origin/main` `c055795` (merged
[#144](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/144)),
branch `squad/145-modern-foundry-cleanup`. Only architecture documents are
authored in this Lead assignment. The
[cleanup inventory and Lead review](../current-state/resource-cleanup-plan.md#lead-planning-review--approved-with-gates)
remain as-of evidence, not a new live inventory.

## Context

The working architecture remains **Foundry → Application Insights → Log Analytics
(LAW) → Event Hub → Function → Arize** (ADR-0002 and ADR-0003).
`infra/main.bicep` invokes `modules/foundry-project.bicep`, creating classic
`Microsoft.MachineLearningServices/workspaces` Hub/Project resources. Its
endpoint is an ML `discoveryUrl`; it grants the classic project Key Vault access
and targets that project with `amlworkspace` private access. Neither this graph
nor the existing public-default KV/Function/network modules reproduces the
observed private modern environment.

The verified #139 `modern-foundry-tracing.bicep` declares an **existing** account
and project and writes only their AppInsights connection. It is not a foundation.
Recreation must be defined before retiring old source or live classic resources.
Four classic workspaces are **conditional candidates**, not unused-certified.
Empty inspected collections, age and quiet traffic do not establish non-use.

Release context is now newer than the cleanup inventory: #144 is merged, QA
approval was delivered by Squad QA and reconciled by the coordinator, and the released
[durable runbook](../current-state/durable-genai-correlation.md#controlled-missing-inline-fallback-evidence-2026-10-19)
records fallback validation and VM deallocation at `15:23:04Z`. The #143 acceptance
hold is released; its evidence/state protections are not. No cloud verification
was performed for this ADR.

## Decision

### 1. One supported modern path; distinct fresh, adopt and retire operations

Replace `infra/main.bicep` with the **modern-only fresh resource-group-scoped
composition** described below. Do not add `useLegacy`, keep a classic deployment
profile, or move the classic template into an executable archive path. Git
history and historical ADR/evidence documents preserve provenance.

Fresh means new, explicitly approved resource identities, not a broad PUT over
the mixed live RG. The supported composition includes the Foundry foundation,
its private reachability and the existing telemetry pipeline's infrastructure;
it must not be advertised as complete while only the account/connection exists.
Application package publication, Prompt Agent version creation and validation
are subsequent separately authorized operations, not Bicep success claims.

**Live adoption is separate:** preserve current identities, names, model tuple,
network and state; keep the #139 connection-only entrypoint and
`durable-genai-rollout.bicep` as narrow, documented modern operations. Do not
expand them into parent-resource redeployments. Any missing live foundation
ownership must be reconciled through exact-resource reviewed changes, not by
running fresh main against the live RG.

**Retirement is separate again:** source removal does not delete live resources
in incremental mode and is not authorization for an exact-ID cleanup manifest.
No Complete-mode RG deployment, deployment-stack unmanaged deletion, RG teardown,
vault purge, prefix sweep or orphan-IAM sweep is an adoption/cleanup mechanism.

### 2. Minimum resource and provider contract

The following are **target implementation contracts**, not resources newly
implemented or provider-validated by this ADR. Pin Foundry ARM resources to
**2025-09-01**, matching the shipped tracing contract; newer public APIs exist,
but an API/SDK modernization is not bundled into this decision.

| Boundary / proposed symbol | Required contract |
|---|---|
| `modern-foundry-foundation.bicep`: `account` | `Microsoft.CognitiveServices/accounts@2025-09-01`, `kind: AIServices`, SKU `S0`, system-assigned MI, `allowProjectManagement=true`, explicit globally unique `customSubDomainName`. `publicNetworkAccess=Disabled`, `disableLocalAuth=true`, `networkAcls.defaultAction=Deny`, `bypass=None`. No ML hub, `amlWorkspace` attachment or implicit public bootstrap. |
| Same module: `project` | `Microsoft.CognitiveServices/accounts/projects@2025-09-01`, parent `account`, same selected location, distinct system MI, `properties.displayName`/`description`. Do not copy ML `hubResourceId`, `discoveryUrl`, workspace SKU or hub dependency fields onto this type. Apply required tags where the API supports them. |
| `modern-foundry-model.bicep`: `modelDeployment` | `Microsoft.CognitiveServices/accounts/deployments@2025-09-01`, parent account, **one** explicit deployment name. `properties.model.{format,name,version}`, `sku.{name,capacity}`, explicit `versionUpgradeOption`; optional existing approved `raiPolicyName`. Use SKU capacity, not deprecated `scaleSettings`. No deployment-per-project assumption, automatic spillover, quota increase or fallback model. |
| Foundation identity edge: `projectAccountAccess` | Project MI requires **Foundry User (formerly Azure AI User)** at the account scope per official RBAC guidance. Caller/deployer identity is different from project MI. Infra must use the published role definition, stable assignment identity and approved scope; no Owner/Contributor blanket substitute. Existing live grants remain untouched. |
| `networking.bicep`: modern account target | `Microsoft.Network/privateEndpoints@2023-11-01`, target **account ID**, group `account`; never a project `amlworkspace` PE. Explicit PE subnet, private DNS zones, `privateDnsZoneGroups` and VNet links (`Microsoft.Network/privateDnsZones@2020-06-01` family). For Azure public cloud cover `privatelink.cognitiveservices.azure.com`, `privatelink.openai.azure.com`, `privatelink.services.ai.azure.com`. Provider-owned PE NIC/IP lifecycle, not hardcoded A-record addresses. |
| KV / Function storage and network | Retain `Microsoft.KeyVault/vaults@2023-07-01`, RBAC, soft delete and purge protection; PNA Disabled, deny-by-default ACLs. Retain keyless `Microsoft.Storage/storageAccounts@2023-01-01`, HTTPS/TLS, `allowSharedKeyAccess=false`, `allowBlobPublicAccess=false`, PNA Disabled. KV `vault` PE/DNS and storage `blob`/`queue`/`table` PE/DNS support runtime dependencies. File-share/content deployment needs are a separate explicit check, not permission to enable shared keys. |
| Function | `Microsoft.Web/serverfarms` and `sites@2023-12-01`, Python worker and system MI, private-runtime-capable hosting (existing demo EP1 preserved). Fresh supported private path uses Premium, not the old Y1/no-VNet default. Explicit delegated Function integration subnet, routing/DNS and deployment-package access are required. Private ingress to a timer/EH worker is not a replacement for outbound VNet integration. |
| Telemetry | Workspace-based `Microsoft.Insights/components@2020-02-02` → `Microsoft.OperationalInsights/workspaces@2023-09-01`; EH namespace/hub/consumer group retain the existing module API pin pending separate provider validation. Explicit native `workspaces/dataExports@2023-09-01` destination namespace ID **and hub name**; no accidental per-table hubs. Trace association is `accounts/projects/connections@2025-09-01`, not an ML diagnostic setting. |

Official account/project/model schemas establish resource shapes, not product
availability, agent-state recovery, private data-plane success or exact role
requirements for every tool. A same-name resource is not restoration.

### 3. Portable inputs and non-secret outputs

Infra owns these proposed public interfaces; module implementation may use
internal helpers but must not silently change the external meanings.

| Interface | Required parameters / outputs |
|---|---|
| `main.bicep` → `modern-foundry-foundation.bicep` | Keep shared `projectToken`, `environment`, `location`, `regionToken`, `ownerTag`, `costCenterTag`/synthetic tags. Add explicit `accountName`, `projectName`, `customSubDomainName`; retain `projectDisplayName`. Shared naming helpers supply fresh-name conventions (`foundry`, `fproj` tokens), while approved existing resource names must not be normalized/renamed. Remove `foundrySkuName` (ML Basic/Free/etc.); S0 is the minimum account contract. |
| `main.bicep` → `modern-foundry-model.bicep` | Required `accountName`, `modelDeploymentName`, `modelFormat`, `modelName`, `modelVersion`, `modelDeploymentSkuName`, positive `modelDeploymentCapacity`, `modelVersionUpgradeOption`; optional approved `raiPolicyName`. No executable profile may rely on an omitted model version or implicit upgrade choice. |
| Network contract | Explicit fresh network address ranges or explicitly provided existing PE/integration subnet IDs; existing private DNS zone IDs plus link ownership must be representable without recreating shared VNets/zones. These are network ownership modes, **not** legacy/public Foundry modes. A reused network must not receive an authoritative truncated subnet list. DNS registration/forwarding, NSGs and egress must resolve Foundry, KV and host storage from both Function and approved private validator. |
| Foundation outputs | `foundryAccountResourceId`, `foundryAccountName`, `foundryAccountPrincipalId`; `foundryProjectName`, `foundryProjectResourceId`, `foundryProjectPrincipalId`; `foundryProjectEndpoint` = `https://<customSubDomainName>.services.ai.azure.com/api/projects/<projectName>` in Azure public cloud. Never emit ML discovery URLs. Other Azure clouds are not certified by this suffix; stop for a reviewed cloud-specific endpoint/DNS contract. |
| Model outputs | `modelDeploymentResourceId`, `modelDeploymentName`; distinguish deployment alias from catalog model name/version and account from project endpoint. No key, token or connection-string outputs. |
| Pipeline outputs | Preserve existing LAW/AppInsights/KV/EH/Function name/ID outputs and meanings; add exact resource IDs where validation currently looks up by name. Preserve `privateEndpointsEnabled` as true for the supported private graph; subnet/PE/DNS IDs are topology identifiers, not reachability proof. |

The inventory's `gpt-5-mini` / `2025-08-07` / `GlobalStandard` / capacity `5`
in `eastus2` is **the existing demo tuple to preserve**, not a portable default,
capacity-to-TPM formula or permission to redeploy it. Each fresh environment
requires owner-approved model/version/region/SKU/capacity/upgrade policy and
data-residency choice, model availability and quota attestation. Quota is
subscription/region/model/deployment-type specific; capacity-unit RPM/TPM varies
by model. No cross-subscription scan, alternate region/model, PTU reservation,
capacity increase or inference probe is an automatic recovery action.

### 4. Tracing, identity and state dependencies are part of completeness

- Reuse the #139 module contract exactly for AppInsights: one supported
  project association, category `AppInsights`, component ARM ID target/metadata,
  explicit sharing and reviewed `peRequirement`/`peStatus`. Current working
  `ApiKey`/private association is preserved; it is **not** an instruction to
  enable Foundry account local authentication. `ProjectManagedIdentity`
  ingestion remains a separately approved migration, including component-scope
  Monitoring Metrics Publisher and provider-readable metadata security review.
  Account-path connection projections remain UNKNOWN; do not deduplicate them.
- `preserveExisting` means **no connection PUT**, not “tracing configured”.
  Fresh completion requires an explicitly approved association creation using
  `@secure` parameters across boundaries and an operator-supplied immutable
  Key Vault deployment reference. No plaintext parameters, key reads, secret
  outputs, secret rotation or assumption that the project MI resolves ARM
  secure parameters. If vault template resolution/private service access is
  unavailable, stop; do not weaken KV/Foundry network controls.
- Remove the classic project→KV automatic reader from fresh main. Do **not**
  replace it with an unjustified modern project→KV grant. Function MI needs
  the retained KV/EH/host-storage grants; project MI needs account access.
  Operator, caller, validator, project and Function principals have separate
  purposes/scopes. Optional evaluation/tool storage requires its own approved
  connection, MI and private path; it is not a mandatory new dependency.
- Preserve existing component ingestion/query controls and LAW/EH connectivity.
  A Foundry PE does **not** make Azure Monitor ingestion private; no AMPLS,
  EH firewall or outbound-network redesign is implied. Fresh profiles must
  document the approved service ingestion/export and Arize HTTPS egress paths.
  If enterprise policy disallows those paths, that environment is blocked
  pending a separately approved network design, not served by public fallback.
- Function identity bindings must preserve `EventHubConnection` (or explicit
  `EVENT_HUB_CONNECTION_SETTING_PREFIX`), `EVENT_HUB_NAME`,
  `EVENT_HUB_CONSUMER_GROUP`, `AzureWebJobsStorage__accountName` and
  `AzureWebJobsStorage__credential=managedidentity`. Wire the intended consumer
  group explicitly; the Python `$Default` fallback does not prove it matches
  the module's created group. Preserve Arize endpoint/project/space and KV
  reference interfaces, without copying their live settings.
- The reusable pipeline must account for native AppDependencies/AppRequests/
  AppGenAIContent export, `genai-correlation` container, additive container-local
  index role/assignment and existing host/blob/queue/table grants. Keep a single
  writer per export rule/container/role: fresh composition provisions the
  desired state, while the narrow durable rollout remains an existing-resource
  operation, not a second concurrent owner. Runtime durable enablement/cutover
  follows ADR-0003; do not enable a fresh consumer before approved readiness.
  In the current demo durable incoming stays enabled and checkpoints unchanged.

No Search, Cosmos DB, ACR, hosted-agent runtime/capability host, managed compute,
new VM/Bastion/NAT or extra evaluation storage is added merely to create an
account/project/model and tracing foundation. These are not established minimum
dependencies of this Prompt Agent scenario. Conversely, absent capability hosts
does **not** certify that a fresh private agent runtime/state path works. If
the selected agent API/tools require BYO stores, VNet injection, newer APIs or
capability settings, Agent/Infra must surface the exact product requirement and
request a scoped decision **before** adding services or claiming completeness.

### 5. Surgical Infra handoff and consumer adaptations

**Infra is the sole edit owner of `infra/**` for the implementation wave.**
Lead owns this ADR/index and cleanup-direction clarification only; Agent owns
Prompt Agent application/config adaptations; Telemetry owns pipeline runtime;
QA owns cross-track validation/docs acceptance. They supply requirements to
Infra, not concurrent edits to its Bicep/scripts/profiles.

| File / existing symbol | Infra-ready change boundary |
|---|---|
| `infra/main.bicep`: `foundryProject`, `foundrySkuName`, KV `readerPrincipalIds`, networking target `aiproj` | Replace classic composition with `modernFoundry`/`modelDeployment` modern modules; remove obsolete ML SKU, implicit classic reader and `amlworkspace` target. Keep `projectDisplayName`. Main composes the private pipeline as well as foundation; no legacy branch. |
| New `infra/modules/modern-foundry-foundation.bicep`, `modern-foundry-model.bicep` | Own account/project + account-scoped MI edge, and account model deployment respectively, using sections 2–3. Neither owns agent definitions, prompts, historical state or existing-resource cleanup. |
| `infra/modules/foundry-project.bicep` | Removal candidate from supported source once main/consumers/tests are adapted; do not move it to an executable archive or retain a “legacy opt-in”. Historical evidence mentioning it stays historical. |
| `infra/modules/app-insights.bicep`: `foundryProjectName`, `wireFoundryDiagnostics`, `existingFoundryProject`, `foundryDiagnosticSettings` | Remove classic ML diagnostic coupling. Keep workspace/component/KV secret responsibilities; AppInsights trace connection is separately wired by the modern module. Do not turn generic platform diagnostics into a claimed trace route or overwrite governance diagnostics. |
| `infra/modules/key-vault.bicep`, `function-app.bicep`, `networking.bicep`, `event-hub.bicep`, `naming.bicep` | Implement private fresh wiring, supported modern naming, Function integration and explicit state/export ownership. Network source currently claims DNS-zone-group creation but declares none: actual zones/links/groups are required, not comment-only support. Keep existing runtime grants/bindings; do not opportunistically change live IAM or auth. |
| `infra/main.parameters.json`, `main.parameters.private-endpoint.json` | Replace classic fields/profiles with secret-free modern private fresh examples and explicit model/network prerequisites. Consolidate the redundant public-vs-private story; no supported public/classic alternate. Existing traced-demo names are not a fresh deployment approval. |
| `modern-foundry-tracing*.json`, tracing module/entrypoint | Preserve exact-name adoption and no-PUT default; only surgical documentation/interface alignment. Do not remove secure-reference safeguards or add foundation writes. |
| `durable-genai-rollout.bicep` and its profile | Preserve narrow existing-resource contract, full table union/enabled destination, role GUID derivation and ledger identity. No migration/replay/reset or live-state rewrite as part of source cleanup. |
| `infra/scripts/validate-deployment.ps1` | Adapt output checks to modern account/project/model IDs and endpoint semantics. Remove unconditional modern project→KV Secrets User expectation (`$foundryPrincipalId` check); test required account access instead. This script currently authenticates/queries, runs what-if and deploys unless `-SkipCreate`: split offline checks from separately authorized cloud operations; never execute it as a local-only validator. |
| `infra/scripts/validate-naming.ps1`, `test_modern_foundry_tracing.py`, `validate-modern-foundry-tracing.py` | Extend offline compiled-graph tests for modern types/no ML/public fallback, required DNS/MI/export wiring and secret-free outputs. Preserve connection-only compiled inventory and exact-name exceptions. Provider acceptance/private readiness still need separate approval/evidence. |
| `infra/scripts/teardown-deployment.ps1` | Do not use as cleanup executor. Remove from the supported modernization workflow; any future destructive tooling requires exact manifest, protected-resource denylist and independent approval. This ADR supplies no deletion commands. |

Exact downstream adaptations (not Lead implementation in this assignment):

- `main` outputs `foundryProjectResourceId`, `foundryProjectEndpoint`,
  `foundryProjectPrincipalId` remain named interfaces with **new resource-type/
  endpoint meanings**; old consumers cannot treat them as ML discovery IDs.
  `appInsights.foundryProjectName` must not receive the modern project name.
  `naming.resourceTypeTokens.foundryHub/foundryProject` consumers must move off
  `aihub/aiproj` for fresh modern names, without renaming existing Azure assets.
- Agent: `src/prompt-agent/prompt_agent/config.py` (`PromptAgentConfig`,
  `load_config`, `has_placeholder_credentials`), `model_client.py`
  (`ModelClient`, `StubFoundryModelClient`) and their tests/README need explicit
  separation of local synthetic stub configuration from the deployed modern
  project + deployment alias + Entra caller interface. `FOUNDRY_API_KEY` and its
  placeholder heuristic are **not** the auth contract for a local-auth-disabled
  modern account. No SDK upgrade, real backend or stub deletion is authorized
  by this Lead artifact; keep useful offline tests, and have Agent report the
  necessary bounded adaptation before live use.
- Telemetry: `src/telemetry-pipeline/telemetry_pipeline/function_app.py` binding
  constants and durable gates consume the settings above; preserve behavior,
  mapper/correlation/exporter code and test fixtures. Do not change replay/
  quarantine semantics to fit new IaC.
- QA/Lead follow-on docs: `README.md`, `infra/README.md`,
  `docs/current-state/architecture.md`, `runbooks.md`, the #139 tracing runbook,
  `demo/runbook.md` and validation guides must distinguish new fresh instructions,
  existing-resource operations and historical receipts. Do not rewrite #143/
  #139 acceptance history or label the new foundation live-validated.

### 6. Preservation and irreversible-change gates

Preserve the active account/project, operational agent version 1 and model;
current AppInsights/LAW/export/EH/Function, all runtime identities and grants;
private access, both protected vaults and storage, DNS/subnets/NSGs/PEs; host
containers/checkpoints, ledger/index/35 imported ACKs and quarantine.
Specifically retain ambiguous operational trace `04f49dc16c02643b6a351a499cd4db5a`,
span `b4cd6555d6c3ea92`: delivery remains unknown; **do not resend**.

Preserve #138 retained evaluation/private-validation/browser assets, #139
retained test project/connection, independent dev telemetry stack, account-path
connection ambiguity, governance diagnostics/destination and storage antimalware
subscriptions until separately cleared. VM deallocation does not release VM,
disk, identity or network retention.

The cleanup plan's **83-row R01–R83 scope and evidence register are unchanged**.
Its classic candidates require positive consumer/asset clearance, governance
signoff, preservation/recovery acceptance and new exact-ID user approval.
Project-first/hub-after-consumers/exclusive-PE-and-DNS-last ordering remains.
Unknown external consumers stay protected; do not inspect secrets or scan other
RGs/subscriptions to resolve them.

Recovery invariants: do not rename/recreate working identities; a recreated MI
has a new principal and needs explicitly approved scope reconciliation. IaC
cannot restore agent/thread/file state, secrets, ledger or checkpoint positions.
Storage backup/versioning coverage is not established by this ADR. Preserve
version-pinned vault references; no purge, blanket rollback promise or automatic
replay. Record private DNS/PE ownership before changes; same-name recreation may
change IPs. Source convergence must precede, never force, live retirement.

## Consequences

- **Current-state impact:** None from this document-only assignment. The
  accepted replacement of legacy deployment defaults is pending implementation.
  #143/#144 release acceptance stands with its bounded native-transport/
  controlled-fixture limits, not a new foundation validation.
- **Future-state impact:** None. Direct OTLP remains conceptual; no direct
  Foundry→Arize shortcut replaces the current bridge.
- **Security considerations:** Private/keyless posture, scoped identities,
  synthetic-only data and secure KV references are mandatory. This work grants
  no permissions and reads no secret/cache/runtime settings or prompt bodies.
- **Observability considerations:** Keep trace/span/parent/correlation IDs,
  typed tokens, inline precedence, durable identity/admission/ACK state and
  quarantine. Infrastructure readiness is not proof of Arize receipt or full
  graph/resource parity.
- **Trade-offs accepted:** No classic compatibility deployment; users with
  classic assets must explicitly migrate or retain them outside this supported
  path. Private Premium hosting has persistent cost. Portability requires an
  explicit approved model/quota/network tuple rather than “deploy anywhere”.
- **Open questions / execution blockers:** (1) Infra must prove the complete
  private graph and fresh idempotence with offline tests, then separately
  approved provider/private-path validation. (2) Resource owner must choose the
  fresh model tuple/upgrade/residency and approve quota/cost; no implicit choice
  is made here. (3) Agent/Infra must verify exact Prompt Agent API/tool/state
  prerequisites; any required BYO services/new API/runtime are a decision gate.
  (4) Secret custody, vault deployment resolution and existing connection
  semantics require owner attestations, not secret reads. (5) Live retirement
  retains all consumer/governance/recovery/exact-ID gates. These block affected
  execution, **not** the approved modern-only architecture/source direction.

### Public provider basis

Official public references read 2026-10-19 (no Azure resource queries). These
establish documented shapes/prerequisites, not live support in the target tenant:

1. ARM 2025-09-01 [accounts](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts),
   [projects](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/projects),
   [deployments](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/deployments)
   and [connections](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/projects/connections).
2. [Create a project](https://learn.microsoft.com/en-us/azure/foundry/how-to/create-projects)
   and [Foundry RBAC](https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry):
   account/project identities and project MI account access; role renames do not
   change role IDs. No portal-created-grants assumption for Bicep.
3. [SDKs and endpoints](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview):
   project endpoint, custom subdomain and distinct OpenAI endpoint. This ADR does
   not adopt the page's latest SDK versions.
4. [Network isolation](https://learn.microsoft.com/en-us/azure/foundry/how-to/configure-private-link)
   and [private endpoint DNS values](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns):
   account PE vs outbound isolation, service-specific group and three DNS zones.
   Standard agent BYO requirements must not be assumed satisfied by a PE alone.
5. [Model deployment options](https://learn.microsoft.com/en-us/azure/foundry/concepts/deployments-overview)
   and [quota](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/quota):
   modern Foundry needs no AI Hub; deployment types, residency and model-specific
   quota differ. This does not authorize quota discovery or model provisioning.

The repository-contained official skill pin has no Foundry `SKILL.md` or reference
tree, only a dependency-checker script; it was not executed. No out-of-repository
skill/reference files or previous sessions were accessed.
