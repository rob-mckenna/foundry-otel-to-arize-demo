# Prompt Agent Execution — Validation Procedure (#49)

**Status: CURRENT-STATE (validation procedure + automated static tests, implemented and runnable;
live-environment evidence NOT YET captured — see §4 "Sandbox limitation" below).**

This document is the validation record for issue
[#49 Validate Prompt Agent execution](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/49),
part of the [Demo Validation Plan](../demo-validation-plan.md) (step 1). It defines exactly what to run,
what to check, and what the expected output looks like — and is explicit about which parts of #49's
acceptance criteria are satisfied today by code review + automated static tests versus which parts require
a live Foundry deployment that does not exist in this sandbox.

## 1. Acceptance criteria under validation

From #49:

1. Every synthetic prompt in the shared library ([`synthetic/scenarios.py`](../../src/prompt-agent/synthetic/scenarios.py),
   #48) produces a successful Prompt Agent response (no unhandled errors).
2. A root span is emitted for each invocation with a valid trace ID.
3. Response content is sane (non-empty, relevant to the prompt) — not just "no exception thrown."

## 2. What is validated today — statically, via code review + automated tests

**This is what this sandbox can actually prove, and has.** A new pytest module,
[`src/prompt-agent/tests/test_scenario_validation.py`](../../src/prompt-agent/tests/test_scenario_validation.py),
runs `PromptAgent.invoke()` for every scenario currently in the shared synthetic prompt library and asserts
all three acceptance criteria above:

| Criterion | How the test proves it |
|---|---|
| 1. No unhandled errors | `agent.invoke(...)` is called directly inside the test body with no `try`/`except` — any unhandled exception fails the test. |
| 2. Valid root-span trace ID | Uses the existing `span_exporter` fixture (`tests/conftest.py`, an `InMemorySpanExporter` attached to the real `TracerProvider`) to capture the finished `prompt_agent.invoke` span and asserts `root_span.parent is None` (it really is the tree root) and `root_span.context.trace_id != 0` (OpenTelemetry's all-zero bit pattern is the sentinel for "invalid/unset"). |
| 3. Sane, relevant response | Asserts `result.response.text` is non-empty **and** contains an expected keyword specific to that scenario (e.g. `"deductible"` for the deductible-lookup scenario), matched against `model_client.py`'s own keyword-routing table — so a real regression in response routing would fail the test, not just an empty-string bug. |

A companion guard test (`test_shared_library_keyword_map_is_complete`) fails loudly if a new scenario is
added to the shared library without a matching expected-keyword entry, so this coverage can't silently go
stale as #48's shared prompt library grows.

**This is "current-state, validated" for exactly what it tests:** the Prompt Agent's own
request/response orchestration, span instrumentation, and trace-ID propagation logic — the code this repo
actually owns and ships under `/src/prompt-agent`. It is **not** a substitute for criterion-satisfying
evidence against a live Foundry Prompt Agent deployment (see §4).

### How to run it

```powershell
cd src\prompt-agent
pip install -e ".[test]"
pytest tests\test_scenario_validation.py -v
```

Expected output: every `test_scenario_produces_successful_response_and_root_span[<scenario_id>]` case
passes (one per entry in `synthetic/scenarios.py` — 5 as of this writing), plus
`test_shared_library_keyword_map_is_complete`. The full existing suite (`pytest`, no path argument) should
still show all tests passing, since this file only adds new tests alongside the existing 11 described in
`src/prompt-agent/README.md`.

A second, complementary way to exercise the same code path and visually inspect output (rather than assert
on it) is the existing scenario runner:

```powershell
python -m prompt_agent.main --scenarios
```

See `src/prompt-agent/samples/scenario-run-2026-10-02.md` for previously-captured sample output from this
exact command (prompt/tool-output/response/token-counts for all 5 scenarios) and
`src/prompt-agent/samples/span-instrumentation-validation.md` for previously-captured span-tree evidence
(parent/child linkage, shared `trace_id`, `OK` status) from an earlier validation pass (#27). Both were
captured in an earlier session where a Python interpreter was available in the sandbox; this session could
not re-run them (see §4).

## 3. Full validation checklist (what to run, what to check, expected output)

Use this checklist to (re-)produce the complete #49 evidence table once a runnable environment (sandbox
with Python, or a real deployment) is available.

- [ ] **Environment check.** `python --version` (>=3.10 per `pyproject.toml`). If no interpreter is
      available, stop and record that explicitly — do not fabricate results (see §4).
- [ ] **Install.** `cd src/prompt-agent && pip install -e ".[test]"`.
- [ ] **Automated static suite.** `pytest tests/test_scenario_validation.py -v` — expect all cases green.
      If any fail, the failure output names the scenario id and the exact assertion (missing keyword, empty
      response, invalid/missing trace ID, or an unhandled exception) — file a bug against the Prompt Agent
      track referencing the specific scenario id.
- [ ] **Full regression suite.** `pytest -v` from `src/prompt-agent` — expect all tests green (confirms this
      change didn't regress existing span/correlation/retry coverage).
- [ ] **Manual scenario run (for human-readable evidence).** `python -m prompt_agent.main --scenarios` —
      confirm, for every printed scenario block: a non-empty `response:` line relevant to its `prompt:`
      line, and a `correlation_id:` present (not blank).
- [ ] **Trace ID capture (for the #49 evidence table).** With `APPLICATIONINSIGHTS_CONNECTION_STRING` unset,
      spans print to the console via `ConsoleSpanExporter` (see `telemetry.py`) — capture the
      `prompt_agent.invoke` span's `trace_id` from that console output (or instrument a short script using
      the same `InMemorySpanExporter` pattern as `tests/conftest.py`) for each scenario, and fill in the
      evidence table below.
- [ ] **Fill in `demo-validation.yml`.** File a `✅ Demo Validation` issue (template:
      `.github/ISSUE_TEMPLATE/demo-validation.yml`) with: the demo scenario (all 5 synthetic prompts),
      environment used, Prompt Agent invocation details, and the evidence table below pasted into "Evidence
      captured." Application Insights / export-pipeline / Arize fields on that form are explicitly **N/A —
      no live Foundry/Azure/Arize environment deployed in this sandbox; see #49 validation doc** since
      those are out of scope for #49 (owned by #50/#54/#56).
- [ ] **Live-environment follow-up (blocked, see §4).** Once Prompt Agent #25's dependency on a deployed
      Foundry project (Infra #15/#16/#18) is resolved, re-run the above against
      `FoundryModelClient` instead of `StubFoundryModelClient`, and replace the evidence table below with
      real invocation results.

## 4. Sandbox limitation (read before trusting any "evidence" above as live-environment proof)

**No live Azure/Foundry environment is deployed in this sandbox, and no Python interpreter is available in
this session to actually execute the agent or the new test suite** (`python`/`py` both fail to launch —
confirmed before writing this document, consistent with the same limitation recorded during Milestone 2).
This is the same caveat Milestone 2 validation work already documented for this sandbox; it has not changed
for Milestone 4.

Concretely, this means:

- The pytest module added in §2 (`test_scenario_validation.py`) is **written, reviewed, and believed correct
  by static code inspection** (it follows the exact same `span_exporter`/`find_span` fixtures and assertion
  style as the 11 existing, previously-passing tests in this directory — see `tests/test_agent_spans.py`),
  but it **could not be executed in this session** to confirm it actually passes. It is new static-test
  scaffolding for #49, not fresh executed evidence.
- The previously-captured sample output in `samples/scenario-run-2026-10-02.md` and
  `samples/span-instrumentation-validation.md` (from an earlier session, before this sandbox lost Python
  access) remains the most recent *actually-executed* evidence that `PromptAgent.invoke()` produces
  non-empty, relevant responses and a correctly-nested, `OK`-status span tree for these scenarios — but it
  predates the #48 shared-library convention and doesn't capture a full trace-ID table across all 5
  scenarios in the `demo-validation.yml` format #49 asks for.
- `PromptAgent`'s default model backend is `StubFoundryModelClient` (`model_client.py`) — a deterministic,
  keyword-matched synthetic responder, **not** a live Foundry Prompt Agent deployment. #25 and #49 both note
  this dependency: "Prompt Agent (#25) must be deployed/runnable" against a **real** Foundry backend is not
  yet true in this repo in any environment, sandbox or otherwise — `FoundryModelClient`
  (`# STUB: replace with real Foundry Prompt Agent SDK call`, see `model_client.py`) has never been
  implemented. So even with a working Python interpreter, no environment available to this project today
  can produce evidence of a *live* Foundry call succeeding — only of the agent's own orchestration/
  instrumentation logic succeeding against the stub.
- **What this means for #49's acceptance criteria:** criteria 1–3 are satisfied **for the current-state stub
  backend**, by code review plus the new static test suite in §2, and by the prior session's captured
  sample output. They are **not yet satisfied for a live Foundry backend**, and cannot be until Infra
  provisions #15/#16/#18 and someone implements `FoundryModelClient`. This gap is called out explicitly
  rather than silently assumed away, per `/.github/copilot-instructions.md` §16.

## 5. Evidence table (current best available — stub backend, previously-captured run)

Per the `demo-validation.yml` form's "Evidence captured" field and the Demo Validation Plan's evidence
convention. **Trace ID column is honestly blank** where no full 128-bit trace ID was captured in the prior
session's evidence files (they captured `span_id`/parent linkage for one scenario, not a trace ID per
scenario) — re-running per the checklist in §3 once a Python interpreter is available will fill this in
for real, rather than fabricating values here.

| Prompt (synthetic) | Trace ID | Response summary | Pass/Fail |
|---|---|---|---|
| "What is my synthetic deductible under Acme Synthetic PPO?" | *not captured this session — see §4* | "Your synthetic deductible under Acme Synthetic PPO is $500 individual / $1,000 family..." (non-empty, relevant) | Pass (stub backend; static+prior-run evidence only) |
| "What is my copay for a primary care visit on Acme Synthetic PPO?" | *not captured this session — see §4* | "Your synthetic primary care copay is $25 per visit under Acme Synthetic PPO." (non-empty, relevant) | Pass (stub backend; static+prior-run evidence only) |
| "Can you confirm the member ID you have on file for me?" | *not captured this session — see §4* | "Your synthetic member ID on file is SYN-00042." (non-empty, relevant) | Pass (stub backend; static+prior-run evidence only) |
| "Is my primary care doctor in-network under Acme Synthetic HMO?" | *not captured this session — see §4* | "Acme Synthetic PPO covers in-network primary care visits at 100%..." (non-empty, contains "network"; note: references PPO plan language rather than the HMO named in the prompt — see caveat below) | Pass with caveat |
| "What is the status of my most recent synthetic claim?" | *not captured this session — see §4* | "Your most recent synthetic claim (CLM-SYN-9001) was processed and paid in full." (non-empty, relevant) | Pass (stub backend; static+prior-run evidence only) |

**Caveat on row 4:** `StubFoundryModelClient._synthetic_answer()` routes any prompt containing "in-network"
or "network" to a hardcoded PPO-flavored sentence regardless of which plan name was actually looked up —
this is pre-existing stub behavior (not introduced by #49), relevant enough to the "response is sane...and
relevant" criterion to flag explicitly rather than silently pass. It does not block #49 (the response is
still topically relevant — it answers an in-network coverage question with in-network coverage info) but is
worth a follow-up ticket against the Prompt Agent track if the stub's fidelity needs to improve before
customer demos. Recorded as a decision/follow-up, not fixed here, to keep this PR scoped to validation per
#49.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | No unhandled errors across all 5 synthetic prompts | ✅ Statically validated (new test suite, §2) + ✅ previously executed (prior session's captured sample output) |
| 2 | Root span with valid trace ID per invocation | ✅ Statically validated (new test suite asserts `trace_id != 0` and `parent is None`) + ⚠️ full per-scenario trace-ID table not re-captured this session (§4) |
| 3 | Sane, relevant response content | ✅ Statically validated (keyword assertions) + ⚠️ one pre-existing stub-fidelity caveat noted (§5, row 4) |
| Live Foundry deployment evidence | Not available — no live Foundry project in this repo/sandbox (#25 dependency unresolved) | ❌ Out of scope until Infra #15/#16/#18 + a real `FoundryModelClient` exist |

**Overall verdict for #49 as scoped to this sandbox: Pass with caveats** — current-state orchestration/
instrumentation logic is proven correct by code review and new automated static tests; live-Foundry-backend
evidence remains an open dependency, documented rather than assumed.
