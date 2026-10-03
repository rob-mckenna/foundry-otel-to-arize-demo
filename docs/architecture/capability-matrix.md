# Capability Matrix

> Maps each of the 11 demo-proof capabilities (the claims a field engineer makes to a customer
> during the demo) to its current-state implementation status. Status is derived by cross-checking
> actual code/IaC under `/src` and `/infra` against the GitHub issues that track each capability —
> not by issue state alone. See `/docs/traceability-matrix.md` for the full requirement-to-evidence
> trace, and `/.github/copilot-instructions.md` §2–§3 for the current-state/future-state diagrams
> this matrix supports.
>
> **Status key:**
> - ✅ **Done** — implemented under `/src` or `/infra`, validated steps evidenced by closed issues.
> - 🟡 **Partial** — implemented in part, or implemented but not yet end-to-end validated.
> - ⬜ **Not started** — no implementation under `/src` or `/infra` yet; tracked by an open issue.

| # | Capability | Current-State Implementation | Status | Tracking Issue(s) |
|---|---|---|---|---|
| 1 | Foundry Prompt Agent execution | `src/prompt-agent/` core prompt/response flow | ✅ Done | #24, #25 |
| 2 | OpenTelemetry trace generation (trace/span/parent-span IDs) | `src/prompt-agent/` OTel SDK bootstrap + span instrumentation on every model/tool call | ✅ Done | #26, #27 |
| 3 | OpenInference semantic convention compliance | OpenInference attribute mapping on model-call spans (`input.value`/`output.value`/model name) | ✅ Done | #28 |
| 4 | Token usage visibility (prompt/completion/total) | OpenInference token attributes on LLM spans | ✅ Done | #28, #34 |
| 5 | Application Insights telemetry capture | `infra/modules/app-insights.bicep` (App Insights + Log Analytics) + custom-dimension capture | ✅ Done | #16, #32 |
| 6 | Trace/correlation-ID preservation (Agent → App Insights → Event Hub → Function) | Correlation-ID propagation in agent code + preservation doc across Event Hub/Function hops | ✅ Done | #29, #37 |
| 7 | Telemetry transformation correctness (Azure Monitor → OTLP mapping) | Field-by-field mapping documented in `src/telemetry-pipeline/README.md`; Azure Function App provisioned (`infra/modules/function-app.bicep`), transform code not yet implemented in `/src` | 🟡 Partial | #19, #36 |
| 8 | Arize OTLP ingestion | No code under `/src` or `/infra` yet — Function App exists but does not export OTLP to Arize | ⬜ Not started | #38 |
| 9 | Arize trace visualization | No Arize dashboards built yet | ⬜ Not started | #42 |
| 10 | Token cost analysis in Arize | No Arize token-aggregation views built yet | ⬜ Not started | #40 |
| 11 | Error/retry handling with full traceability | Bounded retry policy with per-attempt spans in `src/prompt-agent/` | ✅ Done | #30 |

## Drift found during this review

One item: `src/telemetry-pipeline/README.md` is labeled `Status: CURRENT-STATE (validated,
implemented)` and describes itself as holding "the Azure Function transform/mapping code," but the
directory presently contains only that README — no Function code exists yet. The schema-mapping
*documentation* (issue #36) is genuinely done, but the implementation code is not, which makes the
README's blanket "implemented" status label misleading on its own. This has been filed as a finding
in the Milestone 4 separation audit (`/docs/current-state/separation-audit.md`, issue #14) and
routed back to Telemetry rather than edited here, since `/src/telemetry-pipeline` is owned by that
track. Every other "Done" row above was cross-checked against the actual file(s) listed in the
"Current-State Implementation" column at the time of this audit (Milestone 4, 2026-10-03) and no
further drift was found. The "Partial"/"Not started" capabilities (#7–#10) reflect a real
implementation gap, matching the Milestone boundary: Milestone 3 (Arize Integration, issues
#38–#43) is still open.

## Keeping this matrix current

Update this table whenever a capability's implementation status changes (e.g., when #38 lands and
Arize OTLP ingestion moves from "Not started" to "Done"). This matrix should never claim a
capability is "Done" based on an issue being closed alone — always re-verify against the actual code
or IaC referenced in the "Current-State Implementation" column.
