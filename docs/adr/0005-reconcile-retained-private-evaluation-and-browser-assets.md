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
records metadata, exact receipt bindings, costs in conflict and remaining gates.

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
- **Trade-offs accepted:** retained disk/NAT/storage incur persistent costs while
  deallocated. The user-approved USD 53.42/month ceiling conflicts with a historical
  receipt's USD 63.42 figure and additional Servers P2 claim; do not silently
  promote that historical claim into new approval.
- **Open questions:** affected-track agreement; exact operating window and maximum
  running hours; named human custodian; current private access/routing acceptance;
  reconciled cost authority; supported service-side pending-upload/BYOS contract
  and safe disposition of unknown pending state. #138 stays open.
