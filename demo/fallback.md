# Live Demo Fallback / Failure-Mode Guidance

**Status: CURRENT-STATE (documentation) — guidance for a live demo of the current-state
pipeline.** This document is the companion to [`/demo/runbook.md`](runbook.md) (setup → run →
teardown) and [`/demo/narrative.md`](narrative.md) (the talking-point script). Read it *before*
presenting, not while something is already failing in front of a customer.

**Golden rule:** if a live component fails mid-demo, **do not debug live in front of the
customer.** Narrate the fallback talking point below, switch to the backup asset, and keep moving.
Debugging live erodes exactly the trust this demo exists to build.

## Failure modes and fallback talking points

### 1. Prompt Agent fails to start or errors on a scenario

**Symptom:** `python -m prompt_agent.main --scenarios` raises an exception, hangs, or a scenario
errors out without the expected "recovered after retry" behavior.

**Likely cause:** missing/incorrect environment variables (see
`src/prompt-agent/README.md`'s configuration table), a stale virtual environment, or — if
`APPLICATIONINSIGHTS_CONNECTION_STRING` is set — a transient Application Insights ingestion issue.

**Fallback talking point:**
> "I want to show you this running live rather than a canned screenshot, but let's not spend your
> time debugging an environment hiccup — I have a captured run from our validation evidence that
> shows exactly this scenario succeeding, including the retry behavior. Let me walk you through
> that while I sort this out, and I'll follow up with a live re-run afterward."

**Backup asset:** `src/prompt-agent/samples/scenario-run-2026-10-02.md` (captured scenario output)
and `src/prompt-agent/samples/retry-validation.md` (captured retry recovery/exhaustion evidence).

### 2. Application Insights query returns no results / is slow to show data

**Symptom:** The KQL query from `demo/narrative.md` §3 returns zero rows shortly after the
scenario run, or the Logs blade spins for an unusually long time.

**Likely cause:** Application Insights/Log Analytics ingestion latency (typically a few minutes,
occasionally longer) — this is expected platform behavior, not a defect.

**Fallback talking point:**
> "Application Insights ingestion typically lands within a couple of minutes — rather than stare at
> a loading spinner together, here's a captured query result from an earlier validation run
> showing exactly this span tree and its OpenInference attributes. I'll re-run the live query in a
> moment and we can compare."

**Backup asset:** `docs/telemetry/app-insights-custom-dimensions.md` and
`docs/telemetry/custom-dimensions-schema.md` (captured query output/schema evidence).

### 3. Audience asks to see the Arize dashboard

**Symptom:** An evaluator asks to see traces visualized in Arize, assuming the full pipeline is
live end-to-end.

**Likely cause:** reasonable assumption from the architecture diagram — but the Event Hub → Azure
Function transform that forwards telemetry to Arize is not implemented yet (see
`docs/validation/demo-validation-plan.md` capabilities #9/#10).

**Fallback talking point:**
> "Great question — that's actually the next milestone of work, not yet deployed. What I can show
> you right now is the exact field-by-field mapping spec we've already written for that transform
> step, which is what the engineering team is building against — so you can see precisely how your
> trace and token data will map into Arize once that lands, rather than me improvising an answer."

**Backup asset:** `docs/telemetry/field-mapping.md` (full transform spec) and
`docs/current-state/architecture.md` (the zoomed Event Hub → Function diagram).

**Do not** open or fabricate a live Arize screen to cover this gap — this would misrepresent
current-state as validated, which `/.github/copilot-instructions.md` §16/§19 explicitly prohibits.

### 4. Azure Function cold start / infrastructure slow to respond

**Symptom:** Any Function App endpoint used in the demo responds slowly after a period of
inactivity (Consumption-plan cold start — see `infra/README.md`'s Function App section).

**Likely cause:** expected Consumption-plan behavior, not a defect — the infra docs call this
trade-off out explicitly as an accepted cost/latency trade-off for a demo workload.

**Fallback talking point:**
> "This plan is intentionally optimized for near-zero idle cost over instant response, which means
> an occasional few-second cold start after inactivity — in a production POC we'd flip a single
> parameter to a Premium plan to eliminate that, but for today let's give it a moment."

**Backup asset:** none needed beyond the talking point — wait a few seconds and retry once.

### 5. Network/connectivity failure prevents reaching Azure entirely

**Symptom:** `az` commands or the Application Insights portal are unreachable (venue Wi-Fi/VPN
issue).

**Fallback talking point:**
> "Rather than fight the venue network, let me walk you through a fully captured run instead — same
> synthetic scenarios, same evidence we'd be looking at live."

**Backup asset:** the full set of captured evidence under `src/prompt-agent/samples/` and
`docs/telemetry/`, plus this repo's README and architecture docs, all of which work completely
offline since they require no live Azure connection to read.

## Pre-demo checklist (reduces the odds you need any of the above)

- [ ] Run `python -m prompt_agent.main --scenarios` once, successfully, within the hour before
      presenting (confirms environment + any live App Insights export is healthy).
- [ ] Confirm the correlation ID from that run is queryable in Application Insights before you go
      live (confirms ingestion isn't currently lagging).
- [ ] Have `src/prompt-agent/samples/*` and `docs/telemetry/*` open in browser tabs, ready to switch
      to, rather than needing to search for them mid-demo.
- [ ] Confirm you have offline/local copies of the backup assets above in case venue connectivity
      fails entirely (e.g. this repo cloned locally, not only viewed via a browser tab).

## Related

- [`/demo/runbook.md`](runbook.md) — full setup/run/teardown steps this fallback guidance assumes
- [`/demo/narrative.md`](narrative.md) — the talking-point script this guidance supplements
- [`docs/validation/demo-validation-plan.md`](../docs/validation/demo-validation-plan.md) — capability-by-capability status, the source of truth for what is/isn't safe to claim live
