# #153 source validation receipt

**CURRENT-STATE source implementation, offline evidence only — NOT DEPLOYED.**
Related to #153; the issue remains open for separately authorized live acceptance.
This assembly is not Lead approval, owner cost approval or live acceptance.

| Revision / release fact | Exact value |
| --- | --- |
| BASE | `2219075f86a7ba387490abdb88ceae5e2a775e9d` |
| Runtime SOURCE HEAD (first implementation commit) | `38ff29e0d3d9d67989b19e75bc84724feee47194` |
| Branch | `squad/153-pipeline-health-isolation` |
| Final branch HEAD | The separate receipt-only commit containing this document; resolve with `git rev-parse HEAD`. It changes documentation only, not runtime source. |
| Package SHA256 | **NOT BUILT** |
| Dependency artifact / hashes | **BLOCKED: no approved complete Linux/Python 3.11 dependency tree established** |
| Private package URL / readback | **BLOCKED: no final package or private publication evidence** |
| Live runtime parity | **NOT VERIFIED** |
| Legacy rollback identifiers | **BLOCKED: custody baseline package URL + digest and monitoring secret reference/absence attestation missing** |

Use the single authoritative [cutover/resource/cost manifest](pipeline-health-cutover.md)
for exact resource IDs, tags, roles, secret custody, private publication/runtime
gates, diagnostics attestation and containment/rollback. Do not substitute a fresh
environment or deploy `main.bicep` to the existing demo. The one owner choice is a
dedicated non-exported health LAW/component in existing `fotoa-demo-rg`, `eastus2`.
Retail ingestion is USD 2.76/GB: gross USD 82.80/30 days at 1 GB/day before
allowances; the daily cap is not a hard spend ceiling.

## Validation provenance and exact commands

The coordinator independently observed the following results on the assembled
source before the implementation commit (2026-10-20), as supplied in the assembly
handoff. They were not rerun in this final assembly. No runtime source changed
between that handoff and SOURCE HEAD. Commands run from the assigned worktree,
with `$env:PYTHONPATH = "$PWD\src\telemetry-pipeline"` and
`$env:BICEP_CLI = 'C:\repos\foundry-otel-to-arize-demo\.azure-config\bin\bicep.exe'`.

| Command | Observed result |
| --- | --- |
| `python -m pytest src\telemetry-pipeline\tests tests\telemetry-mapping tests\export -q` | **319 passed in 53.19s**, includes durable infrastructure tests |
| `python -B -m unittest discover -s infra\scripts -p 'test_pipeline_health*.py' -v` | **7 tests, OK** |
| `python -B -m unittest discover -s infra\scripts -p 'test_modern_*.py' -v` | **26 tests, OK** |
| `& $env:BICEP_CLI build .\infra\pipeline-health-rollout.bicep --stdout` | **PASS**, no compiler/linter warnings |
| `& $env:BICEP_CLI build .\infra\modules\function-app.bicep --stdout` | **PASS**, no compiler/linter warnings |
| `& $env:BICEP_CLI build .\infra\main.bicep --stdout` | **PASS**, no compiler/linter warnings; compile only |
| `.\infra\scripts\validate-naming.ps1` | **PASS**, 9 modules |
| `.\infra\scripts\test-health-command.ps1` | **PASS**, synthetic commands only |
| `git --no-pager diff --check` | **PASS**; also independently repeated during assembly |

Final assembly additionally checked the exact staged 20-file implementation scope,
`git diff --cached --check`, and the binary source-member hashes below. No Azure
call, what-if/deployment, dependency installation or real package build was run.
Package-builder tests exercised synthetic fixtures only.

## Runtime member SHA256 — binary git bytes

Computed during assembly from SOURCE HEAD using
`git -c core.autocrlf=false -c core.eol=lf archive --format=zip <SOURCE_HEAD> -- src/telemetry-pipeline/`.
Python `subprocess` captured binary stdout; `zipfile` read member bytes and
`hashlib.sha256` hashed those bytes directly. No PowerShell text redirection,
working-copy hashing or newline normalization occurred. Selection is exactly the
builder's `source_members`: three root runtime files and every `.py` under
`telemetry_pipeline`, with only the repository prefix removed. This is a source
inventory, not a dependency-complete deployment package or active runtime proof.

| ZIP-root runtime member | SHA256 |
| --- | --- |
| `function_app.py` | `d1c2c78186940ae71035d6cdfe250ce3db5c419a944ebb5e5a4876f81420dd92` |
| `host.json` | `13afb1d31f4e36fd52c51479aaff6b088cfb01d95aa42ffbd2d58ca1d24784f4` |
| `requirements.txt` | `0efc0036c9ae8d96872c0c5993668a0e0603bcb78c8756fbd1435dda1b05fbcc` |
| `telemetry_pipeline/__init__.py` | `d39aac6fa0692ae17c100f53a51f83c4392a462ba9bc9c3d26ecd3600d588b47` |
| `telemetry_pipeline/batch.py` | `5e680b558ec17f9a4b5fd4329230d521785d2dede3f6ab33439b8fb0a9e57777` |
| `telemetry_pipeline/durable.py` | `9fd3fdd8e9954edc6c92f2580e50ef5cab166320162879221dbb79ba7aa9846c` |
| `telemetry_pipeline/durable_runtime.py` | `2a35a2e0df5791fe08c9865ef2585a9e8fa57a1a5a7feefce6c4c8f38b6e3448` |
| `telemetry_pipeline/durable_store.py` | `0e28345c86b15e630dbc5465daff15b88dd919a8de376f1746c3904a986218c0` |
| `telemetry_pipeline/exporter.py` | `4fcaea480fb7e3d4fd9422fac21beca3f4d2d55f07d858ed5a236c693198d4bc` |
| `telemetry_pipeline/function_app.py` | `f572a5f9a3e49766bbbe8663521a559dbe2da6b6a6661f337fb7d9124eb49522` |
| `telemetry_pipeline/mapping.py` | `2a61d81742b5a0e8cb10f5e8f7b59031d72f8c18ea4f5f76ee23f633007c0de3` |
| `telemetry_pipeline/source_policy.py` | `1232efdf89e22eef52a5c47117dcc7502a9abb78aa47d5f3f269b4797c5cdc29` |
| `telemetry_pipeline/strict_sender.py` | `d210d9f0f80bb4c59f04d7de7a468edf866d7b8563dd6f1c1f20bae0bbe57179` |

## Exact implementation file list / diffstat

BASE → SOURCE HEAD: **20 files changed, 1776 insertions(+), 10 deletions(-)**.
Paths below are repository-relative; counts are added/deleted lines.

| File | + / - |
| --- | --- |
| `docs/current-state/pipeline-health-cutover.md` | 612 / 0 |
| `docs/current-state/pipeline-health-guard.md` | 110 / 0 |
| `infra/README.md` | 9 / 0 |
| `infra/modules/function-app.bicep` | 35 / 4 |
| `infra/modules/function-health.bicep` | 78 / 0 |
| `infra/pipeline-health-rollout.bicep` | 42 / 0 |
| `infra/scripts/build-pipeline-health-package.py` | 104 / 0 |
| `infra/scripts/invoke-health-command.ps1` | 59 / 0 |
| `infra/scripts/test-health-command.ps1` | 55 / 0 |
| `infra/scripts/test_pipeline_health.py` | 136 / 0 |
| `infra/scripts/test_pipeline_health_package.py` | 79 / 0 |
| `src/telemetry-pipeline/README.md` | 14 / 0 |
| `src/telemetry-pipeline/telemetry_pipeline/batch.py` | 10 / 0 |
| `src/telemetry-pipeline/telemetry_pipeline/durable.py` | 51 / 4 |
| `src/telemetry-pipeline/telemetry_pipeline/durable_runtime.py` | 5 / 1 |
| `src/telemetry-pipeline/telemetry_pipeline/durable_store.py` | 1 / 1 |
| `src/telemetry-pipeline/telemetry_pipeline/mapping.py` | 16 / 0 |
| `src/telemetry-pipeline/telemetry_pipeline/source_policy.py` | 49 / 0 |
| `src/telemetry-pipeline/tests/test_durable.py` | 196 / 0 |
| `src/telemetry-pipeline/tests/test_source_policy.py` | 115 / 0 |

The second commit adds this receipt and updates only `pipeline-health-cutover.md`
and `pipeline-health-guard.md` to point to it and pin SOURCE HEAD. It deliberately
does not self-embed its final SHA; resolve that documentation-only HEAD from git/PR.
No mutable `.squad` state, generated caches, root dirt or cancelled #147/PR151
readiness artifacts are part of either commit.

## Pending acceptance gates

- External diagnostic custodian's exact policy assignment ID and bounded
  no-feedback attestation for the identifiers in the cutover manifest.
- Custody baseline: prior immutable package URL + SHA256 and versioned monitoring
  secret URI, or custodian attestation that a legacy URI never existed.
- Approved dependency provenance; final package SHA256; private publication and
  independent running-script-root/dependency parity, package resolution/indexing.
- Owner's one pair/cost approval, separately authorized live cutover/readback,
  and passive synthetic-only acceptance evidence. Parent/user owns the review gate.

Exact service/component exclusions are record-local, not operation/LLM/trace-wide
filters. Durable `excluded` is a distinct 48-hour terminal, **not acknowledged
export**. Genuine non-LLM children remain eligible; no whole-trace completeness,
historical cleanup, replay or exactly-once claim follows from this receipt.
