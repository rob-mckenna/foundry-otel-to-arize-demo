# Operations: Fresh Setup, Existing-Resource Adoption, and Gated Retirement

**CURRENT GUIDANCE (2026-10-19); fresh provider/private/end-to-end validation
PENDING.** [ADR-0004](../adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md)
accepts one supported **modern-only, private fresh path**. Implementation is in
progress; this page is not a deployment authorization or a claim that a clean
clone can already reproduce the live environment. Historical classic/public
setup and RG-wide teardown recipes are superseded, not alternate profiles.

For a no-cloud synthetic walkthrough use the [root README](../../README.md) and
[Prompt Agent README](../../src/prompt-agent/README.md). Local stub output is not
a deployed Foundry agent or evidence of model invocation. The
[demo runbook](../../demo/runbook.md) routes presenters to these same boundaries.

## 1. Choose the operation before choosing a template

| Operation | Supported boundary | Not interchangeable with |
|---|---|---|
| **Fresh** | `infra/main.bicep`: new, explicitly approved resource identities in a fresh RG; modern account/project/model, private reachability and telemetry infrastructure | Broad main deployment over the mixed live RG; account/project creation as proof of a published agent |
| **Adopt / reconcile existing** | Exact-name [#139 connection-only entrypoint](foundry-appinsights-tracing.md) and [durable rollout](durable-genai-correlation.md), each with its own reviewed delta | Fresh main, parent-resource redeployment, runtime reset or a second writer for the export rule/container/role |
| **Retire** | Separately approved exact-ID manifest after consumer, governance and recovery gates in the [cleanup plan](resource-cleanup-plan.md) | Source removal, omission from Incremental mode, RG teardown, Complete mode, stack unmanaged deletion, vault purge or orphan-IAM sweep |

No classic Hub deployment, legacy toggle or public-network fallback is supported.
An existing classic asset is a migration/retention decision, not a fresh setup option.

## 2. Fresh private path: required contract and stop gates

The implementation/parameter authority is [infra/README.md](../../infra/README.md),
subject to ADR-0004. Until Infra finishes the contract and independent review,
do not copy an older deployment command or treat an example profile as executable.
No hypothetical fresh deployment command is supplied here.

### Explicit portable inputs

- Choose `projectToken`, `environment`, `location`, `regionToken`, `ownerTag`,
  `costCenterTag`, `accountName`, `projectName`, `customSubDomainName` and
  `projectDisplayName`. Fresh naming uses `foundry` / `fproj`, not ML Hub tokens.
  Do not normalize or rename existing resource identities.
- Approve **one** account-scoped deployment using `modelDeploymentName`,
  `modelFormat`, `modelName`, `modelVersion`, `modelDeploymentSkuName`,
  positive `modelDeploymentCapacity`, `modelVersionUpgradeOption`, and only an
  already approved optional `raiPolicyName`. A deployment alias is not the
  catalog model name/version. The retained demo tuple is not a portable default.
  Infra's in-progress interface also requires explicit
  `modelDataResidencyApproval` and `modelDeploymentApproved`; supplying them is
  an operator attestation, not proof of quota or permission to invoke a model.
- Attest region/model/SKU availability, subscription-specific quota,
  capacity-unit semantics, residency and cost before provisioning. Premium
  hosting has persistent cost. No automatic alternate model/region, quota
  increase, capacity increase, reservation or inference probe.
- Choose the discriminated network ownership object: `mode=fresh` requires
  three explicit CIDRs for the owned VNet/PE/integration topology and owns seven
  DNS links; `mode=existing` requires approved PE and delegated Function
  integration subnet IDs, seven exact private DNS zone IDs and
  `dnsLinksManagedExternally=true`. Existing mode performs no VNet/zone PUT.
  Exact object property names belong to Infra's implementation guide; do not
  infer them here. Reused shared networks must not receive an authoritative
  truncated subnet list.

### Minimum private graph, not just an account

The target is `Microsoft.CognitiveServices/accounts` (`AIServices`, S0) with a
distinct system-assigned project identity and one account model deployment,
pinned to API `2025-09-01`. Account local auth is disabled, public network access
disabled, ACL default Deny/bypass None. Project MI needs scoped **Foundry User**
(formerly Azure AI User) at the account; this is not caller/deployer authority
or an automatic project-to-vault grant.

The account PE uses group `account` with zone groups, VNet links and private DNS
for `privatelink.cognitiveservices.azure.com`, `privatelink.openai.azure.com` and
`privatelink.services.ai.azure.com`. KV uses `vault` PE/DNS; keyless Function host
storage needs blob/queue/table private paths. The supported Function path uses
Premium with a delegated outbound VNet integration subnet, DNS/routing and an
approved deployment-package path. The selected fresh hosting contract uses a
private Blob URL in `function-packages` with managed identity, **not Azure Files**;
package publication is a separate operation. Private ingress alone is
insufficient. Package existence/access and private runtime readiness still need
evidence; do not enable shared keys to bypass a failure.

The composition must include workspace-based AppInsights → LAW → native export
to an explicit EH namespace **and hub name**, plus the Function infrastructure.
Review `EventHubConnection` (or explicit `EVENT_HUB_CONNECTION_SETTING_PREFIX`),
`EVENT_HUB_NAME`, `EVENT_HUB_CONSUMER_GROUP`,
`AzureWebJobsStorage__accountName` and
`AzureWebJobsStorage__credential=managedidentity`. Do not assume the Python
`$Default` fallback selects the provisioned consumer group. Preserve separate
Function KV/EH/host-storage grants and Arize endpoint/project/space interfaces.

Fresh composition owns the AppDependencies/AppRequests/AppGenAIContent export,
`genai-correlation` container and additive container-local index role/assignment.
The existing-resource durable rollout is not a concurrent second owner.
The fresh incoming consumer and outbox are explicitly disabled in the
in-progress composition. Runtime enablement/cutover remains gated by ADR-0003
readiness; infrastructure creation is not permission to enable them.

### Secure trace association and runtime readiness

Fresh completion requires an approved AppInsights project connection, not merely
`preserveExisting` (which performs **no PUT**, even if absent). Follow the
[#139 secure contract](foundry-appinsights-tracing.md): one intended association,
reviewed sharing/PE properties, secure parameters across boundaries and an
operator-supplied immutable Key Vault deployment reference. Do not read keys,
emit secrets, or assume project MI resolves ARM secure parameters. Unavailable
private vault template resolution is a **stop**, not a public fallback.
Current `ApiKey` association semantics do not authorize account local auth;
`ProjectManagedIdentity` ingestion is a separately approved migration.

Account + project + model is **not** agent definition/version publication,
private agent runtime/state readiness or restoration of conversations/files.
Caller Entra auth and the selected Prompt Agent API/tool/state prerequisites
must be established separately. Do not automatically add Search, Cosmos DB,
ACR, hosted-agent compute/capability hosts, VM/Bastion/NAT, storage or permissions.
Surface an exact product requirement for a scoped decision first.

A Foundry PE does not make Azure Monitor private. Approved ingestion, LAW/EH
export and Arize HTTPS egress must be documented separately; no AMPLS/EH firewall
redesign is implied. If enterprise policy forbids those service paths, stop for
a reviewed network design rather than opening the environment.

### Completion evidence: still PENDING for the fresh composition

1. Offline compilation/graph tests and independent source review.
2. Separately authorized Provider validation, exact what-if, fresh deployment
   and identical redeployment with no unexpected drift.
3. Private validator and Function DNS/MI/network/package/KV access checks.
4. Separately authorized application publication and agent-version/runtime
   readiness, followed by approved synthetic source/destination evidence.

Infra is changing `validate-deployment.ps1` to **offline-only**, with no cloud
modes, and removing the obsolete broad teardown script. Use only its finalized
documented interface after implementation; do not reuse historical cloud-mode
flags or treat an offline pass as Provider/private/runtime verification.

Expected modern outputs include account/project IDs and principal IDs, model
deployment ID/alias, existing pipeline name/ID meanings, and
`foundryProjectEndpoint` =
`https://<customSubDomainName>.services.ai.azure.com/api/projects/<projectName>`
in Azure public cloud, never an ML discovery URL. Other clouds need a reviewed
endpoint/DNS contract. IDs and `privateEndpointsEnabled=true` describe topology,
not private reachability or delivery proof.

## 3. Existing resources: retain, adopt narrowly, do not recreate

- Preserve names, identities, current model tuple, agent v1, network, vaults,
  storage, export destination, runtime settings and checkpoints. Recreating a
  same-name MI changes its principal; IaC is not state/secret recovery.
- #139's `modern-foundry-tracing.bicep` only manages the child connection on an
  existing modern account/project. Preserve exact names and secure-reference
  safeguards; it has no foundation/model/network/role writes. Read the
  [runbook and dated receipts](foundry-appinsights-tracing.md) before any approved
  adoption. Account-path connection ambiguity remains UNKNOWN, not duplication
  to remove. Retain the isolated test project/connection.
- `durable-genai-rollout.bicep` remains the narrow existing-resource four-write
  operation. Preserve the full current table union, enabled state, namespace,
  explicit hub, container/role identity and imported ACKs. It does not publish
  runtime code, reset checkpoints or authorize replay. The live demo's durable
  incoming path stays enabled with checkpoints unchanged.

[#143 accepted evidence](durable-genai-correlation.md) verifies native
content-table transport and unchanged inline precedence; the missing-inline
fallback was verified using **generated fixtures**, not a native missing-inline
Foundry call. No exactly-once, complete graph, custom-correlation, source-total
or full resource-parity claim follows. Preserve quarantine for operational
trace `04f49dc16c02643b6a351a499cd4db5a`, span `b4cd6555d6c3ea92`: delivery
remains unknown; **do not resend**.

## 4. Retirement: a separate irreversible-change gate

The cleanup plan's R01–R83 scope/evidence register is unchanged. The four classic
workspaces are conditional candidates, not certified unused by empty collections
or quiet traffic. Positive consumer/asset clearance, governance signoff,
preservation/recovery acceptance and new exact-ID approval are required.
Order is project first, hub only after all consumers, exclusive PE/DNS last.
Unknown external consumers, governance diagnostics and antimalware subscriptions
stay protected.

Retain #138 evaluation/private-validation/browser assets, #139 test resources,
the independent dev telemetry stack, both protected vaults, host/checkpoint
containers, ledger/index/35 imported ACKs and quarantine. VM deallocation does
not authorize deleting VM/disks/MI/network resources. No broad teardown helper,
prefix deletion, vault purge or blanket IAM cleanup is a supported workflow.

## 5. Troubleshooting without weakening the contract

| Symptom | Bounded response |
|---|---|
| Foundry auth failure | Separate local stub config from deployed modern endpoint/deployment alias/Entra caller. Review the exact caller role; do not restore `FOUNDRY_API_KEY` as account auth or grant blanket Owner/Contributor. |
| Private endpoint/KV/package failure | Stop for approved DNS/routing/NSG/identity/vault-resolution reconciliation. Do not enable public access, shared keys or local auth. |
| EH lag or consumer mismatch | Review intended hub/group and existing checkpoint/retention evidence. No automatic capacity change, consumer reset, replay or new grant. |
| Arize rejection or ambiguous send | Retain bounded IDs/status only, use the [mapping/export contract](telemetry-mapping-export-contract.md) and durable runbook; never print payloads/secrets or blindly resend quarantine. |

This guide authorizes no cloud query, model call, deployment, permission change,
replay or deletion. Historical milestone checklists remain evidence of their
dated scope, not instructions for a new environment.
