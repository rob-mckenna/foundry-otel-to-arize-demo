# Foundry telemetry to Arize demo

A reusable, **synthetic-data-only** observability demo for enterprise healthcare:
Microsoft Foundry Prompt Agent instrumentation → Application Insights → Log Analytics →
Event Hub → Azure Function transform → Arize OTLP.

**Implemented does not mean independently validated end-to-end.** Start with the offline
setup below. Live deployment is a separately approved activity, not a prerequisite for
the synthetic demo and not authorized by this README.

## Current status

| Area | What this asset supports | Evidence limit |
|---|---|---|
| Local Prompt Agent | Synthetic scenarios, stub responses, OpenTelemetry/OpenInference spans, correlation IDs and token attributes | The baseline client is a stub, not a live Foundry model; its token estimates are not live usage |
| Telemetry transform | Native/legacy span mapping, ID preservation, typed metadata/usage, bounded failure handling and OTLP serialization | Offline fixtures and protobuf tests do not prove actual Event Hub delivery or Arize acceptance |
| Function publication | Source reconciled to the package published on 2026-10-16 | Explicit **package-only approval exception**, not completed generic official validation or a new deployment allowance |
| Destination parity | Requires independent same-invocation graph, field and token evidence | **Arize parity UNKNOWN**; publication or an export success count is not destination proof |
| Infrastructure | Existing baseline Bicep retained | Operator review/configuration required; not a turnkey reconciled deployment |
| Future work | Direct OTLP bypass and content conversion | **PROPOSAL ONLY / NOT IMPLEMENTED**; excluded from this asset's implementation |

The [mapping/export contract](docs/current-state/telemetry-mapping-export-contract.md) is the
canonical technical status, including source-package provenance and limitations. Issue #139
is QA-approved locally, **not deployed**. Historical private runtime allowances are **CLOSED
3/3**; evaluation remains **PARTIAL_OR_UNKNOWN_DO_NOT_RETRY**. Offline checks do not reopen
model, replay, registration, evaluation or deployment budgets.

## One supported setup path: offline synthetic demo

### Prerequisites

- Git, Python **3.10+** (3.11 recommended), and PowerShell 7+.
- A fresh shell with `APPLICATIONINSIGHTS_CONNECTION_STRING` **unset** so the Prompt Agent
  uses console export. No Azure login, Arize key, MCP launcher or live `.env` file is needed.
- Package access for the initial dependency installation. Keep the virtual environment local
  and do not stage it or generated package metadata.

Run these commands from the repository root after cloning:

```powershell
git clone https://github.com/rob-mckenna/foundry-otel-to-arize-demo.git
Set-Location .\foundry-otel-to-arize-demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\src\prompt-agent[test]" -e ".\src\telemetry-pipeline[test,otlp]"
```

The `otlp` extra supplies the real protobuf/exporter dependencies used by offline export
tests; installing it does not enable a live destination. Do not set live exporter credentials
for this walkthrough.

### Run synthetic scenarios

```powershell
if (Test-Path Env:\APPLICATIONINSIGHTS_CONNECTION_STRING) {
    throw 'Use a fresh shell without Application Insights export configured.'
}
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONPATH = "$(Resolve-Path .\src\prompt-agent);$(Resolve-Path .\src\telemetry-pipeline)"
python -m prompt_agent.main --scenarios
```

Expect five fabricated member-services scenarios, stub responses, console spans, correlation
IDs and estimated token counts. Inputs live in
[`synthetic/scenarios.py`](src/prompt-agent/synthetic/scenarios.py). This runs neither a real
model nor the live Event Hub/Function/Arize chain. Never substitute patient or customer data.

### Verify offline

In the same shell:

```powershell
python -m pytest -q -p no:cacheprovider src\prompt-agent\tests
python -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests tests\telemetry-mapping tests\export\test_otlp_export_conformance.py
```

These synthetic tests inspect span graphs, correlation, mapping, usage preservation, Function
binding metadata, failures and real OTLP protobuf encoding without live services. They do not
establish destination parity. No separate telemetry lint/typecheck command is configured.

## Live setup: operator review and explicit approval required

There is no supported one-command live deployment in this sharing path. Retained
[`infra/README.md`](infra/README.md) documents baseline resources, not approval to execute its
historical recipes. Before any live action:

1. Obtain explicit scope/budget approval and follow the official Azure prepare → validate →
   deploy lifecycle. Review the exact source/package and deployment plan; a prior exception
   is not reusable authorization.
2. Review baseline parameters: `projectToken`, `environment`, `location`, `regionToken`,
   `ownerTag`, `costCenterTag`, SKUs and networking choices. Keep required tags and synthetic
   classification. Do not apply example defaults to an existing private environment.
3. Independently reconcile Log Analytics export tables/routes, Function package publication,
   identity permissions, networking and binding app settings. Source defaults are hub
   `telemetry`, prefix `EventHubConnection` and consumer group `$Default`; select the actually
   provisioned hub/group explicitly (normally `function-transform`). Held binding/settings
   changes are **not** included in this branch.
4. Review the HTTPS `/v1/traces` destination, Arize Space/key and project resource routing.
   Use Key Vault and managed identity where supported; never print or commit secret values.
5. Plan separately authorized same-invocation source capture, native delivery, OTLP
   acknowledgment and independent Arize graph/field/token checks. Retain immutable evidence;
   do not infer parity from a deployment response, console fallback or local protobuf tests.

Preserve private networking, Entra-only authentication, Key Vault, Defender, deallocated-VM
controls and all runtime guards. No replay, checkpoint reset, evaluation retry, role expansion
or content-protection workaround is implied. Missing source parents, usage or content must
remain missing rather than fabricated.

## Architecture and documentation

- [Current-state architecture and diagrams](docs/current-state/architecture.md): implemented
  path and its explicit evidence limits.
- [Current-state index](docs/current-state/README.md) and
  [mapping/export contract](docs/current-state/telemetry-mapping-export-contract.md):
  current canonical reading path.
- [Future-state designs](docs/future-state/README.md): **CONCEPTUAL — NOT IMPLEMENTED**.
- [Demo archive](demo/README.md): retained historical narratives/runbooks, **not** alternate
  setup instructions or current validation claims.

Current code lives in `src\prompt-agent` and `src\telemetry-pipeline`; baseline Bicep lives
in `infra\main.bicep` and `infra\modules`. Tests use synthetic fixtures under the component
test directories, `tests\telemetry-mapping` and `tests\export`.
The `.squad` framework/casting is retained, not migrated. Tracked portable MCP definitions
are optional contributor tooling, not application setup prerequisites; machine-local launcher
overrides must not be shared.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the repository's issue/PR templates. Keep current
implementation separate from conceptual designs, preserve IDs and supplied token counts,
add focused mapping/export tests for behavior changes, and update the canonical contract
without rewriting dated historical evidence. Never commit credentials, runtime receipts,
local environments, real PII/PHI or customer-identifying data.
