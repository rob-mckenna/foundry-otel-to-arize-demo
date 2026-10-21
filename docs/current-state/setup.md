# Setup and one synthetic invocation

**Technical preview: existing-resource attachment, not fresh-environment deployment.**
All configuration below is placeholder-only. This page grants no deployment,
role, network, registration, replay or model-call authority.

## 1. Confirm the existing environment

An operator must supply and approve:

- An existing modern Foundry project endpoint and an **exact positive numeric
  Agent version**, not `latest`. Use a no-tool Agent approved for synthetic input.
  The caller neither creates nor updates projects, Agents, versions or models.
- Native Foundry tracing linked to the agent Application Insights component and
  its Log Analytics workspace. Enable synthetic content recording only under
  explicit approval. Client instrumentation alone does not establish this link.
- An existing Event Hub and consumer group; workspace export containing
  **AppRequests, AppDependencies and AppGenAIContent**, with an eligible table
  plan, region and network posture for native data export.
- An existing private Function, its system-assigned identity and identity-based
  host storage on an approved Premium plan; the `genai-correlation` container;
  approved Blob read/write, index-tag write/filter permissions and Event Hub receive access.
- A separate Function-health Application Insights component/workspace with
  **no export or indirect route back to the agent pipeline**.
- Existing Key Vault references for secrets, an approved Arize project/space and
  HTTPS OTLP trace endpoint, plus private DNS/connectivity and publication access.

The single bridge composition is [infra/main.bicep](../../infra/main.bicep).
Review the [infra setup contract](../../infra/README.md) and its placeholder
parameters before any authorized preparation. It attaches to existing resources;
it does not provision a Foundry/model/network foundation. Preserve the reviewed
full Function-settings baseline and existing export tables. Preparation leaves
both triggers disabled; it is not permission to enable or publish.

Once the matching infra source is present, these repository-root checks are offline:

```powershell
python infra\scripts\prepare-bridge.py --parameters infra\main.parameters.json
bicep build infra\main.bicep --stdout > $null
python -m unittest discover -s infra\scripts -p "test_*.py" -v
```

The placeholder sample's schema pass prints a parameter fingerprint and required
owner confirmations, **not readiness**. Optional `--attestation` checks an independently
supplied owner's exact `parametersSha256` and all required confirmations; it does not
generate evidence or verify those assertions against Azure. Do not fill confirmations
with `true` merely to pass the checker. Follow Infra's contract for independently
approved actual parameter snapshots; keep credentials out of those files.

Fresh/repeat deployment, provider acceptance, private runtime connectivity and
the simplified source's live end-to-end behavior require independent validation.
Do not weaken private access or grant broader roles to work around missing prerequisites.

## 2. Install locally

Use Python 3.10–3.12 and a virtual environment inside the checkout. From the
repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\src\prompt-agent[test]"
python -m pip install -e ".\src\telemetry-pipeline[test]"
```

Installation may download packages, but does not invoke a model or configure Azure.
The caller's pinned SDK requirements must remain unchanged for live use.

## 3. Validate the invocation offline

From the repository root after installation:

```powershell
python -m prompt_agent.foundry_responses `
  --endpoint "https://example-foundry.services.ai.azure.com/api/projects/example-project" `
  --agent-name "synthetic-benefits-agent" `
  --agent-version "1" `
  --run-id "00000000-0000-4000-8000-000000000001" `
  --authorization-reference "EXAMPLE-approval" `
  --executor-reference "EXAMPLE-private-runner" `
  --dry-run
```

Expected: `status=offline_dry_run` and a binding hash. These illustrative identities
and references are **not authorization** and must never be used for a live attempt.
Dry-run validates/hashes the fixed request without credentials, SDK clients or
receipt-ledger writes. It proves no Agent existence, permissions, telemetry or delivery.

The source contract is [`foundry_responses.py`](../../src/prompt-agent/prompt_agent/foundry_responses.py):
required endpoint, name/version, run UUID and nonsecret approval/executor references;
optional `--managed-identity-client-id` for an approved user-assigned identity.
Omitting that option selects system-assigned managed identity. There is no developer
credential fallback, custom prompt flag or automatic model retry.

## 4. Live use is a separate gate

An approved operator must reconcile the exact endpoint/version, identity custody,
native tracing/content settings, source/destination scope, bounded cost and independent
verification plan. Then repeat the dry-run with **approved nonsecret values and a fresh
lowercase UUID** and approve its binding before replacing `--dry-run` with `--allow-live`.
No live command is executed by these instructions.

The caller sends one foreground, nonstreaming Responses request with a fixed synthetic
prompt, no tools, a 1,024 output-token cap, a 60-second overall timeout and no client
retries. It uses managed identity and returns actual validated input/output/total usage,
not estimates. Its local span is labeled `local_client_not_native_agent`; do not present
it as native Agent evidence or assume its trace ID equals the service trace.

The repository-local `.foundry-live-receipts` directory records once-only intent/outcome.
Keep it under secure operator custody, excluded from Git; verify that exclusion before
any approved live use. Preserve it: a timeout or failure may be ambiguous, not safe
to retry. A fresh UUID does not authorize repeating the same uncertain operation.
Missing or invalid actual usage also fails the caller without making another request.

## 5. Check offline behavior, then verify approved live evidence separately

```powershell
python -m pytest src\prompt-agent\tests -q
python -m pytest src\telemetry-pipeline\tests tests\telemetry-mapping tests\export -q
```

These tests use synthetic fixtures/mocks; they are not live Azure or Arize proof.
For an independently approved live observation, follow the
[README inspection steps](../../README.md#try-it), compare one native source identity
with its Arize identity and respect the [mapping limitations](mapping-and-limitations.md).
Locate the native trace in the approved invocation's bounded UTC window in
AppRequests/AppDependencies; project only `TimeGenerated`, `OperationId`, `Id`,
`ParentId` and `Name` to establish its identity before inspecting approved synthetic
content. Do not assume a local receipt's client trace ID identifies the native trace.
Do not manufacture source correlation, whole-trace completeness or token-total provenance
from the caller's successful response.
