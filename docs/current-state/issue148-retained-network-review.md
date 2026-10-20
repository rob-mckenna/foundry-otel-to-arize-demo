# Issue 148: retained classic private endpoints — owner decision packet

**Execution update (2026-10-20 04:34 UTC):** owner approval was subsequently
recorded for the frozen proposal, but fresh execution preflight stopped before
any mutation because inherited delete-policy applicability was unresolved.
See [the execution record](issue148-retained-network-execution.md).
The preparation packet below remains the historical decision basis, not a
completion claim; the structured proposal is unchanged.

**PREPARATION ONLY — no deletion or network/IAM mutation performed or authorized.**
Infra, 2026-10-19 local / 2026-10-20 UTC. Related: [cleanup history](resource-cleanup-plan.md),
[ADR-0004](../adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md),
[#148](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/148).
Main baseline: `2219075f86a7ba387490abdb88ceae5e2a775e9d`.

## Decision requested

Approve or decline **only two explicit parent PE deletions**, sequentially demo
then dev, including their exact provider-owned NIC lifecycle and contained
configuration effects below. The full, unabridged IDs and unfilled owner fields
are in [the structured proposal](issue148-retained-network-proposal.json).
This packet and a PR merge are **not** execution approval.

Owner must confirm: network/governance authority, no required external or
hardcoded-IP consumers, accepted irreversible loss of NIC/IP/contained
configuration, exact manifest hash and execution window. Same-name recreation
cannot restore deleted workspaces, endpoint identity or IP allocations.
Stop for preservation review after demo before allowing dev.
No new permission is requested; future executor permissions/locks/policy must
be checked without creating grants or testing DELETE.

## Fresh metadata and resolved links

[Raw projected ARM evidence](evidence/issue148-retained-network-20261020-final.json)
was collected **2026-10-20 01:07:46–01:11:58 UTC** (21:07–21:11 EDT on October 19).
Every Azure CLI process set repository `AZURE_CONFIG_DIR` and explicit subscription
`c81fda52-936e-4f14-8af4-951c0dbb92d2`. All requests were GETs with allowlisted
metadata projections, scoped to `fotoa-demo-rg`; no continuation pages remained.
The earlier same-session collection was preliminary and superseded by this one.

For readability only, IDs in the table are relative to this exact prefix:
`/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/`.

| Link | Demo | Dev |
| --- | --- | --- |
| Explicit candidate PE (`Microsoft.Network/privateEndpoints/`) | `fotoa-demo-pe-aihub-eastus2` | `fotoa-dev-pe-aihub-eastus2` |
| Actual `privateLinkServiceId` (`Microsoft.MachineLearningServices/workspaces/`) | `fotoa-demo-aihub-eastus2` | `fotoa-dev-aihub-eastus2` |
| Connection state / group | `Disconnected` / `amlworkspace` | `Disconnected` / `amlworkspace` |
| Actual NIC (`Microsoft.Network/networkInterfaces/`) | `fotoa-demo-pe-aihub-eastus2.nic.f992623e-9cc8-4bc5-ae48-8c5b618cf5e3` | `fotoa-dev-pe-aihub-eastus2.nic.c1b8719d-2dcc-476e-a541-7dfd4a11bd43` |
| Subnet (`Microsoft.Network/virtualNetworks/`) | `fotoa-demo-vnet-eastus2/subnets/private-endpoints` | `fotoa-dev-vnet-eastus2/subnets/private-endpoints` |
| NIC IPs in that subnet | `10.20.0.6`–`10.20.0.9` | `10.20.0.5`–`10.20.0.8` |
| PE `managedBy` | null | null |
| NIC `managedBy` **and** `privateEndpoint.id` | exact demo PE ID | exact dev PE ID |
| Contained DNS zone group | `<exact PE ID>/privateDnsZoneGroups/default` | `<exact PE ID>/privateDnsZoneGroups/default` |
| Zone config target | shared `privatelink.api.azureml.ms` | same shared zone |
| Zone-group `recordSets` | empty | empty |

Ownership is established by reciprocal PE→NIC and NIC→PE metadata, not the NIC
name. Both NICs are Succeeded, have four IP configurations, no VM attachment,
NIC-level NSG, public IP, load-balancer/App Gateway backend/NAT-rule attachment
or ASG reference in the projected configurations. Each NIC is referenced by
exactly one of nine RG endpoints. No PE/NIC-scoped assignment was observed.
The fresh resource list has neither target hub; their four-workspace confirmed
404 results remain immutable history, not repeated DELETEs or new asset probes.

### Remaining consumers: preserve rather than infer exclusivity

- Demo PE subnet contains **seven** PEs: candidate hub plus modern Foundry,
  evaluation Blob, Function Blob/Queue/Table and Key Vault. Its NSG remains shared.
- Dev PE subnet contains **two** PEs: candidate hub and dev Key Vault.
  Its subnet/NSG/VNet are not exclusive to the hub.
- Shared AML DNS zone has **two VNet links** and **only its SOA record**.
  Both endpoint zone groups persist, but their record collections are empty.
  No DNS zone/link removal is proposed even if the zone becomes unused.
- Seven other PEs/NICs and all remaining DNS zone groups are protected.
  The two VNets have overlapping private IP values: IP equality across different
  subnets/VNets is not evidence of shared ownership or a DNS cleanup target.
- No other primary resource's `managedBy` identifies either candidate PE.
  This bounded ARM attachment review is **not** an external caller, route-rule,
  cached DNS, traffic or every-service dependency audit. External/hardcoded
  consumers remain owner-attested UNKNOWN until confirmation.

## Smallest cleanup delta and documented automatic effects

The proposed explicit operation set is **two PE IDs only**. Do not separately
delete a NIC, DNS group, connection, IP configuration, subnet or NSG.

1. Provider-managed NIC lifecycle removes the one exact linked NIC, its four
   IP configurations and subnet IP allocations with each approved PE.
2. The endpoint's contained `aihub-connection` and empty
   `privateDnsZoneGroups/default` disappear with their parent. Remove only their
   corresponding PE/IP-configuration references from the shared subnet; do not
   PUT an authoritative subnet list.
3. DNS zone-group integration can delete associated records when a PE is
   deleted. **Here there are none in either group.** Eight hub-GUID A-records
   were already auto-removed during separately approved workspace retirement.
   The remaining SOA is **not** a cleanup candidate. Expected DNS record delta
   now is **zero**, not another eight. Never manufacture a DNS cleanup step.
4. No IAM effect is expected or accepted. Any automatic IAM/DNS change beyond
   this exact zero-delta expectation is an abort condition, not implied approval.

Official Microsoft documentation retrieved 2026-10-20:

- [Private endpoint overview](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-overview#private-endpoint-properties):
  only Approved connections carry traffic; Disconnected is an informative
  endpoint for cleanup. A read-only NIC is created for the PE lifecycle.
- [Private DNS zone groups](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns-integration#private-dns-zone-group):
  deleting a PE removes DNS records within its zone group. This describes the
  supported mechanism, not proof of an observed delete in this review.

The exact provider effects must still be verified after any future authorized
execution. If a NIC remains, **stop**; do not issue manual NIC DELETE.

## Protected baseline and expected accounting

Fresh metadata matches the completed retirement snapshot on all **79 primary
IDs/projected metadata**, **85 assignment projections** and **17 projected DNS
record sets**. All **48 network resource IDs**, **eight zones** and **ten VNet
links** remain. The modern project ID/principal, `function-transform` consumer
ID/type and four host/state container IDs/types match the historical child
projections; validation VM is freshly observed `PowerState/deallocated`.
Container lease metadata was not refreshed; no blob/state contents were read.
[The persisted comparison](evidence/issue148-retained-network-baseline-comparison.json)
records zero primary/role/DNS projection differences and SHA-256 hashes for all
existing root issue148 history files and the completed plan (64 files total).

| Projected set | Now | After demo only (conditional) | After both (conditional) |
| --- | ---: | ---: | ---: |
| Primary resources | 79 | 77 | 75 |
| Network resources | 48 | 46 | 44 |
| DNS zones / record sets / VNet links | 8 / 17 / 10 | unchanged | unchanged |
| Role assignments | 85 | 85 | 85 |

Counts are secondary checks, never substitutes for exact-ID and metadata diffs.
PE-contained groups/connections and NIC-contained IP configs are not extra
primary resource rows. All **75 other primary IDs**, all remaining metadata
and shared-network configuration stay protected except the exact derived subnet
reference removals described above.

Specifically preserve:

- Modern Foundry account/project/agent v1, model and tracing association;
  Function `fotoa-demo-func-eastus2`, `fotoademosteastus2`, LAW/Insights/EH
  `fotoa-demo-ehns-eastus2/telemetry/function-transform`.
- Both vaults, all storage/dev telemetry, governance diagnostics/antimalware,
  #138 validation/evaluation/private-access assets, #139 retained project.
- Legacy project KV grants `9881514f-8952-53b2-94cd-63fbb7ae35cb` and
  `b72f6eae-6ac5-5d4b-bd65-7798c41d3b1e`; existing sender assignment
  `27c683e5-b400-4b1e-9234-89e40fde2198` **at the EH namespace scope**.
  All 85 assignments remain protected, including inherited ones. No orphan sweep.
- Ledger/checkpoints/35 imported ACKs/quarantine and immutable root
  `.azure-sandbox\issue148*` receipts/intent/submission markers and completed root
  `.azure\deployment-plan.md`.
  Trace `04f49dc16c02643b6a351a499cd4db5a` / span `b4cd6555d6c3ea92` remains
  delivery-unknown: **no resend/replay**.

This is non-atomic management-plane preservation evidence, not runtime/model
health, agent-version revalidation or delivery proof.

## Before/after protocol for the separately approved future executor

1. Freeze/hash the reviewed proposal; record explicit owner selection, comment
   URL, consumer/governance clearance, exact automatic effects and window.
   Do not reuse the workspace retirement approval, guards or completed workflow.
2. Run fresh **azure-prepare → azure-validate → azure-deploy** administrative
   gates. Keep the root completed plan read-only; use this worktree's separate
   ignored local plan (not committed, so merging cannot replace root history).
   No fresh `main.bicep` deployment/what-if against this mixed live RG.
   Refresh inherited locks/policy/exact action permissions; do not grant access.
   The observed RG lock collection was empty; that alone is not governance
   clearance or proof of sufficient permission.
3. Recollect metadata with a new output filename using the command below.
   Before execution, GET **each exact PE/NIC ID** in addition to the RG list;
   recheck type, targets, state, reciprocal ownership, four IP configs, shared
   subnet consumers, group recordSets, all IDs/metadata/protected child
   projections and immutable receipt hashes. Treat any drift/pagination/error
   as unresolved, not empty or approval. No unsupported `/codes` diagnostics.
4. Persist a new exclusive exact-ID submission intent. Execute only the approved
   demo PE once; record response and bounded polling. A 403/error/timeout is not
   absence. Resolve uncertain outcomes by GETs, **never retry DELETE**.
5. Require independent exact-ID HTTP404/ResourceNotFound for parent and NIC,
   empty/absent contained group, no remaining subnet references to those exact
   PE/IP-config IDs, no IAM/DNS-record delta and no other primary removal.
   Compare all protected projections before continuing dev; stop on ambiguity.
6. Repeat only for the never-submitted dev PE if owner-approved continuation is
   still valid. Expected final removal set is exactly four primary IDs in the
   structured proposal. Check every remaining PE/NIC/zone/group/link/record/
   assignment and modern-project/consumer/container/VM projection, allowing only
   those exact subnet reference removals. Preserve logs/guards/receipts.
7. Record verified outcomes and leave unresolved items explicit; do not claim
   #147 deployment/runtime verification or #138 cleanup. No force/purge,
   Complete/RG teardown, manual DNS/IAM fix, VM/model action or state access.

## Reproduction and focused offline checks

From this worktree (all paths relative to it):

```powershell
.\infra\scripts\collect-retained-network-metadata.ps1 -OutputPath 'docs\current-state\evidence\issue148-new-readonly-snapshot.json'
python .\infra\scripts\validate-retained-network.py --evidence .\docs\current-state\evidence\issue148-retained-network-20261020-final.json --plan .\docs\current-state\issue148-retained-network-proposal.json
python -m unittest discover -s .\tests\infra-retained-network -p 'test_*.py' -v
```

The collector uses fixed read-only endpoints and rejects overwrite, an output
outside its worktree, failed GETs or pagination. Its output directory must be
within this worktree; do not point it at root receipts. It has no execution mode.
Offline checks prove packet consistency and reject fabricated NIC-owner drift,
newly active connections, new zone-group records, incomplete inventory,
protected-grant loss and DNS/IAM/manual-NIC scope expansion. They do not validate
cloud permissions, owner authority, stale snapshots or runtime health.

Validation performed: final metadata collector **PASS** (GETs only); offline
validator **PASS**, **7 unittest cases PASS**, collector PowerShell parser
**PASS (zero errors)** and `git diff --check` **PASS**. Primary/role/DNS historical
projection comparisons have zero differences. No mapping/export tests were
needed: the telemetry path is unchanged. No deployment or runtime/model tests run.
