# README Dry-Run Checklist (#59)

**How this checklist was produced:** this automated environment has no usable Python interpreter
and a permission-restricted Azure CLI profile (`PermissionError` on `~/.azure/azureProfile.json`),
so a live, end-to-end execution of every README step was not possible here. Each step below was
instead **statically verified** — command syntax, file paths, and referenced identifiers were
checked against what is actually merged in this repository (module names, config variables, test
counts, CLI flags) rather than assumed. Live execution is flagged explicitly as a follow-up where
it could not be performed, per QA's charter ("skeptical of 'should work'").

| # | README step | Verification method | Result |
|---|---|---|---|
| 1 | Prerequisites list accuracy (Azure subscription, Foundry access, Python 3.10+, PowerShell 7+, Arize account) | Cross-checked against `infra/README.md`, `src/prompt-agent/README.md`'s `pyproject.toml` requirement, and the Demo Validation Plan's capability table for why Arize isn't required yet | ✅ Pass (static) |
| 2 | `git clone` + `az deployment group what-if`/`create` against `infra/main.bicep` | Confirmed `infra/main.bicep` and `infra/main.parameters.json` exist and match the command's file paths; confirmed module list against `infra/README.md` | ✅ Pass (static) — ⚠️ **not executed live**: `az` CLI unusable in this sandboxed environment (`PermissionError` on the Azure profile) |
| 3 | Prompt Agent venv setup (`python -m venv .venv`, `pip install -e ".[test]"`) | Confirmed `src/prompt-agent/pyproject.toml` defines a `test` extra matching this command | ✅ Pass (static) — ⚠️ **not executed live**: no usable Python interpreter available in this sandbox (`python`/`py` both fail to resolve to an installed interpreter) |
| 4 | `pytest` (expect all tests passing) | Confirmed `src/prompt-agent/README.md` states "All 11 tests pass as of this writing" and the `tests/` directory contains the two test modules it describes | ✅ Pass (static, per author's own captured evidence) — ⚠️ **not re-executed live** in this sandbox |
| 5 | `python -m prompt_agent.main --scenarios` | Confirmed this exact flag/entry point exists in `src/prompt-agent/README.md` and `prompt_agent/main.py`'s described behavior; confirmed 5 scenarios match `synthetic/scenarios.py` | ✅ Pass (static) — ⚠️ **not executed live**, same Python-availability limitation as step 3 |
| 6 | Looking up the run's correlation ID in Application Insights | Confirmed the KQL pattern matches `demo/narrative.md` §3 and `docs/telemetry/trace-correlation-preservation.md` §5 | ✅ Pass (static) — requires a live, deployed Application Insights resource to execute; not available in this sandbox |
| 7 | Teardown (`az group delete` + `az resource list`) | Matches `demo/runbook.md` §4 exactly | ✅ Pass (static) — ⚠️ **not executed live**, same `az` CLI limitation as step 2 |
| 8 | "What this demo proves" capability table (11 rows) | Cross-checked every row's status against `docs/validation/demo-validation-plan.md` §2's own status column — no row claims more than that document's own evidence supports | ✅ Pass |
| 9 | No secrets/connection strings/real customer references in README | Manually re-read full README text; only placeholder env var *names* appear, no values; only generic payer-category examples already used elsewhere in the repo's own `copilot-instructions.md` | ✅ Pass |
| 10 | Future-state/aspirational content removed from README body | Confirmed the only future-state reference remaining is the existing link to `/docs/future-state` (unchanged from before this PR) — no aspirational capability is described as working in the rewritten body | ✅ Pass |

## Summary

**9 of 10 checks pass on static verification; the remaining live-execution steps (2, 3, 4, 5, 6, 7)
could not be run end-to-end from this automated environment** due to sandbox restrictions (no
usable Python interpreter, Azure CLI profile permission error). This mirrors the same limitation
already recorded by Infra for Bicep `what-if` validation in `infra/README.md`'s "Validating a
deployment" section.

**Follow-up required:** a team member (or Copilot running in an environment with Azure CLI and
Python access) should execute steps 2-7 verbatim against a clean checkout and update this
checklist's ⚠️ rows to a live pass/fail result, per this issue's own acceptance criteria ("every
setup step... executed verbatim on a clean checkout"). Record that follow-up result in this file
rather than opening a duplicate checklist.
