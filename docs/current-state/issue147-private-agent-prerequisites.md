# #147: no-tool Prompt Agent private-runtime prerequisites

**Technical disposition: NOT READY FOR APPROVAL / live acceptance.**
Discovery date: **2026-10-20 UTC (2026-10-19 Eastern)**. Working as Agent,
supporting acceptance owner **QA (`squad:qa`)**. #147 stays open.
This is a prerequisite assessment, not a deployment authorization, architecture
change, live test, or claim that the fresh environment exists.

Read alongside [the fresh-foundation acceptance packet](fresh-foundation-acceptance.md)
and [ADR-0004](../adr/0004-modern-only-foundry-foundation-and-cleanup-boundaries.md).
No owner approval can substitute for the missing technical/provider evidence below.

## 1. Resolved contract and recommendation

The existing agent is a **new Foundry Prompt Agent**, not a classic Assistants
agent and not a hosted container agent:

| Boundary | Exact supported contract / evidence |
|---|---|
| ARM foundation | `Microsoft.CognitiveServices/accounts`, `/projects`, `/deployments`, pinned **2025-09-01** by ADR-0004 and the shipped modules. ARM version is not the agent data-plane version. |
| Project endpoint | `https://<approved-account-subdomain>.services.ai.azure.com/api/projects/<approved-project-name>`; existing endpoint uses `fotoa-demo-foundry-eastus2` / `fotoa-demo-fproj-eastus2`. An account OpenAI endpoint or an ML discovery URL is not interchangeable. |
| Agent definitions | `AIProjectClient(..., api_version="v1").agents.get_version(agent_name=..., agent_version=...)`; HTTP **GET** `<project-endpoint>/agents/<name>/versions/<version>?api-version=v1`. Returns **`AgentVersionDetails`**, whose `definition` is **`PromptAgentDefinition`** (`kind="prompt"`). [S1] |
| Python packages | Historical live runner pins **`azure-ai-projects==2.0.0`**, **`azure-identity==1.26.0`**, **`openai==2.26.0`**. These are reproducibility pins, not a claim that a newly installed or latest SDK was tested. Source commits are in §7. No package was installed for this assessment. |
| Model reference | `PromptAgentDefinition.model` is the **deployment alias**, not `gpt-5-mini` or an ARM model ID. Existing alias: `fotoa-demo-gpt5mini-eastus2`. `Reasoning(effort="minimal")` is typed configuration in existing v1; no temperature/top-p or tools were present in the reconciled definition. [E1] |
| No tools | Existing v1 metadata GET reports `kind=prompt`, `tool_count=0`, PASS. Fresh publication must separately prove an empty/absent tool list and the exact approved model alias/definition hash. Zero tools does **not** mean zero persisted service state. [E2, S3] |
| Invocation transport | **HTTPS OpenAI-compatible Responses**, synchronous non-streaming POST `<project-endpoint>/openai/v1/responses`. `project.get_openai_client()` supplies `openai.OpenAI`; call `responses.create(input=..., max_output_tokens=..., extra_body={"agent_reference":{"type":"agent_reference","name":...,"version":...}})`. `agent_reference` is an Azure schema extension passed as an OpenAI `extra_body` dictionary, not an invented Python `AgentReference` import. [S1, S2] |
| Authentication | Entra bearer credential scope **`https://ai.azure.com/.default`**. Historical private runner uses **`ManagedIdentityCredential`**, not key auth, CLI auth, dotenv or a connection string. `get_openai_client()` obtains the bearer provider internally. Do not print/read tokens. [S1, E2] |
| Not the selected protocol | Classic `azure-ai-agents` threads/messages/runs, Assistants IDs, account-level chat completions, hosted `/invoke`, WebSockets, A2A, sessions or a local CLI stub are not substitutes for this versioned Prompt Agent contract. The existence of other transports does not establish their acceptance here. |

**Recommendation:** retain this API/SDK/no-tool contract. This is **not** a
recommendation or approval to switch #147's privacy target to Basic. Lead/Infra
must resolve the exact fresh privacy/state contract before owner approval.
The present source can
support a **Basic setup with private inbound account access**, with
Microsoft-managed agent state. Official documentation expressly permits that
combination [S3]. It is **not** Standard private runtime/BYO state or guaranteed
private outbound service execution.

If #147 requires fully isolated outbound runtime and customer-owned state,
the current foundation is **technically incomplete**. Standard requires BYO
Storage **and Search and Cosmos DB**, capability provisioning, agent-subnet
injection, resource PEs/DNS and distinct permissions [S4, S5]. None may be silently
added, omitted because tools are empty, or inferred from the account PE.
Resolve that scope through Lead/Infra and an explicit accepted change before
cost/custody approval. This assessment authorizes no expansion.

Even for Basic/private-inbound acceptance, **capacity 1 provider acceptance,
fresh agent publication/readback, private validator identity/DNS and an immutable
live runner remain gates**. The repository `StubFoundryModelClient` stays offline
even when endpoint configuration exists; its estimated tokens are not live usage.

## 2. State and network support matrix

“New” and “Classic” below describe service generations, not v1 versus v2 agent
version numbers. Existing agent **version `"1"`** is a new-runtime version.

| Property | Basic + private inbound | Standard, public network | Standard + private outbound | Existing v1 / fresh source |
|---|---|---|---|---|
| State ownership | Microsoft-managed, logically isolated storage; not “stateless” | Customer-managed single-tenant stores | Same BYO stores, privately reachable | Existing runtime works historically; current metadata is consistent with Basic, not a certification of internal state placement. Fresh source has no BYO agent-state configuration. |
| Storage / Search / Cosmos | No BYO state trio prerequisite for Basic | **All three required** | **All three required**, even for the no-tool scope; no documented no-tool waiver | Function host storage and durable correlation storage are not evidence of an Agent Service state connection. Do not reuse them by assumption. |
| New-runtime Cosmos data | Platform-managed | `agent-definitions-v1`, `run-state-v1` | Same new-runtime containers | Do not query their contents, create them by hand or adopt/delete historical state. |
| Classic Cosmos data | Not this API contract | `thread-message-store`, `system-thread-message-store`, `agent-entity-store` | Same classic stores | Classic workspace retirement does not migrate new runtime state. |
| Account PE/PNA Disabled | Supported for inbound access | May also secure inbound | Required inbound protection, **not sufficient** for outbound | Existing account PNA Disabled, local auth disabled, ACL Deny/bypass None; fresh module declares those controls. |
| Service-side VNet injection | Not supplied by Basic inbound PE | Not private outbound | Dedicated agent subnet, capability configuration and dependency PEs/DNS required | No injection returned at 2025-09-01; capability-host lists empty at account and project in this read. Fresh composition does not provision this path. |
| Model/private runtime proof | Published model and successful private request still needed | Same | Same plus private state/runtime proof | Historical v1 acceptance is not a fresh foundation result or a promise of future availability. |

**Documentation inconsistency requiring provider reconciliation if Standard is
chosen:** [S4] says a minimum account throughput limit of 3000 RU/s, lists five
containers at 1000 RU/s each, distinguishes two new-runtime containers from three
classic ones, and retains older three-container isolation/troubleshooting prose.
It also says both serverless and provisioned modes are supported. Do not invent
a two-container/2000, three-container/3000 or five-container/5000 costing default.
Infra must obtain the exact provisioning mode, resource throughput constraints,
container set and project scaling requirement for the selected API/runtime from
the supported provider/template contract. No state data inspection is necessary.

The current network how-to [S5] introduces **capability settings at
`2026-07-15-preview`**, but also describes legacy capability-host provisioning.
New settings use the **caller identity** for provisioning; portal/legacy hosts
use the **project MI**. This is not permission to replace ADR-0004's
**2025-09-01** pin. A new API, immutable capability-settings connection or
delete/recreate project flow is a separately reviewed migration, not an
idempotent patch to the existing project.

For Standard/private: the documented agent subnet is dedicated to one Foundry
resource, delegated to **`Microsoft.App/environments`**, same region as Foundry,
minimum **/27**, recommended **/24** [S5]. It is not the Function
`Microsoft.Web/serverFarms` integration subnet or the PE subnet.
PEs to Storage/Search/Cosmos are not automatically created by adding a Foundry
PE. Latest networking pages differ on CGNAT support; use a reviewed RFC1918
address plan, not an inferred CGNAT exception. No subnet or network change was made.

**Runtime worker ID:** not exposed by inspected metadata. This is a Prompt
Agent, not a hosted agent; [S6] specifically shows no Micro VM on the prompt
path. An existing VM client, managed-identity principal, Azure Run Command
resource ID, request ID or agent version is **not** a Foundry runtime worker ID.
No worker ID is invented here.

## 3. Model tuple: what is proven and what is not

Proposed fresh tuple:
**OpenAI / gpt-5-mini / 2025-08-07 / eastus2 / DataZoneStandard /
capacity 1 / NoAutoUpgrade**.

Read-only regional metadata was fetched under the specified subscription and
repo-local Azure configuration. The response has both `OpenAI` and `AIServices`
entries; use the **AIServices** entry for this foundation.

| Question | Finding | Acceptance consequence |
|---|---|---|
| Correct model/version/region? | East US 2 catalog advertises `OpenAI`, `gpt-5-mini`, `2025-08-07`, `GenerallyAvailable`. [E4] [S7] lists East US 2 support for Responses, agents and private VNet. | Metadata support, not a deployment reservation. |
| Agent/API capability? | AIServices model capabilities: **`agentsV2="true"`, `responses="true"`, `assistants="true"`, `chatCompletion="true"`, `area="US"`**. Official model page [S8] lists GPT-5-mini 2025-08-07 and Responses/reasoning support. | Supports selecting the modern Prompt Agent/Responses family. Do not conflate `assistants` capability with the selected API. |
| DataZoneStandard available? | Advertised on AIServices for this model/version in eastus2; `usageName=OpenAI.DataZoneStandard.gpt-5-mini`. | SKU is supported in catalog, subject to provider validation/availability. |
| **Minimum capacity / step?** | DataZoneStandard capacity **`minimum=null`, `step=null`, `allowedValues=null`, `default=10`, `maximum=1000000`**. GlobalStandard also has a null minimum/step. Provisioned SKUs have explicit different minima and are irrelevant to this proposal. | **Capacity 1 remains UNPROVEN.** Null is not 1 or zero; default 10 is not a minimum. Do not borrow PTU minima, multiply quota into a claimed reservation, or replace the tuple with 10 automatically. |
| Quota? | At discovery: **DataZoneStandard 0/300 Count**; **GlobalStandard 605/1000 Count**. [E4] | Headroom is not allocated capacity, eligibility, a successful provider validation or a runtime SLA. No quota changes. |
| Existing working model? | Existing deployment GET: `fotoa-demo-gpt5mini-eastus2`, same model/version, **GlobalStandard capacity 5**, **NoAutoUpgrade**, Succeeded. Historical v1 binds this alias. [E1, E3, E4] | Existing capacity 5/GlobalStandard success does **not** validate fresh capacity 1/DataZoneStandard. Preserve the live tuple. |
| Upgrade/residency? | Existing `NoAutoUpgrade` is real metadata; fresh source accepts the explicit property. [S9] defines DataZoneStandard processing within the specified zone, here US, **not eastus2-only**. | Need fresh provider acceptance of the full tuple. NoAutoUpgrade is not a lifetime/non-retirement guarantee. Model processing residency does not settle Basic agent-state residency or telemetry/Arize residency. |
| Lifecycle? | Catalog reports inference deprecation `2027-02-09T00:00:00Z` at this snapshot. | Recheck before a later deployment. Do not promise the version will remain available indefinitely. |
| Runtime availability / budget? | No new request performed. Historical bounded test 2 hit 429; no replay. | A smaller one-request envelope and zero client retries do not guarantee one service-internal model call or successful admission. Closed allowances remain closed. |

**Precise provider-only missing checks:** validation of the complete fresh
deployment against the exact subscription/account/resource policy and model SKU
capacity 1; current allocatable capacity/eligibility at deployment time;
provisioning result; and successful approved bounded new-runtime invocation.
Metadata/public docs alone cannot discharge those checks. A provider rejection
requires a newly reviewed tuple, not an automatic higher capacity/fallback model.

## 4. Agent → Infra prerequisites (QA integration checklist)

1. **Declare the state/privacy target explicitly.** Basic with private inbound
   account PE and Microsoft-managed state is supported by docs. If fully private
   outbound/BYO state is required, return **technically blocked** until an accepted
   scoped design supplies Storage, Search, Cosmos, provisioning contract and costs.
   Do not seek owner spending approval on an undefined Standard graph.
2. **Provide exact fresh account/project/model identities and outputs** from
   ADR-0004, with provider-accepted tuple. Agent needs deployment **alias**, project
   endpoint, region and explicit agent name/version, not credentials. An agent is
   a data-plane versioned object; Bicep currently does not publish it.
3. **Separate three identities:** deployment/provisioning caller; project MI for
   service dependencies/model access; private validator/agent-consumer MI. Fresh
   module assigns project MI **Foundry User**
   (`53ca6127-db72-4b80-b1b0-d745d6d5456d`) at account scope. That assignment does
   not grant the validator access. [S10] recommends **Foundry Agent Consumer**
   (`eed3b665-ab3a-47b6-8f48-c9382fb1dad6`) at project/agent scope for invocation
   only; creator/readback operator uses the appropriate **Foundry User** permission.
   Validate effective operations and scope; no grant is authorized here.
4. **For Standard only**, reconcile [S4, S5] provisioning and runtime permissions:
   new capability-settings caller needs Storage Blob Data Contributor and Cosmos
   DB Operator; project runtime needs Search Index Data Contributor + Search
   Service Contributor, blob-container data contributor/owner as documented, and
   Cosmos native Built-in Data Contributor at database scope. The doc also lists
   project SMI Cosmos DB Operator and Storage Account Contributor for its flow.
   ARM management roles and Cosmos data-plane roles are different. Decide the
   selected flow's exact minimum scopes with Infra, not blanket Owner, inherited
   Function roles, shared keys or trusted-service bypass.
5. **Supply a private validator that is already authorized and reachable.** No VM
   start is allowed now. DNS from that execution context must map the account FQDN
   through `privatelink.services.ai.azure.com` to private addresses; the account
   suffixes `privatelink.openai.azure.com` and
   `privatelink.cognitiveservices.azure.com` remain in the foundation DNS contract.
   Verify TCP/443/TLS and approved Entra/managed-identity egress. A successful ARM
   GET from this CLI does not test private data-plane reachability.
6. **Provide immutable runner provenance and no-tool publication readback.**
   Pin the three packages above and the complete resolved dependency
   lock/wheel hashes for the selected runtime; the SDK source pins alone are not
   a supply-chain lock. No live runner is added to product code by this task.
   Read back name/version/kind/model/tool count and compare the approved
   definition hash without printing instructions. Never register a replacement
   agent merely to test readiness. Never use “latest” as the acceptance version.
7. **Preserve telemetry gate separation.** AppInsights association, bounded native
   content capture, trace/parent/correlation identifiers and actual
   prompt/completion/total token reconciliation must be independently accepted
   by Telemetry/QA. No raw bodies/state are needed for prerequisite discovery.
   No-connection-PUT staging and a completed model request are not E2E proof.

## 5. Later gated verification commands — NOT EXECUTED

These examples are handoff instructions, **not authorization**. Run only under
a newly approved exact scope and private-validator window. Do not start a VM,
replay a historical request, use dataset probes or read state to obtain evidence.
Placeholders are required owner/Infra outputs, not suggested defaults.

### A. Metadata/provider recheck (no inference)

```powershell
$env:AZURE_CONFIG_DIR = 'C:\repos\foundry-otel-to-arize-demo\.azure-config'
$subscription = 'c81fda52-936e-4f14-8af4-951c0dbb92d2'
$ApprovedRG = '<approved fresh resource-group name>'
$ApprovedAccount = '<approved fresh account name>'
$ApprovedProject = '<approved fresh project name>'
$ApprovedParameterFile = '<reviewed complete repo-contained parameter file>'
$accountId = "/subscriptions/$subscription/resourceGroups/$ApprovedRG/providers/Microsoft.CognitiveServices/accounts/$ApprovedAccount"
$projectId = "$accountId/projects/$ApprovedProject"
az cognitiveservices model list --location eastus2 --subscription $subscription --query "[?kind=='AIServices' && model.name=='gpt-5-mini' && model.version=='2025-08-07'].{capabilities:model.capabilities,skus:model.skus}" --only-show-errors -o json
az cognitiveservices usage list --location eastus2 --subscription $subscription --query "[?name.value=='OpenAI.DataZoneStandard.gpt-5-mini'].{name:name.value,current:currentValue,limit:limit,unit:unit}" --only-show-errors -o json
az rest --method get --url "${accountId}?api-version=2025-09-01" --subscription $subscription --query '{id:id,state:properties.provisioningState,pna:properties.publicNetworkAccess,disableLocalAuth:properties.disableLocalAuth,networkInjections:properties.networkInjections}' --only-show-errors -o json
az rest --method get --url "${projectId}?api-version=2025-09-01" --subscription $subscription --query '{id:id,state:properties.provisioningState}' --only-show-errors -o json
# Separate provider gate: NOT read-only discovery; do not execute under this task.
az deployment group validate --resource-group $ApprovedRG --template-file infra\main.bicep --parameters "@$ApprovedParameterFile" --subscription $subscription --only-show-errors -o json
```

Validation is not a reservation or deployment. Infra must record the exact
provider result for capacity 1; perform scoped what-if and deployment only under
its own later authorization. Do not invoke validate against the mixed live RG
or incomplete example parameters.

### B. Private network and definition readback (no inference)

From the approved private validator, with **no login, grants or network changes**:

```powershell
$ApprovedHost = '<approved-account-subdomain>.services.ai.azure.com'
Resolve-DnsName $ApprovedHost
Test-NetConnection -ComputerName $ApprovedHost -Port 443
# Linux equivalents when that is the approved validator:
# getent ahostsv4 '<approved-account-subdomain>.services.ai.azure.com'
```

The following Python example is **metadata GET only**, not a conversation,
response, state-store or dataset read. Execute it with the pinned environment
only after Infra supplies the three explicit `APPROVED_*` variables.
Never print `agent`, `definition`, instructions or unfiltered exception text.

```python
import json
import logging
import os
from importlib.metadata import version
from azure.ai.projects import AIProjectClient
from azure.identity import ManagedIdentityCredential

os.environ["AZURE_AI_PROJECTS_CONSOLE_LOGGING"] = "false"
logging.disable(logging.CRITICAL)
for package, pin in (
    ("azure-ai-projects", "2.0.0"),
    ("azure-identity", "1.26.0"),
    ("openai", "2.26.0"),
):
    if version(package) != pin:
        raise RuntimeError("Pinned package mismatch")
with ManagedIdentityCredential(
    retry_total=0, connection_timeout=10, read_timeout=10
) as credential:
    with AIProjectClient(
        endpoint=os.environ["APPROVED_PROJECT_ENDPOINT"],
        credential=credential,
        api_version="v1",
        retry_total=0,
        connection_timeout=10,
        read_timeout=20,
        logging_enable=False,
    ) as project:
        agent = project.agents.get_version(
            agent_name=os.environ["APPROVED_AGENT_NAME"],
            agent_version=os.environ["APPROVED_AGENT_VERSION"],
        )
        definition = agent.definition
        tools = getattr(definition, "tools", None)
        result = {
            "name": agent.name,
            "version": agent.version,
            "kind": definition.kind,
            "model": getattr(definition, "model", None),
            "tool_count": 0 if tools is None else len(tools),
        }
        print(json.dumps(result))
```

### C. Invocation contract, not a runnable approval

Only after A/B, publication, package custody, telemetry gates and an independently
reserved new bounded invocation intent pass, the selected SDK call shape is:

```python
# NOT EXECUTED. Requires the approved pinned project client and synthetic input.
# Reserve the new intent durably BEFORE sending; unknown/429/timeout means STOP.
# Disable SDK console/body logging. No automatic retries or polling/continuation.
with project.get_openai_client(max_retries=0) as client:
    raw = client.responses.with_raw_response.create(
        input=approved_synthetic_input,
        max_output_tokens=1024,
        extra_body={
            "agent_reference": {
                "type": "agent_reference",
                "name": approved_agent_name,
                "version": approved_agent_version,
            }
        },
    )
    response = raw.parse()
```

This fragment documents the supported request, **not a complete approved runner**:
the executor must additionally enforce the approved deadline/timeouts, input and
output budget, once-only intent and sanitized error/result handling. Do not copy
it into the local stub or execute an official sample's CRUD/conversation/body
printing. Do not add a `model` override, tools, temperature, top-p, fallback
deployment, agent creation or another request to recover an ambiguous outcome.
Read actual usage from the newly authorized result only; output limits include
reasoning output and are not exact cost/token guarantees. Neither this call nor
zero client retries proves one service-internal model execution.

## 6. Evidence collected and checks performed

All new evidence is uniquely isolated in the worktree's **ignored**
`.azure-sandbox\issue147-agent-runtime\`; QA owns every other concurrent file.
The Agent assessment's only product-track deliverable was this new document;
that assessment performed no index operation, commit, push, existing receipt
edit, runtime registration or cloud mutation. QA subsequently integrated it into
the acceptance, cost and workflow packet in existing PR #151. The original
ignored assessment receipts remain unchanged.

| ID | Source/date and limited interpretation |
|---|---|
| E1 | Root `.azure-sandbox\private-runtime-agent-reconciliation.json`, 2026-10-14 02:21–02:29 UTC: sanitized `actualVersions` and definition hash metadata only; version 1, `PromptAgentDefinition`, typed `Reasoning(effort=minimal)`, deployment alias above. Full definition SHA-256 `69ccd005e568a7429cb23ccd198ec2149981d660491c534d04465166efcf9e97`; no instruction body read or reproduced. |
| E2 | Root `.azure-sandbox\issue143-native-agent-invoke-contract.json`, updated 2026-10-19 08:56 Eastern: `verification.metadata_only_followup`, metadata GET PASS for version 1/prompt/zero tools; package/API/authentication pins. Corroborated by `issue143-native-agent-metadata.sh` source. No script executed here. |
| E3 | Root `private-runtime-model-invariants.json`, 2026-10-13 23:21 UTC: model/version/GlobalStandard capacity 5/NoAutoUpgrade; current model GET repeated in this assessment, not a PUT. |
| E4 | New scoped Azure **metadata GETs** on discovery date: `eastus2-gpt5mini-model.json`, `eastus2-gpt5mini-quota.json`, `existing-model-metadata.json`, `existing-account-metadata.json`, `existing-project-metadata.json`, and account/project capability-host lists. All use explicit subscription `c81fda52-936e-4f14-8af4-951c0dbb92d2`, `AZURE_CONFIG_DIR=C:\repos\foundry-otel-to-arize-demo\.azure-config`; ARM 2025-09-01. Both capability-host lists return `hosts=[]`, `nextLink=null`; capabilitySettings/networkInjections projections null are **not** proof of every hidden/default service implementation. |

No model calls, agent registration, datasets/uploads, evaluation, raw
prompt/response/telemetry/state reads, secret/app-setting/auth-cache inspection,
VM operation, grant, lease, billing export, protection change or teardown occurred.
#148 remains on hold; existing sender, ledgers, ACKs, checkpoints, quarantine and
unknown-delivery identities remain untouched.

The top-level Foundry skill was invoked normally. Its host-installed dependency
script/subreferences were **not accessed**: their paths are outside the explicit
repository boundary and setup/installation is not required for public-source
discovery. This is not claimed as completed official prepare→validate→deploy
workflow evidence; QA's separate workflow reconciliation remains separate.

Offline validation results and exact reproduction command:

```powershell
python -B .azure-sandbox\issue147-agent-runtime\check-contract.py
git diff --check -- docs/current-state/issue147-private-agent-prerequisites.md
```

The checker parses the document's Python examples and the pinned SDK Python
sources without importing/calling SDKs, validates the supported SDK route/type/
bearer/client constructor surface and official OpenAI request surface, verifies
public-source SHA-256 hashes, checks repository-relative links and parses the
PowerShell examples. Results are recorded in ignored `offline-check-result.json`.
These are static checks, **never live acceptance**. No dependency restoration was
needed. **PASS:** 21 public-source hashes, seven metadata receipt hashes, six SDK
source AST parses, two document Python examples, three PowerShell examples,
both local links, the API/type/auth/request surface assertions and the catalog/
capability-host assertions. Direct whitespace validation also covers this new,
untracked file (ordinary `git diff --check` alone does not inspect untracked files).
`git diff --check -- docs/current-state/issue147-private-agent-prerequisites.md`
returned exit 0; no cloud or SDK calls were made by the checker.
Several guessed public Learn routes returned 404; they were replaced by
the authoritative links below, not treated as support evidence. One local
hash-report helper initially hit Windows default-text decoding on a public page;
UTF-8 was made explicit for the final checker.

## 7. Authoritative source pins

Sources fetched directly from official public endpoints on the discovery date.
Learn pages embed the following Git commit IDs in their returned metadata.
`public-source-manifest.json` stores full retrieval timestamps, resolved URLs
and SHA-256 for each downloaded public source; the final static checker verifies
those bytes. A documentation hash establishes what was read, not provider
acceptance or validation of a fresh runtime.

| Ref | Official source and immutable revision |
|---|---|
| S1 | [Azure AI Projects 2.0.0 source](https://github.com/Azure/azure-sdk-for-python/tree/3c342025b7088315522ce1e4d0b5973dd9253232/sdk/ai/azure-ai-projects): `_configuration.py`, `_patch.py`, `models/_models.py`, `operations/_operations.py`, `samples/agents/sample_agent_basic.py`. Tag `azure-ai-projects_2.0.0` resolves to **`3c342025b7088315522ce1e4d0b5973dd9253232`**. Companion `azure-identity_1.26.0` resolves to **`30d8bb95bf21f28fc5ed7a0fc9da43a46765c81e`**. |
| S2 | [OpenAI Python 2.26.0 Responses source](https://github.com/openai/openai-python/blob/15afa21e54952c06e2ac4d3e3a82f144c2cf9ed9/src/openai/resources/responses/responses.py), tag `v2.26.0` → **`15afa21e54952c06e2ac4d3e3a82f144c2cf9ed9`**; [Azure Responses agent-reference schema](https://github.com/Azure/azure-rest-api-specs/blob/09685799a1c25766ba250f5cd6051659be8a4e50/specification/ai-foundry/data-plane/Foundry/src/openai/responses/models.tsp), commit **`09685799a1c25766ba250f5cd6051659be8a4e50`**. Latest schema corroborates type/name/optional version; it does not select a preview API for the pinned runner. |
| S3 | [Agent environment setup](https://learn.microsoft.com/en-us/azure/foundry/agents/environment-setup?view=foundry), commit **`33d8adb8102054cb84b9678020f4edc0e8e12f04`**, SHA-256 **`db40463147e166b5398249892c24d6c77649f59ae3654a0aa9eac1f9faf17dee`**. Explicitly distinguishes private inbound from Standard-only secured outbound. Basic's Assistants comparison is not the new API selection; S1/S2 establish that independently. |
| S4 | [Standard agent setup](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/standard-agent-setup?view=foundry), commit **`0312d552e02dc0983beccdf0c82ca158dcf40436`**, SHA-256 **`c4b6ec259d4f5cbc7ac6e7f8b84a89452a9c5ce325b6fa109d40220eec254165`**. State trio, new/classic containers, provisioning/runtime roles and documented throughput inconsistencies. |
| S5 | [Private networking](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/virtual-networks?view=foundry), commit **`58b932b92b46e2248ac1662001730789ef7e5e06`**, SHA-256 **`126c9b36d9fa302fc0141622b075ddf4a21cb1b15e46732903afc67b27c51ea0`**. |
| S6 | [Agent networking deep dive](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agents-networking-deep-dive?view=foundry), commit **`b3048cbbddfc5b32fb6f0148a2edc46123296e06`**. No Micro VM on Prompt Agent path. |
| S7 | [Agent limits/regions](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions?view=foundry), commit **`eef5e80b2042f4a4b1676c8551a7ece9b67e095c`**. |
| S8 | [Models sold directly by Azure](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure?view=foundry), commit **`9586c846951c6a1142057355d5b7d6f73c63d1b7`**. |
| S9 | [Model deployment types](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types?view=foundry), commit **`32726378f9adc67a78fef2187aa9197cdfea657a`**. |
| S10 | [Foundry RBAC](https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry?view=foundry), commit **`aa8dac9af5c360ba3d338f4fe7ad04e794d98ea5`**. Distinguishes consumer, author, project MI, model and provisioning permissions. |

**QA integration:** this artifact is included in PR #151 without closing #147.
Do not promote “Basic + private inbound” to “Standard private runtime,” change
the existing model tuple, or consolidate numeric/custody approval until the
technical state target and provider-only gates are resolved.
