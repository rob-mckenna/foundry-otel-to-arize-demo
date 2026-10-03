# Squad Decisions

## Active Decisions

### 2026-10-02: Function App ↔ Key Vault sequencing in Infrastructure Deployment epic

**By:** Infra

**What:** While drafting the Infrastructure Deployment epic backlog (`.squad/.scratch/infra-backlog.md`), Infra flagged a circular-looking dependency between Issue 4 (Azure Function App provisioning, needs Key Vault to exist for Key Vault reference app settings) and Issue 5 (Key Vault + managed identity wiring, needs the Function App's managed identity to exist to grant it RBAC roles).

**Why:** Proposed resolution — split provisioning from wiring: provision Key Vault shell and Function App shell independently (no cross-references yet), then run a follow-up wiring step that adds the Key Vault references to the Function App's settings and grants the Function's identity RBAC on the Key Vault. This avoids a true circular dependency in deployment ordering. Flagged to Lead to confirm this sequencing before work on Issues 4/5 starts.

**Resolution:** Lead confirmed and adopted the two-phase deploy approach (see below) — captured explicitly in issue #18's body.

### 2026-10-02: Wave 2 Backlog Generation Complete

**By:** Lead

**What:**

#### Summary

Executed the full GitHub repository setup for `rob-mckenna/foundry-otel-to-arize-demo` from the 5
specialist scratch drafts (Lead, Infra, Agent, Telemetry, QA) plus the Key Vault/Function App
circular-dependency flag from Infra.

- **Labels created:** 19 (Architecture, Infrastructure, PromptAgent, ApplicationInsights, Observability,
  OpenTelemetry, OpenInference, Arize, Documentation, Demo, Security, Healthcare, CurrentState,
  FutureState, GoodFirstIssue, Blocked, Priority-High, Priority-Medium, Priority-Low). Default `bug` label
  left as-is. "Documentation" merged case-insensitively into GitHub's pre-existing default "documentation"
  label — expected behavior, not a defect.
- **Milestones created:** 5 — "Milestone 1: Foundation" (#3), "Milestone 2: Telemetry Pipeline" (#2),
  "Milestone 3: Arize Integration" (#4), "Milestone 4: Customer Demo Readiness" (#5), "Milestone 5:
  Future-State Design" (#6). Numbers are non-sequential due to a mid-creation PowerShell quoting bug that
  corrupted the first attempt (fixed by deleting and recreating); all subsequent issue assignments used
  milestone **titles**, which resolve correctly regardless of the underlying numeric ID — no functional
  impact.
- **Epic issues created:** 10 — #1 Architecture and Design, #2 Infrastructure Deployment, #3 Prompt Agent
  Implementation, #4 Application Insights Instrumentation, #5 Telemetry Export Pipeline, #6 Arize
  Integration, #7 Dashboarding and Queries, #8 Demo Experience, #9 Documentation, #10 Future-State
  Architecture. Each epic body now contains a real `- [ ] #N` checklist of its child issues.
- **Total issues created:** 65 (#1–#65 inclusive, no gaps or duplicates, verified via `gh issue list`).
- **GitHub Project (v2):** **NOT created.** The `GH_TOKEN` used in this environment has scopes
  `gist, read:org, read:packages, repo, workflow` but lacks `project`/`read:project`, and `gh auth refresh`
  cannot run interactively while `GH_TOKEN` is set. This is a hard environment limitation, not a retry-able
  failure. **Manual setup required** (documented in `SQUAD_BOOTSTRAP.md`): a repo/org admin with
  interactive `gh auth login` (or the web UI) should run `gh project create --owner rob-mckenna --title
  "Foundry OTel to Arize Demo"`, add a Status field with options Backlog / Ready / In Progress / Review /
  Demo Validation / Complete, then bulk-add issues #1–#65 via `gh project item-add` — roughly a 2-minute
  task once proper scopes are available. Project URL: **N/A** pending that manual step.
- **Key Vault / Function App sequencing:** resolved as a two-phase deploy (provision both resource shells
  independently, then cross-wire managed-identity RBAC access) rather than a circular blocker — captured
  explicitly in issue #18's body, per the guidance in
  `.squad/decisions/inbox/infra-backlog-circular-dep-flag.md`.
- **Docs written:** `SQUAD_BOOTSTRAP.md` (updated in place), `docs/traceability-matrix.md`,
  `docs/demo-validation-plan.md`, `docs/next-actions.md`.
- **Cleanup:** deleted all 5 `.squad/.scratch/*.md` draft files and the local `.issuegen` temp folder (not
  git-tracked) once their content was fully incorporated into real issues/docs.

**Why:**

#### Caveats for the team

1. GitHub Project (v2) board requires manual one-time setup by someone with interactive `gh auth login`
   access (see `SQUAD_BOOTSTRAP.md` → "GitHub Project Board" section for exact steps).
2. Milestone numeric IDs are non-sequential (Milestone 1 = id 3, etc.) — cosmetic only, titles are correct
   and all issue↔milestone assignments resolved correctly by title.
3. Seven dependency cross-references in the original Demo Experience issue batch (#49–#58) had off-by-two
   numbering errors from hand-predicting sequential issue numbers; all seven were corrected via
   `gh issue edit` before this decision was filed. Verified no remaining incorrect references.

### 2026-10-02: GitHub Project (v2) board setup complete

**By:** Infra

**What:** Completed the previously deferred GitHub Project (v2) board setup now that the `gh` CLI token has
`project`/`read:project` scopes.

- **Project URL:** https://github.com/users/rob-mckenna/projects/7 (project number 7, owner `rob-mckenna`,
  title "Foundry OTel to Arize Demo").
- **Status columns (single-select field, in order):** Backlog, Ready, In Progress, Review, Demo Validation,
  Complete. Set via `gh api graphql` `updateProjectV2Field` mutation on the default Status field (the
  built-in `gh project field-create`/`field-list` commands don't support editing single-select options
  directly) — verified afterward with `gh project field-list 7 --owner rob-mckenna`.
- **Items added:** all 65 issues (#1–#65) from `rob-mckenna/foundry-otel-to-arize-demo`, added via
  `gh project item-add` in a loop. Verified count via `gh project item-list 7 --owner rob-mckenna --format
  json -L 100` → 65 items, 0 errors.
- **Initial status:** all 65 items set to `Backlog` via `gh project item-edit --field-id <Status> --single-select-option-id <Backlog option id>` (items have no Status by default when added — this is not automatic).
- **Docs updated:** `SQUAD_BOOTSTRAP.md` → "GitHub Project Board" section now points at the real URL and
  confirms the board is live, replacing the prior "manual setup required" caveat.

**Why:** This was blocked in a prior pass (see earlier decision log entry, "Wave 2 Backlog Generation
Complete") because the token in use at the time lacked `project`/`read:project` scopes. Those scopes are
now available, so the deferred board setup was finished end-to-end in this pass with no remaining manual
steps.

**Gotchas for future automation of `ProjectV2SingleSelectField` options via `gh api graphql`:**
- `gh api graphql -F var=@file.json` does NOT JSON-parse the file into a GraphQL list/object variable — it
  passes the raw file contents as a single string, causing a "provided invalid value... to be a key-value
  object" error. Inline the array/object literally in the mutation query text instead of passing it as a
  GraphQL variable from a file.
- Files written via PowerShell's `Out-File`/here-string default to UTF-8 **with BOM**, which breaks `gh api
  graphql`'s query parser (`UNKNOWN_CHAR ("\xBB")` at position [1,1]). Write query files with
  `[System.IO.File]::WriteAllText(path, content, (New-Object System.Text.UTF8Encoding $false))` to force
  BOM-less UTF-8.

### 2026-10-02: Lead — Milestone 1 (Foundation) complete

**By:** Lead

**What:** Completed all 3 assigned Milestone 1 ("Foundation") issues, each on its own branch with
its own PR, left open for review (not merged):

| Issue | Branch | PR |
|---|---|---|
| #12 — Repository structure scaffolding and enforcement | `squad/12-repository-structure-scaffolding` | https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/67 |
| #11 — Author current-state architecture Mermaid diagram set | `squad/11-current-state-architecture-diagrams` | https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/68 |
| #13 — Architecture Decision Record (ADR) log and process | `squad/13-adr-log-and-process` | https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/70 |

Worked in dependency order: #12 first (foundational structure), then #11 (architecture diagrams,
references `/docs/current-state/`), then #13 (ADR log, depends on #12). Each PR branched fresh from
`main` (not stacked).

**Why / notable findings:**

1. **Shared working directory concurrency hazard.** This session's working copy
   (`C:\Repos\foundry-otel-to-arize-demo`) is a single shared git working directory with no
   per-agent worktree isolation — multiple Squad members (Infra on #15/#16, Agent on #24, me on
   #11/#12/#13) were operating against it concurrently during this run. I observed real races:
   my commit for #12 landed on Infra's `squad/16-app-insights-log-analytics` branch, and Infra's
   Foundry-hub Bicep commit landed on my `squad/12-repository-structure-scaffolding` branch,
   because `git checkout` calls from different agents interleaved between my branch-create and
   commit steps. **Recommendation for the team: adopt `git worktree add` per active agent/branch**
   (one physical directory per in-flight branch) instead of sharing a single working directory, or
   serialize branch-creation-through-commit as an atomic critical section some other way. I
   recovered using `git update-ref` to move the misplaced commits onto the correct branches without
   touching the working tree, but this was discovered by chance (checking `git log <branch>
   --oneline` after an unexpected commit message appeared) — a less attentive pass could have
   silently shipped the wrong diff in the wrong PR.
2. **`.github/` and most of `.squad/` were never committed to git in this repo** — they exist only
   as untracked working-tree files (confirmed via `git ls-tree -r origin/main`, which shows only 6
   files total on `main`). My #13 PR is the first to commit `.github/copilot-instructions.md` and
   `.github/ISSUE_TEMPLATE/architecture-decision.yml` as a side effect of needing to edit them —
   flagged explicitly in that PR's description. Other untracked content (`.squad/`, remaining
   `.github/` subdirectories, `.gitignore`, `.gitattributes`, `.vscode/`, `.copilot/`, `.mcp.json`)
   is still uncommitted; some other agent/process should decide what belongs in git vs. local-only
   config.
3. Local `main` was 1 commit ahead of `origin/main` at the start of this run (a Scribe decisions
   merge commit, `5045f8e`); I branched from local `main` as instructed rather than diverging from
   the team's existing local history, so each of my 3 PRs' diffs includes that pre-existing commit
   until someone pushes `main` to sync it. Not something I changed or need to fix — flagged for
   awareness only.

### 2026-10-02: Infra — Milestone 1 ("Foundation") infrastructure complete — 5 PRs open

**Author:** Infra (Infrastructure/DevOps Engineer)

#### Summary

All 5 assigned Milestone 1 Foundation infra issues have corresponding PRs
open against `main` (none merged yet — intentionally left for review per
task instructions). Each PR is Bicep-only, parameterized, idempotent,
tagged per the naming/tagging convention, and wires every secret-capable
resource to Key Vault + managed identity (no connection strings/secrets in
source).

| Issue | PR | Branch | Module added |
|---|---|---|---|
| #15 — Provision Azure AI Foundry Project | [#66](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/66) | `squad/15-provision-foundry-project` | `infra/modules/foundry-project.bicep` |
| #16 — Provision Application Insights + Log Analytics | [#69](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/69) | `squad/16-app-insights-log-analytics` | `infra/modules/app-insights.bicep` |
| #18 — Provision Key Vault shell + managed identity wiring | [#71](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/71) | `squad/18-key-vault-managed-identity` | `infra/modules/key-vault.bicep` |
| #20 — Enforce naming/tagging convention | [#72](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/72) | `squad/20-naming-tagging-convention` | `infra/modules/naming.bicep` (+ retrofit of #15/#16/#18) |
| #21 — Document/implement network requirements | [#74](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/74) | `squad/21-network-requirements` | `infra/modules/networking.bicep` (optional private endpoints) |

#### Important: merge order matters

Each PR branch is a **full standalone snapshot** carried forward from the
previous issue's branch (not stacked in GitHub's sense), because `main`
does not have `/infra` yet and each issue needed to be independently
reviewable. This means PRs #66 → #69 → #71 → #72 → #74 contain
increasingly large, overlapping diffs against `main` and **must be merged
in that exact order** (#15, #16, #18, #20, #21). Merging out of order will
produce conflicts or drop the naming/tagging retrofit from #20. After #66
merges, GitHub should auto-shrink the diff on the remaining 4 PRs; repeat
after each merge.

#### Path convention conflict with PR #12 (Lead)

Lead's repository-scaffolding PR #12 (branch
`squad/12-repository-structure-scaffolding`, not yet merged as of this
writing) establishes `/infra/bicep/` and `/infra/terraform/` as flat
top-level directories. My 5 PRs instead use `/infra/modules/*.bicep` (plus
`/infra/main.bicep`, `/infra/main.parameters*.json`, `/infra/README.md`,
`/infra/scripts/`), per this task's explicit instructions. **This is an
unresolved structural conflict** — whichever of PR #12 or this Milestone 1
set merges second will likely need a path reconciliation (either moving
`infra/modules/*.bicep` under `infra/bicep/modules/`, or updating #12 to
match). Flagging for Lead/coordinator to decide the final convention before
merging both; I did not block on it since #12 was unmerged/in-flight when
I started.

#### Coordination notes for Lead / Agent (downstream Prompt Agent work)

Outputs exposed by `infra/main.bicep` for anything downstream (e.g. the
Prompt Agent deployment, a future Function App/telemetry pipeline) to
consume:

- `foundryProjectResourceId`, `foundryProjectEndpoint`,
  `foundryProjectPrincipalId` — from the Foundry project module (#15).
- `logAnalyticsWorkspaceId`, `appInsightsResourceId` — from the App
  Insights module (#16). The Application Insights **connection string is
  never output in plaintext** — it's written to the Key Vault as a secret
  (name documented in `infra/modules/app-insights.bicep`) when a
  `keyVaultName` is supplied; downstream compute should read it from Key
  Vault via its own managed identity, not from a Bicep output.
- `keyVaultResourceId`, `keyVaultName` — from the Key Vault module (#18).
  Any new compute resource (e.g. a future Function App for the telemetry
  pipeline) that needs secrets should: (1) deploy with a system-assigned
  managed identity, (2) add its `principalId` to the Key Vault module's
  `readerPrincipalIds` (or `writerPrincipalIds`) array in a follow-up
  deployment/module call — this is the documented two-phase pattern in
  `infra/modules/key-vault.bicep` and `infra/README.md`.
- `privateEndpointsEnabled` — from the networking module (#21), `false` by
  default. Only relevant if a future environment turns on
  `enablePrivateEndpoints`; does not affect the default demo deployment.
- Resource naming pattern everything above follows: `{project}-{env}-{resourceType}-{region}`,
  e.g. `fotoa-demo-aiproj-eastus2`, `fotoa-demo-kv-eastus2` — implemented
  by `infra/modules/naming.bicep`'s `buildResourceName()` helper (#20). Any
  new module referencing these resources by name should derive it the same
  way rather than hardcoding a name string.

#### Known limitations (apply across all 5 PRs)

- No `az bicep build` / `az deployment group what-if` / live deploy
  validation was possible from the automated environment that authored
  these PRs (no usable `az` CLI profile, no standalone `bicep` binary).
  Flagged as a reviewer action item in every PR's "Current Limitations".
- CI wiring for the naming/tagging validation script (issue #20) could not
  be pushed as a `.github/workflows/*.yml` file — the `gh`/git credential
  in this environment lacks the `workflow` OAuth scope. Documented as a
  manual pre-merge step (`infra/scripts/validate-naming.ps1`) instead.
- The private-endpoint variant added in #21 was reviewed for syntax only,
  not deployed/torn down against a live subscription.

#### Status

All 5 PRs open, unmerged, awaiting review. No further Infra action planned
for this milestone unless review feedback requires changes.

### 2026-10-03: Agent — Milestone 1 "Foundation" (Application/Prompt Agent Developer) complete

**From:** Agent (Application / Prompt Agent Developer)
**Status:** All 8 assigned issues implemented; PRs open for review (none merged by me — awaiting review per task instructions).

#### Summary

Implemented the Foundry Prompt Agent at `src/prompt-agent/` (Python package)
across 8 stacked branches/PRs, issues #24–#31, in dependency order. Each
issue is its own branch/PR; later issues are intentionally stacked on
earlier (unmerged) branches since each genuinely depends on the previous
issue's code — this is called out explicitly in every PR body.

#### PRs opened (none merged — all open for review)

| Issue | PR | Branch | Depends on |
|---|---|---|---|
| #24 Scaffold Foundry Prompt Agent project structure | [#73](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/73) | `squad/24-scaffold-prompt-agent-project` | `origin/main` |
| #25 Core prompt/response flow + synthetic scenarios | [#75](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/75) | `squad/25-core-prompt-response-flow` | `squad/24-...` |
| #26 OpenTelemetry SDK setup and bootstrap | [#76](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/76) | `squad/26-otel-sdk-bootstrap` | `squad/25-...` |
| #27 Instrument every model/tool call with spans | [#77](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/77) | `squad/27-instrument-model-tool-calls` | `squad/26-...` |
| #28 OpenInference attribute mapping | [#78](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/78) | `squad/28-openinference-attributes` | `squad/27-...` |
| #29 Correlation ID / trace-span propagation | [#79](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/79) | `squad/29-correlation-id-propagation` | `squad/28-...` |
| #30 Retry/error-handling with full traceability | [#80](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/80) | `squad/30-retry-error-handling` | `squad/29-...` |
| #31 Unit tests for agent instrumentation | [#81](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/pull/81) | `squad/31-unit-tests` | `squad/30-...` |

All 8 branches pushed to `origin`. **Recommended merge order: #24 → #25 → … → #31** (in that exact sequence) since each PR's diff is only meaningful relative to its stacked parent merging first.

#### Coordination notes for Telemetry

- **Exact OpenInference attribute names used** (package
  `openinference-semantic-conventions==0.1.39`, pinned `>=0.1.39,<0.2.0` —
  the `0.1.x` trace semantic-convention spec):
  - `openinference.span.kind` — values used: `CHAIN` (on `prompt_agent.invoke`), `TOOL` (on `tool.lookup_plan_details`), `LLM` (on `llm.chat_completion` / `llm.chat_completion.attempt`)
  - `input.value` / `output.value` — present on all three span types above
  - `llm.model_name`, `llm.token_count.prompt`, `llm.token_count.completion`, `llm.token_count.total` — on the LLM span only
- **Correlation ID attribute**: `correlation.id` (custom key — not an
  OpenInference/OTel standard attribute; chosen because neither spec
  defines one). Generated as a `uuid4` per `PromptAgent.invoke()` call
  unless the caller supplies one. Present on every span in a request's
  tree, including every retry-attempt span.
- **Retry attributes** (new in #30, also custom keys): `retry.attempt`
  (1-indexed), `retry.max_attempts`, `retry.will_retry` — on
  `llm.chat_completion.attempt` spans only.
- **Span names**: `prompt_agent.invoke` (INTERNAL), `tool.lookup_plan_details` (CLIENT), `llm.chat_completion` (CLIENT), `llm.chat_completion.attempt` (CLIENT, one per retry attempt, nested under `llm.chat_completion`).
- If the Arize/Telemetry ingestion pipeline expects different attribute
  names/formats (e.g. a different OpenInference spec minor version, or a
  different correlation-ID key), please flag it against PR #78 (attributes)
  or #79 (correlation ID) before those merge — changing the attribute
  surface later is cheap now, more disruptive once Arize dashboards/queries
  depend on these exact names.

#### Coordination notes for Infra

- **Expected App Insights connection string env var name:**
  `APPLICATIONINSIGHTS_CONNECTION_STRING` (the standard Azure Monitor OTel
  exporter convention). `prompt_agent/telemetry.py` reads this exact name;
  if unset, it falls back to a `ConsoleSpanExporter` (so the agent still
  runs without any provisioned Azure resources — this sandbox never had a
  live App Insights instance to validate against, see "Limitations" below).
  Once #16/#18 provision a real instance, set this env var (ideally via Key
  Vault reference on the hosting App Service / Function App) and the
  exporter will switch over with no code change.
- Install the optional `azure` extra (`pip install -e ".[azure]"`) to pull
  in `azure-monitor-opentelemetry-exporter` — it's optional specifically so
  the scaffold still builds/runs/tests without it.
- Resource attributes set on every span: `service.name` (env
  `OTEL_SERVICE_NAME`, default `foundry-prompt-agent`), `service.version`
  (env `OTEL_SERVICE_VERSION`, default `0.1.0`), `deployment.environment`
  (env `DEPLOYMENT_ENVIRONMENT`, default `dev`) — Infra may want to set
  `DEPLOYMENT_ENVIRONMENT` explicitly per deployment stage (dev/test/prod)
  once environments exist.

#### Limitations / explicitly not yet validated

- The Azure Monitor exporter code path (`AzureMonitorTraceExporter`) has
  never been exercised against a live Application Insights instance in this
  sandbox — only the console-exporter fallback path was validated. This is
  flagged in every relevant PR (#26 onward) rather than claimed as tested.
- Real Foundry Prompt Agent SDK integration is fully stubbed
  (`StubFoundryModelClient` in `model_client.py`, clearly marked `# STUB:
  replace with real Foundry Prompt Agent SDK call`) behind a `ModelClient`
  protocol seam — swapping in the real SDK once credentials exist should
  not require touching the instrumentation/retry/correlation-ID layers at
  all.

#### Process notes (for other Squad agents sharing this repo)

- This repo's shared working directory is used concurrently by multiple
  Squad agents (Lead, Infra, this agent). Running `git checkout -b` in the
  shared main checkout is unsafe when another agent might run a concurrent
  `git checkout` — use `git worktree add .worktrees/{agent}-{issue} -b
  <branch> <parent-branch>` instead; it's a fully separate checkout
  directory immune to other agents' branch switches. All 8 of my branches
  were built this way under `.worktrees/agent-24` … `.worktrees/agent-31`.

#### Incident: scope-creep attempt outside workspace boundary (resolved)

While hunting for a Python interpreter, Agent attempted a `Get-Content` read of a sibling repository's
`.venv/pyvenv.cfg` outside `C:\Repos\foundry-otel-to-arize-demo`. The sandbox blocked the call before
execution — no data was read. Self-reported by Agent immediately after the attempt.

**Resolution (by coordinator, commit `a364b7d`):** added a "Workspace Scope — Hard Boundary" section to
both `.github/copilot-instructions.md` (policy read by every agent) and `.squad/templates/spawn-reference.md`
(baked into every future Squad spawn prompt), restricting all agents to the repository root going forward.

### 2026-10-02: Network posture for Milestone 1 infrastructure (issue #21)

**By:** Infra

**Related:** issue #21, PR (branch `squad/21-network-requirements`), `infra/modules/networking.bicep`, `infra/README.md` ("Network posture")

**What:**

#### Decision

The default/baseline network posture for all Milestone 1 infrastructure
(`infra/main.bicep` with default parameters) is **public network access,
secured by Azure AD/RBAC authentication and managed identity** - no VNet,
no private endpoints, no private DNS zones. This is the posture every other
Infra PR in this milestone (#15 Foundry project, #16 App Insights/Log
Analytics, #18 Key Vault) assumes and was built against.

An **optional, parameterized private-endpoint upgrade path** was added in
`infra/modules/networking.bicep` and wired into `main.bicep` behind a single
boolean parameter, `enablePrivateEndpoints` (default `false`). When set to
`true`, it additionally provisions private endpoints for the Key Vault
(`groupId: vault`) and the Foundry project (`groupId: amlworkspace`), either
into a small scratch VNet/subnet created by the module or into an existing
subnet supplied via `networkExistingSubnetResourceId`.

#### Coordination notes for other squad members

- **Lead / Agent (Prompt Agent, downstream code):** no change to any
  resource name, endpoint shape, or output contract from #15/#16/#18 - the
  private-endpoint variant does not rename or restructure the Foundry
  project, Key Vault, or App Insights resources. It only adds network
  reachability restrictions when explicitly enabled. Downstream code
  should keep using the same `foundryProjectEndpoint` /
  `keyVaultName` outputs either way; if `enablePrivateEndpoints: true` is
  used in a given environment, whoever runs that deployment must also run
  from inside (or peered with) the target VNet/subnet, or resolution of
  those endpoints will fail from outside the network perimeter.
- **Reviewers:** the private-endpoint variant (`main.parameters.private-endpoint.json`)
  was reviewed for Bicep syntax correctness only. It was **not**
  deployed/torn down against a live Azure subscription from the automated
  environment that authored it (no `az` CLI/subscription access available
  there - see PR "Current Limitations"). Please validate deploy + teardown
  of that variant against a scratch resource group before treating it as
  demo-ready, and record the result as a follow-up note here or in
  `.squad/decisions.md`.

#### Status

Implemented and documented in PR for issue #21 (branch
`squad/21-network-requirements`). Default posture unchanged for all
existing/default deployments; opt-in only.

**Why:**

#### Rationale

This repo is a sales-engineering/demo pipeline using **synthetic data only**
(see `/.github/copilot-instructions.md` section 1). Requiring network
isolation (VNet, private DNS, VPN/ExpressRoute/bastion connectivity) to spin
up a demo adds setup friction with no corresponding security benefit when
no real customer data is involved, and every resource already enforces
Azure AD/RBAC auth regardless of network reachability - "public" here means
"reachable", not "unauthenticated."

Network isolation becomes a legitimate requirement once a prospect wants a
real POC/pilot using their own data. The optional module exists for exactly
that scenario, without forcing every demo deployer to pay the setup cost.

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
