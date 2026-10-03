# Decision: Prompt Agent execution validation (#49) — static-test coverage now, live evidence deferred

**From:** Agent (Prompt Agent Developer)
**Affects:** QA/Demo Validation track (#48 shared plan, #50–#58 downstream validation steps), Infra
(#15/#16/#18), Lead (demo readiness sign-off)
**Date:** 2026-10-03

## Context

Issue #49 asks for proof that every synthetic prompt in the #48 shared library produces a
successful Prompt Agent response with a valid root-span trace ID and sane content. This sandbox has
**no live Foundry/Azure environment deployed** and, as of this session, **no usable Python
interpreter** (`python`/`py` both fail to launch), so the agent could not actually be executed here.

## Decision

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

## Requested action

- **Demo Validation Plan owners (#50–#58):** when a live environment becomes available, re-run the
  checklist in `docs/current-state/prompt-agent-execution-validation.md` §3 to capture a real
  per-scenario trace-ID table and file the `demo-validation.yml` form; the "Pass with caveats"
  verdict here should be revisited once that's done.
- **Infra (#15/#16/#18):** this is a second, independent confirmation (after #25's own note) that
  #49 cannot produce live-environment evidence until a real Foundry project/deployment exists.
- **Whoever next touches `model_client.py`:** consider the PPO/HMO stub-fidelity gap noted above if
  response fidelity becomes demo-relevant before a real `FoundryModelClient` is implemented.
