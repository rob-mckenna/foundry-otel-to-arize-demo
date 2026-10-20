# Issue 147 — fresh application on the supported existing network

**CURRENT-STATE STAGED IMPLEMENTATION / PARTIAL VALIDATION — 2026-10-20.
QA owns OPEN #147; PR #151 remains unmerged. Revised subscription provider
validate passed; revised ResourceIdOnly what-if exited 1 (diagnostic code not
captured safely). Analysis stopped, with no fallback. The derived projection is
33 Create / one unresolved dynamic role assignment, NOT a live what-if result.
No deployment, secret operation, publication, IAM
change, VM start or inference was executed. NOT officially Validated.**

Independent composition revision worker: `c0769ac8-18a5-4872-8916-8d5326dc0c14`.
Baseline: `db53b0ff37dc6fb7d03e63e832b227be3d05509c`.
Runtime identity mechanically asserted different from locked-out composition
author `47b39bff-7553-495e-a0da-117c5b757a62`; no advice, consultation or
coauthoring from that author. Parent re-review remains pending. Secure-bootstrap
author's accepted source and behavior are unchanged.
Exact later resource/role/action/cost handoff:
[first-allocation manifest](issue147-first-allocation-manifest.json).

## Decision and acceptance boundary

Use the **already implemented** `network.mode=existing`, existing PE/integration
subnets and all seven existing private DNS zones, with
`dnsLinksManagedExternally=true`. Create **new application identities/resources
in `fotoa-demo-rg147-eastus2`**, not another deployment over the existing demo.
This removes the previous unrelated-10.40-VNet publishing blocker without
peering, another VM, NAT, VPN, new subnet or network redesign.

ADR-0004 §2 explicitly permits “fresh network address ranges **or explicitly
provided existing PE/integration subnet IDs**” and existing DNS ownership.
#147 requires a separately approved fresh environment, not specifically an
all-new VNet. Thus a clearly labelled fresh-RG/**fresh-application/existing-
network** demonstration can exercise its supported composition and repeat/E2E
acceptance. This is **not standalone full-fresh-network validation**: fresh
VNet/subnet creation, seven zone/link creations and independent validator
connectivity remain unproven. QA must preserve that distinction in the eventual
acceptance record; this preparation closes neither #147 nor that additional
standalone-network proof.

Basic means private **client ingress**, with Microsoft-managed agent runtime
and state, not customer-VNet runtime isolation. No Search/Cosmos/direct-OTLP
expansion is selected. The old GlobalStandard/capacity-5 native evidence does
not validate the new DataZoneStandard/capacity-1 deployment.

## Exact nonsecret foundation profile

[`infra/main.issue147-existing-network.parameters.json`](../../infra/main.issue147-existing-network.parameters.json)
contains all required compiled ARM parameters and no unsupported fields or
placeholders. SHA-256:
`b6ce3d1140ce492a00681571db72cac4f0048da590d1f81bf22957d4e8ff4781`.
It is an offline-valid **staging** profile, not a live-ready tracing assertion.

- Subscription `c81fda52-936e-4f14-8af4-951c0dbb92d2`, `eastus2`, token `fotoa147`.
- Account/subdomain `fotoa147-demo-foundry-eastus2`;
  project `fotoa147-demo-fproj-eastus2`; model alias `qa147-synthetic`.
- `OpenAI / gpt-5-mini / 2025-08-07 / DataZoneStandard / 1 / NoAutoUpgrade`.
- EP1 capacity/minimum/maximum/prewarmed target **1**, Python 3.11.
- Deterministic new connection name **`fotoa147-demo-appi-eastus2`** (26 characters);
  not another naming approval gate.
- Owner/cost-center tags `infra-team` / `demo-engineering` retain the sanitized
  prior-profile provenance; not invented personal identities.
- 24-hour validation window from later allocation; existing retained-state
  review obligations and no automatic destructive teardown remain unchanged.
- Incoming and outbox consumers remain **disabled**.

### Exact network identities and address budget

All IDs below use the subscription above and
`/resourceGroups/fotoa-demo-rg/providers/Microsoft.Network/`.
The profile contains their **full ARM IDs**, not these abbreviated descriptions.

| Resource | Observed GET result |
|---|---|
| `virtualNetworks/fotoa-demo-vnet-eastus2` | East US 2, `10.20.0.0/24`, Azure-provided DNS (custom servers null), no peerings |
| `.../subnets/private-endpoints` | `10.20.0.0/26`, 59 usable addresses, **12 IP configurations**, 7 existing PEs, no delegation; PE network policies Disabled |
| New application's 4 PEs | Foundry account **3 IPs** (`default`, `secondary`, `third` required members), Blob/Queue/Table 3: **6 expected new IP slots**, no new vault PE |
| PE headroom snapshot | **47 remaining** from 59−12; 6 new slots leave **41**. Prior metadata snapshot, not an allocation reservation; recheck before execution |
| `.../subnets/function-integration` | `10.20.0.128/26`, delegated `Microsoft.Web/serverFarms`, existing `AppServiceLink` to `fotoa-demo-plan-eastus2` |
| Existing plan | Same subscription/region, Linux ElasticPremium EP1, 1 site/worker, plan maximumElasticWorkerCount **1** |
| New plan | Distinct fresh-RG EP1, 1 worker; budget at least **2 IPs** for temporary replacement, not a transient instance/billing guarantee |
| Integration availability | GET `check-ip-address` returned **available=true for 10.20.0.133 and 10.20.0.134**; enough for that 2-slot budget at the snapshot, not reserved/static assignments |

The integration subnet's `ipConfigurations` is null: App Service virtual
interfaces are not customer NIC resources. Do **not** call that 59 free addresses
or infer exact total free count. No demonstrated subnet-capacity blocker exists.
If the provider reports different PE member counts or exhausted addresses,
stop and reconcile the actual deficit; do not widen the subnet implicitly.

Cross-RG is not cross-VNet: both subnets and the validator remain in the same
existing VNet. App Service's official MPSJ contract permits multiple plans in
one subnet with **/26 minimum** and same-subscription plans; different resource
groups are not prohibited. This profile satisfies those metadata constraints.
The Functions networking article also retains a conflicting older sentence
that different plans cannot share a subnet, despite its earlier multiple-plan
statement. **Exact EP1 MPSJ admission is therefore an explicit provider
validation/deployment gate**, not something established by source compilation,
a reason to mutate the existing plan, or authority to add a subnet.

### DNS, route and outbound facts versus runtime proof

All seven existing zones are present:
`privatelink.cognitiveservices.azure.com`, `privatelink.openai.azure.com`,
`privatelink.services.ai.azure.com`, `privatelink.vaultcore.azure.net`,
`privatelink.blob.core.windows.net`, `privatelink.queue.core.windows.net`,
`privatelink.table.core.windows.net`.
Their existing VNet links to **fotoa-demo-vnet-eastus2** are
**Completed/Succeeded**, registration disabled. The vault zone's second dev
link is preserved. New application record names differ from existing services.

Both PE/integration subnets have **no route table** and **no custom NSG rules**;
standard NSG defaults allow VNet and Internet outbound. Integration has no NAT
gateway. The fresh Function sets `vnetRouteAllEnabled=true`; the old Function's
false setting is not proof of the fresh Function's egress.
These are configuration facts, **not an effective-route or successful outbound
probe**. No metadata result establishes Arize HTTPS/SNAT availability, extension
bundle download, Entra/Monitor/Event Hub connectivity or private runtime success.
No NAT/firewall/public-access changes are authorized to “fix” an untested path.

Later leased runtime proof must resolve the fresh Foundry, existing custody vault and
Blob/Queue/Table names to the intended PEs; complete TLS 443 and MI operations
from the existing validator and fresh Function; verify Function host/package
startup, extension-bundle access, KV reference **status only**, Event Hub
connectivity, Monitor service ingestion/export and approved Arize egress without
printing bodies/settings/secret values. Native trace proof is separate.

The validator is the **existing** `fotoa-validation-vm-eastus2`,
`10.20.0.196`, MI principal `64c0b8ce-7e6c-4875-a2cb-82552efc0376`,
in `validation-jumpbox` on this VNet. A new 10.40 path is irrelevant to this
profile. No VM start or guest operation occurred here.

## Implemented destination/reference custody and later RBAC

`main.bicep` now forwards typed `keyVaultReferences` to the Function:

- `mode=freshVault` preserves existing source behavior and local-vault grants.
- `mode=existing` constructs App Service `@Microsoft.KeyVault(SecretUri=...)`
  settings from **four URI identifiers**, and suppresses the unused fresh-vault
  reader assignment, owned vault deployment and vault PE/zone-group.
  No values are copied; no external vault/secret/IAM write occurs in fresh main.
  The separate secure bootstrap still writes only the required NEW routing
  secret in the existing custody vault; it does not need an unused fresh vault.
- `keyVaultName` and `keyVaultResourceId` outputs are nullable owned-resource
  metadata: **null** in existing mode, unchanged name/ID in default freshVault.
  `keyVaultReferenceMode` makes selection explicit; `externalKeyVaultReferences`
  returns URI identifiers only in existing mode (otherwise null). The Function's
  owned `keyVaultName` parameter is nullable and receives null only for existing
  mode. No invented owned name, implicit external-vault PUT or grant widening.

Default freshVault still creates its vault, vault PE and local reader and
expects five PEs / seven IP slots. Existing-network/seven-zone input compatibility
and externally owned vault DNS links are unchanged. Existing mode uses four
PE-zone-group pairs and six zones for new records; the supplied vault zone/link
continues serving the existing custody vault. Provider actual IP allocation
and private DNS resolution remain runtime gates.

The offline validator rejects missing fields, non-vault hosts, non-HTTPS URIs,
query/fragment injection, malformed versions and duplicate references.
Runtime URIs may be versionless for normal Key Vault rotation; that does
**not** relax the separate immutable ARM tracing parameter rule.

This profile reuses **existing** custody:

| Setting | Exact URI identifier |
|---|---|
| `ARIZE_OTLP_ENDPOINT` | `https://fotoa-demo-kv-eastus2.vault.azure.net/secrets/arize-otlp-endpoint/` |
| `ARIZE_SPACE_ID` | `https://fotoa-demo-kv-eastus2.vault.azure.net/secrets/arize-space-id/` |
| `ARIZE_API_KEY` | `https://fotoa-demo-kv-eastus2.vault.azure.net/secrets/arize-api-key/` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | `https://fotoa-demo-kv-eastus2.vault.azure.net/secrets/fotoa147-appinsights-connection-string/` (**new secret, not yet created**) |

Only the vault host and approved secret names were used; no secret/settings
read or copy occurred. The first three names are existing sanitized custody
evidence, **not new Function resolution proof**. Destination metadata remains
`fotoa-vm-diagnostic`; durable destination/workspace binding is a later cutover
gate, not configured merely by `arizeProjectName`.

The **new** Function principal will be provider-generated. Existing Function/
runner grants do not cover it. The separately invokable
[`infra/existing-function-secret-access.bicep`](../../infra/existing-function-secret-access.bicep)
records the exact future least-privilege mechanism:
**Key Vault Secrets User `4633458b-17de-408a-b874-0445c86b69e6`**, four individual
secret scopes under
`/subscriptions/c81fda52-936e-4f14-8af4-951c0dbb92d2/resourceGroups/fotoa-demo-rg/providers/Microsoft.KeyVault/vaults/fotoa-demo-kv-eastus2/secrets/`,
names exactly those four table entries; grantee is the actual fresh
`fotoa147-demo-func-eastus2` system principal. No vault-wide Officer/Admin,
project reader or guessed human principal. This template is **not called by
main** and must not be deployed without a separate exact IAM lease.

The existing runner MI later needs **Storage Blob Data Contributor
`ba92f5b4-2d11-453d-a403-e96b0029c9fe`** at the **new `function-packages`
container only**, and separately scoped Foundry User
`53ca6127-db72-4b80-b1b0-d745d6d5456d` on the **fresh project** for approved
agent publication/readback/invocation. No such grants were made or assumed.
The Function's own host-storage/receiver roles remain source-controlled as
before; the publisher grant is not a Function grant.

## Fresh tracing bootstrap — supported server-side automation, staged

**A secret URI cannot be used as the native project's tracing credential.**
`modern-foundry-app-insights.bicep` supplies the component's actual connection
string as ApiKey `credentials.key`, with secure parameters across boundaries.
It does not interpret a URI or the App Service `@Microsoft.KeyVault` syntax.
Putting a URI in that key would not bind the new component correctly.

Actual `azure-ai-projects==2.0.0` source was inspected at immutable SDK commit
`3c342025b7088315522ce1e4d0b5973dd9253232`,
`operations/_patch_telemetry.py`: its telemetry helper calls
`connections._get_with_credentials`, requires `ApiKeyCredentials`, and returns
the literal string; non-ApiKey credentials raise `ValueError`.
**That helper was not invoked.** It is neither keyless bootstrap nor a safe
metadata lookup. `prompt_agent/telemetry.py` similarly supplies the environment
string to `AzureMonitorTraceExporter`, not a vault-URI resolver. Native
service-side tracing and optional client-exporter tracing must not be conflated.
No new application code or Function package rebuild is needed.

The earlier human-custody prerequisite is **superseded by implemented ARM
automation**, not by a secret extraction command:

1. `infra/issue147-first-allocation.bicep` is a subscription wrapper creating
   exactly `fotoa-demo-rg147-eastus2` plus the existing-network foundation.
   It embeds the unchanged nonsecret profile above; it takes no parameters.
2. Only after foundation completion, `issue147-app-insights-bootstrap.bicep`
   references **new** `fotoa147-demo-appi-eastus2` using API `2020-02-02`.
   ARM evaluates `reference(...).ConnectionString` server-side.
3. Its cross-RG module passes that expression directly into **securestring**
   `connectionString` on `modules/app-insights-secret.bicep`. The only writable
   resource in that module is API `2023-07-01`
   `fotoa-demo-kv-eastus2/fotoa147-appinsights-connection-string`.
   No plaintext credential enters an output, profile, command or caller file.
4. Only `secretVersionUri` (the provider's immutable `secretUriWithVersion`)
   and `componentBindingResourceId` are returned. These are identifiers,
   not values. The secret's tags bind its source component and required tags.

The actual pinned public provider schema supports this ordinary ARM operation.
Azure/azure-rest-api-specs commit
`9584a076a20d33bf725cf5fe0cf2595b1cc9aab1`:

- [Key Vault secrets 2023-07-01](https://github.com/Azure/azure-rest-api-specs/blob/9584a076a20d33bf725cf5fe0cf2595b1cc9aab1/specification/keyvault/resource-manager/Microsoft.KeyVault/KeyVault/stable/2023-07-01/secrets.json),
  SHA256 `54450876376678f28ee0c305bbd6c8700aa551263a9c5437ba8263cf768ee1b5`:
  `Secrets_CreateOrUpdate` is ARM PUT; `SecretProperties.value` is intended for
  ARM deployments and **never returned** by this management API.
  `secretUriWithVersion` is a read-only identifier.
- [App Insights components 2020-02-02](https://github.com/Azure/azure-rest-api-specs/blob/9584a076a20d33bf725cf5fe0cf2595b1cc9aab1/specification/applicationinsights/resource-manager/Microsoft.Insights/ApplicationInsights/stable/2020-02-02/components_API.json),
  SHA256 `2eee98c98f6f31615568e516d0d2c70b7843b86a48d704a50947a3569b63dc83`:
  `ConnectionString` is a read-only component property.

Fresh metadata GET confirmed existing vault RBAC=true, PNA=Disabled,
enabledForTemplateDeployment=true, ACL default Deny / bypass AzureServices.
No vault policy/network/role change is needed by this staged control-plane
secret-resource contract. The deployment executor needs the precise
`Microsoft.KeyVault/vaults/secrets/write` action on the new secret and nested
deployment permissions in its existing RG, **not a new broad vault data role**.
Actual successful provisioning/private resolution remains unexecuted; metadata
and provider analysis do not certify runtime access.

This wrapper is **first-allocation only**, not a repeat-deployment command:
ARM CreateOrUpdate can rotate an existing name. The later executor must bind
source/profile/compiled/manifest hashes and verify the exact new RG/component/
secret are absent through metadata-only admission; stop on an existing,
ambiguous or non-Create secret result. Do not retry ambiguous execution or
overwrite the secret. Subsequent foundation repeat proof uses `main.bicep`
without the bootstrap writer. No old Arize GET/list/copy, VM SDK bootstrap,
custom transport, authentication code or additional service is required.

After that later leased automation, the **narrow** tracing entrypoint (not a repeat of broad
main with invented material) receives `tracingAssociationMode=ApiKey`,
reviewed private sharing / `NotRequired` / `NotApplicable`, name
`fotoa147-demo-appi-eastus2`, and a secure ARM parameter `reference` with:
vault ID above, secretName `fotoa147-appinsights-connection-string`,
**actual returned immutable secretVersion**. The operator needs scoped
project connection read/write and vault `deploy/action`; actual private
template resolution must pass. Existing vault metadata says template deployment
enabled, RBAC true, PNA Disabled; it is not a new resolution success.
No project secret-reader role, plaintext profile, `listSecrets`, component
connection-string extraction command or metadata-leaking MI migration is used.
This checkpoint does **not** invent a version or create that association.

The committed foundation profile deliberately remains `preserveExisting`
(no association PUT). It is **complete for staging**, not a pretend complete
active-tracing profile. The Function's new runtime reference is unresolved
until that custody operation and the later fresh-principal role assignments.

### Actual safe provider analysis and reproduction

From TEAM_ROOT; all Azure CLI processes set repository-local config and the
explicit subscription. Output files contain compiled expressions or projected
identifiers only. Local compilation used Bicep **0.47.16.16243**.

```powershell
.\.azure-config\bin\bicep.exe build .worktrees\issue147-readiness\infra\issue147-first-allocation.bicep --outfile .worktrees\issue147-readiness\.azure\issue147-first-allocation.compiled.json
.\.azure-config\bin\bicep.exe build .worktrees\issue147-readiness\infra\issue147-app-insights-bootstrap.bicep --outfile .worktrees\issue147-readiness\.azure\issue147-app-insights-bootstrap.compiled.json
$env:AZURE_CONFIG_DIR = 'C:\repos\foundry-otel-to-arize-demo\.azure-config'
$env:AZURE_LOGGING_ENABLE_LOG_FILE = 'false'
$env:AZURE_CORE_COLLECT_TELEMETRY = 'no'
# These two commands were run with stdout/stderr captured in process memory:
# only the --query projection was persisted; raw failures would emit codes only.
az deployment sub validate --location eastus2 --name issue147-first-allocation-analysis --template-file .worktrees\issue147-readiness\.azure\issue147-first-allocation.compiled.json --subscription c81fda52-936e-4f14-8af4-951c0dbb92d2 --only-show-errors -o json --validation-level Provider --query '{id:id,errorCode:error.code,errorCodes:error.details[].code}'
az deployment sub what-if --location eastus2 --name issue147-first-allocation-analysis --template-file .worktrees\issue147-readiness\.azure\issue147-first-allocation.compiled.json --subscription c81fda52-936e-4f14-8af4-951c0dbb92d2 --only-show-errors -o json --validation-level Provider --query '{status:status,changes:changes[].{resourceId:resourceId,changeType:changeType},errorCode:error.code}' --result-format ResourceIdOnly --no-pretty-print --no-prompt
```

- Both builds **PASS, no warnings**.
- CLI **2.91.0**, selected subscription Enabled; fresh RG metadata **false**.
- Historical pre-revision validate **exit 0**, 2026-10-20 **08:09:20Z** start.
- Historical pre-revision what-if **exit 0 / Succeeded**, **08:09:28Z** start; **36 Create,
  0 Modify, 0 Delete, 1 Unsupported**. The secret is specifically **Create**.
- The Unsupported item is the already-source-defined container-local durable
  index role assignment: its deterministic GUID incorporates the **future
  Function principal ID**, which what-if cannot resolve. It is **not** a
  rejected secure-bootstrap schema or an observed authorization/network error.
  Do not call that assignment validated or guess a principal to remove the gap.
- Revised Provider validate **exit 0**, **08:25:18Z** start, error null.
- Revised ResourceIdOnly what-if **exit 1**, **08:25:29Z** start. The safe
  capture yielded no parenthesized error code and deliberately persisted no raw
  failure. Exact provider diagnostic is therefore **unknown**, not an empty
  successful result or a proven permission denial. Analysis stopped; no retry,
  fallback, further provider query or mutation. Diagnosis requires a separately
  authorized safe error-code capture; official workflow remains incomplete.
- **Derived, not live proof:** 36 prior Creates minus owned vault, vault PE and
  vault zone-group = **33 projected Creates**, retaining the NEW external secret
  and the unresolved future-principal index assignment. New graph has four
  PE/zone-group pairs. No predicted VNet/subnet/zone/link resource PUT; new DNS
  record registration and separately leased secret-scoped IAM remain required.
- Admission analysis is **not allocation proof** of EP1 MPSJ, capacity-1 model,
  network egress, secret provisioning or private resolution. No execution
  occurred and no permission/provider/network failure was bypassed.

Historical receipts: worktree `.azure/bootstrap-provider-{validate,what-if}.json`.
Revised receipts: `.azure/composition-provider-{validate,what-if}.json`,
hashes and source/compiled bindings in the manifest. No full what-if properties
were emitted or saved. The manifest distinguishes exact Windows-checkout
CRLF source hashes from independently verified canonical LF Git blob hashes;
compiled/package/receipt hashes remain exact bytes. A later executor must
verify the applicable exact binding, never relax a hash guard on a mismatch.
The official pinned workflow was started through
**AddValidationSteps only**; its unadapted helper prints raw failures and omits
explicit subscription on two CLI commands, so it was not run. The safe
subscription commands above are **partial gate evidence**, not official
workflow completion. Plan status remains **Approved PREPARATION / partial
validation**, never Validated. No new helper/workflow was introduced.

## Immutable package and publication proof binding

Reuse, do not rebuild:
`telemetry-936946c8-b6ffdb3739e261f612a5b1f568f509365da88094a175a3efabc6aaf9c4f2b9ff.zip`,
**8,472,610 bytes**, SHA-256
`b6ffdb3739e261f612a5b1f568f509365da88094a175a3efabc6aaf9c4f2b9ff`.
The prior handoff's exact artifact was hashed again and matched.
No Function application source changed.

Destination:
`https://fotoa147demosteastus2.blob.core.windows.net/function-packages/telemetry-936946c8-b6ffdb3739e261f612a5b1f568f509365da88094a175a3efabc6aaf9c4f2b9ff.zip`.
Function fetch uses its **system-assigned MI** and
`WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID=SystemAssigned`.
No SAS, shared keys, public SCM or basic credentials; this graph has no SCM PE.

Later publication custody must bind **this profile hash**, ZIP hash/size, the
exact VM ARM ID/principal above, source HEAD, container-scoped publisher grant,
new Function principal and private DNS/TLS results in one lease/receipt.
After authorized secure staging of the same artifact/profile on that runner,
the exact Python publication/proof body is:

```python
# NOT RUN. Later private-runner/publication lease only; files colocated.
import hashlib
import json
from pathlib import Path
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobClient

profile = Path("main.issue147-existing-network.parameters.json")
assert hashlib.sha256(profile.read_bytes()).hexdigest() == "b6ce3d1140ce492a00681571db72cac4f0048da590d1f81bf22957d4e8ff4781"
p = json.loads(profile.read_text())["parameters"]
package = Path(p["functionPackageBlobName"]["value"])
digest = hashlib.sha256(package.read_bytes()).hexdigest()
assert digest == "b6ffdb3739e261f612a5b1f568f509365da88094a175a3efabc6aaf9c4f2b9ff"
assert package.stat().st_size == 8472610
url = "https://fotoa147demosteastus2.blob.core.windows.net/function-packages/" + package.name
with ManagedIdentityCredential() as credential, BlobClient.from_blob_url(url, credential=credential) as blob:
    with package.open("rb") as content:
        blob.upload_blob(content, overwrite=False, metadata={"sha256": digest})
    properties = blob.get_blob_properties()
    assert properties.size == 8472610
    assert properties.metadata["sha256"] == digest
    downloaded_digest = hashlib.sha256()
    for chunk in blob.download_blob().chunks():
        downloaded_digest.update(chunk)
    assert downloaded_digest.hexdigest() == digest
    print(json.dumps({"bytes": properties.size, "sha256": digest,
                      "etag": properties.etag, "privatePublicationVerified": True}))
```

Only execute on the lease-bound VM/system MI after independently checking
that ARM identity and private DNS/TLS, never on an unbound host with a default
credential chain. On an existing blob or ambiguous upload response: **stop,
do not overwrite/retry**; reconcile its properties and streamed hash read-only
under the same lease. Later ARM trigger sync, host readiness, synthetic
invocation and consumer enablement are **separate** approvals.

## Compiled proof, tests and evidence

Run from the issue worktree with repository-local `BICEP_CLI` set:

| Executed command | Result |
|---|---|
| `bicep.exe build infra\main.bicep --outfile .azure\main-existing-network.compiled.json` | PASS, no warnings |
| `bicep.exe build infra\existing-function-secret-access.bicep --outfile .azure\existing-function-secret-access.compiled.json` | PASS, no warnings |
| `python -B infra\scripts\validate-modern-foundation.py --parameters infra\main.issue147-existing-network.parameters.json` | PASS: offlineProfileValid true; tracingPutRequested/providerValidated/privateRuntimeVerified/consumerEnabled false |
| `python -B -m unittest discover -s infra\scripts -p 'test_modern*.py' -q` | PASS, 34 tests; includes both selected compiled vault graphs |
| `.\infra\scripts\validate-naming.ps1` | PASS, 9 modules |
| `python -B -m unittest discover -s tests\readiness -p 'test_issue147_planning.py' -q` | PASS, 6 tests, including selected-route inventory/cost/hash consistency |
| `.\tests\readiness\check-issue147-docs.ps1` | PASS, 18 documentation examples and 2 pinned scripts parse; none executed |
| `$env:PYTHONPATH="$PWD\src\telemetry-pipeline"; python -B -m pytest -q -p no:cacheprovider tests\telemetry-mapping tests\export` | PASS, 108 synthetic mapping/export tests |
| `git diff --check` | PASS |

Compiled ARM uses `equals(network.mode,'fresh')` on VNet and `fresh` on
zones/links, where `fresh` is that same equality: **all false for the committed
existing profile**. There is no standalone subnet resource elsewhere in the
compiled graph. New PE/zone-group PUTs are expected; externally owned VNet,
subnet, zone and link PUTs are not. Automatic DNS **record registration** through
new PE zone groups is not a zone-resource PUT and remains the explicit
private-endpoint integration path.

New tests cover the real profile's required/unsupported-parameter completeness,
false external-network PUT conditions, URI forwarding without external grants,
secret-scoped access inventory, and malformed/injected/missing URI rejection.
The existing fresh-vault and tracing tests continue to pass. Telemetry transform
code/package is unchanged; previous mapping/export results are not relabelled
as new runtime proof.

Ignored worktree-local metadata receipts:
`.azure\existing-network-evidence` (collector:
`.azure\collect-existing-network.py`). Every Azure CLI invocation used repository
`AZURE_CONFIG_DIR` and explicit subscription, metadata GET only.
The initial Python `az` executable lookup failure and a quoted `az.cmd` URL
ampersand parsing failure were corrected with executable resolution and the
supported `vnet check-ip-address` command; neither performed a mutation.
Authenticated GitHub SDK-reference discovery returned SAML 403; the same
public source was obtained unauthenticated over normal TLS, without auth changes.

Necessary public sources retained locally:

- App Service VNet integration, official documentation source revision
  `19f0e4da74ed7135a920fea16f2764fd1305bf71`, retained HTML SHA-256
  `c5d68c9a03f9588834f9ad6e4226bd8efc1c23d97e241e0eb06c0d88073574b8`.
- Functions networking, official source revision
  `f4f548f0cdac257f2f558aa079dedace3b6590ca`, retained HTML SHA-256
  `243ae2c00a7c5b2315be4413d5135b9d64ddad8a44a59bf3e4ca9d8740bff654`.
- SDK telemetry source pinned above, SHA-256
  `3e58ff9b3a2a7af9676cb0ec283b9be6e29d55712f153eccdd57552ff5a51888`.

Top-level `azure-prepare` was invoked normally. Only its **repo-contained,
pinned official equivalent** references were read, as described in
[workflow gates](issue147-workflow-gates.md); no installed profile references
were accessed. The worktree-local plan was updated before source edits.
That earlier preparation remained **Planning**. The implementation continuation
above stages secure bootstrap and records successful provider validate/what-if,
but **not officially Validated**: actual MPSJ/model-capacity allocation, effective
runtime networking, secure provisioning, official workflow completion, scoped
later leases, repeat and E2E remain unexecuted.
No closed root plan, receipt, old execution ledger or #148 proposal was changed.
