# #147 existing native request — independent verification (2026-10-20)

**Existing native flow PROVEN with documented limits — not full criterion
acceptance or a fresh POC PASS.** QA retains ownership; #147 stays OPEN and PR #151 unmerged. This is
existing GlobalStandard/capacity 5 evidence, **not** the separate undeployed fresh
DataZoneStandard/capacity 1 milestone.

Verifier `6912405f-f0c9-4cd3-acf6-b97f1844e68e` is independent of executor
`6f62330e-9039-4a38-a51f-87c695b55c9d`. Verification used existing Azure auth
and an existing same-origin Arize browser session, metadata projections only.
No VM start, inference, deployment, replay, grant, credential inspection or
content-body read was performed by this verifier.

Metadata-only follow-up worker `1eea1404-59a3-49ba-8c6a-fd28b803a378`
closed destination nonempty-I/O and model verification at `07:22:06Z`.
Under the explicit current-two-synthetic-spans exception, the existing Arize
application runtime fetched the exact spans and reduced values to booleans,
lengths and a model/resource whitelist **before** returning any tool result.
No bodies, broad attributes, credentials or browser storage were exposed or
persisted. There were zero additional model calls, VM starts or cloud mutations.

## Exact request binding

- Run: `d2c13606-e59e-4143-8b04-9e7dc7fcf471`.
- Authorization: `issue147-existing-native-20261020T065000Z`;
  executor reference: `qa-existing-native-mi-20261020`.
- Response: `resp_01a5508925f97685006ad711210f688197aa32beed7db906cb`,
  successful receipt at `2026-10-20T06:58:43.804231Z`.
- Agent: `fotoa-demo-agent-eastus2/1`, zero tools per executor preflight.
- Model alias: `fotoa-demo-gpt5mini-eastus2`; native request/response model:
  `gpt-5-mini-2025-08-07`.
- Actual returned usage: **104 input / 34 output / 138 total**.
- W3C/native trace `89d6a1200019ef6d6a77eba778e11f07`;
  CLIENT span `5db9efa4b4c938f6` was deliberately **unexported external context**,
  not a missing native Agent. The actual native Agent is `02b160c26004ea61`.
- Request custody chain is the actual durable current run receipt above →
  exact response ID → the two response-bound native spans → matching Arize
  identities. This is evidence-level correlation, not a native run-UUID attribute.

## Hop and attribute matrix

| Boundary | Result | Independent evidence / limitation |
|---|---|---|
| Foundry → Application Insights / LAW | VERIFIED for two native service spans | A broad, bounded `06:57–07:02Z` source query did not assume service trace equality. An exact response-ID query independently found `invoke_agent` and `chat`; both bind agent/version/response and native Foundry metadata. |
| Native service graph | VERIFIED within native-service boundary | AGENT `02b160c26004ea61` → deliberately unexported external CLIENT context `5db9efa4b4c938f6`; LLM `8879301ec48ecbb6` → AGENT. Both service spans use trace `89d6a1200019ef6d6a77eba778e11f07`. The parent reference is preserved; a fully exported graph root is not claimed. |
| Native content-table source | VERIFIED | Two matching `AppGenAIContent` rows preserve exact trace/span/parent IDs. Input/output fields are present, lengths **642/154** characters on each row, matching inline field lengths. No bodies were retrieved; lengths are not content-fidelity proof. |
| LAW → Event Hub configuration | VERIFIED configuration only | Exact enabled `fotoa-demo-e2e-app-spans` rule selects **AppDependencies, AppRequests, AppGenAIContent**, destination namespace `fotoa-demo-ehns-eastus2`, hub `telemetry`. Not per-request delivery evidence by itself. |
| Event Hub → Function → durable ACK | Exact admission/ACK audit remains UNVERIFIED | Source establishes the exact hashing formula below. Resolved `ARIZE_OTLP_ENDPOINT` and `ARIZE_SPACE_ID` strings are not present in allowed metadata; prior sanitized receipt explicitly says `NOT_READ`. Event Hub namespace/hub/group are not hash inputs and cannot replace them. No guessed-key/trace-ID Function query or old-ledger/state inspection was performed. Destination arrival proves delivery, not an exact durable ACK record. |
| Arize actual native graph | VERIFIED for two service identities | Existing-session metadata query in project `fotoa-vm-diagnostic` returns exactly the two matching service spans, both OK, same parents and start times at millisecond resolution; `hasNextPage=false`. No historical/fallback trace substituted. |
| Token provenance | VERIFIED 104/34 and derived/reporting total 138; native total NOT preserved | Exact response returns **104/34/138**. Native LLM has `gen_ai.usage.input_tokens=104`, `output_tokens=34`; native and OpenInference total attributes are both null. Mapper aliases the two counts, never synthesizes total. Arize `tokenCountTotal=138` equals **104+34** and the response total; it is a destination reporting total, not a preserved native total attribute. AGENT usage remains null. |
| Custom request correlation | Observed source limitation | Native `correlation.id` and run UUID are absent for this request. Actual receipt/response/W3C identity binding above remains available. This is not a universal claim about vendor support or custom-header propagation. |
| Arize I/O presence | VERIFIED nonempty, not content parity | Both spans have JSON Input **642** / Output **154** characters, nonempty. Source lengths match; neither equality of lengths nor presence proves content fidelity. No content parity or fallback execution claimed. |
| Arize model | VERIFIED | Both spans preserve `gen_ai.request.model`, `gen_ai.response.model` and `llm.model_name` = `gpt-5-mini-2025-08-07`, provider `microsoft.foundry`. Deployment alias remains receipt/preflight metadata, not a substituted native model name. |
| Resource/project lineage | Source VERIFIED; destination resource parity UNVERIFIED | Source component is `fotoa-demo-appi-eastus2`, role `responsesapi`, native project `fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-eastus2`. Destination project is `fotoa-vm-diagnostic` (`TW9kZWw6MTAzNzkwMDE2NDc6Tm5nUA==`). No whitelisted resource keys returned from destination span attributes; OTLP resource block was not established. Mapper builds `service.name` from role, not a complete native resource block; native project/agent IDs are outside its string-field allowlist. Do not silently claim their end-to-end preservation. |

## Exact Function-key derivation and bounded exception

`telemetry_pipeline/durable_runtime.py` builds the scope from
`DURABLE_ALLOWED_WORKSPACE_ID`, `DURABLE_ALLOWED_COMPONENT_RESOURCE_ID`,
`DURABLE_ARIZE_PROJECT`, and the literal concatenation
`ARIZE_OTLP_ENDPOINT + "|" + ARIZE_SPACE_ID`.
`durable.py` / `durable_store.py` then use:

```text
canonical(x) = UTF8(json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False))
namespace = SHA256(canonical([workspace.lower(), component.lower(), project, endpoint+"|"+space]))
ledgerKey(span) = "ledger/" + namespace + "/" + traceId + "-" + spanId
operationalKey(span) = SHA256(UTF8(ledgerKey(span)))
```

Workspace and component IDs are established above. Project name
`fotoa-vm-diagnostic` is observed in destination and the sanitized prior
`otelResourceAttributes` projection; exact durable-setting equality is not independently
attested by that projection. The precise unavailable scope inputs are the resolved
**`ARIZE_OTLP_ENDPOINT` and `ARIZE_SPACE_ID`** strings, whose Key Vault references
were previously projected as Resolved but whose values were explicitly NOT_READ.
Browser route space IDs, documented endpoint examples, successful destination
arrival, Event Hub `fotoa-demo-ehns-eastus2/telemetry`, and consumer
`function-transform` do not establish those byte-exact runtime strings.

Therefore both exact operational-key hashes remain **not derivable from allowed
evidence**, not guessed or fabricated. No settings listing, secret read, state
dump, trace-as-Function-key query, or old-ledger lookup was used to bridge this
specific gap. The missing artifact is a nonsecret exact scope/namespace attestation
for this Function; this is not an inference-budget or new-consent request.

## Queries, custody and reproducibility

All Azure commands used explicit subscription
`c81fda52-936e-4f14-8af4-951c0dbb92d2` and
`AZURE_CONFIG_DIR=C:\repos\foundry-otel-to-arize-demo\.azure-config`.
Source workspace `4658bdb1-b9ca-4f57-a733-6b81f316dc45`,
component `fotoa-demo-appi-eastus2`, RG `fotoa-demo-rg`.

New ignored local evidence directory (repository-root relative):
`.azure-sandbox\issue147-native-verification-6912405f-f0c9-4cd3-acf6-b97f1844e68e-20261020`.
It contains exact KQL, request JSON, query start/completion UTC, results/errors,
export-rule metadata and metadata-only Arize GraphQL/result:

- `01-source-spans.json`: initial query `07:04:12–07:04:17Z` failed
  `AuthorizationRequiredError`, correlation
  `5074d7f6-448f-4de0-aefc-bfcfddcc10ca`. No login/grant attempted.
- `02-source-spans-audience.json`: correct explicit
  `--resource https://api.loganalytics.io`, `07:04:34–07:04:43Z`, exit 0.
  Twenty-six bounded rows: two actual native dependencies and 24 other requests.
- `03-native-attributes.json`, `04-native-content.json`,
  `05-function-correlation.json`: `07:05:29–07:05:48Z`, exits 0.
  Respectively two exact-response native rows, two content rows, and zero
  literal-trace Function-key rows (hashed-key limitation above).
- `06-export-rule.json`: exact rule GET `07:06:10Z`, exit 0.
- `07-source-binding-and-graph.json`,
  `08-function-operational-counts-not-per-request.json`:
  `07:07:57–07:08:09Z`, exits 0.
- `09-arize-native-metadata.json`: GraphQL HTTP 200
  `07:06:57.341–07:06:57.459Z`; exact query and result retained.
  Query selects IDs, parents, status, times, numeric tokens and I/O MIME only.
  It never selects input/output values or broad attributes. Browser filesystem
  persistence was unavailable; the original successful tool result was
  transcribed into this evidence file and explicitly marked as such.

Follow-up ignored metadata evidence:
`.azure-sandbox\issue147-native-metadata-1eea1404-59a3-49ba-8c6a-fd28b803a378-20261020`.
It records actual worker identity/custody, the successful `07:22:06.310–.443Z`
same-origin application-filtered destination projection, a bounded schema
projection (no usable resource field established, not a universal API claim),
and exact-response source model/resource/total-field KQL at
`07:24:21.780–07:24:29.699Z`, exit 0. `evidence-sha256.json` seals those
metadata receipts and the offline validation result. Original evidence is untouched.

No ingestion-wait polling was necessary. Original executor receipts remain
untouched. Executor summary independently records final deallocation and release
at `07:00:50.404124Z`; this verifier did not allocate the VM.

## Next technical gaps

QA may accept the **existing native flow with these explicit hop limits**:
native service identities/parent references, 104/34 token preservation, derived
138 reporting total, nonempty I/O and model preservation are established.
Exact run-bound Function admission/ACK hashes, native custom-correlation/total
attribute preservation, destination resource parity and byte/content fidelity
are not established. These are specific remaining criteria, not a blanket
claim that no native flow works. The fresh DataZoneStandard/capacity-1 milestone
and its independent gates remain unchanged. **Do not replay or issue a
replacement model request to fill metadata gaps.**
