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

### 2026-10-03: Prompt Agent execution validation (#49) — static-test coverage now, live evidence deferred

**By:** Agent

**Affects:** QA/Demo Validation track (#48 shared plan, #50–#58 downstream validation steps), Infra (#15/#16/#18), Lead (demo readiness sign-off)

**What:**

#### Context

Issue #49 asks for proof that every synthetic prompt in the #48 shared library produces a
successful Prompt Agent response with a valid root-span trace ID and sane content. This sandbox has
**no live Foundry/Azure environment deployed** and, as of this session, **no usable Python
interpreter** (`python`/`py` both fail to launch), so the agent could not actually be executed here.

#### Decision

- Added `src/prompt-agent/tests/test_scenario_validation.py`: a pytest module parametrized over
  every scenario in `synthetic/scenarios.py`, asserting #49's three acceptance criteria (no
  unhandled error, valid non-zero root-span trace ID with no parent, non-empty/relevant response)
  using the same `span_exporter`/`find_span` fixtures as the existing, previously-passing suite.
  This is new static-test scaffolding, **not executed in this session** — it needs a working Python
  interpreter (or CI) to actually run and confirm green.
- Added `docs/current-state/prompt-agent-execution-validation.md`: the full validation procedure,
  checklist, and an honest evidence table. It is explicit that current "Pass" verdicts cover the
  current-state `StubFoundryModelClient` backend validated via code review + the new static suite +
  a prior session's captured sample output — **not** a live Foundry Prompt Agent deployment, which
  does not exist anywhere in this repo yet (#25's `FoundryModelClient` is still a documented stub).
- Flagged a pre-existing (not introduced here) stub-fidelity gap: `StubFoundryModelClient`'s
  keyword router answers any "network"/"in-network" prompt with PPO-plan language regardless of
  which plan was actually asked about (see validation doc §5, row 4). Not fixed in this PR to keep
  scope to validation per #49 — flagging for whoever next touches `model_client.py`'s synthetic
  answer routing.

#### Requested action

- **Demo Validation Plan owners (#50–#58):** when a live environment becomes available, re-run the
  checklist in `docs/current-state/prompt-agent-execution-validation.md` §3 to capture a real
  per-scenario trace-ID table and file the `demo-validation.yml` form; the "Pass with caveats"
  verdict here should be revisited once that's done.
- **Infra (#15/#16/#18):** this is a second, independent confirmation (after #25's own note) that
  #49 cannot produce live-environment evidence until a real Foundry project/deployment exists.
- **Whoever next touches `model_client.py`:** consider the PPO/HMO stub-fidelity gap noted above if
  response fidelity becomes demo-relevant before a real `FoundryModelClient` is implemented.

### 2026-10-03: End-to-end deployment validation script (issue #22)

**By:** Infra

**What:**

#### Decision

`infra/scripts/validate-deployment.ps1` runs `az deployment group what-if`
then `az deployment group create` against a scratch resource group, checks
every module's resource(s) for `provisioningState: Succeeded` (resolved
dynamically from `main.bicep`'s own outputs, not hardcoded resource name
guesses), spot-checks three RBAC assignments documented in
`infra/README.md` (Function App -> Key Vault Secrets User, Function App ->
Event Hub Data Receiver, Foundry project -> Key Vault Secrets User), and
prints a single pass/fail summary table with timestamps.

#### Rationale

- Dependency ordering is left to Bicep/ARM itself (via the `module` graph
  in `main.bicep`) rather than re-implemented in the script - avoids a
  second, driftable source of truth for module order.
- Resource identification is driven off `main.bicep`'s own outputs so the
  script stays in sync automatically as modules are added, instead of a
  hardcoded resource-name list that silently goes stale.
- `-SkipCreate` (what-if only) and `-CreateResourceGroupIfMissing` (opt-in
  resource group creation) are separate switches so a fast, free pre-PR
  check and a full paid validation run are both single commands without
  accidentally creating billable infrastructure by default.

#### Sandbox limitation (carried forward from Milestone 1/2)

`az` CLI is still not usable in this automated authoring environment (same
`PermissionError` reading `~/.azure/azureProfile.json` documented in
`.squad/agents/infra/history.md`), and `pwsh` (PowerShell 7, which this
script - like the existing `validate-naming.ps1` - targets) is present only
as an unprovisioned Windows Store execution-alias stub, not a real
installation. The script was validated by:

1. Static PowerShell parse-checking
   (`[System.Management.Automation.Language.Parser]::ParseFile`) - zero
   syntax errors.
2. A logic smoke test of the `az`-missing / not-logged-in failure paths,
   run under Windows PowerShell 5.1 with a temporary 2-arg `Join-Path`
   substitution (PS 5.1 does not support the 3-arg `Join-Path` form this
   script - and the existing `validate-naming.ps1` - uses; PS7/`pwsh` does).

A team member with real `az` CLI access and a scratch subscription should
run both the `-SkipCreate` and full-deploy example commands in
`infra/README.md` ("End-to-end deployment validation script" section)
before treating this script as demo-ready, per issue #22's validation
steps (success run + an intentionally-broken-parameter run).

### 2026-10-03: Demo resource teardown/cleanup script (issue #23)

**By:** Infra

**Related PR:** squad/23-cleanup-teardown-script

**What:**

#### Decision

Added `infra/scripts/teardown-deployment.ps1` to safely tear down the demo
resource group (or a targeted subset of resources) provisioned by
`infra/main.bicep`, as a companion to the `validate-deployment.ps1` script
from issue #22.

#### Design choices

- **Resource-group-level deletion is the default/primary mode** (one
  parameter, `-ResourceGroupName`), since that mirrors how the demo is
  actually provisioned (one RG per demo environment) and is the fastest
  path to a clean slate. **Targeted resource deletion** (`-ResourceIds`) is
  supported as a secondary mode for partial cleanup without tearing down
  the whole environment (e.g. only the Function App while iterating).
- **Two independent, separately-confirmed destructive actions**, not one:
  resource/group delete vs. Key Vault soft-delete purge. Azure Key Vault's
  soft-delete model means a vault can be recovered within its retention
  window after the resource-group delete; purging it is a second,
  irreversible step with its own blast radius (secrets become permanently
  unrecoverable), so it gets its own confirmation prompt rather than being
  bundled into the main "are you sure?" prompt.
- **`-Force` switch** skips both confirmation prompts for non-interactive
  CI/scripted use (e.g. a scheduled "nightly demo cleanup" job), consistent
  with the pattern requested in the issue.
- **Polling for absence** after delete (`az group show`/`az resource show`
  retried with backoff) rather than trusting `--no-wait` blindly, so the
  script's final pass/fail summary reflects reality rather than merely
  "the delete command was accepted."
- **Orphaned role-assignment check** after deletion: Azure normally cleans
  up role assignments when their scope resource is deleted, but this is
  documented as an eventually-consistent/edge-case behavior worth
  confirming explicitly rather than assuming, given this demo's RBAC-heavy
  (no shared keys) design.
- **Reused `main.bicep` outputs** (`keyVaultName`, etc.) where possible so
  the script doesn't need hardcoded resource names, consistent with the
  issue #22 script's approach.

#### Sandbox limitation and validation approach

`az` CLI is present in this authoring sandbox but every invocation throws a
Python traceback (`PermissionError` on the cached profile at
`~/.azure/azureProfile.json`) - a previously-documented environment issue,
not something fixed by this script. The script cannot be run end-to-end
against a real Azure subscription from this environment.

**Validation performed instead:**
1. `[System.Management.Automation.Language.Parser]::ParseFile` - 0 syntax
   errors.
2. A Windows PowerShell 5.1 smoke test (with a local, non-committed 3-arg
   `Join-Path` -> 2-arg-chained substitution, since the script targets
   `pwsh`/PowerShell 7 like the existing `validate-naming.ps1`) exercising
   the "az present but not authenticated" failure path: confirmed clean
   `[FAIL]` reporting, a correctly-populated Passed/Failed summary table,
   and exit code 1 - i.e. the script degrades gracefully instead of
   crashing when `az` is broken.

**New reusable PowerShell lesson found during this work:** under
`$ErrorActionPreference = 'Stop'` (set script-wide for fail-fast behavior),
piping a native command's stderr into the success stream via `2>&1` (e.g.
`$raw = & az @args 2>&1`) causes the merged `ErrorRecord` objects to throw
as **terminating** errors the instant they're produced, bypassing the
script's own custom fail-handling/summary logic entirely. Fixed by
introducing `Invoke-AzJson`/`Invoke-AzCommand` helper functions that
temporarily scope `$ErrorActionPreference = 'Continue'` around each
individual native `az` call (restored in a `finally` block), capture
`$LASTEXITCODE`, and wrap any JSON parsing in its own try/catch returning
`$null` on failure. This pattern should be reused by any future script in
this repo that shells out to `az`/`gh`/other native CLIs under a
`Stop`-preference script.

A team member with real Azure access must run this script end-to-end
against a scratch resource group before relying on it for demo cleanup,
confirming: resource-group deletion, targeted-resource deletion, Key Vault
purge, and the orphaned-role-assignment check all behave as documented.

#### Alternatives considered

- **Single confirmation prompt covering delete + purge together:** rejected
  - purge is meaningfully more dangerous (permanent vs. recoverable-within-
    window) and deserves its own explicit "yes."
- **Always purge Key Vault automatically on group delete:** rejected - an
  operator may want the soft-delete retention window as a safety net before
  committing to full purge; `-PurgeKeyVault` keeps that an explicit opt-in.

### 2026-10-03: src/telemetry-pipeline/README.md overstates implementation status

**By:** Lead

**Affects:** Telemetry track (owner of `/src/telemetry-pipeline`)

**Related:** Issue #14 (current/future-state separation audit), issue #60 (capability matrix), issue #19, #36

**What:**

#### Finding

`src/telemetry-pipeline/README.md` currently opens with `**Status: CURRENT-STATE (validated,
implemented)**` and states the directory "holds the Azure Function transform/mapping code and
Event Hub consumer logic that forms the validated telemetry pipeline." In reality the directory
contains only that README — no Function transform/consumer code exists yet under
`/src/telemetry-pipeline`.

This was surfaced during the Milestone 4 current-state/future-state separation audit (issue #14,
see `/docs/current-state/separation-audit.md` Finding 3) and reflected as a "Partial" capability in
`/docs/architecture/capability-matrix.md` (issue #60, capability #7).

#### Why this wasn't fixed directly

`/src/telemetry-pipeline` is owned by the Telemetry track per `.squad/agents/telemetry/charter.md`.
Lead's charter is explicit about not writing telemetry pipeline code or editing another track's
owned files directly — this is filed as a decision/finding for Telemetry to action instead.

#### Suggested resolution (either is acceptable)

1. **Soften the claim** to match `src/prompt-agent/README.md`'s pattern — that README carries the
   same `Status: CURRENT-STATE` header but is accurate because it explicitly flags what's still a
   placeholder. A similar callout in `src/telemetry-pipeline/README.md` (e.g. "Function transform
   code is tracked in #19/#36 and not yet implemented as of this writing") would resolve the drift
   without any code change.
2. **Implement the Function transform code** referenced by issues #19 (provision Function App —
   already closed, infra only) and #36 (field-by-field mapping doc — already closed, doc only), so
   the README's claim becomes true.

#### Action requested

Telemetry (or whoever picks up #19/#36 follow-on work) should apply option 1 or 2 above. No
action is required from Infrastructure, Prompt Agent, or QA tracks.

**Resolution (2026-10-03, by Telemetry):** actioned option 1 — `src/telemetry-pipeline/README.md`
corrected in PR #121 as part of the Milestone 4 Wave B batch; issue #37 (correlation-ID evidence)
was also reopened in the same pass as a related honesty finding (see below).

### 2026-10-03: Doc-drift checklist (issue #62)

**By:** QA

**What:** Added `CONTRIBUTING.md` at the repo root with a 5-question doc-drift checklist PR
authors should run through before opening a PR (does this change current-state behavior,
future-state design, a referenced setup step, the telemetry transform path, or add a new known
limitation — if so, update the matching doc in the same PR). Validated it retroactively against
PR #74 (network requirements, issue #21) as a worked example showing it would have passed with no
gaps.

**Why:** Per QA's charter, stale docs should be treated as a bug, not a follow-up chore. This is
intentionally lightweight (a mental checklist, not a blocking gate) so it doesn't slow down PR
velocity, while giving reviewers a concrete, repeatable thing to check for rather than relying on
memory.

**Ask for whoever owns `.github/pull_request_template.md` (Lead/Scribe):** please add a short
reference line to `CONTRIBUTING.md` under the template's existing **Documentation Updates**
section (e.g. "See CONTRIBUTING.md's doc-drift checklist").

### 2026-10-03: Event Hub partition-key and Function checkpointing requirements for correlation-ID preservation

**By:** Telemetry

**Affects:** Infra (#17 Event Hub, #19 Azure Function)

**What:**

#### Context

While documenting trace/span/correlation-ID preservation across Event Hub and Function hops (#37),
two implementation requirements were identified that Infra's #17/#19 Bicep modules and any
accompanying Function code should satisfy to avoid breaking cross-system trace correlation:

1. **Event Hub partition key:** whatever writes spans to Event Hub (Log Analytics Data Export, #35)
   should use `operation_Id` (the App Insights trace ID) as the partition key, so every span
   belonging to one trace stays in relative order within a single partition. Without this, spans
   from one trace could be delivered out of order across partitions.
2. **Function checkpointing strategy:** the Azure Function's Event Hub trigger should use
   whole-batch checkpointing (checkpoint only after the full batch succeeds), not per-event
   checkpointing with silent drop-on-failure. Per-event checkpointing risks orphaning child spans
   if a parent span's event fails mid-batch while children already succeeded.

#### Why this matters

Both are flagged in `/docs/telemetry/trace-correlation-preservation.md` §3/§4 as **blocking
concerns** for correlation-ID preservation, not optional tuning — per Telemetry's charter policy of
treating any hop where correlation IDs could be dropped as a blocking defect unless Lead explicitly
accepts it as a known limitation.

#### Requested action

Infra: please consider these two requirements when implementing #17 (Event Hub) and #19 (Azure
Function). Not blocking #17/#19's current scope — flagging now so the requirement is visible before
those modules are built, rather than discovered as a bug afterward.

**Note:** this note's original inbox file was never found on disk by a later Scribe pass (see
Infra's `agents/infra/history.md` team-update entry, 2026-10-03T03:18:22-04:00) — reconstructed and
merged here from the copy preserved in Telemetry's own inbox drop for this batch.

### 2026-10-03: Milestone 3 (Arize Integration) deliverables — doc/spec-only, live-environment validation still pending

**By:** Telemetry

**What:**

#### What was delivered

All 10 Milestone 3 issues (#89, #90, #91, #92, #38, #39, #40, #41, #42, #43) were delivered as
doc/spec/query-pack/test-scaffold PRs, each in its own dedicated worktree + branch + PR (no
self-merge), per the same "no live Azure/Arize environment in this sandbox" posture Telemetry used
in Milestone 2:

- #89-#92: field-by-field mapping specs under `docs/telemetry/mapping/` for the four field groups
  `field-mapping.md` (#36) already indexes.
- #41: a 5-query KQL validation pack under `docs/telemetry/kql/`.
- #38: OTLP export conformance spec + a reference-transform test scaffold
  (`tests/export/test_otlp_export_conformance.py`) proving the mapping specs are internally
  consistent — explicitly **not** a test of the production Azure Function, which does not exist in
  this repo yet.
- #39, #40, #42, #43: cross-system trace join, Arize token-analysis view, Arize trace-visualization
  dashboard, and token-analysis parity-check specs, each with hand-computed/hand-traced synthetic
  evidence where executable validation wasn't possible.

#### Standing risk/decision for the team

**None of Milestone 3's acceptance criteria that require a live Application Insights instance, a
live Arize space, or the as-yet-unwritten Azure Function transform code (src/telemetry-pipeline/ is
still a placeholder) have been executed.** Every doc in this milestone explicitly splits
"validated-via-review" (field inventory, query syntax, arithmetic, cross-references to already-
merged Milestone 1/2 docs — all correct independent of environment) from "requires
live-environment re-verification" (anything needing a real KQL run, a real Arize query, or a real
OTLP export). Whoever implements #19's Function transform code should treat these 10 docs as the
spec to build against and re-run every validation query/test listed once live infra exists — do not
treat "PR merged" as equivalent to "live-validated" for this milestone.

#### Follow-up risk carried forward

Reconfirms the Milestone 2 flag already in Infra's history: Event Hub partition-key choice and
Function batch-checkpointing strategy remain the two places a correlation ID could still be lost
end-to-end, and nothing in this milestone's doc work closes that gap — it can only be closed once
#19's Function code and live infra exist to test against.

### 2026-10-03: Milestone 4 (Customer Demo Readiness) telemetry-validation batch — #37 reopened, #130 filed

**By:** Telemetry

**Affects:** Whoever picks up #19's Function implementation; Lead (Milestone 5 planning); QA

**Related:** #50-#58, #37 (reopened), #121-#129, #131, #130 (new gap issue)

**What:**

#### Summary

Delivered validation docs for all 9 Milestone 4 issues assigned (#50-#58) plus a README-drift fix
(#121, addressing Lead's `src/telemetry-pipeline/README.md` drift finding above). No live
Azure/Arize environment or Python interpreter exists in this sandbox, so every doc is explicit about
validated-via-review vs. blocked/requires-live-environment, per repo convention.

#### Net result, grouped by what's actually provable today

- **Source-side (Prompt Agent) telemetry capture is solid.** #50 (App Insights capture, partial —
  exporter wiring + span-attribute shape proven, live ingestion blocked), #51 (prompt/response
  fidelity, pre-export proven exact-match; long-prompt truncation test identified as a genuine gap
  and not yet written), #52 (token metrics, fully proven by an existing 25-span test suite),
  and #58 part (a) (retry visibility, fully proven) are all backed by real, already-written,
  already-passing-by-design unit tests in `src/prompt-agent/tests/`.
- **Everything downstream of the Prompt Agent is blocked, not partially passing.** #53
  (cross-system correlation), #54 (export-pipeline execution), #55 (transformation correctness),
  #56 (Arize ingestion), #57 (Arize visualization), and #58 part (b) (export-pipeline outage
  handling) all terminate at the same root cause: **no Azure Function transform/consumer code
  exists under `src/telemetry-pipeline`, and no Arize instance has ever been deployed in this
  repo's history.** These are marked Blocked, not Pass-with-caveats — there is a real difference
  between "an acceptance criterion that's awkward to test" and "an acceptance criterion whose
  subject doesn't exist yet," and conflating them would misrepresent demo readiness to Lead/QA.

#### Issue #37 reopened

While fixing the README drift, found issue #37 ("Trace/span/parent-span/correlation-ID
preservation across Event Hub and Function hops") was closed (`COMPLETED`, zero comments, no
linked PR) despite requiring live KQL+Arize evidence that doesn't exist. Reopened it with an
explanatory comment.

#### New gap filed: #130 (exporter observability)

Found a concrete, fixable-today gap while validating #58: `telemetry.py`'s `shutdown_tracing()`
discards `force_flush()`'s return value, and no export success/failure counter exists. Filed as
issue #130 (Effort: S, no new infra required) — assigned to Milestone 4, labeled
Observability/OpenTelemetry/Priority-Medium.

#### Recommendation for Milestone 5 / whoever implements #19

Treat #53-#57 and #58(b) as the concrete scope of "implement + validate the export pipeline,"
using the Milestone 3 specs (`docs/telemetry/*.md`) as the build spec and the Milestone 4 docs
created in this batch (`docs/current-state/*-validation.md`) as the checklists to re-run once
real infrastructure exists — do not treat any of those 6 items as already passing.

### 2026-10-03: README enhancement for clarity/navigation (issue #132, PR #133)

**By:** QA

**What:**

#### Context

User explicitly asked to "make the README more informative" after the prior accuracy pass (#59 /
PR #106). Opened issue #132 and built the enhancement in a dedicated worktree
(`.worktrees/readme-enhance`, branch `squad/readme-enhance`) rather than the main checkout, per
mandatory worktree convention.

#### What changed

Added to root `README.md` (additive, not a rewrite — all previously accuracy-passed content
preserved): an Overview/customer-scenario section, a table of contents, a Quick Start table that
distinguishes steps requiring zero Azure/Arize access from steps requiring a live environment, a
Documentation map linking every doc the task asked for, and a Known Limitations section that
explicitly surfaces #37 (trace-correlation preservation across Event Hub/Function — reopened) and
#130 (exporter observability gap) rather than hiding them.

#### Note for other agents / Scribe

The task description referenced `docs/telemetry/queries/` as an expected path. That directory does
not exist in the repo — the actual KQL query pack lives at `docs/telemetry/kql/`. QA linked to the
real path (`docs/telemetry/kql/`) instead of creating a broken link or a new directory. If a future
issue intends `docs/telemetry/queries/` as a distinct future directory, that should be clarified
explicitly rather than assumed equivalent to `docs/telemetry/kql/`.

#### Status

PR #133 opened against `main`, `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE`. Not merged by QA —
coordinator to verify and merge.

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
