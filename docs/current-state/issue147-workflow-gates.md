# Issue 147 — official workflow reconciliation and residual gates

**2026-10-20 approved minimal followup:** [bounded source preflight](issue147-bounded-execution.md)
records owner-selected Basic private client ingress/Microsoft-managed runtime,
exact EP1 plan/app maximum **1**, 24h validation lifetime, finite operator
retention reviews and actual safe security-plan metadata. Routine scope choices
below are superseded, not missing approval. Full-cost entitlement, immutable
runner/custody and technical/provider gates remain; prepare is incomplete.
Official validation status has not started/advanced; NOT Validated.

**2026-10-19 · preparation evidence only; no official validation completed
for this fresh foundation.** See [acceptance](fresh-foundation-acceptance.md)
and [cost ledger](issue147-cost-estimate.md), now integrated with the
[Agent prerequisites](issue147-private-agent-prerequisites.md).

**Fresh-readiness hold / NOT READY FOR EXECUTION APPROVAL.** The exact runtime is resolved:
ARM **2025-09-01**; new Prompt Agent definitions/readback **v1**;
HTTPS Responses **`<project-endpoint>/openai/v1/responses`**;
`azure-ai-projects==2.0.0`, `azure-identity==1.26.0`, `openai==2.26.0`.
These historical contract pins are not fresh functional proof. Basic private
inbound uses Microsoft-managed state and is not fully private outbound/BYO
runtime. **Correction (2026-10-20):** this does not make Standard resources
prerequisites for ADR-0004's no-tool private **client-ingress** foundation.
[Agent §1a](issue147-private-agent-prerequisites.md#1a-correction-adr-promise-authoritative-distinction-and-bounded-choices)
quotes the ADR and pinned official contract: Basic ingress/service-managed
runtime-state is supportable with an explicit scope clarification; only selecting
fully VNet-isolated Standard requires the missing BYO/injection graph and an
accepted ADR amendment. US-zone model processing is a separate residency choice,
not blanket every-service residency. Lead/QA and owner must record that real
boundary choice, not approve unproven fully private runtime. No implicit scope
selection, preview API upgrade or expansion is authorized. Actual fresh package,
runner, network/identity, capacity/provider and official-workflow gates remain.

## Provenance, not missing-reference escalation

The normal top-level `azure-prepare` and `azure-validate` skills were invoked
again on 2026-10-19. No external user-profile reference file was read. Existing
repo-contained official references were inspected in
team-root `.azure-sandbox\official-azure-skills-20261016`; their provenance pins
Microsoft's public `GitHub-Copilot-for-Azure` repository to
`d6269a3a6a9369c6a54c4fc51590f4f01892eabb`.

Only needed public official equivalent files were deliberately fetched into
the **new ignored** team-root directory
`.azure-sandbox\issue147-workflow\qa-followup-20261019`.
Current public `main` resolved to immutable commit
**`a480d4c73380e6dd77c9e1553f6523620c724edf`**.
Thirty selected files retain exact public URLs, byte lengths and SHA-256 in
`provenance.json`; the tracked [evidence index](issue147-planning-evidence.json)
preserves that manifest and its hash. Fetching public documentation requires
no Azure login, paid API, billing export or user-profile access.

Raw URL prefix:
`https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/a480d4c73380e6dd77c9e1553f6523620c724edf/plugins/azure-skills/skills/`.

The following four files are **byte-identical** at the previous and current pins:

| Relative upstream file | SHA-256 |
|---|---|
| `azure-prepare/SKILL.md` | `c77e1484d0da84591a621e19147f626a767c0a539df4c80396f3b8401fb17a36` |
| `azure-validate/SKILL.md` | `83e0f0f5e701e2b019ce2d8db9bdb35ecb244e7190ba45694e19faa19d3c719b` |
| `azure-validate/references/scripts/workflow.ps1` | `d8b7512cd91b4ec3620d6a48abc1f80179630bd26add65dc0400a34e42745ff9` |
| `azure-validate/references/recipes/scripts/validate-deployment.ps1` | `ac49678e5941f2946d8b216370e30dbd8b3451cb15652f8042bb9fad77bcb9bb` |

The exact official workflow **was already discoverable inside the repository**.
The missing external reference tree is no longer a preparation blocker and is
not an owner decision. This evidence does **not** attest the unread external
files' hashes, complete every transitive vendor reference, or execute a skill
workflow. Only the applicable branches are loaded; unselected AZD/Terraform/
container/other-service branches are not fetched.

## Existing receipts do not transfer acceptance

The preserved retirement snapshot
`.azure-sandbox\issue148-validation-prior-status-20261019.json`
contains `completedStep: UpdateStatus`; the preserved exact-workspace-retirement
receipt says it used the completed, scoped **administrative DELETE** workflow.
Those receipts and the root completed plan were not overwritten or reopened.
They are not approval/provider evidence for new resources.

The older
`.azure-sandbox\arize-fidelity-20261016-official-validation.json`
records an actual previous workflow progressing only through
`AddValidationSteps` for a **package-only existing-resource** release, blocked
because the official AZCLI core helper requires ARM build/validate/what-if.
Neither that applicability exception nor a retirement completion means this
fresh deployment passed. Fresh `infra/main.bicep` **does have** an ARM template;
there is no justification to skip its full official Bicep core validation.

## Exact applicable preparation path

Mode **MODIFY existing source / fresh cloud target**, classification synthetic
demo POC, small scale. Recipe **standalone Bicep**: existing composable Bicep
entrypoints, direct ARM control, no AZD project or new scaffolding.
AZCLI recipe shares the same core helper; it is not a shortcut.

| Official requirement | Current evidence | Remaining gate / responsible execution |
|---|---|---|
| Plan first | Issue-worktree `.azure/deployment-plan.md` pre-existed this skill refresh; root plan remains immutable | Populate the official numbered inventory/quota/policy/functional/proof sections before final plan presentation; status remains **Planning** |
| Analyze, scan, recipe, architecture | Existing source and offline contracts documented in acceptance; no code/IaC generated here | Preserve ADR-0004 graph, keyless/private controls and disabled triggers; source reuse is not new-template generation |
| Requirements and Azure context | Exact subscription supplied; minimal private-client-ingress direction/model and 24h source-validation plan approved in 2026-10-20 receipt | Technical profile/custody/full-cost exceptions in bounded followup remain; no repeated routine scope choice or `az account set`/login/default reuse |
| Full provisioning-limit inventory | Resource inventory and quantities in cost ledger; prior scoped model usage 0/300 is useful but not a whole-foundation capacity check | Infra completes plan-template §6 two-phase inventory/usage/limits for account/project/model, plan/app/storage/EH/KV/VNet/subnets/5 PEs/7 zones/7 links and role/export resources. Invoke `azure-quotas` for that authorized collector; **never retry exhausted unsupported-provider/codes cycles**, register providers, raise quota or claim a reservation |
| Policy constraints | Source tags/security contracts passed offline | Infra reconciles applicable inherited subscription/RG policies, allowed SKUs/locations, diagnostics and paid security plans using safe projected metadata; no policy exceptions/disablement |
| Research and security | Public preparation refs reconciled; Agent assessment resolves v1 Responses, exact SDK pins, no-tool semantics, Basic private-ingress compatibility and advertised model SKU | Record explicit A/B boundary per Agent §1a: clarify ADR ingress for A; accepted amendment/design needed for B's absent Standard graph. Do not mandate Standard resources for A. Fresh publication/readback, immutable runner/lock, author/consumer identities and Infra custody/network/scale/retention feasibility remain technical gates, not owner guesses |
| Functions composition references | Official selection/composition branches fetched and read | They govern **new generation**. No new template/function/IaC generation is requested. Do not `azd init -t`, regenerate this repository, or add DTS/Search/Cosmos because a generic routing keyword says “durable” |
| Functional verification before handoff | Existing offline tests prove limited contracts, not private host/API/MI paths | Record applicable local build/test evidence and explicit unavailable private checks; determine whether any remaining check requires separately authorized runtime, never substitute a stub |
| Approval and handoff | Minimal direction approved 2026-10-20; no invented numeric ceiling; exact technical prerequisites remain | Only after preparation/cost/custody/functional requirements actually complete, edit issue plan to **Ready for Validation** and invoke official `azure-validate` again; do not ask routine scope-choice questions |

Public prose does not fill missing live inventory or functional evidence.
Capacity 1 for the advertised DataZoneStandard tuple remains provider-unproven
(minimum/step null, default 10 not a minimum); exact policy/name/tuple validation,
allocatable capacity, provisioning and later separately bounded runtime success
are provider/execution gates, not owner attestations. Current-source technical
preparation must be completed first. Scope/privacy/residency, complete budget/
retained lifetime and named custody are the later genuine owner choices.
This document is a discovery/gap record, **not the completed approval-ready
official plan**. No top-level skill was allowed to access external references.
The validation invocation stopped at its **Approved-or-later prerequisite**;
it did not create or advance workflow status.

## Official validation sequence — NOT RUN for issue 147

The immutable `references/scripts/workflow.ps1` requires these completed-step
values in order:

`LoadPlan → AddValidationSteps → RunValidation → BuildVerification →
StaticRoleVerification → RecordProof → ResolveErrors → UpdateStatus`.

It writes `.azure\validate-status.json` under the supplied workspace. It does
not check proof itself; passing `-CompletedStep` is an assertion by the caller.
Never advance a step just because it prints the next instruction.

1. Once prerequisites pass, start the pinned script with the **issue worktree**
   `-WorkspacePath` and **no** `-CompletedStep`. Read the approved plan.
2. Copy Bicep recipe checklist as children of “All validation checks pass”:
   core CLI/auth/build/ARM validate/what-if, optional lint, Azure Policy.
3. Execute the pinned official `recipes\scripts\validate-deployment.ps1`,
   group scope, explicit approved RG, immutable reviewed parameters, source
   template, `-Subscription c81fda52-936e-4f14-8af4-951c0dbb92d2`.
   It runs **az version; az account show; az bicep build; az deployment group
   validate; az deployment group what-if**. It is **not** the same as the
   repository's offline-only `infra\scripts\validate-deployment.ps1`.
4. Complete applicable project build and **static** least-privilege
   service-identity/role/scope/operation review. Live role readback belongs to
   post-deployment verification, not a reason to grant roles now.
5. Record exact commands/results/timestamps/profile/source hashes in plan
   **Section 7: Validation Proof**, address errors, then and only then set
   `Validated` and acknowledge `UpdateStatus`.
6. Do **not** invoke deploy merely because validation passes. The 2026-10-20
   receipt permits the exact minimal fresh path only if full cost/runtime/
   identity/private-runner/custody gates genuinely pass and the parent grants
   the exclusive mutation lease. Those prerequisites are not met; no paid
   `azure-deploy`, repeat or private/E2E run is authorized by missing evidence.
   This is a technical stop, not a request for renewed routine scope consent.

### Known official-helper compatibility gate

Source inspection shows `az version` and `az bicep build` in the helper do not
take its `-Subscription` argument, while cloud account/deployment commands do.
The task requires **every Azure CLI process** to use repo-local
`AZURE_CONFIG_DIR` and explicit subscription. The helper also allows missing
parameters and advertises login/account-set on auth failure. Those defaults
are **not permitted here**.

Therefore **do not execute that unadapted helper now**. At the authorized
validation handoff, Infra must document/review a narrowly scoped invocation
adapter that preserves the official five checks and exit/result proof, binds
every Azure CLI subprocess to explicit subscription/config, rejects missing/
unapproved parameter files, and fails closed without login/account-set,
extension installation or provider registration. Record adapter hash/diff
against this pin; do not label an improvised offline replacement “official
workflow passed”. Check installed CLI syntax first without cloud mutation.
Neither a parser check nor a no-argument workflow-script start completes this
compatibility gate.

All live ARM validation/what-if, provisioning, uploads, trigger sync/enablement,
private runtime checks, model calls and repeat/E2E acceptance are **NOT RUN**.
No approvals, mutation lease, root plan/status or completed receipt changed.
