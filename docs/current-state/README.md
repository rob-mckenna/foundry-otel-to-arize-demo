# docs/current-state

**Status (2026-10-19): current bridge with bounded #139/#143 acceptance;
fresh private foundation/provider/runtime/end-to-end validation PENDING.**

Start with the [root README](../../README.md) for the supported offline setup and synthetic
demo, then the [mapping/export contract](telemetry-mapping-export-contract.md) for current
behavior, publication provenance and evidence gates.
Implementation, package publication, source capture, native delivery and independent Arize
parity are separate claims; destination parity remains **UNKNOWN**.

## Supported operations: one fresh path, narrow adoption, gated retirement

Start with [current operations](runbooks.md) and
[ADR-0004](../adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md).
The accepted fresh composition is modern-only and private: account/project/model,
private network/KV/host storage, Premium Function and telemetry infrastructure.
Source implementation and offline checks are reported complete by Infra;
**Ready for Validation** is not Validated. No #145 cloud validation/deployment
was performed, and no classic Hub/public fallback is supported.
Account/project/model alone is not agent-version publication or private runtime/
state readiness. Model/quota/residency/cost, network ownership, secure immutable
KV resolution and agent API/tool prerequisites remain explicit operator gates.

Adoption keeps the existing-resource entrypoints below narrow; never run fresh
main broadly over the live mixed RG. Retirement needs separate exact-ID approval,
positive consumer/governance clearance and recovery acceptance under the
[cleanup plan](resource-cleanup-plan.md), not RG teardown or vault purge.

[`architecture.md`](architecture.md) retains the implemented-path diagrams with scoped
limitations. Solid edges describe the implementation, not proof of live delivery.

## Modern Foundry tracing association

The [#139 tracing runbook](foundry-appinsights-tracing.md) describes the recovered
connection-only Bicep entrypoint, explicit same-auth adoption and separate optional
MI path. Reviewed source `2fb796d` passed native same-name adoption and identical
redeployment, then isolated clean creation/redeployment on 2026-10-17 UTC.
The runbook records exact retained test IDs, immutable receipts and Telemetry's
bounded fresh playground/source-table/export signoff. Arize Input is
**user-observed**, not independent full destination graph/output/token parity.
Source/build or association readback alone never proves telemetry delivery.

## Durable content correlation (#143)

The [durable runbook](durable-genai-correlation.md) records the deployed/enabled
existing demo and accepted native content transport with inline precedence.
Independently verified missing-inline fallback used **generated fixtures**;
no native missing-inline Foundry call was observed. Complete graph,
custom-correlation, source-total and full resource parity remain unproven;
this is not exactly-once delivery. Keep imported ACKs/checkpoints and the unrelated
ambiguous operational send quarantined; do not resend or replay.
These receipts do not validate a fresh modern foundation.

## Retained ancillary storage and Windows access (#138)

The [reconciliation and operator packet](private-storage-and-windows-jumpbox.md)
distinguishes existing keyless storage/private Windows resources from pending
cross-track ADR agreement and human navigation. The historically approved single
five-case registration attempt is **consumed (pending-upload HTTP 403)**, not
reusable authority. No after-shutdown VM start or inference/evaluation is authorized.
See [ADR-0005](../adr/0005-reconcile-retained-private-evaluation-and-browser-assets.md).

## Historical reference — not the active setup path

The validation reports, milestone audits and capability matrix linked below are
retained historical records. Their dated evidence remains intact, but earlier blanket
"validated" or "not implemented" summaries are superseded by the canonical contract above.
Do not execute their recipes or treat their checklists as fresh authorization.

See [`prompt-agent-execution-validation.md`](prompt-agent-execution-validation.md) for the
Prompt Agent execution validation procedure, checklist, and evidence record (#49), including an
explicit breakdown of what is proven by static tests/code review versus what still requires a
live Foundry deployment.

The old operational recipes have been replaced by the bounded fresh/adopt/retire
guide in [`runbooks.md`](runbooks.md); historical deployment receipts remain dated
evidence in their original runbooks.

For a capability-by-capability implementation status check (done / partial / not started, each
cross-checked against the actual code/IaC), see
[`/docs/architecture/capability-matrix.md`](../architecture/capability-matrix.md).

See [`separation-audit.md`](separation-audit.md) for the Milestone 4 current-state/future-state
separation audit (issue #14), a historical milestone check rather than current validation.

Only describe implementation under `/src` and `/infra` with explicitly scoped evidence. Known
limitations, unvalidated assumptions, and schema-mapping gaps must be called out explicitly here
rather than silently omitted (see `/.github/copilot-instructions.md` §16).

Conceptual/proposed designs do not belong here — see `/docs/future-state`.
