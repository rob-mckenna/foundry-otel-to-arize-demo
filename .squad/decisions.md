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

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
