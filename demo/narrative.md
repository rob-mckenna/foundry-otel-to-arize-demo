# Demo Narrative: Member Services Benefits Chatbot

**Status: CURRENT-STATE where marked ✅, flagged otherwise.** This script is written to be read
nearly verbatim by a field engineer presenting to a healthcare enterprise evaluator (e.g. a UHG,
CVS Health, or Elevance Health observability/platform team). **All member names, member IDs, plan
names, and claims details below are entirely fabricated** — see
`src/prompt-agent/synthetic/README.md` for the fixture policy. This script never requires or
references real patient data.

This narrative follows the Demo Validation Plan's shared synthetic scenarios
(`docs/validation/demo-validation-plan.md`, §1) so every claim made live is independently
reproducible by the customer afterward.

## Before you start

Make sure the environment is deployed and reachable — see
[`/demo/runbook.md`](runbook.md) for the full setup sequence. If anything fails mid-demo, switch to
[`/demo/fallback.md`](fallback.md) rather than troubleshooting live in front of the customer.

## 1. Set the scene (talking points, ~2 minutes)

> "What you're about to see is a Foundry Prompt Agent — think of it as a member-services benefits
> chatbot — answering a handful of synthetic member questions. Every prompt, member ID, and plan
> name on screen is fabricated for this demo; nothing here is real member data. What we're
> actually demonstrating is the **observability** wrapped around that agent: every request is
> captured as an OpenTelemetry trace with LLM-specific attributes — model used, token counts,
> prompt/response content — and that trace is designed to flow through to Arize for
> cross-system correlation and analysis."

Point to the current-state architecture diagram
(`docs/current-state/architecture.md`) on screen or printed:

> "Today, end-to-end, we have validated the agent itself: it runs, it's fully instrumented, and
> every span — including retries — carries a correlation ID that ties a whole request together.
> The transform-and-export half of this pipeline, from Application Insights through to Arize, is
> designed and specified in detail, and the infrastructure to run it is provisioned — but the
> Function code that actually performs that transform hasn't been built yet, so we'll be explicit
> about which parts of what you're seeing are live today versus coming next."

This sentence is intentional and should not be dropped or softened — see
`docs/validation/demo-validation-plan.md` §2 for exactly which capabilities are validated versus
pending, and `.github/copilot-instructions.md` §16 on never implying validation that hasn't
happened.

## 2. Run the synthetic scenarios (live, ~5 minutes)

From a terminal with the Prompt Agent environment set up (see `src/prompt-agent/README.md`):

```powershell
cd src/prompt-agent
python -m prompt_agent.main --scenarios
```

Narrate as it runs:

> "Each of these five scenarios is a different synthetic member question — a deductible lookup, a
> copay question, a network-coverage check, a claim-status check, and a member-ID confirmation.
> None of these member IDs or plan names are real — they all use a `SYN-` prefix and obviously
> fictional plan names like 'Acme Synthetic PPO,' by design, so this demo can run the same way for
> every customer without any real data ever touching it."

Call out the console output as each scenario completes:

> "For each one, you can see the prompt, the tool lookup the agent made, the response, and the
> token counts it reported. Behind the scenes, every one of those steps — the overall invocation,
> the tool lookup, and the model call — is its own OpenTelemetry span, and all of them share one
> correlation ID for this request."

**Sample scenario to narrate in detail** (from `src/prompt-agent/synthetic/scenarios.py`):

- Prompt: *"What is my synthetic deductible under Acme Synthetic PPO?"*
- Synthetic member: `SYN-00042`
- What to point out: the tool-lookup step (`tool.lookup_plan_details`), the model response, and
  the reported prompt/completion/total token counts.

## 3. Show the trace in Application Insights (live, ~3 minutes)

> "Now let's look at what actually landed in Application Insights for that request."

Open Application Insights → Transaction Search (or the Logs blade) and run:

```kql
AppDependencies
| where customDimensions["correlation.id"] == "<correlation ID printed by the run above>"
| project timestamp, operation_Id, operation_ParentId, id, Name, customDimensions
| order by timestamp asc
```

> "This confirms three things live: the request was captured, the span tree — invoke, tool
> lookup, model call — is intact with correct parent/child linkage, and the OpenInference
> attributes — model name, token counts, prompt/response values — came through on each span's
> custom dimensions."

**Do not promise the audience a live Arize screen yet** unless your environment has the Function
transform pipeline deployed and validated (it is not part of current-state as of this writing —
see `docs/validation/demo-validation-plan.md` capability #9/#10). If asked, say plainly:

> "The schema mapping from Application Insights into Arize's OTLP format is fully specified
> — down to the exact field-by-field transform — and the infrastructure to run it is provisioned.
> The transform code itself is the next milestone of work, so today I can show you the validated
> source-side telemetry and walk through exactly how that maps forward, rather than a live Arize
> screen that isn't backed by deployed code yet."

## 4. What this demonstrates (wrap-up talking points, ~2 minutes)

> "To summarize what you just watched proven live, with reproducible evidence: the agent runs
> against synthetic data only, every call is fully instrumented with OpenTelemetry and
> OpenInference-standard LLM attributes, token usage is captured per call, retries are bounded and
> fully traceable even when a call fails and recovers, and every one of those spans lands in
> Application Insights with a correlation ID that lets you tie a whole conversation together. The
> next phase of this pipeline — Event Hub streaming, the Azure Function transform, and Arize's
> ingestion — is fully designed against your specific App Insights schema, with infrastructure
> already in place, and is the next deliverable."

Close with where to find the written evidence for every claim made above:

> "Every one of those claims maps to a validation task in our Demo Validation Plan
> (`docs/validation/demo-validation-plan.md`) — you don't have to take my word for it, you can
> re-run every one of these checks yourself against the same synthetic data."

## Reference

- Shared synthetic scenarios: [`src/prompt-agent/synthetic/scenarios.py`](../src/prompt-agent/synthetic/scenarios.py)
- Current-state architecture: [`docs/current-state/architecture.md`](../docs/current-state/architecture.md)
- Demo Validation Plan: [`docs/validation/demo-validation-plan.md`](../docs/validation/demo-validation-plan.md)
- Operational runbook: [`demo/runbook.md`](runbook.md)
- Fallback guidance: [`demo/fallback.md`](fallback.md)
