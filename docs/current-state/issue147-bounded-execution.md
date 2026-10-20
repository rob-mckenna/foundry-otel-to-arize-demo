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

## Existing-target native request — 2026-10-20 06:58Z

Separate approved existing-target lease SHA256
`C7754054BBBA38B5A84CB7CB9971B8144F169505178BD48504452AD00A46931F`;
exclusive Infra executor `6f62330e-9039-4a38-a51f-87c695b55c9d`, custodian
Squad QA. **Existing GlobalStandard/capacity 5 only**: no fresh deployment,
DataZone/capacity-1 completion or US-zone processing assertion.

Fresh VM identity/state/permissions/governance and exact model tuple passed.
Guest accepted source, dependency lock, actual wheels/interpreter/environment
hashes matched without installation. Private DNS resolved `10.20.0.14`, TLSv1.3;
existing managed-identity SDK GET retrieved `PromptAgentDefinition`, prompt v1,
zero tools and exact model alias. Canonical retrieved definition SHA256
`69ccd005e568a7429cb23ccd198ec2149981d660491c534d04465166efcf9e97`.
Immutable preflight at `06:58:38.800394Z` binds definition/source/environment/
lease and request before invocation.

Exactly one accepted built-in synthetic Responses request completed, outcome
`06:58:43.804231Z`, run/request UUID
`d2c13606-e59e-4143-8b04-9e7dc7fcf471`, response ID
`resp_01a5508925f97685006ad711210f688197aa32beed7db906cb`.
Actual input/output/total usage: **104 / 34 / 138**. Output cap 1024 includes
reasoning; zero client/SDK/HTTP retries and no tools. Durable per-run and
per-authorization intents precede authentication; old receipts untouched.

Client-only trace `89d6a1200019ef6d6a77eba778e11f07`,
span `5db9efa4b4c938f6`, initialized by a standard OTel SDK provider with no
exporters. **These IDs and the successful client receipt are not native graph
or end-to-end proof.** Independent Insights/LAW → Event Hub → Function → Arize
presence/content-field/token/correlation verification remains pending.

One START `06:57:22.285537Z`; immediate finally deallocate submitted
`06:59:12.271628Z`. Independent DEALLOCATED/release `07:00:05.348617Z`;
second-process confirmation `07:00:50.400324Z`. No VM held for telemetry.
New sanitized evidence only, under TEAM_ROOT
`.azure-sandbox\issue147-native-6f62330e-9039-4a38-a51f-87c695b55c9d-20261020`:
`exclusive-custody.json`, `start-submission-guard.json`, `preflight.json`,
`outcome.json`, `ledger-*.json` (new guest paths/hashes), power/release receipts,
`verified-summary.json`, `evidence-sha256-final.json`.
Guest current-run copies persist under the approved root's
`native-6f62330e-20261020`; canonical immutable intents/outcome remain in
`.foundry-live-receipts`. No second model call, registration or publication.

Validation: `python .azure-sandbox\issue147-native-6f62330e-9039-4a38-a51f-87c695b55c9d-20261020\execute.py --prepare-test`
**passed** (syntax, supported dual-shape power polling, timeout and finally
restoration tests); same command with `--execute` **passed** the scoped live
operation/restoration. This is not a full deployment or native E2E test.

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

## 5. Final canonical private-runner bootstrap — 2026-10-20

**Existing-runner non-inference readiness PASS; fresh foundation and native E2E
acceptance remain NOT RUN. #147 stays OPEN, owned by QA; PR #151 unmerged.**
This later, separately leased administrative slice supersedes earlier
no-VM-start statements only for the exact existing Linux runner below.

Final cycle 3 executor `59e5093d-6f0b-4196-ad19-6437d954736b` replaced
`edb98808-1c0a-47c7-8131-8d7e1abe564a`; Squad QA retained ledger custody.
Physical lease SHA256:
`F40184EAB3FEA00807C326C56000A620108D7B3F5775F8740B4FFD08F900B7BC`.
Safe immutable command/UTC/exit receipts are under repository-root
`.azure-sandbox\issue147-executor-59e5093d-20261020`.

| Operation / observed fact | Result |
|---|---|
| Exact ZIP/base64 round trip, member extraction and accepted Git blob comparison before START | PASS, canonical commit `5783af8c7dc3b7605d0c816a7d51fa212f4cf912` |
| Actual executor wrapper tests | PASS, 3 cases: bootstrap failure finally restoration; ambiguous START never replayed; baseline denial never allocates |
| Supported bounded `vm get-instance-view` polling and restoration smoke | PASS; dual direct/nested statuses projection |
| Fresh VM/MI/OS, permissions, locks, extensions, NIC and policy metadata | PASS; Linux, expected MI, no public NIC, no locks or returned policy assignments |
| ONE final START submission | 06:38:54.319914Z, CLI exit 0; RUNNING observed |
| RunShellScript bootstrap | 06:39:28.604476Z–06:41:35.876189Z, CLI exit 0 **and guest completion marker observed** |
| Guest source verification/import | Exact canonical hashes below; imported source from accepted checkout, real `.git` root; existing ledgers untouched |
| Python/dependencies | Python 3.10.12; 53 resolved packages, wheel build/install and `pip check` PASS |
| Offline help, dry-run, mocked caller smoke | PASS, zero live submissions; post-test OTel console-exporter closed-file warning retained, not hidden |
| Private DNS / normal certificate-validated TLS | `10.20.0.14`, all resolved addresses private; TLSv1.3 |
| Existing MI SDK `agents.get_version` metadata GET | HTTP 200, historical v1 prompt agent, zero tools; no inference |
| Finally deallocation submitted | 06:41:35.876189Z, CLI exit 0 |
| Independent final power / lease release | DEALLOCATED 06:42:34.267238Z; released 06:42:34.271212Z |
| Second-process independent read | DEALLOCATED 06:43:10.862919Z |

The actual final allocation interval was under four minutes. Restoration was
required to begin by 06:59:54.319914Z and finish by 07:04:54.319914Z,
both earlier than the lease's absolute 07:15Z limit. No cycle 4 is authorized.

Observed guest artifact/environment SHA256 values:

| Artifact | SHA256 |
|---|---|
| Transported ZIP | `8f2f51676d4e3e267e7cd703ab5363e6e1e4c9cb5356caeb3728f835f7649da0` |
| Canonical LF module, also verified after actual import | `455b59932073895d0daeba5320fd06b01172b4295e90ac5cd372e0a3a6a603a7` |
| Interpreter executable | `a2f33a6e006989270f4340528eb61f8f97366e00a5d1b602ac8672ea44fc56ae` |
| Interpreter metadata | `7e78e26f896cae0dde67f45dfddc6035903e9b4f35096d4a3198ea2a09d3f377` |
| Actual resolved dependency lock | `5135f3639712b67294701addbaed36c103287c0a245e0e5fd09d46ff1b80716a` |
| Wheel hash manifest | `a5739f06e9b3b3f8ae60e97b9c16c0ea77c5c9b36d93a30788f09c905e68db90` |
| Built prompt-agent wheel | `8fa335efe9c388376e0f4ba4c05a2bbea43bc5e83ee2c919178aa11dab72839a` |
| Environment (lock + interpreter metadata + wheel manifest) | `1443f5bc8df6faa760278a1c0f09ddb3e86073ee7460a4b0fc9e1093229172f3` |

The Windows CRLF hash was local provenance only, not the portable Linux binding.
No guest normalization/hash relaxation occurred. See the caller README's
command-scoped LF archive recipe. Prior cycle 2 emitted no actual guest digest;
these newly observed hashes do not retroactively establish its guest digest.

Remaining acceptance blockers are **not bootstrap failures**: fresh exact
DataZoneStandard/capacity-1 model/provider/network/profile approval and deployment,
fresh no-tool publication/readback and definition hash, approved once-only
envelope and private artifact/custody handoff, G/L/managed-state cost terms,
and native service → App Insights → Arize correlation/usage acceptance.
The existing historical v1 references `fotoa-demo-gpt5mini-eastus2`
(historical GlobalStandard/capacity 5), not the still-undeployed fresh target.
No model/Responses/evaluation/registration/publication request, resource/grant,
security/network/shutdown change, ledger reset or replay was performed.
