# #147 existing native request — independent verification (2026-10-20)

**PARTIAL — native service spans reached Arize; full native E2E acceptance NOT
PASSED.** QA retains ownership; #147 stays OPEN and PR #151 unmerged. This is
existing GlobalStandard/capacity 5 evidence, **not** the separate undeployed fresh
DataZoneStandard/capacity 1 milestone.

Verifier `6912405f-f0c9-4cd3-acf6-b97f1844e68e` is independent of executor
`6f62330e-9039-4a38-a51f-87c695b55c9d`. Verification used existing Azure auth
and an existing same-origin Arize browser session, metadata projections only.
No VM start, inference, deployment, replay, grant, credential inspection or
content-body read was performed by this verifier.

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
- CLIENT trace `89d6a1200019ef6d6a77eba778e11f07`,
  CLIENT span `5db9efa4b4c938f6` is not itself native-service evidence.

## Hop and attribute matrix

| Boundary | Result | Independent evidence / limitation |
|---|---|---|
| Foundry → Application Insights / LAW | VERIFIED for two native service spans | A broad, bounded `06:57–07:02Z` source query did not assume service trace equality. An exact response-ID query independently found `invoke_agent` and `chat`; both bind agent/version/response and native Foundry metadata. |
| Native service graph | PARTIAL | AGENT `02b160c26004ea61` → parent CLIENT `5db9efa4b4c938f6`; LLM `8879301ec48ecbb6` → AGENT. Both service spans use trace `89d6a1200019ef6d6a77eba778e11f07`. CLIENT parent is not an exported row in the bounded source/destination result; do not invent a native root. |
| Native content-table source | VERIFIED | Two matching `AppGenAIContent` rows preserve exact trace/span/parent IDs. Input/output fields are present, lengths **642/154** characters on each row, matching inline field lengths. No bodies were retrieved; lengths are not content-fidelity proof. |
| LAW → Event Hub configuration | VERIFIED configuration only | Exact enabled `fotoa-demo-e2e-app-spans` rule selects **AppDependencies, AppRequests, AppGenAIContent**, destination namespace `fotoa-demo-ehns-eastus2`, hub `telemetry`. Not per-request delivery evidence by itself. |
| Event Hub → Function → durable ACK | UNVERIFIED per request | Time-bounded Function logs show admissions/matches/ACKs and two content admissions. Operational keys are SHA256 hashes. A literal trace-ID key search returns zero by construction, not evidence of missing delivery. No exact scope/key binding was available without restricted settings/state access. Aggregates are not attributed to this run. |
| Arize actual native graph | VERIFIED for two service identities | Existing-session metadata query in project `fotoa-vm-diagnostic` returns exactly the two matching service spans, both OK, same parents and start times at millisecond resolution; `hasNextPage=false`. No historical/fallback trace substituted. |
| Token preservation | PARTIAL | Native LLM source **104/34** equals receipt and Arize **104/34**. Source total is absent; Arize reports **138**, but source-total preservation/provenance is unproved. AGENT usage is absent. |
| Custom request correlation | MISSING at native source | Exact response ID binds the native rows to the receipt. Native `correlation.id` and run UUID are not observed. W3C trace/parent propagation is observed for this call, not proof of custom correlation-header propagation. |
| Arize content/model/resource parity | PARTIAL / UNVERIFIED | Both I/O objects and `application/json` MIME are observed. Values, nonempty value lengths, model attribute and resource block were not retrieved: broad attributes/value APIs would expose content. Do not claim full destination content/model/resource parity. |

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

No ingestion-wait polling was necessary. Original executor receipts remain
untouched. Executor summary independently records final deallocation and release
at `07:00:50.404124Z`; this verifier did not allocate the VM.

## Next technical gaps

Provide an approved metadata-only exact scope/key binding to reconcile these
two new native identities against Function admission/ACK logs, without opening
old ledger/state or reading settings/secrets. Establish native custom correlation
and total-token emission/provenance; decide the treatment of the nonexported
CLIENT parent. An approved server-side destination projection is still needed
for nonempty I/O value presence and model/resource parity without body exposure.
Do **not** replay or issue a replacement model request to fill these gaps.
