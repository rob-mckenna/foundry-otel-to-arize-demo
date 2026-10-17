# docs/current-state

**Status: CURRENT-STATE implementation; NOT independently E2E validated (2026-10-16).**

Start with the [root README](../../README.md) for the supported offline setup and synthetic
demo, then the [mapping/export contract](telemetry-mapping-export-contract.md) for current
behavior, publication provenance, held binding/settings work and evidence gates.
Implementation, package publication, source capture, native delivery and independent Arize
parity are separate claims; destination parity remains **UNKNOWN**.

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

## Historical reference — not the active setup path

The validation reports, milestone audits, capability matrix and runbooks linked below are
retained historical records. Their dated evidence remains intact, but earlier blanket
"validated" or "not implemented" summaries are superseded by the canonical contract above.
Do not execute their recipes or treat their checklists as fresh authorization.

See [`prompt-agent-execution-validation.md`](prompt-agent-execution-validation.md) for the
Prompt Agent execution validation procedure, checklist, and evidence record (#49), including an
explicit breakdown of what is proven by static tests/code review versus what still requires a
live Foundry deployment.

Historical operational runbooks (superseded for setup):
[`runbooks.md`](runbooks.md).

For a capability-by-capability implementation status check (done / partial / not started, each
cross-checked against the actual code/IaC), see
[`/docs/architecture/capability-matrix.md`](../architecture/capability-matrix.md).

See [`separation-audit.md`](separation-audit.md) for the Milestone 4 current-state/future-state
separation audit (issue #14), a historical milestone check rather than current validation.

Only describe implementation under `/src` and `/infra` with explicitly scoped evidence. Known
limitations, unvalidated assumptions, and schema-mapping gaps must be called out explicitly here
rather than silently omitted (see `/.github/copilot-instructions.md` §16).

Conceptual/proposed designs do not belong here — see `/docs/future-state`.
