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
5. Today's seven successful read-only Azure metadata commands below confirm retained
   assets, not replay historical private/runtime checks.

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
These commands did not establish fresh effective NSG rules, Bastion session
success, private DNS/TLS, identity permissions, scanning effectiveness or actual
invoice spend. NAT's egress public IP is not a VM public IP or public RDP approval.

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
| Exact delta, access, egress, costs, custody, identity | Historical provisioning exists; no recreation. Infra reconciles retained inventory, effective route/NSG/private endpoint and project MI role metadata, antimalware and cost discrepancy; human confirms custody. No grant/change permission inferred. |
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
   explicit new approval. User scope says **USD 53.42/month persistent if NAT
   needed + USD 0.188/running VM hour**; final receipt instead says **63.42**
   and claims extra Servers P2 acceptance with unknown multiplier. Infra must
   resolve provenance/total against requester authority before another running
   window; neither receipt nor this ADR increases the ceiling. Do not disable
   protection to force a price fit.
2. **Custody:** name the human authorized for Windows credential custody and
   Foundry project sign-in. They privately retrieve the designated credential in
   `fotoa-demo-kv-eastus2`; never paste it into chat, receipts or CLI arguments.
   VM credentials and Entra/project permissions are separate. No agent extraction,
   credential reset or role grant.
3. **Routing:** Infra verifies retained Developer Bastion/private RDP and existing
   NAT/NSG/private endpoint path metadata first; no second NAT, paid Bastion,
   public VM IP, Internet RDP or public service fallback. In the approved window,
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
