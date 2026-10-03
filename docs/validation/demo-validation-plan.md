# Demo Validation Plan

**Status: MIXED — plan structure is current-state (this document and the synthetic prompt
library below are complete and usable today); the validation *results* for each capability are
tracked per-capability and range from "validated" to "blocked on upstream implementation." See the
per-capability status column in §2 — do not infer "validated" from the existence of this plan
alone.**

This is the single, authoritative Demo Validation Plan for `foundry-otel-to-arize-demo`. It exists
so a customer evaluator can re-run proof of the pipeline themselves instead of taking a live demo
on faith (see issue #48). Every validation task below uses the **same shared synthetic
prompt/data set** (§1) and the **same evidence-capture convention** (§3), so results are
consistent and comparable across capabilities and across re-runs.

Individual capability validation tasks are tracked as `demo-validation.yml` issues (see
`.github/ISSUE_TEMPLATE/demo-validation.yml`); this plan is the index that ties them together and
defines the shared inputs/outputs they must all use.

## 1. Shared synthetic prompt/data set

All validation tasks in this plan **must** reuse the existing synthetic fixture library rather
than invent new prompts — this is what makes results comparable across capabilities and across
re-runs. The canonical source is:

- [`src/prompt-agent/synthetic/scenarios.py`](../../src/prompt-agent/synthetic/scenarios.py) — 5
  synthetic member-services / benefits-lookup scenarios (`Scenario` dataclass instances), e.g.:

  | `scenario_id` | Synthetic member ID | Synthetic plan | Prompt |
  |---|---|---|---|
  | `benefits-deductible-lookup` | `SYN-00042` | Acme Synthetic PPO | "What is my synthetic deductible under Acme Synthetic PPO?" |
  | `benefits-copay-lookup` | `SYN-00077` | Acme Synthetic PPO | "What is my copay for a primary care visit on Acme Synthetic PPO?" |
  | `member-id-confirmation` | `SYN-00042` | Acme Synthetic PPO | "Can you confirm the member ID you have on file for me?" |
  | `network-coverage-lookup` | `SYN-00118` | Acme Synthetic HMO | "Is my primary care doctor in-network under Acme Synthetic HMO?" |
  | `claim-status-lookup` | `SYN-00077` | Acme Synthetic PPO | "What is the status of my most recent synthetic claim?" |

  All member IDs use the `SYN-` prefix, all plan names are obviously fictional ("Acme Synthetic
  PPO"/"Acme Synthetic HMO"), and every scenario is tagged `synthetic: true` — see
  `src/prompt-agent/synthetic/README.md` for the fixture-naming policy these follow.

- Run them via `python -m prompt_agent.main --scenarios` from `src/prompt-agent/` (see that
  directory's README for setup). Each run prints the prompt, any tool-lookup output, the response,
  and token counts per scenario, and generates a fresh correlation ID / trace ID per invocation —
  exactly the identifiers validation tasks query on downstream.

**Do not fabricate new prompts per validation task.** If a capability needs a prompt
characteristic the 5 scenarios above don't cover (e.g. a prompt engineered to trigger a retry),
add it to `synthetic/scenarios.py` (coordinate with Agent) rather than a one-off string embedded
in a validation doc, so it stays in the shared, reusable library.

## 2. The 11 capabilities → validation tasks

One validation task per capability, each filed as a `demo-validation.yml` issue (`#49`–`#57` per
the Epic #8 backlog). Status reflects what has actually been confirmed in this repo as of this
writing — **not** aspirational end-state.

| # | Capability | Owner | Status | Evidence location |
|---|---|---|---|---|
| 1 | Prompt Agent execution (invoke + response) | Agent | ✅ Validated (synthetic, in-process) | `src/prompt-agent/samples/scenario-run-2026-10-02.md` |
| 2 | OpenTelemetry span creation + parent/child linkage | Agent | ✅ Validated (`InMemorySpanExporter` tests) | `src/prompt-agent/samples/span-instrumentation-validation.md` |
| 3 | OpenInference attribute mapping (model, token counts, I/O) | Agent | ✅ Validated | `src/prompt-agent/samples/openinference-attribute-validation.md` |
| 4 | Token-usage telemetry (prompt/completion/total) | Agent / Telemetry | ✅ Validated at source; ⚠️ not yet confirmed end-to-end through Arize (blocked on #19) | `docs/telemetry/token-usage-validation.md` |
| 5 | Correlation ID generation + propagation (incl. retries) | Agent | ✅ Validated (in-process, incl. retry attempt spans) | `src/prompt-agent/samples/correlation-id-propagation-validation.md` |
| 6 | Trace/span/parent-span ID preservation end-to-end | Telemetry | ⚠️ Partially validated — source-side generation proven; Event Hub/Function hops **not yet validated** (no live Event Hub consumer / Function code exists yet) | `docs/telemetry/trace-correlation-preservation.md` |
| 7 | Application Insights capture of spans + custom dimensions | Infra / Telemetry | ✅ Infra provisioned (`infra/modules/app-insights.bicep`); schema inventory documented | `docs/telemetry/app-insights-custom-dimensions.md`, `docs/telemetry/custom-dimensions-schema.md` |
| 8 | Log Analytics → Event Hub export | Telemetry | ⚠️ Baseline/design documented; **not yet deployed/validated live** | `docs/telemetry/log-analytics-export-baseline.md` |
| 9 | Azure Function schema transform (App Insights → OTLP) | Telemetry | 🔴 Spec only — **no Function transform code exists yet** in `src/telemetry-pipeline/` (infra shell only, see #19); this is a documented field-mapping spec to build/audit against, not a result | `docs/telemetry/field-mapping.md` |
| 10 | Arize OTLP ingestion | Telemetry | 🔴 Not yet implemented/validated — depends on capability 9 | *(none yet — track against `tests/export`)* |
| 11 | Error/retry handling with full traceability | Agent | ✅ Validated at source (bounded exponential backoff, retry-attempt spans, error status propagation) | `src/prompt-agent/samples/retry-validation.md` |

**Reading this table:** ✅ = validated today with captured evidence a customer can reproduce.
⚠️ = partially validated; the gap is explicitly documented, not hidden. 🔴 = not yet implemented —
documented as a spec/design only, consistent with `/.github/copilot-instructions.md` §16's rule
against implying validation that hasn't happened. This table must be updated in the same PR that
changes any underlying capability's status — see issue #62's doc-drift checklist.

## 3. Evidence-capture convention

Every validation task (current or future `demo-validation.yml` issue) must capture evidence in
this shape, matching the `demo-validation.yml` issue form fields:

1. **Trace ID / correlation ID** used for the run (from a synthetic scenario in §1 — never a
   hand-typed example ID).
2. **Query or command used to retrieve the evidence** — e.g. a KQL query against Log Analytics, a
   `pytest` invocation, or an Arize query — copy-pasted verbatim so a customer can run the exact
   same thing.
3. **Query/command result** — pasted output (redacted of anything that isn't synthetic, though in
   this repo that should never be necessary since only synthetic data is used) or a screenshot
   reference stored under the relevant `samples/` directory.
4. **Pass/fail determination** stated explicitly — "looked fine" is never acceptable per QA's
   charter; state what was checked and what the expected vs. actual result was.
5. **Status label** — ✅ validated / ⚠️ partial / 🔴 not yet implemented, matching §2's table.

A validation task is not complete without all five elements captured in its issue and (for
anything long-lived) mirrored into the relevant `docs/current-state` or `docs/telemetry` file.

## 4. Relationship to other demo docs

This plan is the capability-by-capability proof backbone. Other demo artifacts build on it rather
than duplicating it:

- [`/demo/narrative.md`](../../demo/narrative.md) (#44) — the live walkthrough script, which
  references this plan's shared scenarios.
- [`/demo/runbook.md`](../../demo/runbook.md) (#45) — operational setup/run/teardown steps.
- [`/demo/fallback.md`](../../demo/fallback.md) (#46) — what to do if a live component fails
  mid-demo.
- [`/demo/one-pager.md`](../../demo/one-pager.md) (#47) — non-technical leave-behind summary.

## 5. Known limitations of this plan

- Capabilities 6, 8, 9, and 10 above depend on infrastructure/code that is not yet merged
  (`src/telemetry-pipeline/` Function transform, live Event Hub wiring). This plan's structure and
  shared prompt set are ready to use the moment those land; the capability table must be updated
  (not silently left stale) as each one is validated — see §2's note and issue #62.
- This plan does not replace the individual `docs/telemetry/*.md` deep-dive documents — it indexes
  and cross-references them, matching their own stated validation status rather than restating it
  optimistically.
