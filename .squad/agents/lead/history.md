# Project Context

- **Owner:** Rob McKenna
- **Project:** foundry-otel-to-arize-demo — a reusable observability demo repository showing how to instrument Microsoft Foundry Prompt Agents with OpenTelemetry/OpenInference, capture telemetry in Application Insights, export it through a transformation pipeline, and visualize/correlate traces and token usage in Arize. Built to be reused across enterprise healthcare customers (UnitedHealth Group, CVS Health, Elevance Health, etc.) evaluating observability for Foundry Prompt Agents.
- **Stack:** Azure (Foundry, Application Insights, Log Analytics, Event Hub, Azure Functions, Key Vault, managed identities), Infrastructure-as-Code (Bicep/Terraform), OpenTelemetry + OpenInference semantic conventions, Arize OTLP ingestion
- **Created:** 2026-10-02

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->
- This repo must clearly separate current-state (validated, implemented) from future-state (conceptual, direct-OTLP) architecture, in both docs and directory structure.
- Audience is enterprise healthcare customers — synthetic data only, no real PII/PHI anywhere in the repo, including demo transcripts and issue forms.

### Wave 2 backlog generation (2026-10-02)

- Executed full GitHub repo setup from 5 specialist scratch drafts: 19 labels, 5 milestones, 10 epic
  issues, 55 child issues (65 issues total, #1–#65), all cross-referenced with real dependency issue
  numbers and added to the correct milestone. GitHub Project (v2) creation is blocked in this environment
  — the `GH_TOKEN` in use lacks the `project`/`read:project` OAuth scopes and `gh auth refresh` cannot run
  non-interactively while `GH_TOKEN` is set. Documented as a gap with manual 2-minute setup steps in
  `SQUAD_BOOTSTRAP.md` rather than blocking the rest of the work, per the task's own contingency guidance.
- **PowerShell gotcha #1:** passing a loop variable's property into an external command unquoted
  (`gh api ... -f title=$m.title`) does NOT do member access — PowerShell stringifies `$m` via
  `ToString()` and appends the literal `.title`, producing garbage. Always quote
  (`-f "title=$($m.title)"`) or use literal strings when looping over `gh api -f` calls.
- **PowerShell gotcha #2:** capturing multi-line external command output into a variable
  (`$body = gh issue view N --json body -q .body`) produces an **array of lines**, not a single string.
  `$body.Length` silently returns line count, and regex `-replace` against it can silently no-op. Always
  `($output -join "`n")` before treating captured command output as one string.
- Issue numbering is strictly sequential and predictable when single-threaded, which let me pre-compute
  expected issue numbers for cross-referencing dependencies before creation — but any manual
  re-ordering or retried creates invalidates the predictions, as happened with 7 dependency
  cross-references in the Demo Experience batch that needed post-hoc correction via `gh issue edit`.
  Prefer a two-pass "create all, then patch cross-references" approach for large batches with heavy
  interdependency, rather than relying on prediction.
- Resolved the Key Vault / Function App "circular dependency" flag from Infra's decision file by framing
  it as a two-phase deploy (provision both resource shells first, wire managed-identity RBAC access
  second) rather than a true blocker — captured explicitly in issue #18's body.
- Wrote 4 final planning docs: `SQUAD_BOOTSTRAP.md` (updated in place, preserving the original business
  brief), `docs/traceability-matrix.md`, `docs/demo-validation-plan.md`, `docs/next-actions.md`. The
  `/docs` directory did not exist yet — `create` tool calls fail if the parent directory is missing, so
  it must be created first with `New-Item -ItemType Directory`.

### Milestone 1 PR conflict cleanup (2026-10-03)

- Two of my Milestone 1 PRs (#68 "current-state architecture diagrams" / issue #11, #70 "ADR log
  and process" / issue #13) had diverged from a shared, non-worktree checkout before PR #66
  (Foundry Bicep) and #67 (repo-structure scaffolding) merged to main. Because all these branches
  were cut from the same stale base in the same physical working directory, each one silently
  picked up in-flight content from sibling branches/agents (PR #70's issue was purely docs, yet it
  carried a full copy of `infra/*` that belonged to Infra's PR #66 — classic shared-checkout
  cross-contamination, not a real code conflict).
- Fix pattern that worked cleanly: `git worktree add .worktrees/lead-{pr} {branch}` to get an
  isolated checkout per PR, diff the branch against `origin/main` at the merge-base
  (`git diff --stat origin/main...HEAD`) to see the *actual* file-level blast radius, then
  surgically reset contaminated paths with `git checkout origin/main -- <path>` (and `git rm` for
  branch-only files that never existed on main) rather than trying to hand-resolve a conflict that
  was never really about conflicting intent.
- For the genuine content conflict (PR #68's `README.md` / `docs/current-state/README.md` vs
  PR #67's repo-structure scaffolding), a real `git merge origin/main` was the right tool — both
  sides had added legitimate, non-overlapping content, so the fix was literally "combine both
  halves," not reconcile competing designs. Diffing full file contents with
  `git show <ref>:<path>` into comparison files before touching markers made it obvious when a
  "conflict" was actually zero-difference noise (e.g. PR #70's `.github/copilot-instructions.md`
  conflicted only because my branch predated main's later Workspace-Scope-guardrail addition —
  main's version was already a strict superset, so no manual merge was needed at all).
- **New race discovered mid-cleanup:** merging PR #70 right after PR #69 (Infra's App Insights
  module) landed — my "strip infra/*" diff was computed a few seconds before #69 was visible from
  my fetch — caused my own cleanup commit to *delete* `infra/modules/app-insights.bicep` that #69
  had just added. A parallel Infra-track fix (`865be73`) restored it. Lesson: when multiple agents
  are merging to `main` within seconds of each other, a worktree-isolated branch still isn't immune
  to races against *main itself* — re-fetch `origin/main` and recompute the diff stat immediately
  before the final commit/push, not just once at the start of the cleanup.
- Going forward: every squad member should cut their working branch from a **worktree**
  (`git worktree add`), never from a shared checkout's `main`, and should re-fetch/re-diff against
  `origin/main` right before merging, not just at branch-creation time — the base can move under
  you in a multi-agent repo even within a single cleanup session.
