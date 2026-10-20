# #153 source validation receipt

**MONITORING-ONLY PASSIVE OBSERVATION PASSED; CUTOVER DEPLOYED; TRIGGERS RESUMED.**
**APP CODE/PACKAGE NOT PUBLISHED; SOURCE GUARD NOT LIVE (HELD).**
This receipt combines retained offline source/package evidence with the parent's
verified monitoring-only execution facts below. Issue #153/draft PR #154 remain
open. No Azure/SCM call was made for this documentation update.

| Revision / release fact | Exact value |
| --- | --- |
| BASE | `2219075f86a7ba387490abdb88ceae5e2a775e9d` |
| Runtime SOURCE HEAD (first implementation commit) | `38ff29e0d3d9d67989b19e75bc84724feee47194` |
| Branch | `squad/153-pipeline-health-isolation` |
| Immutable package source/build-tools SHA | `a49bfd21d242b28f070500a446e9d38c2b8839cc`; pinned offline input, not deployed |
| Package SHA256 | `16de4fdd0e951efa957d470d9e71822d5de558bcb3f16fb44522169a9bd40382` |
| Dependency artifact / hashes | Approved #143 input `c1a276b62af37da8810c0c120b9cbe8cdff913fc76f43e51399f50db61d540f7`; 29 distributions /1,415 staged files |
| Package transport / readback | Historical GET/VFS evidence only; no package published. Code phase/further SCM work HELD |
| Live runtime parity / guard | Worker-byte parity **NOT VERIFIED**; app code unchanged, source guard **NOT LIVE** |
| Live monitoring | `issue153-function-health` succeeded; health LAW UUID `898b620f-3873-4a53-bbee-2b7b96701984`; exact versioned health reference Resolved; triggers resumed; bounded passive observation PASSED |
| Legacy baseline | ARM/SCM active identity agrees, but actual SCM-visible source differs (8 mismatches /4 missing). Worker-mounted bytes unproven; separately authorized authoritative proof or explicit containment-only recovery remains |

Use the single authoritative [cutover/resource/cost manifest](pipeline-health-cutover.md)
for exact resource IDs, tags, roles, secret custody, private publication/runtime
gates, observed governance routing and containment/rollback. Do not substitute a
fresh environment or deploy `main.bicep` to the existing demo. The owner approved
the dedicated non-exported health LAW/component in existing `fotoa-demo-rg`, `eastus2`.
Retail ingestion is USD 2.76/GB: gross USD 82.80/30 days at 1 GB/day before
allowances; the daily cap is not a hard spend ceiling.

## Verified monitoring-only execution — parent evidence (2026-10-20)

- Official monitoring-only validation completed: all **5 Core checks PASS**;
  actual what-if **3 Creates /0 Modify /0 Delete**. Lead metadata revision and
  bounded policy review accepted by parent before execution.
- Deployment **`issue153-function-health` succeeded**, creating health component
  **`fotoa-demo-funcappi-eastus2`** and health LAW
  **`fotoa-demo-funclaw-eastus2`**, UUID
  **`898b620f-3873-4a53-bbee-2b7b96701984`**.
- Triggers paused **2026-10-20T16:35:52.2613051Z**; **150-second drain** observed.
  Monitoring switched **2026-10-20T16:39:30.7098697Z** and legacy
  `APPINSIGHTS_INSTRUMENTATIONKEY` removed.
- Exact versioned health secret:
  `https://fotoa-demo-kv-eastus2.vault.azure.net/secrets/function-health-connection-string/09b48bda9a8e45f6ab915f77970e80af`,
  confirmed **Resolved** through **GET**
  `/config/configreferences/appsettings?api-version=2024-11-01`.
  The earlier POST `/list` used the wrong API; it was not evidence of a failed
  reference. No secret value was read/emitted.
- At **2026-10-20T16:43:39.876321Z**, parent atomically restored incoming
  disabled=`false`, outbox disabled key **ABSENT**, and verified **all other app
  settings unchanged in memory**, without emitting credentials.
- Existing enabled rollback-monitoring secret metadata was found:
  `appinsights-connection-string`, version `1ec98e6a56c34d569ccbee29e770e1c9`;
  its value was never read. This is not a tested code rollback image.
- **No app code/package was published.** Agent export tables/allowlist,
  `genai-correlation`, ledger and checkpoints are unchanged; no VM/new container.
  Guard remains **HELD/NOT LIVE**. Historical queued self-spans can finish
  draining; their retirement must not be attributed to the undeployed guard.

### MONITORING-ONLY PASSIVE OBSERVATION PASSED — bounded parent evidence

Observation initiated **2026-10-20T16:49:03.0245964Z**; query cutoff
`TimeGenerated > 2026-10-20T16:43:39.876321Z`:

- Health LAW: **9 DurableGenAIOutbox AppRequests** generated
  **16:44:30.0085008Z–16:48:30.0038171Z**, plus **618 host/timer AppTraces**;
  all observed resource IDs point to the health AI.
- Separate Success aggregate: **3 successful timer executions**
  (`true`, result `0`, through **16:46:00Z**). Do **not** infer all 9 requests
  were successful from this evidence.
- Final role-filtered agent-LAW union of **AppRequests, AppDependencies and
  AppTraces**: **zero Function-role rows** after resumption within the query
  window. This aggregate did not cover other LAW tables.
  Function **Running**, both **TelemetryTransform** and **DurableGenAIOutbox**
  indexed.
- At **16:46:47Z**, health LAW `dataExports=[]`, LAW `diagnosticSettings=[]`,
  health AI `diagnosticSettings=[]`; existing agent export remains enabled with
  the same three tables/Event Hub destination.
- Earlier health LAW DCR associations `[]`, default DCR `null`. Health AI
  DCR-association API **UnsupportedResourceType** is **not** an empty-result proof.

These observations pass the narrowed monitoring-only check within this window.
Route metadata supports isolation beyond the observation, not an all-tables/
universal future no-feedback proof, whole-trace completeness, or deployment/
acceptance of the source guard. Historical queued self-spans may still drain;
no guard retirement claim is made. #153 remains open and #154 draft because
broader source/backlog guard acceptance remains incomplete.

## Cycle 2 executed evidence (2026-10-20)

- Lead independently revised rejected health-secret metadata; original author
  Infra was excluded from revision/advice. Five synthetic tags and enabled
  expiry, 90-day reusable default, consistent input propagation; explicit
  rollout expiry `1800230400` (2027-01-18T00:00:00Z), renewal by 2027-01-04.
  Parent subsequently accepted that metadata revision on review.
- Four changed Bicep entrypoints compiled; scoped rollout inventory exactly
  deployment + LAW + component + secret. Fresh-caller inventory unchanged.
- `python -B -m unittest discover -s infra/scripts -p 'test_pipeline_health*.py' -v`:
  **14 passed in 15.861s**. Wrapper synthetic tests and diff check PASS.
- Parent independently reviewed runtime and ran the exact runtime command below:
  **319 passed in 60.98s**, accepts guard/child preservation/quarantine/ETag
  source. No runtime edit or rerun by this cycle.
- Approved archive SHA independently checked via PowerShell and Python. All
  distribution RECORDs and recursive current Linux311 dependency closure
  checked. Native wheel tags and six ELF64 x86_64 members checked; maximum
  detected GLIBC requirement 2.28. This is not running-worker import proof.
- Two identical real offline ZIP builds from final source: **8,522,761 bytes**,
  **1,428 members** (13 runtime +1,415 dependencies), Python 3.11.9 /zlib 1.3.1.
  All 13 binary-git runtime hashes equal initial SOURCE HEAD below. No Windows
  environment, old source, settings or payload was included.
- Binary-git builder SHA256:
  `047b8026a2710af4e550333a643991cef228b27417a2c7eda71f942ef2149760`.
- Safe read-only baseline: expected Function/MI/Python3.11, durable/source scopes
  unchanged, monitoring present/non-KV/legacy key present; package setting absent.
  ARM active deployment `127794d4-c4a1-466f-b000-08ca0bec3bcb` matches the
  historical project release receipt, not fresh current-code proof.
- Exact authorized governance LAW's dataExports and diagnostic-settings lists
  both empty. No policy-assignment ID/custodian attestation is needed to describe
  those observed routes. No universal external no-feedback claim is made.
- Proposed `function-packages` ARM container GET: `ContainerNotFound`, exit 1.
  Existing SCM route is the concrete narrower option, not private-Blob readiness.
  No VM is needed for that option (0 minutes /$0 incremental VM); existing B2s
  remains deallocated.

Full generated evidence remains ignored, available in this worktree:

| Evidence path | SHA256 |
|---|---|
| `.release/dependency-vetting.json` (versions, wheel/native evidence, every dependency hash) | `0e145eba36fa8dbc60874d8f41afe7ee966d918142769ab57045caf19368fe0f` |
| `.release/pipeline-health-final-a.receipt.json` (all source/dependency member hashes) | `2e89247c11dfbced591cd10000c2e4c746217ac4b47bd716288240aa1c47b808` |
| `.release/compiled-resource-inventory.json` | `0d3226b7af37a1ee3ab5fe3869a5cf22e01d2d84930ccbdc7e656be8a8a11bad` |
| `.release/baseline-metadata.json` | `384e9dbb2778af272514e30a46f3cdd312970b310efddc761df4474f2feb0095` |

Both `.release/pipeline-health-final-a.zip` and `-b.zip` have the package
digest above; both package receipts are equal. Generated files and parent-owned
`.azure/deployment-plan.md` are not committed. During the offline preparation
described in this section, this child performed no Azure CUD, credentials/settings
dump, VM start, telemetry/log read, model call or #147 artifact access. The parent's
later monitoring-only execution is recorded separately above.

### Fresh authorized bearer GET/VFS evidence

At 2026-10-20T16:03:44.968162Z, the fixed-target helper independently hashed
the allowlisted SCM-visible source. ARM before/after and authenticated SCM GET
agreed on active successful deployment `127794d4-c4a1-466f-b000-08ca0bec3bcb`.
**All 8 readable source members differ** from the original digest-checked #143
source ZIP; **4 durable/strict-sender members return HTTP 404**. This proves bearer
GET access, not the worker-mounted script-root binding. Exact fresh old-runtime
rollback bytes remain **unproven**. No package/FS discovery, settings values,
dependency reads, remote commands or POST occurred.

Full hashes/statuses are in ignored
`.release/scm-baseline-allowlisted-complete.json` (15 GETs /0 POSTs); the initial
fail-fast 404 remains `.release/scm-baseline-proof.json`. The new minimal
`infra/scripts/pipeline-health-scm.py` pins targets/package digest, bounds responses,
keeps bearer only in memory, blocks redirects and retries, and gates future ZIP
POST behind explicit authorization plus a durable single-attempt intent.
Its **10 synthetic tests passed**. Future `readback` mode explicitly proves only
SCM-visible source, not worker imports/dependencies. For any later code phase,
parent would need separate authoritative-worker verification or explicit
containment-only recovery acceptance. That phase is now **HELD**; no further
SCM read/POST or remote command is authorized by the monitoring-only execution.

| GET-only evidence | SHA256 |
|---|---|
| `.release/scm-baseline-allowlisted-complete.json` | `f4db24086b720e4379722b694762f6dd17f9cad99ca76a735acbb77c7c12a19d` |
| `.release/scm-baseline-proof.json` (initial fail-fast 404) | `bc50826e500398361ff6ee9f5174a086fab699a52bf75dafe05a47a84515da3a` |

No ARM/AAD 429 occurred in these SCM reads. Parent's separate policy metadata
collection/throttling and ignored `.azure` evidence were not read or modified.

## Initial assembly validation provenance and exact commands

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

## Original implementation file list / diffstat (historical)

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

The original second commit added this receipt and updated only `pipeline-health-cutover.md`
and `pipeline-health-guard.md` to point to it and pin SOURCE HEAD. It deliberately
does not self-embed its final SHA; resolve that documentation-only HEAD from git/PR.
No mutable `.squad` state, generated caches, root dirt or cancelled #147/PR151
readiness artifacts were part of either original commit. Cycle 2 adds the
independent metadata revision, package vetting/safe metadata tooling and tests,
generated-file ignores, then refreshes only this receipt and the cutover manifest.

## Bounded monitoring pass / held code boundary

- **Monitoring-only passive observation PASSED**, bounded by the cutoff and
  observations above. Validation, health resource deployment, exact KV reference
  resolution and trigger resumption are completed facts, not remaining execution
  instructions or universal future guarantees.
- **Code phase HELD:** no further SCM reads/POSTs, package publication or guard
  activation is authorized. Worker-byte proof remains unresolved for any later
  separately authorized code phase, not an instruction to expand this narrower
  monitoring-only result. Offline package hashes are not deployed-runtime proof.
- Keep issue #153 open and PR #154 draft because broader source/backlog guard
  acceptance remains incomplete; no replay, historical cleanup or attribution of
  queued self-span retirement to the undeployed guard.

In the **undeployed source**, exact service/component exclusions are record-local,
not operation/LLM/trace-wide filters. Durable `excluded` is a distinct 48-hour
terminal, **not acknowledged export**. Genuine non-LLM children remain eligible
under that source policy; no live activation, whole-trace completeness,
historical cleanup, replay or exactly-once claim follows from this receipt.
