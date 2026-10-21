# Contributing

Read [the contribution rules](.github/copilot-instructions.md) and
[setup](docs/current-state/setup.md). Use synthetic data only, Key Vault for
secrets and managed identity for Azure access. Offline work does not authorize
cloud access, deployment, replay or model calls.

## Offline checks

Use Python 3.10–3.12 and a checkout-local virtual environment. CI installs both
package manifests and the Function requirements in a clean runner, then tests
both components and the root mapping/export contract.

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\src\prompt-agent[test]" -e ".\src\telemetry-pipeline[test]" -r src\telemetry-pipeline\requirements.txt
python -m pytest src\prompt-agent\tests -q
python -m pytest src\telemetry-pipeline\tests tests\telemetry-mapping tests\export -q
python infra\scripts\prepare-bridge.py --parameters infra\main.parameters.json
bicep build infra\main.bicep --stdout > $null
python -m unittest discover -s infra\scripts -p "test_*.py" -v
```

Install the standalone Bicep compiler in the checkout if it is not on PATH.
Set `$env:BICEP_CLI` to its absolute path for compiled infra tests and invoke
that same executable for `build`. A missing compiler means compiled cases are
**not validated**; a skipped suite is not a passing infrastructure check.
CI requires the compiler before running those tests.

The immutable package builder and prerequisites are documented in
[infra](infra/README.md#minimal-immutable-packaging). Use finalized committed
source and a separately prepared Linux Python 3.11 dependency tree, not Windows
or inherited host packages. Package receipts prove byte provenance only.

## Before proposing a change

- Update the relevant [current-state docs](docs/current-state/setup.md) whenever
  commands, settings, architecture or behavior change. Keep the README plus the
  three focused docs as the supported narrative, not a second setup path.
- Cover changed behavior with focused tests; mapping/export changes must
  preserve IDs and actual usage without synthesizing missing source values.
- Label conceptual work **CONCEPTUAL — NOT IMPLEMENTED**. Do not implement a new
  architecture or present source changes as deployed evidence without approval.
- Record exact test commands and results, skips, installation blockers and
  unvalidated behavior in the full [PR template](.github/pull_request_template.md).
  State why no documentation update is needed if that is the case.
- Never include live settings, raw telemetry, credentials or local receipts.
  Keep local evidence in ignored `.local`, `.release` or
  `.foundry-live-receipts` directories under approved custody.

Push, PR creation, merge and all live operations require separate approval.
