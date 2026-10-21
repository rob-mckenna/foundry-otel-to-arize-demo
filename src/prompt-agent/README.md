# Minimal Foundry caller

One real Responses API call to an **existing exact agent version**, using managed
identity and one fixed synthetic prompt. No stub runtime, registration, allocation,
deployment, replay, tools, or automatic model retries.

## Install and check offline

From the repository root (Python 3.10+):

```powershell
Set-Location .\src\prompt-agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m prompt_agent.foundry_responses --help
.\.venv\Scripts\python.exe -m prompt_agent.foundry_responses `
  --endpoint https://synthetic-account.services.ai.azure.com/api/projects/synthetic-project `
  --agent-name synthetic-no-tool --agent-version 7 `
  --run-id 4bd64a85-a504-4603-ad48-97e19b8b8c01 `
  --authorization-reference synthetic-approval `
  --executor-reference synthetic-private-runner-mi --dry-run
```

Dry-run only validates configuration and prints a binding hash: no SDK client,
authentication, ledger writes, or network. Tests mock credentials and HTTP.
Runtime SDK dependencies are installed without an extra; `[test]` adds pytest
and the in-memory OpenTelemetry SDK used by tests.

## Live contract — requires separate explicit approval

On the approved managed-identity runner, supply the existing project endpoint,
agent name, exact positive numeric version (never `latest`), fresh lowercase
UUID run ID, fresh approved nonsecret authorization reference, and approved
nonsecret executor/custody reference. References accept 1–96 letters, digits,
underscores, dots, or hyphens and must start with a letter or digit.

```powershell
.\.venv\Scripts\python.exe -m prompt_agent.foundry_responses `
  --endpoint $approvedProjectEndpoint `
  --agent-name $existingAgentName --agent-version $exactAgentVersion `
  --run-id $freshRunId --authorization-reference $approvedFreshReference `
  --executor-reference $approvedRunnerReference --allow-live
```

These variables are operator-supplied nonsecret configuration, not environment
variable defaults; no `.env` is read. For approved user-assigned identity add
`--managed-identity-client-id $approvedManagedIdentityClientId`; omit for system
identity. No API key, CLI credential fallback, or workload-identity token file
is accepted. The caller identity needs existing project access and network
reachability; the project's identity is not the caller identity. This command
example grants **no** live authorization.

The fixed input is `SYNTHETIC DEMO ONLY. Reply with one short sentence: this is a
fabricated benefits enquiry.` Bounds: 60 seconds overall, 1,024 output tokens,
16,384 response-text bytes. Only valid actual API token usage is accepted; raw
output and service errors are never printed or persisted. Exit 0 reports
`offline_dry_run` or `succeeded`; exit 1 reports a fixed sanitized error code.
`--dry-run` takes precedence if both mode flags are supplied.

Exclusive intent and outcome files live in `.foundry-live-receipts` at the
source checkout root. Preserve these receipts (including partial/inflight files).
Reuse of either authorization reference or run ID is refused, including after
timeout, crash, or ambiguous failure. Never erase the ledger to rerun; reconcile
an ambiguous attempt before seeking any separate new authorization. This is a
local replay safeguard, **not** an exactly-once service guarantee or approval system.
Source/editable checkout is required; do not run concurrent copies on different
checkouts as a substitute for shared authorization custody.

Native App Insights/Log Analytics → Event Hub → durable Function → Arize telemetry
requires the retained environment's independently configured service-side path.
This caller does not configure exporters or manufacture native trace/span IDs,
correlation, model names, or token counts. Its optional local `CLIENT` span is
not a native agent span; provider propagation, complete traces, downstream
delivery, and deployed-code parity are not asserted by caller success.
