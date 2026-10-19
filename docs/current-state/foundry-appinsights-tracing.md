# Modern Foundry project → Application Insights association (#139)

**CURRENT-STATE implementation; native adoption, clean creation and identical
redeployments verified (2026-10-16/17 UTC).**
Local builds/tests, association metadata, deployment, source capture and observed
trace delivery remain separate evidence gates. The executed evidence below
supersedes earlier local-only/not-deployed status. This runbook does not itself
authorize another deployment, invocation, RBAC, authentication or network change.

## Scope and recovery

**Current boundary (2026-10-19):** this remains an **existing-resource,
connection-only** entrypoint. The accepted modern-only private fresh foundation
is implemented in source separately under
[ADR-0004](../adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md).
Infra reports offline checks complete, not cloud validation.
Fresh provider/private/runtime/end-to-end validation is **PENDING**; #139 clean
connection creation on an existing account is not fresh-environment validation.
Use [current operations](runbooks.md) for fresh/adopt/retire boundaries; do not
run fresh main over the mixed live RG.

**Historical #139 recovery scope:** the implementation starts at main `ebaca4c`. Only the connection
entrypoint/module, parameter profiles, bounded readback and relevant tests are
recovered/adapted from preserved #139 work. The full unpublished modern Foundry
foundation, model and private DNS/endpoint templates are deliberately **not**
restored **in that recovery**. At that baseline `infra\main.bicep` was the legacy
hub composition, not the modern project tracing entrypoint. This is historical
context, not a supported classic deployment path.

Use `infra\modern-foundry-tracing.bicep` independently against **existing**
modern account/project resources in the deployment resource group. It creates
a clean connection on an already provisioned approved project, or adopts an
existing connection. It does not provision an entire Foundry environment.
Parameterize account, project, exact connection name, component ARM ID, sharing
and reviewed connection private-endpoint settings. Region/environment are
embodied in those existing resource identities,
not hardcoded in the module. Child connections have no tags/location API fields;
parent tags and all existing posture remain unchanged.

| Mode | PUT behavior and prerequisite |
|---|---|
| `preserveExisting` (default) | No connection PUT, including when the connection is absent. Not an existence/health check, adoption, deletion or rollback. |
| `ApiKey` | Explicit same-auth creation/adoption with equivalent secure material in `credentials.key`; does not enable local auth or add a key-auth fallback. |
| `ProjectManagedIdentity` | Separate optional preview migration/creation; requires approved ingestion identity/role, component configuration and provider-readable routing metadata. Never forced on a working ApiKey link. |

Both writing modes require `appInsightsConnectionPropertiesReviewed=true`.
The module rejects review=0 and empty secure material through nested ARM
parameter constraints. That is a validation guard, **not** a live authorization
or an assertion that the supplied material is equivalent.

### Documented provider contracts

Verified against official sources on 2026-10-16:

- [ARM 2025-09-01 child connection reference](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-09-01/accounts/projects/connections):
  `Microsoft.CognitiveServices/accounts/projects/connections`, `ApiKey`,
  secure `credentials.key`, target, metadata and explicit sharing.
- [Pinned 2025-09-01 OpenAPI contract](https://github.com/Azure/azure-rest-api-specs/blob/e9369ed0ffbd1acfd34db5e669e66b6ba6798f5c/specification/cognitiveservices/resource-manager/Microsoft.CognitiveServices/CognitiveServices/stable/2025-09-01/cognitiveservices.json):
  `ProjectConnections_Create` consumes `ConnectionPropertiesV2BasicResource`;
  its ApiKey properties inherit `ConnectionPropertiesV2`. Both `peRequirement`
  and `peStatus` are in that request schema, with **no** `readOnly` or
  read-only `x-ms-mutability` annotation on either property or referenced enum.
  Despite its name, `peStatus` is not documented as read-only in this pinned API.
  In contrast, `group` and `createdByWorkspaceArmId` explicitly have
  `readOnly=true`; `isDefault` is not a declared request property.
- [Pinned Microsoft ApiKey sample](https://github.com/microsoft-foundry/foundry-samples/blob/82724a4056091791628e7919396777ba55b29dca/infrastructure/infrastructure-setup-bicep/01-connections/connection-application-insights.bicep):
  category `AppInsights`, target/metadata `ResourceId` = component ARM ID,
  `ApiType=Azure`, and the component connection string as `credentials.key`.
  The sample uses an earlier preview API; the module uses the documented
  2025-09-01 credential shape. Exact provider validation is still required.
  Its account-level connection and evaluation reader grants are **not** copied.
- [Pinned Microsoft MI sample](https://github.com/microsoft-foundry/foundry-samples/blob/82724a4056091791628e7919396777ba55b29dca/samples/python/foundry-autopilot-agent/infra/modules/project.bicep):
  child connection API `2025-09-01`, `authType=ProjectManagedIdentity`, and
  `metadata.ApplicationInsightsConnectionString`. A narrow BCP036 suppression
  matches the sample because the ARM discriminator schema is stale.
- [Foundry Entra trace-ingestion documentation (preview)](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/trace-ingestion-entra-authentication):
  service-side ingestion uses the **project system-assigned identity**, not
  the account, deployer or client exporter. Only one AppInsights connection
  per project is supported. ApiKey metadata does not prove MI is unsupported.

Do not substitute legacy hub `applicationInsightsResourceId`, generic `AAD`
or `ManagedIdentity` auth discriminators, or guessed MI properties. Compilation
checks the generated wire contract, not service acceptance.

## Secure material, identity and preserved posture

For either writing mode, supply equivalent material **only** by an approved
[ARM Key Vault parameter reference](https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/key-vault-parameter)
with an explicit immutable `secretVersion`. Secure parameters cross both
module boundaries; no credentials, connection strings or secret-derived values
are outputs. Never use a plaintext parameter `value`, CLI literal, credential
GET, `listKeys`, `listSecrets`, raw response/log dump, `--debug` or `--verbose`.
The secure-reference example contains placeholders and is **not executable**.
Pinning and approval are operator checks; Bicep cannot inspect how an ARM
secure parameter was resolved.

The deployment operator needs deployment operations at the deployment scope,
`Microsoft.CognitiveServices/accounts/projects/connections/read` and
`Microsoft.CognitiveServices/accounts/projects/connections/write` at the exact project scope, and
`Microsoft.KeyVault/vaults/deploy/action` on the approved vault. The existing
vault must already allow template deployment and its approved resolution path.
Project MI does not need secret-reader access when ARM resolves this parameter.
No role is granted here. Use existing scoped authorization; do not add broad
Contributor/Owner access as a workaround.

For **optional MI ingestion**, the documented minimum is **Monitoring Metrics
Publisher** (`3913510d-42f4-4e42-8a64-420c390055eb`) for the **project** identity
at the exact component scope, plus AppInsights Entra-only configuration.
Hosted-agent code can separately need Agent Identity authorization; that is not
this Prompt Agent change. Human Log Analytics Reader (and Privileged Monitoring
Data Reader for protected content tables) concerns viewing, not ingestion.
Do not infer permissions from an ApiKey connection or grant these roles for
same-auth adoption.

**MI metadata security gate:** the official MI sample places routing material in
ordinary provider metadata. `@secure()` protects deployment parameters, **not**
arbitrary provider metadata GETs. This is not a runtime vault reference or proof
of protected storage. Obtain separate security acceptance of that surface before
selecting MI; absent acceptance, do not deploy MI or invent another field.
Use only allowlisted projections even when a connection uses MI.

Preserve private endpoints, DNS/VNet, account publicNetworkAccess Disabled,
disableLocalAuth, ACL Deny/None, and all component ingestion/query controls.
This entrypoint has no parent, role, network, model, vault or component writes.
It must not be paired with a broad legacy/foundation redeployment for adoption.
Missing permission, vault resolution or service connectivity is a blocker,
not permission to open endpoints, switch tenants, enable key/local auth, or
weaken firewalls.

## Profiles, preflight and ownership

- `modern-foundry-tracing.parameters.json`: exact existing demo identities,
  preservation only, no secret reference or PUT.
- `modern-foundry-tracing.dev.parameters.json`: dev names and target placeholders;
  preservation only, not evidence of a deployed dev project.
- `modern-foundry-tracing.secure-reference.parameters.json`: non-executable
  starting point for **either** writing mode. Replace all placeholders with
  approved resource identities and the equivalent version-pinned vault reference;
  explicitly choose auth, sharing and review=true only after approval.
  Do not deploy it unchanged, even in preservation mode: ARM can resolve a
  supplied vault reference independently of whether the child PUT is skipped.

Before adoption, inventory the exact project with the validator below. It must
contain exactly the intended single AppInsights connection. Keep its existing
name; never generate a second association. Sharing is explicit:
`private` = `isSharedToAll=false`, `projectShared` = true.
Review all other nonsecret writable properties before the PUT, not just the
validator's identity subset. Reconcile nonempty `sharedUserList`, expiry,
private-endpoint settings, extra metadata or other omitted fields in the exact reviewed
delta; do not assume omitted fields or credentials survive PUT.
The module's ApiKey branch explicitly sets `useWorkspaceManagedIdentity=false`.
Provider default/omission behavior still needs provider validation and what-if.
Secret equivalence cannot be proven from metadata and must not use a credential GET.

Explicitly set `appInsightsConnectionPeRequirement` and
`appInsightsConnectionPeStatus` to the reviewed request values. Both pass through
the module into **both** auth branches; the defaults and example profiles use
`NotRequired` / `NotApplicable`, matching the observed demo connection, not a
universal preservation guarantee. The allowed requirement values are `Required`,
`NotRequired`, `NotApplicable`; allowed status values are `Inactive`, `Active`,
`NotApplicable`. Do not infer actual endpoint health from a supplied status.
The provider's observed status and acceptance of these request values must still
be checked independently after approved validation/deployment.

Do not replay read-only `group`/`createdByWorkspaceArmId`, undeclared response
extensions such as `isDefault`, or raw GET objects into PUT. Observing those
fields is not itself an omission blocker; verify their classification against
the pinned write schema. The common Resource base does not declare connection
`tags`/`location` request fields either. Any additional **writable** nonempty
field remains a blocker until its exact preservation is reconciled.

For a clean connection, first verify an approved existing modern project and an
empty AppInsights category inventory with a projected read-only GET. The strict
validator intentionally fails for a missing association; do not suppress that
failure as a post-deployment success. Create only the reviewed stable connection.

No cleanup is authorized. The existing demo connection is shared, manually
created infrastructure; ownership must be reconciled before marking it managed.
Incremental deployment/omitting the module preserves it; neither is rollback.
Removing a temporary deployment record is not connection cleanup. Any separately
approved deletion must target only the owned connection, never its shared
account/project, AppInsights, LAW, vault or private networking.

## Focused local validation

Run from repository root with a usable Bicep executable and Python:

```powershell
bicep build .\infra\modern-foundry-tracing.bicep --stdout | Out-Null
bicep build .\infra\modules\modern-foundry-app-insights.bicep --stdout | Out-Null
python -B -m unittest discover -s .\infra\scripts -p test_modern_foundry_tracing.py -v
git --no-pager diff --check
```

Tests discover Bicep via `BICEP_CLI`, PATH, then Azure CLI (`az bicep build`).
They compile **current sources in memory**, not old recovery artifacts. The
12 focused tests include 24 mutations of actual compiled auth/target/secure
boundaries, opt-in/review/sharing gates, resource inventory, stable connection
name, endpoint-configuration forwarding/defaults/allowed values, safe outputs,
and Incremental mode, plus synthetic CLI/readback failures.
This does not validate live provider enforcement or secret equivalence.

For the existing repository-local compiler, this session used
`$env:BICEP_CLI=(Resolve-Path .\.azure-config\bin\bicep.exe).Path` (0.47.16).
Both builds and all 12 tests passed (24 mutation cases), independently reviewed
on source `2fb796d`. The naming linter excludes only this
connection-only module because its API has no tags and adoption needs the exact
name; compiled tests guard that exception. Its script execution was blocked by
the host's signing policy; do not bypass the policy.

## Exact bounded metadata readback

Use only the approved repository-contained CLI context; do not log in, inspect
host caches or switch tenant/subscription. This session established target
subscription `c81fda52-936e-4f14-8af4-951c0dbb92d2`, tenant
`e500988a-f788-4f81-b1ba-e3ad7cd66171`, state Enabled with a projected account
read. No new authorization is implied.

```powershell
$env:AZURE_CONFIG_DIR=(Resolve-Path .\.azure-config).Path
$project='/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-eastus2'
$appi='/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/Microsoft.Insights/components/fotoa-demo-appi-eastus2'
python -B .\infra\scripts\validate-modern-foundry-tracing.py --project-resource-id $project --connection-name fotoa-demo-appi-eastus2-2199 --app-insights-resource-id $appi --expected-auth-type ApiKey --expected-sharing private
```

The readback passed on 2026-10-16: exactly one intended AppInsights/ApiKey/private
association; `associationVerified=true`, `sharingVerified=true`,
**`traceDeliveryVerified=false`**. This validator reports metadata only.
Subsequent actual IaC deployments are evidenced separately below; its false
delivery field is not a denial of the separately observed fresh trace.

The tool performs one projected ARM list GET, explicit subscription, 90-second
timeout, no retries/pagination or credential endpoints. Missing/multiple
associations, pagination, wrong project/name/category/target/metadata ResourceId,
auth or requested sharing fail loudly with exit 1. Raw CLI errors/responses
are suppressed. It does not assert provisioning health, effective permissions,
private service egress, UI-origin traffic or trace/span/token fidelity.
After a separately approved MI migration require
`--expected-auth-type ProjectManagedIdentity`; an ApiKey pass cannot satisfy it.

## Existing-resource deployment procedure and historical prerequisites

Historical cycle3 receipts reported vault metadata-version listing blocked by
`Forbidden/ForbiddenByConnection`, no affirmed component Entra-only property,
and no matching direct/inherited project-MI component assignment in that query.
These are dated prerequisite observations, not fresh effective-authorization
claims. No credential value was retrieved. Same-auth adoption does not require
MI migration, but still requires approved equivalent secure resolution.

The originally approved adoption target was **only** the exact demo child connection printed above,
in resource group `fotoa-demo-rg`, leaving its name/target/ApiKey/private settings
unchanged. Before any writing operation the coordinator must approve the exact
source/profile, pinned vault ID/name/version, property delta and target, establish
serialized ownership, and complete **azure-validate → azure-deploy** gating.
Do not run the baseline scratch-deployment/teardown helper for this shared target.

Reusable validation commands for a separately approved profile follow. Actual
native commands/results for the executed phases are retained in the receipts
below; the unsigned PowerShell helper workflow was not executed or bypassed.

```powershell
# $approvedProfile is the reviewed repo-local nonsecret reference-only profile.
# It explicitly selects ApiKey, private, review=true and an approved pinned vault reference.
# It also preserves reviewed connection peRequirement/peStatus; neither proves endpoint health.
az deployment group validate --subscription c81fda52-936e-4f14-8af4-951c0dbb92d2 --resource-group fotoa-demo-rg --template-file .\infra\modern-foundry-tracing.bicep --parameters "@$approvedProfile" --validation-level Provider --query "{state:properties.provisioningState}" --output json --only-show-errors 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Provider validation failed; retain sanitized status only.' }
az deployment group what-if --subscription c81fda52-936e-4f14-8af4-951c0dbb92d2 --resource-group fotoa-demo-rg --template-file .\infra\modern-foundry-tracing.bicep --parameters "@$approvedProfile" --validation-level Provider --result-format ResourceIdOnly --no-pretty-print --query "{status:status,changes:changes[].{resourceId:resourceId,changeType:changeType}}" --output json --only-show-errors 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Scoped what-if failed; retain sanitized status only.' }
```

Accept only the intended connection Modify plus module scaffold for adoption,
or connection Create plus scaffold for a separately approved clean project.
Reject parent/network/auth/RBAC/vault/model drift. Then, and only after separate
deployment approval, perform clean connection deployment and identical
redeployment, repeat exact readback, and verify no duplication/removal/drift or
credential exposure. No create command here grants deployment approval.

For a future new delivery validation, Telemetry/operator must perform **one separately approved synthetic
Foundry UI-origin invocation**, record bounded UTC window and available
request/trace/correlation identifiers, then verify actual AppInsights/LAW rows.
Client exporter preflight, old model receipts and OTLP acknowledgments are not
substitutes. The forwarding path covers **AppRequests/AppDependencies** span
rows, **not AppEvents**; inspect actual table placement. Route any AppEvents or
other uncovered-table mapping/export dependency to Telemetry before claiming
end-to-end coverage. No invocation or new issue is created by this change.
Association metadata alone never proves Arize ingestion, full graph/ID/content
or prompt/completion/total token preservation.

The previously prepared native LAW export selected AppRequests/AppDependencies;
that broader export IaC remains held, not restored here. Baseline AppInsights
diagnostic settings are not a replacement for that route. Independently reconcile
the actual export configuration before claiming either table reaches Arize.

## Executed acceptance evidence (2026-10-16/17 UTC)

The receipts below remain the dated #139 record. Later #143 native content
transport and generated-fixture fallback acceptance is recorded separately in
the [durable runbook](durable-genai-correlation.md); it does not rewrite these
historical table/mapper observations or validate the fresh foundation.

Reviewed implementation source is `2fb796d66f75384cdd4858bbee985eee2081d539`.
This follow-up changes documentation only; deployed infrastructure source and
the independently reviewed 12-test/24-mutation contract remain unchanged.

### Existing-demo adoption and idempotence

The user-approved **native CLI** method completed Provider validation,
ResourceIdOnly what-if, one Incremental same-name adoption and one identical
redeployment. Deployments `issue139-2fb796d-20261016t2045z-7c81a2` and its
`-r2` both reached **Succeeded**. Each readback found the same single intended
ApiKey/private connection, `peRequirement=NotRequired`,
`peStatus=NotApplicable`. Safe account/project/component/vault controls matched.
Receipt: `.azure-sandbox\issue139-native-approved-2fb796d-20261016T2045.json`.
This was adoption, not clean creation. The generic unsigned-helper workflow
remains incomplete; no signing-policy bypass or generic Validated claim is made.

### Isolated clean creation and identical redeployment

The requester then explicitly approved one isolated project inside the existing
account, same component and pinned vault reference, with
**temporaryCleanup=false**. Exact retained IDs:

```text
Project:
/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-139test-eastus2
Connection:
/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-139test-eastus2/connections/fotoa-demo-appi-139test-eastus2
```

Collision-free preflight confirmed the project absent. Official project API
`2025-09-01` documents 2–64-character names and project tags. The initial
identity-omitted minimal shape passed Provider validation/what-if but reached
terminal **Failed/BadRequest**: this live provider requires project managed
identity. No project existed after that failure. A second distinct, revalidated
creation added **only the new project's required SystemAssigned identity**;
`issue139-clean-project-20261017-r1` succeeded. No role assignment, existing
identity/authentication-mode change, network change or model deployment occurred.
The operational project fixture is ignored, not shipped product infrastructure.
Required tags were applied to the project; the child API is untaggable.

The new project then had **zero AppInsights connections**. The strict validator
correctly exited 1 for the missing association; this expected pre-create result
was not misrepresented as post-deployment success. Reviewed Bicep built, Provider
validation passed, and ResourceIdOnly what-if reported **only the intended new
connection Create** (other existing resources Ignore). This format proves scope,
not a property-level diff. The profile used ApiKey/private, review=true,
NotRequired/NotApplicable, and the same approved ARM-only vault reference:
secret `appinsights-connection-string`, immutable version
`1ec98e6a56c34d569ccbee29e770e1c9`. No value was retrieved.

| Deployment | ARM timestamp UTC | Exact readback |
|---|---|---|
| `issue139-clean-2fb796d-20261017` | `2026-10-17T00:10:30.193876Z` | Succeeded |
| `issue139-clean-2fb796d-20261017-r2` | `2026-10-17T00:11:51.561700Z` | Succeeded |

Both used identical compiled source/profile and stable connection name; only
the outer deployment name differed. After **each**, the reviewed validator
passed, the inventory contained exactly one intended AppInsights connection,
and category/target/metadata/ApiKey/private/PE values matched with no duplicates.
Fresh safe controls for the working demo connection/project, parent,
component and vault equaled their preflight snapshots after project creation,
clean connection creation and redeployment. No model/UI call or teardown ran.

Immutable sanitized receipt (local/ignored):
`.azure-sandbox\issue139-clean-20261017.final.json`.
It retains exact native commands, IDs, timestamps, source/profile hashes and
project-only failure/recovery evidence. Profile SHA-256:
`1cfb5e3cf6af596387d96122c5a4d4452ac2e7cdcc7c0f422527d70e5d189315`.
Connection entrypoint/module SHA-256:
`e0f6362a1c30e91c74e655e93b88394363b299055bbbcfa9c4f4327cefa43e61` /
`af391c2647e0f5a8909a82c7e88208b73dfc7c37687f684c1367d437712a4272`.

**Ownership/retention:** Infra owns validation tracking for this isolated
project/connection; the requester explicitly chose retention. Leave both in
place. Any later removal needs separate explicit authorization and exact owned
resource reconciliation; never delete/repoint the working demo association or
shared component, LAW, vault, account or networking.

### Bounded UI-origin/source/export acceptance

[Telemetry signoff](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/139#issuecomment-6227001478)
accepts the Telemetry dependency and criteria 8/9 for the operator-attested
synthetic playground trace `a1322599fe5c4c5488bf2ed17f38cb54` only.
The requester reports Arize **Input**, explicitly **USER-OBSERVED**, not an
independent authenticated Arize UI/API inspection.

Independent QA content-free reconciliation found two `AppDependencies` rows,
UTC `2026-10-16T23:28:14.3953233Z`–`23:28:14.9962786Z`, inline input/output
lengths 832/276, parent/child `d4e79f0bee6dcc88` → `66e051be9a06a846`,
and child native input/output counts 131/49. No explicit correlation-ID
attribute or source total-token attribute was observed. The enabled LAW export
actually selects AppDependencies/AppRequests, covering these rows; configuration
alone does not prove per-event health. QA receipt:
`.azure-sandbox\qa-139-acceptance-20261016T2335.json`.

Upstream parent `a07a3da112f940d3` was absent at source, **not** proven lost by
export. Full Arize graph, Output/content fidelity and token parity remain
unverified. AppGenAIContent/AppEvents remain unforwarded/unjoined; no rows from
those other searched tables returned for this trace/window. That general
coverage gap remains Telemetry-owned follow-up before broader claims, not a
blocker for this observed inline-AppDependencies case. No new issue or invocation
was needed. The deployed mapper remains source `e2c557f`, deployment
`3f880a64-208b-498a-8f84-d6bbcd329ecb`, with eight-source parity and 157 recorded
passing relevant tests; this documentation does not alter that package.
