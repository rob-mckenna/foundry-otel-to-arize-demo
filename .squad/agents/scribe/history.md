# Project Context

- **Project:** foundry-otel-to-arize-demo
- **Created:** 2026-10-03

## Core Context

Agent Scribe initialized and ready for work.

## Recent Updates

📌 Team initialized on 2026-10-03

## Learnings

Initial setup complete.

## Work record — 2026-10-19 — #143 acceptance in progress

- For Rob McKenna, appended supplied verified #143 rollout facts to existing `log/2026-10-14T11-07-28.4106103-04-00-squad-owned-execution-wave.md`: commits `cce9eb3` and `f650fed983a687eb97211b634af3d99e7286d6e1`, 260 passing tests/seven passing CI jobs, one deployment, ACK/import and grant cleanup, resumed processing, one native synthetic call, and independent Arize trace/content/parentage evidence without prompt bodies.
- Final acceptance and independent source-content fallback eligibility remain pending with Infra/Telemetry; no resource-attribute live-parity claim, closure, or merge. VM still running for bounded acceptance; deallocation required at end. This is factual work capture only, not a new decision, preference, policy, or general learning.

## Work record — 2026-10-19T13:19:03.099-04:00 — #145 source phase complete; live validation pending

- Requested by Rob McKenna; supplied facts recorded without new research or test execution. User approved modern-only cleanup direction; ADR-0004 accepted. Source commits: `b2b10ce` architecture/inventory/offline-client clarification; `8f250fc` Lead-approved active guides; `3358374` modern-only private Infra implementation.
- Source removes classic `foundry-project.bicep` and broad teardown. Modern AIServices/project/model composition includes private Key Vault, keyless storage, Premium Function VNet integration, five private endpoints/seven DNS zones, fresh or read-only existing networking, private Blob managed-identity package delivery without Azure Files, and explicit group/three-table export/state. Fresh triggers are disabled; narrow tracing/durable entrypoints remain unchanged.
- Reported offline compilation/naming, 26 foundation/tracing tests and five durable-infra tests passed. Independent Lead verdict: APPROVE_WITH_GATES for source and latest guides. Official plan is Ready for Validation, NOT Validated: no cloud changes, fresh-provider/private/idempotence/E2E proof, or live cleanup established.
- Fresh model/quota/cost/residency, secure custody, agent state, and exact classic-consumer/governance/recovery/exact-ID confirmation remain gates. Four-candidate read-only clearance preflight is active with Infra `4ed6931e` and Agent; it grants no deletion authority. Preserve existing modern foundation/pipeline, ledger/checkpoints/quarantine, #138 retained assets, #139 fixtures and dev telemetry stack.
- #143/#144 are already complete; no new delivery claim or resend. Draft PR #146 remains open, not ready or merged. Parent root README current status was corrected; cleanup-plan status document remains pending commit.
- Applicable Lead inbox `lead-145-modern-foundation.md` inspected and retained unmodified. Canonical decision merge deferred: measured decisions.md at 52,079 bytes, with 0 entries older than 30 days and 16 older than seven days; charter requires seven-day archival before merge, conflicting with this task's append-only/no-new-notes scope. No archival, consolidation or inbox deletion performed. No Git staging/commit/push/branch, cloud, source/runtime/document-owner edits or secret-file reads performed.

- Subsequent coordinator handoff: requester explicitly approved merge/issue closure. All seven checks passed for `9a62077`; remaining fresh/provider/private/E2E validation is tracked in #147 and exact-resource live retirement in #148. No cloud deletion or new deployment is implied by source merge.

## Work record — 2026-10-19 — #148 first retirement phase; contained-cascade clarification

- User approved only four exact classic demo/dev Project+Hub workspace IDs in `fotoa-demo-rg`, projects before hubs; all other resources excluded. Infra submitted exactly one DELETE, `fotoa-demo-aiproj-eastus2`, and verified HTTP 404 `ResourceNotFound` at `2026-10-19T18:41:58Z`. The other three were present and unsubmitted at that checkpoint. An initial post-delete `UserError` stopped execution and was later resolved read-only.
- Preservation comparison: 79 non-target resources, 48 network IDs, eight zones/25 DNS records and 90 remaining roles unchanged; VM deallocated. One assignment scoped to the deleted Project and granted to its own managed identity disappeared through provider deletion, not explicit IAM cleanup.
- Following the parent's new preservation clarification, user selected `allow-contained-cascade`: “Continue: allow Azure to remove roles scoped only to the workspaces being deleted.” This permits automatic removal only of roles scoped to approved deleted workspaces; explicit IAM cleanup, outside-target/shared role removal, networking/DNS deletion, force/purge and fresh deployments remain unauthorized.
- Infra is resuming the remaining THREE; their deletion is NOT YET established. Never repeat the original demo-project DELETE. Preserve phase-one receipt/intent and keep continuation evidence separate. #148 remains open, including unapproved exclusive-network scope; fresh #147 validation remains separate, and source #145/#146 are complete.
- Evidence references supplied by parent: `.azure-sandbox\issue148-exact-workspace-retirement.json`, `.azure-sandbox\issue148-preservation-comparison.json` and issue #148. Parent posted factual outcomes/consent in #148 and updated the current-state cleanup document locally. This entry records supplied facts only; no cloud investigation or future-success claim.

## Work record — 2026-10-19 — #148 four-workspace retirement complete; dependencies remain open

- Parent reviewed final receipts/comparison: all four approved classic workspaces verified HTTP 404 `ResourceNotFound` on 2026-10-19 UTC: demo Project `18:41:58`, demo Hub `20:12:26`, dev Project `20:31:08`, dev Hub `20:35:31`. Exactly one DELETE per workspace; all delete/wait commands exited 0.
- After contained-role clarification, demo Hub deletion exposed its own managed identity's resource-group grant removal and four Hub-GUID DNS record removals; execution stopped. Owner separately accepted those observed demo effects and authorized ONLY exact dev automatic equivalents (resource-group role `2758236d` and four dev-Hub-GUID DNS records), then the dev pair completed. No explicit IAM, DNS or network cleanup occurred; this is not broad cleanup authority.
- Final comparison at `20:44:00Z`: primary resources 83→79 (only four approved removals), roles 91→85 (four contained and two exact resource-group automatic removals), DNS records 25→17 (eight exact Hub-GUID A-record removals). All 79 non-target primary IDs/metadata, 48 network IDs, eight zones, remaining assignments/DNS, modern project, Event Hub consumer/host-state containers, sender and both legacy Project Key Vault grants preserved; validation VM deallocated. Original evidence/guards hash-verified unchanged.
- No runtime/model/data-content validation, deployment, replay, force/purge or new grants. Final evidence: `.azure-sandbox\issue148-exact-workspace-retirement-final.json` and `.azure-sandbox\issue148-exact-workspace-retirement-final-aggregate-preservation.json`; parent owns #148/public current-state documentation updates. #148 remains OPEN for separately unapproved exclusive private endpoints/NICs/other dependencies; #147 fresh provider/private/repeat/E2E validation remains OPEN and unperformed. Supplied verified facts only; earlier first-phase history retained unchanged.
