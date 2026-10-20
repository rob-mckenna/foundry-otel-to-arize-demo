# ADR-0005: Reconcile retained private evaluation storage and Windows browser assets

## Status

**Proposed cross-track acceptance, updated 2026-10-20; historical provisioning already
completed.** Working as Lead (Architect / Tech Lead), actual `squad:lead` owner
of [#138](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/138).
This record does not grant provisioning, VM-start, registration or runtime authority.

**Owner-approved direction, not missing consent:** requester Rob McKenna's
2026-10-20T04:37:07.301Z approval explicitly authorizes cost reconciliation and
existing Windows/Developer Bastion private-access acceptance with protection
preserved. Receipt SHA256
`C971F23D46D9C7033102A2F503EABA83E0E08755ADE37E82C43FD888A8C1CC5E`.
The old $53.42 target no longer binds; no numeric ceiling was invented.

Lead has applied the [existing ADR process](README.md), which defines Accepted
as affected-track agreement, and team consensus governance. Operational owner
approval does not fabricate Infra, Agent or QA concurrence. Their existing
technical evidence is not an ADR assent. Narrow remaining **decision-status**
criterion: actual concurrence from those three tracks on retaining the existing
protected ancillary assets/minimal private access, with no new runtime or
registration authority. Until recorded, this ADR remains Proposed. No new
architecture-decision issue is needed for this retrospective record under that
process. Human navigation, finite cost/runtime bound and provider acceptance are
separate technical criteria, not a request to repeat general owner approval.

## Context

Issue #138 describes dedicated evaluation storage, a project AAD connection and
private Windows Foundry UI access without changing the telemetry architecture.
Its original “Proposed / not implemented” summary predates deployment. The closed,
read-only root `.azure/deployment-plan.md` records later successful storage and
Windows deployments and an unsuccessful, consumed registration attempt.
Current main `2219075` has no ancillary ADR or the historical
`private-storage-and-windows-jumpbox.md` runbook referenced in that plan.
Neither that missing document nor missing ancillary source in current main means
the retained cloud resources should be recreated.

Historical references to “ADR-0003 remains Proposed” must not be applied to the
present ADR-0003: that number now identifies the independently accepted durable
GenAI correlation decision. ADR-0004 governs modern foundation/retirement,
not ancillary acceptance. This new number avoids rewriting either decision.

The [reconciliation and operator packet](../current-state/private-storage-and-windows-jumpbox.md)
records metadata, exact receipt bindings, itemized costs/provenance and remaining gates.

## Decision

Record owner-approved direction to retain and reconcile the existing dedicated keyless evaluation
storage and private Windows jumpbox through existing free Developer Bastion,
not repurposing Function storage or rebuilding ancillary infrastructure.
Preserve private storage/Foundry, existing security controls and human-only
credential custody. Keep NAT as the observed existing egress path; any proposed
egress replacement needs Infra ownership and separate reviewed authorization.

Treat these as separate acceptance stages:

1. Affected-track architecture agreement (still Proposed; owner direction approved).
2. Historical provisioning and present control-plane metadata.
3. Historical browser/RDP/private DNS/TLS prerequisites.
4. Human Windows/Entra/project navigation.
5. Consumed registration attempt and any separately authorized future attempt.
6. Inference/evaluation readiness and a separate fresh runtime allowance.

Exactly one historically approved fresh five-case registration attempt is recorded
as consumed. It failed at pending-upload HTTP 403 before Blob upload or dataset
PUT. Do not retry or use its receipt as authorization. Do not infer a successful
dataset, completed five-case upload, service-side route or evaluation.

## Consequences

- **Current-state impact:** documentation correction only. Existing ancillary
  resources are implemented, retained operational assets with bounded evidence;
  no change to the Application Insights → LAW → Event Hub → Function → Arize bridge.
- **Future-state impact:** None. Direct OTLP remains conceptual and unimplemented.
- **Security considerations:** human retrieves the designated Windows credential
  privately from Key Vault; agents never extract it. No public VM IP, Internet
  RDP, paid Bastion, shared-key storage or public Foundry/storage fallback.
  Preserve governance, antimalware, project/VM identities and existing grants.
- **Observability considerations:** None to span IDs, parent/correlation IDs,
  tokens or telemetry mapping. Navigation/registration is not delivery proof.
  Preserve ambiguous sends, ledger/checkpoint/ACK/quarantine state without replay.
- **Trade-offs documented; revised necessary-cost direction approved, not a full quote:** retained disk/NAT/storage incur
  persistent costs while deallocated. Original $53.4184 rounds to the authorized
  $53.42/month; historical $63.4184 adds a $10 **Storage Defender** allowance,
  not Servers P2. Current 128-GiB Standard_LRS/HDD metadata contradicts historical
  E10 SSD, lowering the disk planning line from $9.60 to $5.888. Public calculator
  basis yields **$59.4884/month** (or $59.7064 using the historical $10 allowance),
  before variables; this still exceeds $53.42. Public compute $0.188/hour plus
  indicative P2 $0.02/node-hour gives $0.208/hour, not a verified contract charge.
  Retail P2 $0.006849/workload-unit-hour has an **unknown per-VM multiplier**.
  Closed-plan/receipt claims of older expanded consent remain secondary prose.
  The new primary approval supersedes the old target but supplies no numeric
  ceiling. Protection disablement remains excluded; invoice/protection scope and
  a finite all-in bound remain unverified. The complete conditional formula,
  P2/server sensitivity, scan-cap sensitivity and explicit lifetime/quantity
  exceptions are in the [dated acceptance handoff](../current-state/issue138-private-access-window.md).
- **Prerequisites discovered:** existing same-VNet Developer Bastion/NAT,
  subnet NSG private TCP3389 allow then other-inbound deny, no VM public IP,
  Approved Blob/Foundry PEs and linked DNS, project MI's account-scoped Blob
  Contributor, private/keyless services, inherited VM P2 and configured storage
  scanning. Windows VM has **no MI**; human identity is separate. Trusted Launch
  and MDE extension provisioning are confirmed, not guest protection health.
  Both NIC effective-view reads failed without a VM start; configured rules/routes
  are not fresh effective-table or runtime-connectivity proof.
- **Operating handoff:** candidate 2026-10-20 05:30–06:00 UTC / 01:30–02:00 EDT,
  after #148 release at 04:49:29Z, at most 30 allocated minutes with the last five
  reserved for deallocation. NOT activated: no verified actual human availability,
  operator/custodian/access, finite cost-bound inputs or completed official gates.
  Keep 19:00 Eastern shutdown; no VM start in this step.
- **Open questions:** actual Infra/Agent/QA agreement; actual human identity/custody/
  availability and runtime access; finite retained lifetime/usage allowances,
  actual invoice/protection scope and workload-unit conversion; supported
  service-side pending-upload/BYOS contract and safe disposition of unknown
  pending state. #138 stays open. No broad owner-consent question remains.
