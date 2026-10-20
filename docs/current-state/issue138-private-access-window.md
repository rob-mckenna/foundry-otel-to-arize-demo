# #138 — approved direction, cost model and human private-access handoff

**CURRENT-STATE retained assets; 2026-10-20. No new live acceptance asserted.**
Lead owns #138; issue stays OPEN, PR #150 stays unmerged.

## Authority and decision

Primary owner approval: `2026-10-20T04:37:07.301Z`, requester Rob McKenna,
"Consider all of them approved, just move forward."
Root receipt `.azure-sandbox\squad-three-issues-proceed-approval-20261020T043707Z.json`,
SHA256 **C971F23D46D9C7033102A2F503EABA83E0E08755ADE37E82C43FD888A8C1CC5E**,
matches the supplied binding. #138 scope is cost reconciliation and existing
Windows/Developer Bastion acceptance with protection preserved. The original
$53.42 target is **no longer the binding approval gate**. No numeric ceiling
was supplied; revised necessary cost direction is not unlimited spending.

[ADR-0005](../adr/0005-reconcile-retained-private-evaluation-and-browser-assets.md)
remains **Proposed for affected-track agreement**, not because owner consent is
missing. The [existing ADR process](../adr/README.md) defines Accepted as agreed
by affected tracks; team governance also requires consensus. Lead records the
owner-approved retention/minimal-access direction now. Infra's configuration/cost
report and existing Agent/QA evidence are evidence, not statements of ADR assent.
Only explicit Infra/Agent/QA concurrence on this narrowed retained-resource scope
can complete that status transition. No new issue/process or fabricated agreement.
Human access, provider registration support and runtime acceptance remain separate
even after eventual ADR acceptance. No new registration/runtime authority here.

## Conservative cost model — all terms exposed

Use the existing [itemization and public-source bindings](private-storage-and-windows-jumpbox.md).
USD public retail planning, not invoice/contract verification. No paid API or
billing export. Retained resources stay protected; no savings assumed from
recreation, disabling Defender or removing NAT.

For one planning month, define:

- `T`: retained network-resource hours (730 for the monthly illustration).
- `H`: Windows allocated compute hours, not just time the browser is open.
- `B`: P2 billable hours, including allocated Stopped. Do not assume `B=H`;
  include transitions and verify terminal deallocation.
- `M`: actual P2 workload units per server; **unknown**. VM metadata says inherited
  Standard/P2/no trial. Subscription AgentlessVmScanning is enabled; VM-scoped
  extensions do not establish effective guest health or every billable entitlement.
- `S`: retained Hot LRS GB-months. Historical 1 GB is an assumption, **not a cap**.
- `G`: scanned GB/month. Configured on-upload scan setting is 5000 GB/month;
  sensitive-data discovery is enabled and subscription settings inherited.
  This setting is neither a total-storage cap nor a guaranteed dollar hard stop.
- `N`: NAT-processed GB; `Q`: chargeable directional PE-processed GB.
- `F_storage(T)`: actual inherited Storage Defender/account protection charge.
  Calculator basis `0.0134*T`; use **$10/month allowance** rather than $9.782
  for the 730-hour conservative illustration, not a verified contractual maximum.
- `U`: transactions, disk operations, DNS queries, bandwidth/egress, monitoring,
  scan-side operations, discovery/protection overages and other applicable charges.
  No free tier, promotion, discount, shared-resource credit or double-counted
  subscription protection charge is assumed.

```text
C = 5.888                       # one actual retained S10 HDD; full monthly charge
  + (0.01 + 0.045 + 0.005) * T  # one Blob PE + retained NAT + static egress IPv4
  + 0.0184 * S                  # Hot LRS first-tier planning rate
  + F_storage(T)
  + 0.188 * H                   # Windows D2s_v5, not Linux/Spot
  + 0.006849 * M * B            # P2 workload-unit meter, not one unit per VM
  + 0.045 * N + 0.01 * Q + 0.15 * G + U
```

Existing Developer Bastion is $0 incremental. Disk stays charged while VM is
deallocated. NAT/IPv4/PE continue charging independently of VM power; zero VM
hours does not mean zero lifetime cost. PE rates are explicitly dated carry-forward
prices, not freshly verified. Additional shared environment, Arize and future
inference costs are outside this **ancillary-only** model, not claimed free.

At `T=730, S=1, F_storage=10`, the fixed planning portion is **$59.7064**.
Calculator variant `F_storage=9.782` is **$59.4884**, not a full quote.
At the full configured scanning setting, scanning alone adds **$750**, giving
**$809.7064 + 0.188H + 0.006849MB + 0.045N + 0.01Q + U**.
This is a scanning sensitivity, **not** a hard upper bound: scanning enforcement,
storage volumes, operation counts and `U` have no evidenced finite total cap.

### P2 dollars/server and operating sensitivity

Public calculator indicates **$0.02/server-hour**, or **$14.60/server for 730
billable hours**, hence indicative Windows+P2 **$0.208/hour**.
Retail P2 meter is **$0.006849/workload-unit-hour**; claimed multipliers must be
compared to the actual inherited plan/contract, not reverse-engineered from a
rounded calculator rate. The following are **sensitivity scenarios, not configured
or accepted multipliers**:

| Hypothetical M | P2/server at B=730 | P2 at B=0.5 | Windows H=0.5 plus P2 B=0.5 |
|---:|---:|---:|---:|
| 1 | $4.99977 | $0.0034245 | $0.0974245 |
| 3 | $14.99931 | $0.0102735 | $0.1042735 |
| 10 | $49.99770 | $0.0342450 | $0.1282450 |

Calculator half-hour combined indication is **$0.104**; it is not an accepted
per-server contract or bound. At `H=B=20`, M=3 sensitivity gives
**$63.87734** fixed+compute+P2 before traffic/scanning/`U`; calculator variant
gives the historical **$63.6484** using the lower $59.4884 base.
Neither statement turns M=3 into an observed fact. Deallocated periods have
zero indicated P2 power-state billing, not an invoice proof.

**Lifetime:** proposed access session is at most 30 minutes including transitions,
with deallocation beginning by minute 25. That bounds scheduled allocated time,
not provider completion or billing granularity. Existing resources remain retained:
no end-of-retention date or deletion authority has been established. For `L`
retained months the conservative fixed illustration is `59.7064*L`, with all
volume/traffic/protection terms added per month and VM billing separately.
No finite lifetime implies no finite unconditional lifetime total.

**Exact remaining cost exception:** a finite executable bound cannot honestly be
closed from these projected receipts: actual P2 conversion/coverage and Storage
Defender overage basis, stored GB/operation/traffic allowance and retention
end/review date remain unverified/unbounded. Do not invent a numeric cap or call
$809.7064 an all-in maximum. The model is complete and conservative about missing
terms; a finite cost-bound gate for VM start is **NOT PASS**. Retained baseline
spend already exists; leaving deallocated avoids incremental compute, not all cost.

## Actual human evidence, not a guessed identity

Rob McKenna is the named requester/owner. No existing evidence establishes that
Rob is the actual Windows operator, credential custodian, target-tenant user or
currently available human. Git/GitHub authorship is not Entra identity evidence.

Projected receipt root `.azure-sandbox\jumpbox-human-access.json`,
SHA256 **53F17864A7CEA35DBBB1AFBF62D8899857D863A6A88847B7ED9886F93A13107A**,
finished `2026-10-14T13:37:32Z`, reports:

- Requester confirmed portal uses the same native **User** account.
- Graph resolved only a home-tenant object; target-tenant object **null**.
- Target-tenant metadata required MFA (`AADSTS50076`, InteractionRequired).
- Target-tenant effective assignments and interactive authentication **not verified**.
- No grants, login attempts, persistent account switch or alternate identity.
- Vault is private; RBAC alone does not make credential retrieval reachable.

This is dated evidence of a precise unresolved identity/access prerequisite,
not permission to reauthenticate or grant roles. No password, secret version,
auth cache or CLI profile was read. Human must attest their actual target-tenant
identity/access and custody privately, without supplying a credential value.
Agent cannot perform or claim human Windows login/navigation.

## Short explicit window and official lifecycle handoff

Prepared at **2026-10-20T04:56Z**, after #148 lease release
**2026-10-20T04:49:29Z** (definitive permission stop, zero DELETE).
Candidate window: **2026-10-20 05:30–06:00 UTC =
2026-10-20 01:30–02:00 Eastern Daylight Time (UTC−04:00)**.
Not activated; human availability is missing. No automatic rollover, recurrence,
start or scheduled job. Window expiration requires a new dated window, not renewed
general owner consent. Do not overlap a later #147 mutation lease.

Preserve **Enabled/1900/Eastern Standard Time** shutdown. Only the activated
30-minute window would be the documented after-hours exception; never edit,
disable or reschedule that protection. Start deallocation by **05:55 UTC** and
verify **PowerState/deallocated** by **06:00 UTC**, including on any failure.
No human availability means **skip VM start**, not start and wait for a human.

New worktree-local `.azure\deployment-plan.md` records the approved direction and
blocked prerequisites; root's closed plan stays untouched. Official references
are already repository-contained at root
`.azure-sandbox\official-azure-skills-20261016`, with paths/hashes in
`official-azure-skills-20261016-provenance.json`, pinned official upstream
`microsoft/GitHub-Copilot-for-Azure` commit
**d6269a3a6a9369c6a54c4fc51590f4f01892eabb**.
Read prepare SKILL, validate SKILL/workflow/AZCLI recipe and deploy
SKILL/pre-deploy checklist/AZCLI recipe. Verify hashes before use.

Official lifecycle is **prepare → validate → deploy → verify**. Existing AZCLI
examples deploy infrastructure; they are **not** permission to redeploy
`infra/main.bicep`. Its core helper includes unscoped CLI version/auth/build
commands, so do not run it unchanged under this step's every-process subscription
restriction. Infra must document the applicable retained power-only checks/N/A
reasons and scoped command mapping, then complete the real official workflow
with recorded proof. Do not blindly advance `-CompletedStep` or manually set
Validated. This is a technical workflow mapping, not missing general owner consent.

### Executable checklist (PowerShell; commands not a claim of execution)

After preparation prerequisites actually pass and the plan is Ready for Validation,
from the worktree load the **official validation driver only**; it is local and
does not start a VM. Do not invoke it now with the blocked preparation status.
Perform each returned action before acknowledging it:

```powershell
$root = 'C:\repos\foundry-otel-to-arize-demo'
$worktree = Join-Path $root '.worktrees\issue138-ancillary'
$official = Join-Path $root '.azure-sandbox\official-azure-skills-20261016'
$env:AZURE_CONFIG_DIR = Join-Path $root '.azure-config'
& "$official\azure-validate\references\scripts\workflow.ps1" -WorkspacePath $worktree
# Preparation is currently blocked: do not run the driver until those gates pass.
# Never use -CompletedStep to claim work that was not actually done.
```

Before an operator may execute the start line below, **all** boxes must have real
proof in the new local plan and official workflow:

- [ ] Infra/Agent/QA actually concur with ADR-0005 retained-resource decision.
- [ ] Finite cost-bound inputs, billing interpretation and retained lifetime resolved.
- [ ] Named human operator AND custodian, target-tenant/project access and private
      credential retrieval route established; no values copied into artifacts.
- [ ] That human explicitly confirms synchronous availability for this exact window.
- [ ] Coordinator's current #138 exclusive lease remains valid; no #147/#148 mutator.
- [ ] Official scoped prepare/validate/deploy gates and actual validation proof pass.

Only after those prerequisites, within the activated window, use existing
Developer Bastion → Windows → Edge `https://ai.azure.com` → existing authorized
project. Human signs in themselves. Record login/navigation outcome and timestamps
only, not screen content. Do not open pending-upload, register, upload, run prompts,
evaluate, replay unknown traces or change any grants/protections.

Power commands for the officially gated human/operator handoff (not run here):

```powershell
$env:AZURE_CONFIG_DIR = 'C:\repos\foundry-otel-to-arize-demo\.azure-config'
$sub = 'c81fda52-936e-4f14-8af4-951c0dbb92d2'
$rg = 'fotoa-demo-rg'
$vm = 'fotoa-demo-wjump-eastus2'
# Do NOT uncomment until every checklist item and official gate has actual proof.
# az vm start --resource-group $rg --name $vm --subscription $sub --only-show-errors
# Human performs navigation above; no AI login or data-plane calls.
# Completion/failure cleanup, required if any later authorized start occurs:
az vm deallocate --resource-group $rg --name $vm --subscription $sub --only-show-errors
if ($LASTEXITCODE -ne 0) { throw 'Deallocation failed; exact VM needs operator attention.' }
az vm get-instance-view --resource-group $rg --name $vm --subscription $sub `
  --query "instanceView.statuses[?starts_with(code, 'PowerState/')].code" -o json --only-show-errors
if ($LASTEXITCODE -ne 0) { throw 'Terminal power-state verification failed.' }
# Require the returned state to be PowerState/deallocated; never merely Stopped.
```

**Exact human exception/handoff:** an actual human must supply their operator and
custodian designation, privately resolve the target-tenant MFA/access and private
credential retrieval prerequisite, and confirm live presence for the dated
window. That evidence is absent; no generic approval request is outstanding.
Do not start on the strength of the owner's broad approval alone.

## Actual operations in this bounded step

Two Azure control-plane reads only, existing auth, repository-local
AZURE_CONFIG_DIR and explicit subscription on each process:

| UTC start → finish | Command scope | Exit / safe metadata |
|---|---|---|
| 04:55:58.5013616 → 04:56:08.8130959 | `az vm get-instance-view` on retained VM | 0; **PowerState/deallocated** |
| 04:56:08.9116397 → 04:56:21.7595273 | `az resource show`, shutdown schedule, API 2018-09-15 | 0; **Enabled / 1900 / Eastern Standard Time** |

Date for both rows: 2026-10-20. No VM start, deallocate, deployment, login,
registration, paid API, billing export or cloud mutation. No fresh effective-route,
guest DNS/TLS, protection health or human navigation claim. Old probe remains
CONSUMED_DO_NOT_RETRY; old 3/3 budget CLOSED. All protected assets and completed
receipts remain unchanged. No #148 operation/retry or #147 mutation.
