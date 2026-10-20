# Issue 147 — full-source cost ledger and conditional planning estimate

**2026-10-19 public USD retail basis; PREPARATION ONLY. Not a vendor quote,
invoice forecast, approved budget, or enforceable spending limit.**

**2026-10-20 approved-direction update:** no-tool Basic/private client ingress
with Microsoft-managed runtime/state is selected, not a pending Standard choice.
Fresh source now explicitly bounds plan/app EP1 scale to **1**, with minimum 1
and prewarmed target 1 inside that ceiling. See [bounded execution proof and
finite operator retention plan](issue147-bounded-execution.md) and
[safe metadata index](issue147-bounded-execution.json). The 24h validation lifetime
and day-7/day-30 tail reviews do not authorize deletion or implement a billing
TTL. New security metadata establishes Standard AI/CloudPosture and precise
Storage/KV/ARM subplans, **not their entitlement/rates**. G/L/R still prevent
an all-in estimate; no fresh paid execution occurred. Older scope/approval
proposals below are historical where superseded by this update.

This supplements the [acceptance packet](fresh-foundation-acceptance.md).
It prices the **entire existing source foundation**, not a new architecture:
`infra/main.bicep` plus its referenced modules, including private package/host/
durable storage. Search, Cosmos DB, NAT, VM, private resolver, AMPLS, ACR, hosted
agent compute and Durable Task Scheduler are **not added**. If the eventual Agent
contract requires any of them, this scenario is inapplicable, not permission to
expand it. The [integrated Agent assessment](issue147-private-agent-prerequisites.md)
resolves the historical v1 Responses contract and SDK pins, not fresh readiness.

**Fresh-readiness hold / NOT READY FOR EXECUTION APPROVAL:** the ledger prices the present
source graph, not a proven fully private Agent runtime. Basic can use private
inbound with Microsoft-managed state; that is not Standard private outbound/BYO
state. If fully private runtime is required, Standard's Storage/Search/Cosmos,
dedicated agent-subnet injection, capability provisioning and dependency
PE/DNS/permissions are missing and **not priced here**. Resolve the supported
contract and accepted scope first, then replace the applicable resource/meter
inventory; do not silently select Basic or label those missing services a
zero-cost R addend. No architecture expansion is authorized.
**2026-10-20 correction:** Standard dependencies are **conditional**, not
missing mandatory meters for ADR-0004's private-client-ingress/no-tool foundation.
[Agent §1a](issue147-private-agent-prerequisites.md#1a-correction-adr-promise-authoritative-distinction-and-bounded-choices)
provides exact A/B boundary wording and ADR clarification/amendment requirements.
A retains this source inventory and service-managed state; B invalidates it and
requires accepted redesign/repricing. US-zone model processing is independent
and does not certify every service's residency. No choice or fresh gate is passed
here; package/runner/custody/security/retention/overage addends remain unresolved.

## Evidence and reproducibility

[Selected public meters and calculation inputs](issue147-planning-evidence.json)
retain exact meter IDs, effective dates, region, SKU, units, tier, retrieval
timestamps, public request URLs and SHA-256 of each complete projected response.
Source: [Azure Retail Prices API](https://prices.azure.com/api/retail/prices),
queried directly without Azure credentials, customer prices or billing exports.
All queries are USD Consumption; every successful result was fully paginated.
The large source responses remain ignored at team-root
`.azure-sandbox\issue147-workflow\qa-followup-20261019\price-*.json`.
Azure returned the same meter ID for Hot LRS write and list/create-container
operations with distinct display names. The ledger budgets separate 100,000
operation quantities (200,000 combined), not two fees for each operation;
deduplicating solely by meter ID would undercount this envelope.
One initial storage request returned 429 and was not treated as a zero price;
a later combined supporting-service request succeeded (1,782 rows, two pages).
An initial broad model query was incomplete and deliberately not quoted; the
narrow complete model query supplies the selected rates.

Recompute offline, from the issue worktree:

```powershell
python -B -m unittest discover -s tests\readiness -p 'test_issue147_planning.py' -v
.\tests\readiness\check-issue147-docs.ps1
```

Public prices are not subscription entitlements. Free allowances, trials,
discounts, reservations, negotiated minimums, tax, FX and support contracts
are not assumed. Where a free tier exists, use the positive marginal rate
conservatively; do not claim another environment's free allowance.
Both commands **passed** again after same-issue Agent integration: four
calculation/provenance/link tests (including both Agent Python examples parsed
without execution), 14 PowerShell examples and two pinned official scripts
parsed, none executed.

## Explicit scenario, quantities and clock

The modeled window is **24 billable hours per retained resource**, starting
with its first billable provisioning/allocation, not the first invocation.
A longer deployment, retries, publication, review delay or cleanup tail adds
hours. No deletion is authorized at hour 24. No resource automatically expires.
Reserve **25 charge-hour buckets** for EH/PEs to cover a partial-hour start/end;
the core/memory EP1 calculation remains per-second over 24 hours.
[Private Link](https://azure.microsoft.com/pricing/details/private-link/) charges
partial hours as full hours; [EH](https://azure.microsoft.com/pricing/details/event-hubs/)
uses the maximum selected TUs in each billed hour. The Dedicated EH four-hour
minimum does **not** apply to this Standard SKU.

The volume envelope is a planning condition, **not controls implemented by
this PR**: at most 1 GB Analytics ingestion, 1 GB LAW export, 1 million billable
EH ingress events (including 64-KB event billing chunks), 10 GB blob occupancy
(package + host + durable state + every retained version/snapshot/deleted copy),
1 GB queue and 1 GB table occupancy, 100,000 operations in **each** listed storage
operation class, 10,000 KV operations, 1 million DNS queries, 10 GB in and
10 GB out **summed across all PEs**, 10 GB internet egress, 10 GB potentially
billable inter-region traffic, and 10 GB malware-scanned uploads including
rescans. Occupancy is held at the upper amount for all 24 hours.
EH retained bytes including headers/overhead are bounded to **10 GB**, below
the **84 GB/TU included allowance**. Assume total simultaneous AMQP brokered
connections at most **2N+2** (all clients/control paths). Reserve the paid
**$0.03/connection monthly unit in full**, without applying the shared
subscription's first-1,000 allowance or daily proration. This is a conservative
monthly reserve, not proof of this application's connection pooling. If the
actual client contract exceeds that count, reprice before execution.
[Official brokered-connection billing](https://azure.microsoft.com/pricing/details/service-bus/)
actually sums hourly concurrent peaks divided by **730** over the month before
applying shared allowances. The full-unit reserve above is deliberately larger
than `(2N+2) × 25 / 730 × $0.03`; it is **not** a claimed minimum monthly bill.

Storage GB-month arithmetic reserves a **28-day month** (`GB / 28` for one day),
not a 730-hour division of every meter. DNS is charged daily with monthly
proration: reserve **two calendar charge-days** for a 24-hour interval that
crosses midnight, each at `7 × $0.50 / 28`. No additional charge for seven VNet
links is introduced. This is deliberately more conservative than a one-day
30-day-month estimate. Invoice calendar/rounding can differ.

### EP1 floor and maximum — not interchangeable

Source `modules/function-app.bicep`: **Linux EP1, capacity 1**, one app.
It now sets **maximumElasticWorkerCount=1, functionAppScaleLimit=1,
minimumElasticInstanceCount=1, preWarmedInstanceCount=1**. Main and both example
profiles expose/constrain `functionMaximumInstances=1`; the prepared-profile
gate rejects any other value. Public schema and pinned official CLI support 1;
fresh provider acceptance/readback remains outstanding. Prewarmed allocation
stays inside the app maximum per Premium guidance. Capacity alone was not a cap.
The supported floor is **one billed EP1 even idle**.

[Official Premium billing/scaling](https://learn.microsoft.com/azure/azure-functions/functions-premium-plan)
specifies 1 core + 3.5 GB for EP1, per-second allocated-instance billing, no
separate execution charge, and billable prewarmed buffers when allocated:

`EP1 cost = instance-hours × ($0.16 + 3.5 × $0.0114) = instance-hours × $0.1999`.

- One instance for 24h: **$4.7976**, not free when triggers are disabled.
- Conditional maximum **N=20 allocated instances including buffers** for 24h:
  **$95.9520**. This is an illustrative ceiling only if the approved profile
  and provider readback establish that effective plan/app maximum; **not the
  source profile, which now only permits 1**. Retained as historical sensitivity.
- Stress sensitivity N=100: **$479.7600** compute alone. This is not a claim
  that this region/subnet/account can allocate 100 instances.

The source maximum is **1**, but effective provider acceptance and subnet
feasibility (including scale transitions/replacement) remain unestablished.
Current `/26` example is not certified against Premium networking guidance's
at-least-100-available-address recommendation. No CIDR changed in this slice.
Source scale limits are not monetary caps or proof against transient replacement
allocation. G/L/R, continuing usage and actual retirement timing mean there is
still **no unconditional all-inclusive numeric upper bound**.

## Complete source-resource/meter ledger

Rates below are retrieved 2026-10-19; quantities are the above assumptions.
`N` means average allocated EP1 instances over the whole day, buffers included.
Subtotals retain precision in the JSON; USD figures here are display-rounded.

| Source resource / meter | Quantity × retail rate | 24h modeled USD |
|---|---|---:|
| One modern AIServices S0 account, one project, one PAYG model deployment | No separately priced idle account/project/deployment capacity meter selected; token cost below. Not PTU/reserved capacity. Agent runtime/state extras unresolved below. | 0 separate foundation fee |
| One Linux Elastic Premium EP1 plan + one Function | `24 × N × (0.16 + 3.5 × 0.0114)`; no Consumption execution fee added | `4.7976 × N` |
| One EH Standard namespace, one TU, one hub, two partitions, one custom consumer + platform default | `25 reserved TU-hours × 0.03`; auto-inflate **false**, max TU inflation **0**, TU explicitly **1** | 0.750000 |
| EH ingress | `1 million events × 0.028 / million` | 0.028000 |
| EH AMQP brokered connections | `(2N+2) × 0.03`, paid Standard **Service Bus pricing meter used by EH**, full monthly-unit reserve, **not a new Service Bus resource** | `0.06 × N + 0.06` |
| EH retention / egress / Capture | **1-day retention** in source; no Capture configuration, Kafka client, geo-replication, Premium/Dedicated extended-retention meter or second namespace. Standard consumer delivery does not add a separate per-read event charge. Source parameter accepts up to 7 days but main uses default 1. | 0 additional selected meter |
| One StorageV2 Standard_LRS account, Hot blob occupancy | `10 GB × 0.0184 / 28` | 0.006571 |
| Blob writes + list/create-container operations | `100,000 × 0.05 / 10,000` **each** | 1.000000 |
| Blob reads + all-other operations | `100,000 × 0.004 / 10,000` **each** | 0.080000 |
| Queue capacity | `1 GB × 0.045 / 28` | 0.001607 |
| Queue class 1/class 2 + class 1/class 2 additional I/O | `100,000 × 0.004 / 10,000` **each of four classes**, StorageV2 rates, not cheaper legacy Queue rates | 0.160000 |
| Table capacity | `1 GB × 0.045 / 28` | 0.001607 |
| Table read/write/list/delete/scan/batch write | `100,000 × 0.00036 / 10,000` **each of six classes**; standard, not account-encrypted tier | 0.021600 |
| Existing package/host/durable containers within that account | `function-packages`, host/checkpoint/lease blobs, `genai-correlation` indexes/ACK/outbox/quarantine all count in occupancy/operations above; no duplicate container base fee | included |
| Five private endpoints | Foundry + KV + Blob/Queue/Table: `5 × 25 reserved charge-hours × 0.01` | 1.250000 |
| Private Link processing | `10 GB ingress × 0.01 + 10 GB egress × 0.01`, first-tier **Global** meter | 0.200000 |
| Seven private DNS zones + seven VNet links | `7 × 0.50 × 2 / 28`; first-25 tier conservative, query meter separate | 0.250000 |
| DNS queries | `1 million × 0.40 / million` | 0.400000 |
| Fresh VNet, two subnets, delegation, endpoint NICs, zone groups | No separate base resource fee; PE bills above. No public IP/NAT/gateway/firewall/VM/resolver introduced. Private validator's existing costs not silently assigned to zero. | 0 separate source fee |
| Internet transfer to Arize/package destinations | `10 GB × 0.087`, East US 2 Microsoft-network paid marginal rate; no free first-100-GB assumption | 0.870000 |
| Inter-region transfer allowance | `10 GB × 0.02`; only if actually metered; not a claim model routing is separately billed this way | 0.200000 |
| One PerGB2018 LAW + one workspace-based App Insights | `1 GB Analytics ingestion × 2.76`; do not bill same workspace ingestion twice | 2.760000 |
| LAW continuous data export | `1 GB × 0.10`, independent of EH ingress/network fees | 0.100000 |
| Analytics retention | Source **30 days**, within included Analytics retention; no archive/search jobs/restore/Basic/Auxiliary/commitment tier selected | 0 extra for this scenario |
| One Standard KV, versioned secret custody | `10,000 secret operations × 0.03 / 10,000`, including set/get/list/refresh/publication custody; MI/ARM deployment refs do not make operations free | 0.030000 |
| KV keys/certificates/HSM/rotation/renewal | No managed HSM, premium keys, key rotation, certificate issuance or separately charged renewal configured. If added, reprice; e.g. returned Standard automated rotation **$1/rotation**, secret renewal **$1/renewal** | 0 configured |
| Managed identities, scoped RBAC/custom role, ARM modules/association/export rule | No separately priced base meter; source-defined roles are **not** authority to grant during preparation. Secure upload/build/private access costs require explicit custody, not shared-key fallback | 0 separate source fee |
| Model gpt-5-mini DataZoneStandard input | `1,024 uncached tokens × 0.275 / 1,000,000` | 0.000282 |
| Model gpt-5-mini DataZoneStandard output | `1,024 tokens × 2.20 / 1,000,000`, includes reasoning; zero client retries, no tools/evals | 0.002253 |
| Defender for Storage node allowance | `1 storage node × 24 × 0.0134`; conditional applicable node-based meter, no trial assumed | 0.321600 |
| Malware scanning allowance | `10 GB uploaded/scanned × 0.15`, **not** disabled or exempted | 1.500000 |
| Defender for Key Vault node allowance | `1 vault node × 24 × 0.00034` | 0.008160 |
| Defender for App Service allowance | conservatively `24 × N node-hours × 0.02` | `0.48 × N` |
| Defender for Resource Manager allowance | `1 node × 24 × 0.0069`; conservative allocation, may be shared rather than incremental | 0.165600 |
| Governance/security services not represented by above plan | Policy/IAM management has no source-defined paid extension; **actual inherited Defender/CSPM/AI protection/diagnostic policies, partner plans and minimum billing need existing sanitized plan/entitlement attestation** | **G: unresolved** |
| Arize destination ingestion/storage/retention/license/minimum | No public per-unit entitlement established for the destination workspace/contract. No paid API or invoice requested | **L: unresolved** |
| Agent runtime/state, private runner, publisher/build platform, external access/support/license commitments | Historical v1 Responses/SDK contract is resolved, but fresh publication/private validation/immutable runner are not. Basic state ownership/residency needs explicit treatment; Standard would invalidate this inventory and require accepted redesign/repricing, not merely an assumed R value. No new compute/data service added or old VM started | **R: unresolved** |

### Conditional totals, not an approval request for missing discovery

The JSON/test computes the numeric rows, **including the four conditional
Defender allowances and malware**, without using any trial/free allocation:

- N=1: **$15.504880 USD** for this assumed 24h source/volume/security scenario.
- N=20: **$116.919280 USD**, historical sensitivity, not selectable source scale.
- N=100 sensitivity: **$543.927280 USD**, not selectable source scale.

These are **conditional priced subtotals**. Full cost is
`priced subtotal + G + L + R + billable overages + time tail + tax/contract effects`.
No finite all-inclusive total can honestly be asserted while G/L/R and retention
duration are unknown. The account/product pricing, effective Defender meter
applicability and usage envelope must be reconciled before treating even the
conditional subtotal as a ceiling. Legacy Defender Storage transaction pricing
returned **$0.1492/million transactions**; it is an alternative plan basis, not
silently added to node pricing. The API's node meter is not evidence which plan
this subscription uses. Per-resource AI protection or CSPM charges cannot be
inferred absent from a scoped price query.

The former **$185.93/month** figure covers only EP1 + five PEs + seven zones;
it is not a full quote. **USD25 has never been an approved cap**. The modeled
N=20 subtotal already exceeds it before G/L/R or a post-run tail.
USD1 inference likewise remains proposed, not permission; modeled one-call
tokens cost $0.0025344 but service-added context, outputs beyond the envelope
or ambiguous-delivery retries invalidate that estimate.

## Retention, minimum billing and the hour-24 decision

- **Keep is the current authorization default.** Stopping invocation, disabling
  triggers, stopping the Function or collecting QA evidence does not deallocate
  the EP1 plan, EH TU or PEs. They keep billing until separately authorized
  retirement actually completes. Budget alerts do not cap charges.
- EH automatically ages messages out after **one day**, not the namespace/TU.
  LAW keeps the configured **30 days** of records after collection stops;
  retention expansion/long-term retention adds billable GB-months (public
  Analytics extended-retention rate **$0.12/GB-month**). Export/ingestion and
  platform diagnostics may continue after the intended request window.
  [Analytics retention](https://learn.microsoft.com/azure/azure-monitor/logs/data-retention-configure)
  includes 31 days in ingestion pricing; per-table exceptions (including
  App Insights tables with 90-day defaults) must be attested rather than
  assumed erased at day 30. Shortening retention also does not authorize
  purging data or eliminate a service's deletion-delay semantics.
- Blob/queue/table capacities are **not provisioned fixed disks**. Hot LRS
  charges stored byte-time plus operations. Source does not configure a storage
  management lifecycle, blob/version/delete retention policy, or automatic
  durable-state expiry. Versioning/soft-delete defaults or governance injection
  must be attested from safe configuration metadata before a bound is final.
  Count all retained versions, soft-deleted bytes, snapshots, indexes, leases,
  ACKs, outbox and quarantine, not just the current package. No state-content
  read or deletion is authorized. Hot has no cool/cold/archive early-deletion
  minimum; moving to those tiers would introduce minimum-duration and retrieval
  charges and is **not** assumed here.
- KV has **90-day soft-delete and purge protection** in source. Secret material
  is not automatically purged at hour 24; vault recovery/name reservation can
  outlast deletion. No purge is authorized. Standard secrets here have operation
  charges, not a fabricated 90-day secret-capacity charge; paid key/cert plans
  would need their own retained-object terms.
- Function EP1 includes its plan disk allocation; private run-from-package is
  Blob-backed, **not an Azure Files share or managed disk**. Retained ZIPs and
  repeated MI fetches cost blob capacity/operations/transfer above. Upload,
  private DNS/network access, build runner minutes and custodian licensing are
  in R if not already included in an established entitlement.
- For an illustrative **30 further days kept idle** (720 additional hours),
  floor compute + 5 PEs + 1 TU + 7 full-month zones + unchanged 10/1/1 GB
  storage is **$205.302**; node-based security allowances add **$29.2608**.
  Thus **$234.5628 additional**, conditional on that plan basis, before
  partial-hour buckets, brokered-connection billing periods, continuing
  operations/ingestion/export/scanning/G/L/R/retention overages. Reserve another
  $0.08 for one extra EH/five-PE charge hour and $0.12 per touched monthly
  brokered-connection period at the N=1 assumed four-connection count. A
  30-day interval can touch three calendar months, so conservative fixed-tail
  reserve becomes **$235.0028**, still before continuing usage and G/L/R.
  This is additional to the first day, not a total or permission to retain
  for 30 days. Without a finite approved retained lifetime the cost tail
  is **unbounded**, even if the one request never runs.

Technical gates belong to Infra/Agent/Telemetry: attest effective EP1 limits,
storage policies, inherited paid-plan applicability and private execution/
publication prerequisites, using permitted metadata or documented evidence.
Only contract/invoice/license entitlements remain owner/provider-only facts.
The owner then decides complete scope, spending envelope and retained lifetime;
approval does not substitute for technical discovery or authorize teardown.

The precise remaining model-provider gate is acceptance of
`OpenAI/gpt-5-mini/2025-08-07/eastus2/DataZoneStandard/capacity 1/NoAutoUpgrade`
under the exact fresh subscription/account/policies, then allocatable capacity,
provisioning and separately approved runtime admission. Catalog support and
0/300 Count headroom do not prove that gate. Null minimum/step and default 10
are not authority to increase capacity. Owner choices are the eventual supported
privacy/residency scope, complete spending/retained lifetime and custodians;
they cannot replace missing technical implementation or provider acceptance.
