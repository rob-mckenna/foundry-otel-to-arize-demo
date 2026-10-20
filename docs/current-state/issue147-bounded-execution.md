# Issue 147 — bounded Infra source preflight

**2026-10-20. QA remains primary owner; #147 OPEN / PR #151 unmerged.
Source controls implemented; fresh provider/private/repeat/E2E acceptance NOT RUN.**

Owner's `04:37:07.301Z` proceed receipt selects **no-tool Basic, private client
ingress, Microsoft-managed runtime/state**. This is the ADR-0004 foundation's
ingress interpretation, not fully VNet-isolated Standard, a new architecture
decision, or permission to add Search/Cosmos. US-zone model processing does not
certify telemetry, Arize or every service's residency. The exact tuple remains
`OpenAI/gpt-5-mini/2025-08-07/eastus2/DataZoneStandard/capacity 1/NoAutoUpgrade`.
No fallback is allowed. Historical existing private-VM v1 success is not fresh proof.

The approval SHA-256 and safe evidence are in
[the execution index](issue147-bounded-execution.json). The receipt has **no
numeric spending ceiling**; neither USD25 nor USD60 is invented as one.

## 1. EP1 scale proof and implemented controls

`infra/main.bicep` exposes `functionMaximumInstances=1`, constrained by
`@allowed([1])`; both reusable example profiles explicitly select 1.
The offline prepared-profile gate requires an actual integer 1 (not true,
zero/unbounded, string `"1"` or a higher value). The Function module sets:

| Resource / property (API 2023-12-01) | Value |
|---|---:|
| Plan `sku.capacity` | 1 |
| Plan `properties.maximumElasticWorkerCount` | 1 |
| App `siteConfig.functionAppScaleLimit` | 1 |
| App `siteConfig.minimumElasticInstanceCount` | 1 |
| App `siteConfig.preWarmedInstanceCount` | 1 |

These values are not derived from a price assumption:

- [Plan ARM schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/serverfarms)
  defines maximumElasticWorkerCount as the maximum total workers; it is an int.
- [App ARM schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites)
  applies functionAppScaleLimit to Consumption/**Elastic Premium**, minimum 0;
  minimumElasticInstanceCount allows 0–20; preWarmedInstanceCount allows 0–10.
- [Pinned official CLI implementation](https://github.com/Azure/azure-cli/blob/9f94e6ba60714a817efd09744dea81105eba2bf6/src/azure-cli/azure/cli/command_modules/appservice/custom.py)
  `update_functionapp_app_service_plan` accepts max-burst 0–20 for EP and assigns
  maximumElasticWorkerCount. Thus **1 is supported by the documented/source
  contract**; 20 is not a required minimum or a justified demo default.
- [Premium scaling/billing guidance](https://learn.microsoft.com/en-us/azure/azure-functions/functions-premium-plan)
  states at least one active billed instance, default prewarmed target 1, and
  “No instances are prewarmed or activated beyond the maximum.” The prewarmed
  target is inside the app ceiling, **not a second permanently allocated worker**.
  One always-ready app/one plan; no second app or slot is part of this profile.

The three official pages and immutable CLI source were saved in the ignored
worktree `.azure-sandbox\issue147-bounded` with exact SHA-256 provenance.
Public GitHub CLI pin resolution initially received 403 SAML; unauthenticated
public GitHub HTTPS resolved the same public branch without changing auth.

**Limit of proof:** Bicep compilation and public constraints are not provider
acceptance. Require fresh ARM validate/what-if, deployment and projected plan/
app scale readback before runtime. Never increase 1 automatically on rejection.
Scale settings are not an Azure monetary hard cap or a guarantee against
transient platform replacement allocations. The `/26` example is not certified
against Premium's documented 100-available-address guidance; final topology
review is still required. No CIDR, network, live plan or protection was changed.

## 2. Validation lifetime and retained-state/security tail

**T0 = first billable allocation**, not first request. Validation/publication/
repeat/one synthetic request must finish by **T0+24h**; at that deadline stop
initiating acceptance operations. No TTL/tag pretends to stop Azure billing.
QA records T0/deadline and the executor's operation receipts before paid work.
One new synthetic request only; no tools/evaluation, ≤1,024 input tokens,
max_output_tokens 1,024 including reasoning, zero client retries; timeout,
429 or ambiguous delivery means STOP, not a second request.

The retained-state operator plan is finite, **not automatic destructive
authorization**:

| Deadline / owner | Non-destructive obligation |
|---|---|
| T0+24h / QA + Infra | Close acceptance window; reconcile safe resource IDs, cost/tail and evidence hashes. Keep both consumers disabled unless a separately authorized cutover succeeded. Do not stop production/shared services. |
| Within 7 days after validation deadline / QA + Infra + Telemetry | Review fresh-only retained artifacts and configuration metadata. Protect package versions, host/checkpoints, ledger/index/ACK/outbox/quarantine. Record unresolved/ambiguous work without reading payloads or replaying it. |
| Within 30 days after validation deadline / QA + resource/contract custodians | Complete an exact-ID retention/disposition proposal with state/recovery dependencies and dated cost reconciliation. Separately authorized retirement or an explicitly dated/repriced retention extension is required; missed deadline is an execution exception, never implied deletion permission. |

EH message retention remains 1 day; LAW remains 30 days (table-specific
retention may differ); KV soft delete/purge protection remains 90 days.
Storage has **no automatic durable-state expiry/lifecycle deletion**.
Keep malware scanning/Defender/governance controls. No policy removal, purge,
existing-data deletion, IAM cleanup or whole-RG teardown is authorized.
Stopping a Function or its triggers does not deallocate EP1, EH TU or PEs.
An operator plan is not a guaranteed bill cutoff; without actual authorized
retirement or a funded extension the residual bill remains open.

## 3. Cost reconciliation and exact execution exceptions

The [existing 39-meter ledger](issue147-cost-estimate.md) remains reproducible:
**$15.504880 USD** conditional 24h subtotal at N=1, including its conditional
Defender/malware allowances and one bounded model-call envelope. The old N=20/
100 scenarios are stress sensitivities, **not selectable source profiles**.
The **$235.0028** further-30-day idle reserve includes the ledger's selected
security/capacity/rounding/connection assumptions, not a full entitlement quote.
Combined conditional day-plus-tail reserve is **$250.507680** before G/L/R,
continuing ingestion/operations/scans, overages, contract and tax effects.
Replacement allocations are not priced as impossible. No all-in ceiling exists.

One narrow read-only Azure operation ran **05:09:18.8769322Z–
05:09:32.0186456Z**, exit 0, explicit subscription and repo-local configuration:

```powershell
$env:AZURE_CONFIG_DIR = 'C:\repos\foundry-otel-to-arize-demo\.azure-config'
az security pricing list --subscription c81fda52-936e-4f14-8af4-951c0dbb92d2 --query "value[?name=='StorageAccounts' || name=='KeyVaults' || name=='AppServices' || name=='Arm' || name=='CloudPosture' || name=='AI'].{name:name,tier:pricingTier,subPlan:subPlan,enforce:enforce,extensions:extensions[].{name:name,isEnabled:isEnabled}}" --only-show-errors -o json
```

Result: Standard AppServices; StorageAccounts **DefenderForStorageV2** with
OnUploadMalwareScanning/SensitiveDataDiscovery enabled; KeyVaults **PerKeyVault**;
Arm **PerSubscription**; CloudPosture Standard; AI Standard, AIPromptEvidence
and AIPromptSharingWithPurview enabled, AIModelScanner disabled. This was
configuration metadata only; no billing query, prompt evidence or state read.
Do not disable/change these extensions to make a test cheaper or less visible.
Use synthetic content only. Subscription tier is no per-resource entitlement
attestation; new-resource/policy application and diagnostic destinations remain
unverified.

| Exact missing fact / artifact | Why it cannot be filled by this approval or public prices |
|---|---|
| **G:** actual applicability/rates of DefenderForStorageV2, PerKeyVault, PerSubscription, AI and CloudPosture, inherited diagnostics and retained usage | Safe tier GET succeeds but carries no customer meter/rate/minimum/included entitlement. The ledger's generic node allowances do not establish these precise subplans or AI/CSPM incremental allocation. Billing APIs/exports are prohibited; need sanitized existing contract/entitlement attestation, not trial/zero-cost inference. |
| **L:** Arize destination contract, ingest/retention/minimum terms and authorized workspace/custodian attestation | No applicable workspace contract or allowance exists in this packet; Azure metadata and public retail meters cannot price a third-party negotiated entitlement. No secret retrieval or paid API may be used to discover it. |
| **R:** an already-authorized private executor/author/consumer/publisher, complete immutable dependency/wheel lock and ZIP custody manifest, Basic managed-state retention/recovery/charging terms | Historical API/SDK pins and existing VM evidence supply neither a fresh authorized identity/path nor an immutable runner/artifact. No new VM/start, grant, auth-cache inspection, secret access, registration or model request may substitute. Build/runner entitlement and service-managed state tail cannot be assigned zero. |
| Fresh exact provider/model/network gates | Capacity 1 minimum/step remain null in prior catalog metadata; no provider acceptance/reservation. Final reviewed CIDRs, identity/custody reference attestations and complete executable parameter profile are absent. Examples remain deliberately non-executable. |

These are **technical/contract evidence exceptions**, not a request to choose
Basic vs Standard again or approve USD25/USD60. Complete sanctioned source
artifacts offline; stop the paid step. No provider validate/what-if, create/
repeat, upload, agent publication, inference, VM start, delete or IAM write ran.
No cloud-mutation lease was acquired. #138/#148 released leases and their
definitive permission stops remain untouched.

## 4. Reproducible preflight and official handoff

The worktree `.azure\deployment-plan.md` was updated before the metadata GET.
Repo-contained official prepare/validate references remain pinned to
`a480d4c73380e6dd77c9e1553f6523620c724edf`; phase-1 inventory/capacity,
custody/functional and cost prerequisites remain incomplete. Consequently the
official validate skill's Approved-or-later/Ready-for-Validation gate is **not
passed**. Do not start/advance workflow status or mark Validated. The official
helper's every-subprocess explicit-context adapter is still required before
its five checks; offline compile is not a substitute.

From the issue worktree:

```powershell
$env:BICEP_CLI = 'C:\repos\foundry-otel-to-arize-demo\.azure-config\bin\bicep.exe'
python -B -m unittest discover -s infra\scripts -p 'test_modern*.py' -v
.\infra\scripts\validate-deployment.ps1
python -B -m unittest discover -s tests\readiness -p 'test_issue147_planning.py' -v
.\tests\readiness\check-issue147-docs.ps1
```

First two commands **PASS**: 28 compiled/profile/tracing tests; three entrypoints
compile (two unchanged BCP334 warnings at durable rollout 87/92). New tests
verify top-level→module→plan/app bound propagation, explicit warm settings and
reject omitted/noninteger/zero/higher scale values. Remaining two commands also
**PASS**: five readiness/pricing/provenance/link tests; 17 PowerShell examples
and two pinned official scripts parse (none executed). Naming passes for eight
modules; mapping/export/pipeline regression command below **PASS: 260 tests**.

```powershell
.\infra\scripts\validate-naming.ps1
python -B -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests tests\telemetry-mapping tests\export\test_otlp_export_conformance.py
git diff --check
```

`git diff --check` also passed. No packages were installed or restored.
Both `python -B infra\scripts\validate-modern-foundation.py --parameters
infra\main.parameters.json` and the same command with
`infra\main.parameters.private-endpoint.json` returned **expected exit 1**:
the reusable examples remain intentionally incomplete, not paid execution profiles.

Publication/readback and invocation retain the exact **v1** project API and
`azure-ai-projects==2.0.0` / `azure-identity==1.26.0` / `openai==2.26.0`.
The [Agent handoff commands](issue147-private-agent-prerequisites.md#5-later-gated-verification-commands--not-executed)
are explicit, parsed, **NOT fresh runtime-tested**. Publication must use a
reviewed zero-tool definition and pinned version, compare definition hash,
never “latest”; private ZIP upload/fetch uses authorized MI and immutable blob
SHA-256, no SAS/shared-key/public-SCM fallback. Complete dependency lock,
publisher/private runner identities and secure KV **reference** attestations
must precede official prepare → validate → deploy. No credentials or raw bodies
belong in acceptance proof.
