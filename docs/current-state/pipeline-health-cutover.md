# #153 — targeted existing-demo cutover manifest

**SOURCE/PACKAGE PREPARED; NOT DEPLOYED OR LIVE-ACCEPTED.** Cycle 2 replaces
the earlier speculative Blob/custodian prerequisites. It does not authorize
cloud CUD. Parent owns official Azure validation, final reviewed cutover and
`.azure/deployment-plan.md`. No fresh #147 work, model call, replay, Arize
deletion, VM start, IAM change or diagnostic/policy write is included.

## Approved scope and immutable inputs

Rob McKenna approved the two monitoring resources and existing Function cutover:

```text
Subscription: c81fda52-936e-4f14-8af4-951c0dbb92d2
R: /subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg
Location: eastus2
Function: fotoa-demo-func-eastus2
Function MI: 34e9edde-18e4-4cca-b109-7364de41fa76
Final source/build-tools commit: a49bfd21d242b28f070500a446e9d38c2b8839cc
Initial runtime source: 38ff29e0d3d9d67989b19e75bc84724feee47194
Package: .release/pipeline-health-final-a.zip
SHA256: 16de4fdd0e951efa957d470d9e71822d5de558bcb3f16fb44522169a9bd40382
Bytes: 8522761
```

| Target | Only approved intended change |
|---|---|
| `R/providers/Microsoft.OperationalInsights/workspaces/fotoa-demo-funclaw-eastus2` | New isolated health LAW, `PerGB2018`, retention 30 days, cap 1 GB/day; no export/forwarder |
| `R/providers/Microsoft.Insights/components/fotoa-demo-funcappi-eastus2` | New Function-health component backed only by that LAW |
| Existing `R/providers/Microsoft.KeyVault/vaults/fotoa-demo-kv-eastus2` | ARM-custodied `function-health-connection-string`; identifiers only in output |
| Existing Function | Guard-enabled immutable ZIP, exact exclusion arrays, monitoring KV reference, remove obsolete instrumentation key, temporary trigger gates |
| Agent component/LAW, Event Hub, `genai-correlation`, checkpoints, ledger, source scope | **Unchanged**; no resets, receipt imports or quarantine replay |

All new health resources, including the secret, carry:
`environment=demo`, `owner=infra-team`, `project=foundry-otel-to-arize-demo`,
`costCenter=demo-engineering`, `dataClassification=synthetic`.

Public ingestion rate already reviewed: USD 2.76/GB; gross 30 days at 1 GB/day
is USD 82.80 before allowances/taxes/contract adjustments. This is not a spend
ceiling: the cap can overshoot and stop health ingestion. No additional owner
cost-choice loop is required. Secret operations and ZIP storage/transfer remain
minor usage charges, not a new compute SKU.

## Independent revision and exact offline checks

Infra authored the rejected secret metadata. **Lead, not Infra**, independently
revised it; Infra did not advise/coauthor this cycle. Lead's result remains
subject to parent review; compilation is not policy/live approval.

The secret now has all five synthetic tags and enabled expiration.
`functionHealthSecretExpirationEpoch` is propagated consistently through the
module, scoped rollout and fresh callers. Its default is deployment time +90
days, with integer bounds 1..2147483647. Those bounds alone cannot reject a past
date. For this rollout explicitly use **1800230400 = 2027-01-18T00:00:00Z**,
validated as future and within 90 days of the supplied session timestamp.
Recheck relative to execution time before deployment. Renew by **2027-01-04**
through a separately approved additive rollout; verify secret metadata only,
refresh/verify the Function reference and health ingestion. A versioned reference
must be updated to the renewed version (or explicitly approved versionless
reference); expiry does not rotate the component's ingestion credential.

Standalone Bicep 0.43.8 compiled all four changed entrypoints. Scoped rollout
writes exactly one nested deployment, one LAW, one component and one secret.
Health module writes exactly the latter three. Fresh callers preserve their
existing resource inventory; **do not deploy them against this existing app**.
Full inventory is `.release/compiled-resource-inventory.json`.

With the existing standalone compiler:

```powershell
$env:BICEP_CLI = 'C:\repos\foundry-otel-to-arize-demo\.azure-config\bin\bicep.exe'
python -B -m unittest discover -s infra/scripts -p 'test_pipeline_health*.py' -v
.\infra\scripts\test-health-command.ps1
git diff --check
```

Observed: **14 tests passed in 15.861s**, wrapper tests PASS, diff check PASS.
Parent independently accepted runtime review: **319 passed in 60.98s**, including
child preservation and quarantine/ETag cases; this cycle did not rerun runtime
tests or modify runtime source.

## Real package evidence — no dependency approval gap

Only dependency bytes from the explicitly approved root archive
`.azure-sandbox/issue143-f650fed-built.zip` were used. Both independent
`Get-FileHash` and validator SHA256 matched
`c1a276b62af37da8810c0c120b9cbe8cdff913fc76f43e51399f50db61d540f7`.
No #147 artifact was read or used.

`infra/scripts/stage-pipeline-health-dependencies.py` verified 29 distribution
RECORD inventories/hashes/sizes, all six current requirement roots and recursive
Linux/Python 3.11 markers/extras (31 closure contexts). It rejected traversal,
links, Windows wheels/binaries, missing or unowned code and source/settings
members. Three Oryx-relocated console launchers had their RECORD hashes verified
but were omitted, as was bytecode. Only 1,415 vetted files from
`.python_packages/lib/site-packages/` reached `.release/dependencies`.

All wheel tags intersect Linux CPython 3.11 x86_64 compatibility tags. Six native
members are ELF64 little-endian x86_64: cffi, two charset-normalizer modules,
MarkupSafe, cryptography and protobuf. Cryptography uses
`cp311-abi3-manylinux_2_28_x86_64`; protobuf uses
`cp310-abi3-manylinux2014_x86_64`; other native wheels include cp311 manylinux2014
tags. Detected GLIBC symbols require at most 2.28. This is actual static
compatibility evidence, **not** an import test on the running Linux worker.
Requirements and dependency manifests were not changed, and no Windows venv
was packaged.

Two builds using Python 3.11.9 / zlib 1.3.1 produced identical bytes and receipts:
13 exact binary-git runtime members + 1,415 dependency files = **1,428 members**.
All runtime hashes also equal initial runtime source `38ff29e…`. The builder uses
binary `git -c core.autocrlf=false -c core.eol=lf archive`; no text redirection or
newline normalization is used for packaging or source hashing.

```powershell
# Already executed twice with final-a.zip and final-b.zip; outputs are immutable.
python -B infra/scripts/build-pipeline-health-package.py `
  --source-head a49bfd21d242b28f070500a446e9d38c2b8839cc `
  --dependencies .release/dependencies --output .release/pipeline-health-final-a.zip
```

Full source/dependency hashes are in the ignored package receipts. They are
available in this worktree for parent review, not committed dependency payloads.
See the [source receipt](pipeline-health-source-receipt.md) for inventory digests.

## Actual bounded read-only baseline

All Azure processes used the explicit subscription above and
`AZURE_CONFIG_DIR=C:\repos\foundry-otel-to-arize-demo\.azure-config`,
dynamic installs disabled. Only safe projections were emitted; no raw CLI
failures, setting values, credentials or logs were recorded.

| Fact | Observed 2026-10-20 |
|---|---|
| Function | Running, `functionapp,linux`, `Python|3.11`, expected MI |
| Monitoring | Connection-string setting **present**, KV syntax **false**; legacy instrumentation-key name **present** |
| Run-from-package | Setting **absent**; local `1` **false**, HTTPS/blob **false**. Do not demand a nonexistent old Blob URL or infer code absence |
| Trigger flags | Neither incoming nor outbox disable flag is effectively true; durable enabled |
| Source scope | Exact workspace and agent-component allowlist matches both true |
| Agent LAW | `4658bdb1-b9ca-4f57-a733-6b81f316dc45`, PerGB2018 /30 days /1 GB |
| Source export | Enabled `fotoa-demo-e2e-app-spans`: AppRequests, AppDependencies, AppGenAIContent → `fotoa-demo-ehns-eastus2` / `telemetry` |
| Function governance diagnostic | Preexisting `setByPolicy-MCAPSGovernance` → known McapsGovernance LAW |
| That ONE governance LAW | `dataExports` GET returned `[]`; diagnostic-settings GET returned `[]` |
| Storage | Public access disabled; three approved private-endpoint connections |
| Proposed package container | Exact ARM GET failed `ContainerNotFound`, exit 1 |
| Existing validation VM | Standard_B2s, expected MI `64c0b8ce-7e6c-4875-a2cb-82552efc0376`, **deallocated** |
| SCM network metadata | Main and SCM rules show Allow all, SCM uses-main false, default-action null; not a demonstrated private endpoint |

Governance operations were exactly GET on
`/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/McapsGovernance/providers/Microsoft.OperationalInsights/workspaces/mcaps4f148af4951c0dbb92d2-la/dataExports?api-version=2020-08-01`
and that LAW's `/providers/Microsoft.Insights/diagnosticSettings?api-version=2021-05-01-preview`.
They establish **no configured feedback via those two observable route types**,
not a universal assertion about unobserved external systems. No governance
telemetry, log records, policies or assignments were read/changed.

ARM `sites/.../deployments` GET identifies active successful deployment
**127794d4-c4a1-466f-b000-08ca0bec3bcb**, start/end
2026-10-19T13:46:12.1206466Z /13:46:33.3393485Z.
It matches project-owned `issue143-f650fed-active-source-proof.json`, which
historically records built package `20261019134629.zip`, archive SHA above and
runtime source `f650fed983a687eb97211b634af3d99e7286d6e1`.
This is concrete ARM-to-historical-receipt binding, **not fresh live byte proof**
or permission to call the dependency input a current rollback image.

## Concrete transport, runtime channel and recovery limits

The previous #143 deployment used native config-zip. Earlier in-repo
`.azure-sandbox/e2e-execute.py` (`bearer`, `scm`) and
`e2e-root-v2-publish.py` show an ARM-bearer SCM ZIP/VFS mechanism without
SCM/basic-auth publishing credentials or host keys. They are **reference only**:
do not execute/import historical entrypoints with old mutation logic.

### Authorized GET-only follow-up: channel proven, old bytes NOT bound

Parent accepted Lead's tag/typed-90-day-expiry revision and separately authorized
only ARM-bearer SCM GET/VFS reads. The new fixed-target helper
`infra/scripts/pipeline-health-scm.py` extracts no old mutation entrypoint:
in-memory `az account get-access-token` for the explicit subscription/ARM audience,
exact tenant/subscription validation, HTTPS with certificate verification,
redirects/retries disabled, bounded responses and structured redacted diagnostics.
It never reads publishing credentials, host keys, settings, env files or logs.

At **2026-10-20T16:03:44.968162Z**, ARM before/after and authenticated SCM
deployment GET all agreed on active, complete, status-4 deployment
`127794d4-c4a1-466f-b000-08ca0bec3bcb` with the historical timestamps above.
However, exact GET hashes of the allowlisted SCM-visible `site/wwwroot` files
did **not** match the independently digest-checked original #143 source ZIP:

| Allowlisted files | Result |
|---|---|
| `function_app.py`, `host.json`, `requirements.txt`, `telemetry_pipeline/{__init__,batch,exporter,function_app,mapping}.py` | 8 readable, **all 8 exact byte hashes differ** |
| `telemetry_pipeline/{durable,durable_runtime,durable_store,strict_sender}.py` | 4 HTTP **404 NotFound** |

No newline-normalized equality or historical receipt was substituted for those
actual hashes. This is **SCM-visible filesystem evidence**, not proof that those
bytes are the Linux worker's mounted/running script root. Worker/package binding
therefore remains unproven; do not conclude that the worker is executing the eight
different files or that the historical active-package receipt is currently true.
No dependency metadata was needed/read after this source-binding failure.

Ignored immutable evidence:
`.release/scm-baseline-allowlisted-complete.json` contains all eight fetched
SHA256s, all 12 expected candidate hashes, every mismatch/404 and before/after
deployment identity. The first fail-fast 404 is separately preserved in
`.release/scm-baseline-proof.json`. The complete pass used exactly **15 GETs,
zero POSTs**; no broader directories, package ZIPs or command endpoints were read.

The helper has **10 passing synthetic tests**, including exact path allowlisting,
unauthorized/digest-mismatched POST rejection, HTTP error redaction, redirect
blocking, source mismatch/missing-file handling, explicit CLI 429 classification
and deployment-race rejection.
Parent must review the helper before future cloud-write use.

Narrow transport option for parent review: one ARM-bearer POST of the complete
offline ZIP to
`https://fotoa-demo-func-eastus2.scm.azurewebsites.net/api/zipdeploy?isAsync=true`,
remote build disabled, token held in memory only, no redirects/retries on
ambiguous submission. Reconcile deployment status via GET, then use the same
bearer-authenticated VFS channel to read active package/script-root bytes and
compare the source hashes. **The observed SCM VFS mismatch means this channel
alone is not an established worker-mounted-root/dependency/import proof.**
Worker verification needs a separately authorized known authoritative channel;
no POST-based command is authorized by this follow-up.
This is an **existing SCM management channel, not a private Blob
publisher or new public ingress**. Current metadata and historical success
support the transport option; current bearer GET authorization is now proven.
ZIP POST authorization/success and worker runtime parity remain untested.

No private publisher is needed for that option, so VM start needed: **no**;
incremental VM duration/cost: **0 minutes / $0**. If parent requires a strictly
private publisher/runtime channel instead, that is not established: the known
VM is off and `function-packages` does not exist. Do not create a container,
grant roles, start a VM or claim private publication is ready. Parent must make
that concrete alternate-scope decision first; a VM start alone cannot fix a
missing destination. Existing storage/Function runtime private dependencies are
not evidence that SCM itself is private.

Before changing code, parent must either separately authorize authoritative
worker-byte verification or explicitly accept containment-only code recovery.
Historical receipts do not prove an exact present rollback image. Original
monitoring exists but no safe old KV URI was found. Its known agent component
identity permits a separately authorized ARM-custodied monitoring recovery
(component reference transferred without CLI credential retrieval); do not
invent an absence attestation or retrieve the current plaintext setting.

## Narrow remaining live sequence — NOT EXECUTED

1. Parent finishes official workflow validation/what-if against only
   `infra/pipeline-health-rollout.bicep`, reviews Lead metadata and this package,
   chooses the existing bearer route and explicitly accepts the recovery limit
   or separately authorizes authoritative worker-byte verification. The executed
   GET-only attempt did not establish exact old-runtime bytes.
   Pair/cost/cutover approval and Lead metadata acceptance are already recorded.
2. Recheck `1800230400` is future and <=90 days away at execution. Deploy only
   the health rollout after parent authorization:

   ```powershell
   az deployment group create --subscription c81fda52-936e-4f14-8af4-951c0dbb92d2 `
     --resource-group fotoa-demo-rg --name issue153-function-health `
     --template-file infra/pipeline-health-rollout.bicep `
     --parameters projectToken=fotoa environment=demo location=eastus2 regionToken=eastus2 `
       ownerTag=infra-team costCenterTag=demo-engineering keyVaultName=fotoa-demo-kv-eastus2 `
       functionHealthConnectionStringSecretName=function-health-connection-string `
       functionHealthSecretExpirationEpoch=1800230400 `
       workspaceSkuName=PerGB2018 retentionInDays=30 dailyQuotaGb=1 `
     --query properties.outputs --output json --only-show-errors
   ```

   Use sanitized failure handling, identifiers-only output. Verify new secret
   tags/expiry, component→LAW, empty exports and no unexpected forwarding.
3. Pause both triggers via settings-only update, observe existing 120-second
   claim boundary plus at least 150 seconds and content-free in-flight counts.
   Preserve all leases/checkpoints/quarantine. No build-setting values were read
   in this follow-up. Optional flags that must be false for this complete ZIP:
   `SCM_DO_BUILD_DURING_DEPLOYMENT=false` and `ENABLE_ORYX_BUILD=false`
   (change only if not already false; no dependency-resolution/remote-build step).
   One reviewed bearer
   ZIP submission, no blind retry. No new `WEBSITE_RUN_FROM_PACKAGE` Blob setting,
   no storage publication or Function parent PUT.
4. Set exact JSON arrays:
   `PIPELINE_EXCLUDED_SERVICE_NAMES=["fotoa-demo-func-eastus2"]`,
   `PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS=["R/providers/Microsoft.Insights/components/fotoa-demo-funcappi-eastus2"]`
   (expand literal `R`). Never exclude the agent component. Verify authoritative
   worker bytes, Linux dependency imports and indexing, not merely SCM status/VFS.
5. Confirm the health output URI belongs to the exact expected vault/secret,
   record its version as metadata, and set `APPLICATIONINSIGHTS_CONNECTION_STRING`
   to the consistent versionless reference
   `@Microsoft.KeyVault(SecretUri=https://fotoa-demo-kv-eastus2.vault.azure.net/secrets/function-health-connection-string)`;
   remove only
   `APPINSIGHTS_INSTRUMENTATIONKEY`. Refresh/verify KV reference resolution.
   Do not restore remote build to true for this offline package.
6. Restore outbox first, then incoming only after count-only health/agent/Arize
   evidence establishes isolation and legitimate child preservation. No model
   calls/replays/deletions are authorized by this prep handoff.
7. On unresolved routing/code/parity, keep both triggers paused. Do not reset
   sending/ambiguous/rejected ledger states or claim full rollback. Parent alone
   accepts live result; keep draft PR #154 and issue #153 open until then.

### Exact helper commands for the future authorized parent cutover

The fixed package remains `16de4fdd…40382` from source `a49bfd21…839cc`;
adding this helper does not rebuild or change runtime bytes. It has no arbitrary
URL/path/token argument and no remote-command implementation.

```powershell
# OFFLINE tests only (executed in this follow-up)
python -B -m unittest discover -s infra/scripts -p 'test_pipeline_health_scm.py' -v

# CLOUD WRITE — NOT executed; requires separate parent authorization AFTER
# trigger pause, remote-build-off and recovery/runtime-channel gates above.
python -B infra/scripts/pipeline-health-scm.py --mode publish --authorize-zip-post

# GET-only source comparison after the new deployment becomes active.
# This checks SCM-visible files ONLY, not worker/import/dependency acceptance.
python -B infra/scripts/pipeline-health-scm.py --mode readback
```

The publish mode pins the exact ZIP digest, writes a single-attempt local intent
before POST and refuses another submission if that intent exists. No automatic
poll/retry is hidden in the helper. Status GET is exactly
`https://fotoa-demo-func-eastus2.scm.azurewebsites.net/api/deployments/<returned-guid>`.
On ambiguous POST, reconcile GET-only; never delete the intent to retry blindly.
Sanitized failures distinguish HTTP 401/403/404/409/429, blocked redirects,
TLS certificate/handshake, DNS, timeout and connection failure; no raw response,
error body or bearer material is persisted/emitted.
