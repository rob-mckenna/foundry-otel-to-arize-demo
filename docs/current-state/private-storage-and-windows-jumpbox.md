# Retained private evaluation storage and Windows access — #138

**CURRENT-STATE ancillary resources; metadata reconciled 2026-10-19 Eastern.
ADR agreement, human navigation and registration/evaluation readiness are separate
and incomplete. No deployment or running window is authorized by this document.**

Owner: Lead (Architect / Tech Lead), actual `squad:lead`.
Related: [#138](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/138),
[ADR-0005](../adr/0005-reconcile-retained-private-evaluation-and-browser-assets.md).
This replaces the absent historical runbook link with a bounded reconciliation,
not a recreation recipe. Root `.azure/deployment-plan.md` remains closed history
and untouched. No deployment is being prepared in this worktree.

## Evidence hierarchy and correction

1. The original issue's Proposed status is retained for **cross-track agreement**,
   not interpreted as absence of cloud resources.
2. `.azure-sandbox\storage-resume-outcome.json` records storage deployment
   `fotoa-demo-eval-storage-stage-a` Succeeded, private endpoint/DNS, project AAD
   connection and scoped project MI Blob role. Its Windows NOT_PROVISIONED and
   registration NOT_EXECUTED fields are earlier, superseded stage facts.
3. `.azure-sandbox\windows-final-outcome.json`, finished
   `2026-10-14T07:01:36.963519+00:00`, records prerequisite and Windows deployments
   Succeeded, browser/private TLS/RDP prerequisites PASS, human login NOT_VERIFIED,
   registration CONSUMED_DO_NOT_RETRY and terminal deallocation.
4. The later read-only reconciliation confirms dataset GET 404 and preserved
   receipt/ledgers. Dataset absence does **not** establish no pending-upload state.
5. Today's initial seven successful reads and Infra's subsequent 27 recorded
   metadata requests confirm retained configuration, not replay historical runtime
   checks. Two of those NIC effective-view requests failed (exit 1); neither
   was retried and neither caused a VM start.

No ancillary ADR existed in current main before ADR-0005. Historical mentions of
Proposed ADR-0003 do not modify today's durable-correlation ADR-0003. Modern-only
foundation ADR-0004 and completed classic retirement #149 are independent;
do not reopen deletion guards or recreate classic workspaces.

### Present metadata (all seven commands exit 0)

Every Azure CLI process used existing auth,
`AZURE_CONFIG_DIR=C:\repos\foundry-otel-to-arize-demo\.azure-config`,
explicit subscription `c81fda52-936e-4f14-8af4-951c0dbb92d2`,
RG `fotoa-demo-rg`; retained resources are in `eastus2`.
Only projected metadata was emitted; no secret/list-keys/content endpoints.

| Command / metadata target | Observed 2026-10-19 Eastern |
|---|---|
| `az vm get-instance-view --name fotoa-demo-wjump-eastus2` | Provisioning succeeded; **PowerState/deallocated** |
| `az storage account show --name fotoademoevalstc81fda52` | Succeeded; public network Disabled, shared keys false, public Blob false, firewall default Deny |
| `az network bastion list` | `fotoa-validation-bastion-eastus2`, Developer, Succeeded |
| `az network vnet subnet show --vnet-name fotoa-demo-vnet-eastus2 --name windows-jumpbox` | Existing `fotoa-demo-nat-wjump-eastus2` and `fotoa-demo-nsg-wjump-eastus2`; defaultOutboundAccess false; no route table |
| `az resource show --api-version 2025-06-01` on operational project connection `fotoa-demo-eval-storage` | AAD; AzureStorageAccount; target dedicated evaluation Blob endpoint |
| `az network nic show --name fotoa-demo-nic-wjump-eastus2` | Private `10.20.0.228`; public IP reference null |
| `az resource show --api-version 2018-09-15` on `shutdown-computevm-fotoa-demo-wjump-eastus2` | Enabled, 1900, Eastern Standard Time |

Project connection parent:
`Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-eastus2`.
Shutdown resource type: `Microsoft.DevTestLab/schedules`.
These initial commands did not establish effective NSG rules, Bastion session
success, private DNS/TLS, identity permissions, scanning effectiveness or actual
invoice spend. Infra's deeper configuration findings follow. NAT's egress public
IP is not a VM public IP or public RDP approval.

### Infra retained prerequisites, 2026-10-19 21:36–21:46 Eastern

Safe command arguments/results are retained in ignored repository-local
`.azure-sandbox\issue138-infra-metadata-20261019.json` and
`issue138-infra-metadata-supplement-20261019.json`. The collector is
`issue138-infra-metadata-20261019.ps1`. All Azure processes used the same explicit
subscription and repository-local config described above. Of 27 recorded requests,
**25 succeeded, two effective-view requests failed**. A separate disk REST read
also corroborated the corrected SKU/size. No guest command, network
probe, secret retrieval, VM start, IAM or resource change occurred.

| Prerequisite | Confirmed configuration, not live access |
|---|---|
| Retained access host | `Standard_D2s_v5`, deallocated; NIC `10.20.0.228`, no public IP, no NIC-level NSG; Windows VM **identity null**, not a managed-identity login mechanism. |
| Developer Bastion | Developer/Succeeded, attached to the same demo VNet. This is the existing free access resource; human session/portal permission remains untested. |
| Routing/egress | Windows subnet `10.20.0.224/27` has existing Standard NAT and its Standard/Static egress IPv4, default outbound false, **no route table**; VNet has no peerings/custom DNS. No second NAT is needed. This is configured egress, not observed packet delivery or a fresh effective-route table. |
| NSG composition | Windows subnet NSG: priority 100 allows TCP3389 `VirtualNetwork` → `VirtualNetwork`; priority 4096 denies all other inbound, ahead of default rules. No Internet RDP allowance. Outbound retains default VNet and Internet allows, **not an HTTPS-only allowlist**. |
| Effective views | `az network nic list-effective-nsg` and `az network nic show-effective-route-table` each exit 1 with no usable result while VM is deallocated; stderr was suppressed, so no specific provider error is asserted. Static attachment/rule composition is confirmed; fresh effective views/runtime are **not verified**, not an owner-choice substitute. No retry/start. |
| Private endpoints/DNS | Evaluation Blob and modern Foundry PEs Approved, groups `blob`/`account`, both on private-endpoints subnet; PE network policies Disabled. Blob A=`10.20.0.15`, Foundry services A=`10.20.0.14`; both private DNS zones have Completed links to the demo VNet. Records/links do not prove current guest resolution/TLS or service-side BYOS routing. |
| Project identity/RBAC | Project SystemAssigned MI `650c8a38-543b-4a9b-b497-4d4f2f19c4d2`; account-scoped Storage Blob Data Contributor on **dedicated evaluation storage**, condition null. This read confirms that assignment, not absence of every inherited grant/deny, effective token access, or which identity the pending-upload service uses. |
| Service boundaries | Evaluation account StorageV2/Standard_LRS, PNA Disabled, shared keys/public Blob false, HTTPS required/TLS1.2 minimum, firewall Deny/bypass None, dedicated Defender scanner resource rule. Foundry PNA Disabled/local auth disabled/firewall Deny/bypass None. Existing project connection AAD per initial read. |
| Vault/custody | Demo vault PNA Disabled, RBAC/soft-delete/purge-protection true, firewall Deny with existing AzureServices bypass. No credential values/versions or human principal permissions read. Named human custody and reachable authorized retrieval remain necessary. |
| VM/security | TrustedLaunch, Secure Boot/vTPM true; `MDE.Windows` and `enablevmAccess` extension provisioning Succeeded. Subscription Standard/P2 with no trial and AgentlessVmScanning enabled; VM-scoped pricing read explicitly **inherited True / Standard / P2** from subscription. These are configuration/installation evidence, not guest antimalware health or verified protection/billing coverage across all resources. |
| Storage protection | Account Defender enabled, inherits subscription settings, on-upload scanning and sensitive discovery enabled; configured cap **5000 GB/month**, not a spending cap or evidence of scanned bytes. No malware scan was submitted. |
| Retained disk correction | Fresh disk REST metadata: **128 GiB Standard_LRS (Standard HDD/S10)**, Reserved/Succeeded; historical final receipt says StandardSSD_LRS/E10. Current cost uses actual HDD; the time/actor/reason for this discrepancy is not established and no disk change was made here. |
| Shutdown | Enabled, 1900, Eastern Standard Time; VM remains deallocated. No after-hours exception or execution window inferred. |

Historical RDP/NLA/browser/DNS/TLS PASS remains dated evidence only. Current human
Windows login, Entra/project authorization, private credential retrieval, runtime
connectivity, scan health and the provider's private pending-upload contract
remain untested. Windows has no VM MI; project MI, Foundry account MI and human
identity are distinct. Do not add a VM identity or new grants to “repair” this packet.

## Cost reconciliation and bounded planning estimate

**Authority remains USD53.42/month persistent + USD0.188/running VM hour** as
recorded in #138's requester scope. Dollar figures below are public USD planning
illustrations, **not an invoice, spending cap, authorization increase or quote**.
Use 730 allocated monthly hours, one retained OS disk, one new Blob PE and
**assumed 1 GB Hot LRS**; actual Blob quantity was not read. Existing unrelated
resources are excluded. Existing NAT is counted in full, not silently reallocated
or treated as free because already deployed.

| Item | Original estimate basis | Historical revised receipt basis | Current public planning basis |
|---|---:|---:|---:|
| OS disk | E10 SSD $9.60/month | $9.60 | **S10 HDD $5.888/month**, actual retained SKU |
| One evaluation Blob PE | $0.01 × 730 = $7.30 | $7.30 | $7.30; historical Retail API rate carried forward (fresh numeric refresh unavailable) |
| 1 GB Hot LRS | $0.0184 | $0.0184 | $0.0184, first tier |
| Standard NAT | $0.045 × 730 = $32.85 | $32.85 | $32.85, existing association verified |
| Standard static NAT IPv4 | $0.005 × 730 = $3.65 | $3.65 | $3.65; egress only, no VM public IP |
| Existing Developer Bastion | $0 incremental | $0 | $0 incremental, no paid Bastion |
| Defender for Storage | **Excluded**, not free | **+$10/account/month allowance** | Public calculator $0.0134/account-hour × 730 = **$9.782**; also retain $10 conservative allowance sensitivity |
| **Persistent subtotal** | **$53.4184 → $53.42** | **$63.4184 → $63.42** | **$59.4884 → $59.49** with calculator; **$59.7064 → $59.71** with $10 allowance |

The exact $10 historical difference is **Storage Defender**, not Servers P2,
an extra NAT or VM compute. `storage-jumpbox-plan.json` explicitly excluded
Defender licensing. Root's closed plan (read-only, lines 2141–2150) explains the
$10 allowance and a throttled historical retail refresh; its later sections
“Explicit approval superseding stopped cost/bootstrap gates” and “Fresh
authorization — 2026-10-14 Windows and registration continuation” *claim*
revised $63.42 and additional P2 acceptance. `storage-resume-outcome.json` and
`windows-final-outcome.json` repeat those claims, including
`additionalServersP2ChargesExplicitlyAccepted=true`. These are **secondary
execution narratives**, not independently verified requester consent. The
existing #138 issue/comments contain the original $53.42 ceiling, not primary
corroboration of either expansion. Preserve historical artifacts without adopting
their “approved” field as current authority.

### Running-hour and variable charges

- Windows pay-as-you-go D2s_v5: **$0.188/hour**, public Windows/non-Spot meter,
  not the Linux/Spot/Low Priority rate.
- Public Defender calculator exposes `servers-standard` **$0.02/node-hour**.
  Thus an **indicative** combined running rate is **$0.208/hour**; at 20 running
  hours, calculator illustration is `$59.4884 + 20 × $0.208 = $63.6484`
  before variables. This is not a verified subscription per-VM charge.
- Historical and fresh Retail API show `Servers P2 Node Defender Workload Unit`
  **$0.006849/workload-unit-hour**, meter
  `ae9d6592-94a1-572c-940d-98f72ee3a479`, effective 2026-10-01.
  Exact subscription running expression remains
  **`$0.188 × H + $0.006849 × M × B`**, where `M` is the **unknown
  per-VM workload-unit multiplier** and `B` is billable P2 hours. Do **not**
  assume `M=1`, `M=3`, or infer it by dividing the differently rounded calculator
  rate. No invoice/billing export/paid API was accessed.
- Official Servers FAQ bills Starting/Running/Stopping/**Stopped allocated**,
  not Deallocating/Deallocated. Therefore `B` need not equal active human
  session hours; shutdown/deallocation verification matters. Current deallocated
  metadata supports a zero-running illustration, not proof of billed usage.
- Variable basis: NAT processed **$0.045/GB**; malware scanning **$0.15/GB**;
  historical PE processing **$0.01/GB** first tier (directional); Blob/disk
  transactions, DNS queries, bandwidth/egress, scan-side operations and any
  additional protection/monitoring charges remain usage-dependent and unquantified.
  Do not interpret the 5000-GB scanning configuration as a dollar limit.

**Original ceiling feasibility:** even the current lower HDD/calculator
persistent illustration exceeds $53.42 by **$6.0684/month** (or **$6.2864**
using the $10 allowance), before any VM hours/variables. Compute alone exactly
matches $0.188/hour, but retained P2's public indication adds $0.02/hour; its
actual multiplier/contract is unresolved. Therefore **the retained configuration
cannot be represented as fitting the original combined envelope**. Counting
NAT/IPv4 at zero would hide $36.50/month, not establish savings. No resource
removal, protection disablement or spending increase is recommended/authorized.
First consolidate these facts with Lead; only primary authority could change
the ceiling, and no such request is made by this reconciliation.

### Public source/provenance and limitations

Retrieved 2026-10-19 Eastern, without subscription billing credentials:

- [Azure Retail Prices API](https://prices.azure.com/api/retail/prices):
  exact filters, product/meter IDs, effective dates, units and public responses
  in `.azure-sandbox\issue138-public-prices-20261019.json`. Six queries
  completed, no pagination. Initial throttling recovered with bounded retry.
  Private Link-specific refresh remained HTTP429 in two separate requests;
  its public calculator alternative was HTTP404. Its numeric rates above are
  **dated carry-forwards from the original projected receipt**, not fresh prices.
- [Official Defender pricing](https://azure.microsoft.com/en-us/pricing/details/defender-for-cloud/)
  and its [public USD calculator data](https://azure.microsoft.com/api/v3/pricing/defender-for-cloud/calculator/?culture=en-us&currency=USD):
  `storage-standard.pernodeperhour.us-east-2=0.0134`,
  `servers-standard.pernodeperhour.us-east-2=0.02`,
  `storage-malware-scanning.pergb.us-east-2=0.15`. Saved public calculator
  response is `issue138-public-defender-calculator-20261019.json`.
  Calculator versus workload-unit meter differences are exposed, not reconciled
  into an invented conversion. Storage workload-unit conversion likewise is
  not a verified account quote; $9.782/$10 are planning bases only.
- [Servers FAQ, power-state billing](https://learn.microsoft.com/en-us/azure/defender-for-cloud/faq-defender-for-servers),
  published source revision `b830ea0b14cf400d8893ff7923f0208dd3585b5e`.
  [Upcoming billing identification update](https://learn.microsoft.com/en-us/azure/defender-for-cloud/release-notes#upcoming-billing-updates-for-defender-for-servers)
  is effective **November 1, 2026**, not evidence of today's invoice/multiplier.
- [Private Link pricing](https://azure.microsoft.com/en-us/pricing/details/private-link/)
  distinguishes hourly endpoint and directional processing charges; the fetched
  static page omits numeric prices.

Content hashes for saved evidence and pinned official compute workflow/pricing
references are in `issue138-infra-evidence-hashes-20261019.json`. No installed
profile skill references were read. This was retained-resource pricing/reconciliation,
not a new VM recommendation or official prepare/validate/deploy execution.

### Immutable receipt bindings (offline SHA256)

Paths below are relative to the repository's ignored `.azure-sandbox` directory.
Hashes checked with `Get-FileHash -Algorithm SHA256`; compressed receipt was
hashed only, never decompressed or inspected.

| Receipt | SHA256 |
|---|---|
| `windows-final-outcome.json` | `e625acca4dd275165dfbd52366c1bce972603a5cf051dcb43ca261698f0ce5a6` |
| `windows-final-readonly-reconciliation.json` | `d7c23df687539113816b42623dbef4c1c2f7dbad0147bca4934f108bc9410143` |
| `windows-final-probe-receipt-metadata.json` | `1d989c23e7b79c92e7fc085e43507dd2ac387df8356ceb3c7b97224ff70e9084` |
| `windows-final-probe-receipt.zlib` | `5fe874216af1efbe3505a9db77424d73469c0ca02cfdf61ce3e50a91a28a649b` |

The metadata reports full receipt length **8178 bytes**, SHA256
`645d382b0f38d0e0397ba5ae4353ab39251a767b34f469d86eb240434589b446`.
That full hash is a historical metadata binding, not a new independent full-content
verification. The closed plan binds exactly ONE fresh five-case source to script
SHA256 `478c004a11486979c89ca454ab94e124e144da15e8953925e18b99d4bc7d09a0`
and exclusive receipt basename
`fotoa-demo-agent-eastus2-smoke-storage-probe-1.private-registration.json`.
The final outcome matches that receipt identity and full hash.

**Conclusion: the historically approved attempt was consumed, not reusable.**
The metadata records **1 pending-upload attempt / 0 Blob uploads / 0 dataset PUTs**,
`datasets.pending_upload`, HTTP **403 / UserError**; no safe request ID.
Read-only reconciliation reports one dataset GET, HTTP **404**,
`fotoa-demo-agent-eastus2-eval-seed` version `v1`; suite UNREGISTERED.
It proves a failed attempt and historical dataset absence, not that all five cases
uploaded or that service-side pending state was cleaned up. No retry, registration,
suite, inference, evaluation or generation call occurred in this reconciliation.
The old **3/3 inference budget remains CLOSED**.

## Exact remaining acceptance and owner handoff

| #138 acceptance area | State and required next evidence |
|---|---|
| ADR with actual agreement | ADR-0005 Proposed; Infra, Agent and QA review/signoff needed before Accepted. Lead owns reconciliation, not implied consensus. |
| Convention/architecture impact | No implementation, telemetry architecture or convention change; `.github/copilot-instructions.md` unchanged intentionally. |
| Current/future separation | Ancillary retained assets only; direct OTLP remains conceptual. |
| Track notification | Lead outcome comment provides Infra/Agent/QA handoffs and informs Telemetry that the bridge is unchanged; coordinator must route actual work. |
| Exact delta, access, egress, costs, custody, identity | Infra configuration/cost findings above complete this bounded discovery. Effective NIC views failed without VM start; runtime, guest protection health, actual invoice/multipliers and named human access remain unverified. Human confirms custody/window; no grant/change permission inferred. |
| Provisioning versus navigation versus registration | Provisioning evidenced; historical prerequisites pass; human Windows/Entra/project navigation pending; registration failed; inference/evaluation not authorized or ready. |
| Fresh probe authority/receipt | Historical authority consumed. Agent/QA identify pinned SDK/API/identity/source/receipt tuple and support-approved route before requesting any NEW bounded probe authority. |

Historical final outcome describes Edge installed, no installer calls, RDP/NLA
prerequisites pass and private Blob/Foundry DNS/TLS pass; human login remains
unverified. Its 38 focused tests PASS and provider/build/what-if results are dated
reports, **not rerun or fresh Validated claims**.

### Minimal consolidated parent request — not permission to run

1. **Window and cost:** approve a specific date/start/end, maximum VM running
   hours, named operator, and deallocation owner. Today is after 19:00 Eastern:
   **no start now**. Preserve 19:00 Eastern shutdown; any exception requires
   explicit new approval. The itemized estimate above explains the historical
   **$10 Storage Defender** delta and actual retained **HDD** correction;
   **$59.49/month + indicative $0.208/hour**, before variables, does not fit the
   original **$53.42 + $0.188/hour** envelope. Subscription invoice/protection
   scope and workload-unit multiplier remain unverified. Neither historical
   approval prose nor this ADR increases the ceiling; do not request a raised
   budget based on unverified receipt claims or disable protection to force a fit.
2. **Custody:** name the human authorized for Windows credential custody and
   Foundry project sign-in. They privately retrieve the designated credential in
   `fotoa-demo-kv-eastus2`; never paste it into chat, receipts or CLI arguments.
   VM credentials and Entra/project permissions are separate. No agent extraction,
   credential reset or role grant.
3. **Routing:** retained Developer Bastion, NAT/NSG/private endpoint/DNS and
   project MI assignment metadata are now confirmed as described above;
   effective NIC views/current runtime access are not. No second NAT, paid Bastion,
   public VM IP, Internet RDP or public service fallback. Only in a later approved window,
   human uses existing Developer Bastion → retained Windows VM → Edge
   `https://ai.azure.com` → authorized project. Record only navigation success/
   failure and safe metadata; **no prompt, evaluation, registration or screenshot
   containing content**. Finally deallocate, verify instance state and retain assets.
4. **Probe identity decision:** Agent/QA and product support determine the
   documented Projects 2.0.0 BLOB_REFERENCE pending-upload/BYOS private-access
   contract and identity (human, bridge MI and project MI are not interchangeable).
   HTTP 403 does not justify account network injection, extra Blob/quota roles,
   changed auth or public storage. Establish unknown pending-state disposition and
   exact source hash, five synthetic cases, new exclusive receipt, zero runtime
   calls and stop conditions before requesting a fresh one-shot probe.
   No new probe is requested for execution in this packet.

Any later infrastructure change belongs to **Infra**, with a new worktree-local
`.azure\deployment-plan.md` and official prepare → validate → deploy lifecycle;
never overwrite/reuse root's closed plan. Repo-contained applicable official
Azure skill references must be refreshed then; unavailable references block that
step, not this documentation correction. No profile/reference escape is permitted.
Keep #138 open until affected tracks and the operator supply the missing evidence.
