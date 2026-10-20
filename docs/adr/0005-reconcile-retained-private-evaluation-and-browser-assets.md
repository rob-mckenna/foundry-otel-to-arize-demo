# ADR-0005: Reconcile retained private evaluation storage and Windows browser assets

## Status

**Proposed cross-track acceptance, 2026-10-19; historical provisioning already
completed.** Working as Lead (Architect / Tech Lead), actual `squad:lead` owner
of [#138](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/138).
This record does not grant provisioning, VM-start, registration or runtime authority.

The 2026-10-14 user approval is an operational scope approval, not evidence of
affected-track ADR agreement. Retained resources and consumed probe receipts
contradict a blanket “not implemented” description, but do not justify marking
the full decision Accepted. Infra, Agent and QA agreement remains outstanding.

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

Propose retaining and reconciling the existing dedicated keyless evaluation
storage and private Windows jumpbox through existing free Developer Bastion,
not repurposing Function storage or rebuilding ancillary infrastructure.
Preserve private storage/Foundry, existing security controls and human-only
credential custody. Keep NAT as the observed existing egress path; any proposed
egress replacement needs Infra ownership and separate reviewed authorization.

Treat these as separate acceptance stages:

1. Affected-track architecture agreement.
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
- **Trade-offs documented, not newly accepted:** retained disk/NAT/storage incur
  persistent costs while deallocated. Original $53.4184 rounds to the authorized
  $53.42/month; historical $63.4184 adds a $10 **Storage Defender** allowance,
  not Servers P2. Current 128-GiB Standard_LRS/HDD metadata contradicts historical
  E10 SSD, lowering the disk planning line from $9.60 to $5.888. Public calculator
  basis yields **$59.4884/month** (or $59.7064 using the historical $10 allowance),
  before variables; this still exceeds $53.42. Public compute $0.188/hour plus
  indicative P2 $0.02/node-hour gives $0.208/hour, not a verified contract charge.
  Retail P2 $0.006849/workload-unit-hour has an **unknown per-VM multiplier**.
  Closed-plan/receipt claims of expanded consent are secondary prose, not
  independent primary authority. No higher ceiling or protection disablement
  is recommended or authorized; actual invoice/protection scope remain unknown.
- **Prerequisites discovered:** existing same-VNet Developer Bastion/NAT,
  subnet NSG private TCP3389 allow then other-inbound deny, no VM public IP,
  Approved Blob/Foundry PEs and linked DNS, project MI's account-scoped Blob
  Contributor, private/keyless services, inherited VM P2 and configured storage
  scanning. Windows VM has **no MI**; human identity is separate. Trusted Launch
  and MDE extension provisioning are confirmed, not guest protection health.
  Both NIC effective-view reads failed without a VM start; configured rules/routes
  are not fresh effective-table or runtime-connectivity proof.
- **Open questions:** affected-track agreement; exact operating window and maximum
  running hours; named human custodian/access; untested current runtime access;
  primary cost authority within the original envelope, actual invoice/protection
  scope and workload-unit conversion; supported service-side pending-upload/BYOS contract
  and safe disposition of unknown pending state. #138 stays open.
