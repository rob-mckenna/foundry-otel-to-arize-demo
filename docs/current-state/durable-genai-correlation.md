# Opt-in durable GenAI content correlation (#143)

**CURRENT-STATE PIPELINE ENHANCEMENT: source and scoped infrastructure deployed;
durable admission ENABLED in the approved demo. Native content-table transport
and unchanged inline delivery verified; live content fallback NOT YET VERIFIED.**
This is not the conceptual direct-OTLP architecture. The existing deployed inline
path remains the baseline. [ADR-0003](../adr/0003-opt-in-durable-genai-content-correlation.md)
records the accepted preparation policy; this document grants no deployment,
export-rule, permission, replay, model invocation, or live OTLP authority.

### Verified rollout and remaining acceptance (2026-10-19)

Source `f650fed983a687eb97211b634af3d99e7286d6e1` is deployed with all twelve
active source hashes verified. The scoped four-resource rollout is complete.
All 35 approved legacy identities were imported once as content-free ACKs;
both temporary VM grants were removed. Five actual empty-outbox successes
preceded resuming the existing incoming consumer at `13:52:44Z`, preserving
checkpoints. Relevant offline tests: **260 passed**; all seven source CI jobs passed.

The first approved native synthetic call produced trace
`73f0d801bf44af6dc1b7caad743b558e`. Independent source and Arize metadata agree on
AGENT `9b5e6e600a520b25` and LLM `20cc9cf2a4cc00b5`, their parent IDs, model,
timestamps and full 12,482-character synthetic user input. The LLM's prompt and
completion counts arrive as integers, 5260 and 23. Two matching valid
`AppGenAIContent` rows arrived through native export.

**This call did not exercise fallback:** both originals retained valid full
13,551-character inline input JSON and 118-character output JSON, which correctly
won precedence. Exceeding an assumed 8-KiB inline boundary did not force truncation.
No duplicate observed identity or content-generated span was found in the bounded
destination snapshots. This is not an exactly-once guarantee.

The upstream parent `98b6be7816270067` was not observed as an original in the
bounded source query or among these destination spans. Source `correlation.id`
and total-token fields were absent; Arize's reported total 5283 has no established
source-total provenance. The REST response does not expose an OTLP resource block.
Do not claim complete graph, custom-correlation, total-token or resource parity
from this test. One global send was quarantined as ambiguous; its identity and
delivery remain unresolved, and it must not be blindly resent. #143 remains open.

## Routing, admission and identity

`DURABLE_GENAI_ENABLED` defaults to `false`. Missing/false preserves the original
`transform_batch`, exporter selection/retries, console fallback and checkpoint
behavior. An invalid flag fails explicitly. True selects durable admission and
a separate 30-second timer; it never selects the console exporter.

The Event Hub trigger decodes the existing object/array/`records` envelopes and
commits each admitted record before returning. It performs no waiting or sends.
The timer is bounded and does not depend on arrival order, process memory,
partition affinity, or the original worker remaining alive. Partial batch admission
is safe to replay; the already-admitted original's clock is unchanged.

- Original rows use the existing strict `AppDependencies`/`AppRequests` mapper,
  including native/legacy alias agreement, root markers, nanosecond timing and typed
  tokens. Legacy fixtures without `Type` remain supported with required provenance.
- Content rows require `Type=AppGenAIContent`, valid nonzero 32-hex `TraceId` and
  16-hex `SpanId`, optional valid `ParentSpanId`, and timezone-aware UTC
  `TimeGenerated`. Capture time is validated, **not** used as span start or deadline.
  Validation reuses the mapper's nanosecond parser across Python 3.10-3.12;
  native seven/nine-digit fractions must not be rejected as malformed content.
  Content `Id` is not a span ID. A content-only row never produces a span.
- Every row must match configured `TenantId` (workspace UUID) and `_ResourceId`
  (allowed Application Insights component resource ID), case-insensitively.
  No wildcard source admission or automatic query fallback is supported.
- A ledger key hashes workspace/component plus destination project/endpoint/space,
  and includes normalized trace/span IDs. Wrong sources cannot attach content;
  different traces with the same span ID and different destinations are isolated.
- Malformed/disallowed content keys, capture times and parents are count-only
  rejects, so they do not suppress valid neighboring originals. Invalid content
  message envelopes omit only the affected side. Oversized records/candidates,
  invalid originals, storage failures and contention exhaustion instead fail
  admission with backpressure. They are **not** silently skipped/truncated.

**Checkpoint limitation:** the host retains its finite three-retry policy. An
admission error raises before invocation success, but Event Hub checkpoints can
advance after host retry exhaustion. Never-admitted events are not in the ledger.
Alert and preserve safe partition/sequence/identity evidence for separately
authorized recovery. This is not an exactly-once or automatic lossless guarantee.

## Join and precedence

The join deadline is **300 seconds from first durable original admission**.
Content arriving first does not start it; duplicates, old event times and subsequent
content arrivals do not reset it. A span is relevant for waiting when mapped
`openinference.span.kind` is `LLM`/`AGENT`, or it has a nonempty
`gen_ai.operation.name`. Ordinary dependency/tool/CHAIN spans without that operation
do not wait. Names alone do not classify a span. For relevant spans both input and
output are required for early completeness; empty explicit strings/valid empty
message arrays count as present. Complete spans can send on the next timer pass
without waiting out the deadline.

Each side independently uses:

1. An explicit OpenInference `input.value` / `output.value`, including `""`;
   existing strict string and MIME validation is unchanged.
2. A valid inline `gen_ai.input.messages` / `gen_ai.output.messages`.
3. A unique valid `InputMessages` / `OutputMessages` content-table array.

The existing `_message_json` role/parts validator is shared; no separate envelope
implementation or additional truncation. Generated value/MIME are JSON string and
`application/json`. Invalid/missing inline can fall back to content. Arrays retain
message/part order and nested data; object-key order is canonicalized for duplicate
detection. Identical arrays, including repeated content `Id`, are idempotent.
Different valid arrays on a side are a conflict, not concatenated or selected by
arrival time. A higher-precedence valid original side still wins. Otherwise a
conflicted side is omitted at deadline. Input and output can arrive independently.

A supplied content parent must agree with the original's validated parent.
Absent/empty content parent supplies no parent assertion. Mismatched content
does not attach or replace parent metadata. All timing, status, resources, model,
correlation and tokens remain original-derived; total tokens are not inferred.

At deadline, send the original with whatever valid enrichment is then available.
There is no content-generated root/child, retransmission for late enrichment, or
upsert assumption. The timer's cadence, bounded scans and backlog add scheduling
latency: 300 seconds is the join policy, not a wall-clock delivery SLA. Content
received before actual finalization may still enrich that pending original.

## Blob ledger, claims and delivery outcomes

Use private `genai-correlation` in existing Function storage, **not** host checkpoint
blobs. Conditional creates and ETag replacements atomically serialize admission,
freeze, ownership claims and acknowledgment. The physical namespace is
`ledger/<scope-hash>/<trace>-<span>`; the separate `control/<scope-hash>/scan` blob
persists the opaque query cursor and fixed cutoff for each scan cycle.
Conditional uploads set content-free `scope` and `due` Blob index tags together
with the document. The drainer queries only due work: unexpired tombstones,
content-only orphans, waiting originals, and retained recovery entries do not
consume each active-work scan page. New content brings a waiting original due
again; acknowledgment schedules only expiry, and recovery removes the due tag.
Two instances may scan the same page, but only
the worker committing a `sending` transition may send.

| State | Behavior |
|---|---|
| `pending`, original absent | Retain content-only evidence; observably delete at 24h from first receipt. Never send. |
| `pending`, original present | Join until complete/deadline; nonrelevant spans bypass wait. |
| `sending` | Actual serialized OTLP protobuf bytes, SHA-256, original/candidates, finalization metadata and claim time persisted before HTTP. |
| `retry` | Only explicit throttling rejection; retain identical frozen bytes until due. Late input is unapplied. |
| `acknowledged` | Replace entire content-bearing document with state/ack time/expiry only. Suppress replay for initial 48h, then conditionally delete. |
| `ambiguous` | Retain frozen bytes and evidence indefinitely; no automatic resend/deletion. |
| `rejected` | Permanent rejection or throttling retry exhaustion; retained operator recovery, no automatic resend/deletion. |

The strict sender uses stdlib HTTPS with certificate validation, a single POST,
20-second socket timeout, no redirects and no exporter-SDK automatic retries.
It sends `application/x-protobuf` with configured `api_key` and `space_id`.
Project routing is frozen as resource `openinference.project.name`; it does not
depend on another worker's later resource detector.

| Outcome | Strict classification |
|---|---|
| HTTP 200, parseable OTLP response, no rejected spans/error message | Confirmed protocol delivery; replace with tombstone. An empty protobuf response is valid. |
| HTTP 429 | Explicit rejection; up to five total attempts, backoff 30/60/120/240 seconds, then retained `rejected`. |
| HTTP 400/401/403/404/405/413/415 | Definitive protocol rejection; retained `rejected`, operator correction required. |
| Partial-success rejection/warning, malformed/oversized response, unexpected status including 5xx/redirect, timeout/socket/connection error | `ambiguous`; no automatic resend. |
| `sending` claim at least 120 seconds old | `ambiguous`; crash could have occurred before or after receiver acceptance. |
| Success followed by uncertain/failed acknowledgment write | Stored `sending`/uncertain state becomes ambiguous; if the tombstone actually committed, it suppresses replay. |

**Conservative policy, not a receiver guarantee:** quarantine can strand delivery
that actually never reached Arize. Retrying every uncertain request could instead
duplicate an accepted identity. No verified receiver idempotency/merge mechanism
resolves this transaction boundary. Frozen bytes cannot change after claim, even
while retries, concurrent content arrival or operator investigation are pending.

## Protective bounds and overload

These are local safety choices, **not** Azure/Arize vendor limits:

| Bound | Value / action |
|---|---|
| Source scope/destination field | Nonempty, at most 1,024 characters each; fixed-size hashed namespace. |
| Event Hub message | 1 MiB before JSON parsing; 256 records/message, 1,024 records/invocation. |
| Individual source record | 128 KiB encoded JSON. |
| Content candidates | Four distinct candidates/side, including parent assertion; fifth fails atomic admission. |
| Ledger document / download | 1 MiB; check blob size before download, conditional bounded read, recheck bytes. |
| Frozen OTLP request / HTTP response | 256 KiB / 64 KiB; oversize request fails before claim, response is ambiguous. |
| Admission/drain CAS attempts | Eight; exhaustion raises, retaining prior state. No trigger sleep. |
| Timer page / send attempts | At most 16 ledger entries and four HTTP attempts per invocation. |
| Rejected-throttle attempts | Five total; frozen payload retained after exhaustion. |

Candidate and complete-ledger bounds are checked before any write. Distinct
original payloads on an existing identity fail as original-identity conflict
rather than replacing authoritative evidence. SDK storage operations use bounded
retry settings and sanitized errors; no raw parser/SDK dumps in application logs.

Persisted continuation advances across due entries and individual failed entries,
avoiding first-page starvation. An entry failure
is observed, the page's cursor is committed, then the timer invocation fails.
If listing/cursor storage fails, no successful cursor advance is claimed.
At the end of a query the next scan begins with a fresh cutoff. Send-budget exhaustion leaves
other pending work untouched for later rotations. Each attempt counts even if its
acknowledgment subsequently fails. Continuous backlog still needs capacity planning;
there is no global account-wide key-count quota or latency guarantee.

Blob index updates are eventually visible. Conditional ledger reads/claims, not
query results or tags alone, determine whether a send is permitted; stale index
results cannot authorize a second send. Index propagation adds scheduling latency.
Before rollout, verify index-tag support, query latency/cost and managed-identity
permissions for `blobs/tags/write` and `blobs/filter/action`. Existing ordinary
Blob read/write roles are **not** proof of those permissions. The runtime and
baseline preparation add no grant; the separate opt-in rollout template below
defines only the two additive index permissions. See [Microsoft's Blob index guidance](https://learn.microsoft.com/azure/storage/blobs/storage-manage-find-blobs).

Never apply unconditional storage lifecycle TTL to this container. **Unsent,
ambiguous and rejected entries are retained indefinitely**, so storage can grow.
Monitor backlog/oldest age/cost, restore capacity/access on storage admission
failure, and obtain separate scope before changing limits or deleting recovery
state. A limit failure is not permission to advance/replay checkpoints manually.

After acknowledgment/orphan expiry, deletion is of the active ledger payload.
Blob versions, snapshots, soft-delete and backups may retain previous content.
**Before rollout, approve and verify those policies** and confirm they satisfy
the required physical deletion/retention boundary. This code does not silently
disable account protections or assert historical versions were purged.

## Opt-in configuration and release gates

Runtime requires all of:

- `DURABLE_GENAI_ENABLED=true`
- `DURABLE_ALLOWED_WORKSPACE_ID`: exact source workspace UUID
- `DURABLE_ALLOWED_COMPONENT_RESOURCE_ID`: exact component ARM resource ID
- `DURABLE_ARIZE_PROJECT`: approved destination project
- Existing `ARIZE_OTLP_ENDPOINT` (full HTTPS `/v1/traces`), `ARIZE_SPACE_ID`,
  and Key Vault-resolved `ARIZE_API_KEY`; never print/read these for test evidence.
- Identity storage `AzureWebJobsStorage__blobServiceUri` or
  `AzureWebJobsStorage__accountName`. Current adapter supports the public Azure
  `*.blob.core.windows.net` HTTPS endpoint (including private DNS routing), not
  arbitrary hosts, SAS/connection strings, Azurite or sovereign-cloud suffixes.
  It uses the system-assigned managed identity, not developer credentials.
- Existing private `genai-correlation` container and approved reachable Blob data
  access. Runtime does not create it or widen roles.

`prepareDurableGenAIContainer=false` is the default Bicep parameter. True prepares
only that private child container in the existing Function account. It changes
neither runtime settings nor table export nor role assignments. Container children
do not support the account's tag model; the existing required account tags remain.
The retained baseline `infra/main.bicep` contains no native LAW data-export rule.
**Source publication/container preparation alone
does not enable live AppGenAIContent export.** Any actual rule change remains an
explicit, separately reviewed opt-in; do not deploy the broad baseline as a shortcut.

For an approved existing-pipeline rollout, the standalone
[`infra/durable-genai-rollout.bicep`](../../infra/durable-genai-rollout.bicep)
prepares only the private container, an RG-assignable custom role containing
`blobs/tags/write` and `blobs/filter/action`, its container-scoped Function MI
assignment, and the existing export-rule update. Required snapshot parameters
preserve its full table list, enabled state, namespace and explicit Event Hub name.
There are no Function settings or parent-resource writes, and no retention changes.
The [infra recipe](../../infra/README.md#narrow-existing-resource-rollout)
documents offline tests, drift review and coordinator validation/what-if commands.
The scoped rollout has been deployed for #143, including AppGenAIContent on the
existing export. Compilation and resource deployment alone cannot establish
effective MI access, native content transport, enablement or destination fidelity.

Before any enablement, authorize and verify:

1. Exact source/destination and synthetic-only content-table exposure, table plan,
   same-region native export eligibility and actual independently arriving content.
   ARM rule creation alone is not delivery evidence. Do not silently switch to queries.
2. Existing account/container identity grants (including index-tag write/filter),
   network/DNS access, encryption and
   version/soft-delete/backup retention; no new grant assumed from source patterns.
3. Real upstream retry, Event Hub retention, operational replay/recovery horizon.
   Keep 48h tombstones only if that horizon is covered. Template `1d` is not live data.
4. Cutover boundary: stop/drain or otherwise explicitly coordinate the old immediate
   exporter and new ledger. Historical replay/already-exported spans are excluded
   unless separately reconciled. Do not enable two consumers that export the same
   originals, or empty/delete the ledger as a rollback shortcut.
5. Capacity/load/cost, timer lag, dependency versions, and bounded sender behavior.
   Package deployment alone is not safe proof that strict mode is live.
6. Approved independent destination verification of one logical original identity,
   content fidelity, parent/correlation/tokens/resources and receipt counts. No live
   calls, new synthetic invocation or replay are authorized by these local tests.

Rollback needs its own plan for retained outbox work. Simply disabling strict mode
restores legacy immediate export for subsequent deliveries but leaves pending
ledgers unsent and can duplicate identities on replay. Preserve state and reconcile
before resuming another sender.

### First-cutover acknowledgment migration

A fresh ledger does not know which identities the legacy sender already delivered.
For the approved #143 cutover, pause the incoming trigger without changing its
consumer group or checkpoints, then take a complete, bounded identity-only
snapshot from the exact Arize project. Reconcile the query window with observed
source age and the approved recovery horizon; an empty/incomplete query is not
proof of nondelivery.

Import only confirmed trace/span identities as create-only `acknowledged` records
in the actual configured runtime namespace. Use the ordinary content-free schema,
48-hour expiry and atomic `scope`/`due` tags. Do not import prompt/response bodies,
resend historical spans, fabricate acknowledgments for unseen identities or
overwrite pending work. Verify every imported receipt and the complete due-index
identity set before admitting events. An existing nonempty ledger requires
separate reconciliation rather than rerunning this fresh-ledger procedure.

The approved temporary migration identity receives Blob Data Contributor plus
the existing two-action index role only at `genai-correlation`. Remove both
temporary assignments before admitting new traffic; no host-checkpoint access,
Event Hub receiver grant, credential forwarding or permanent operator grant is
needed. Preserve the snapshot and explicit partial-failure evidence. A failed or
ambiguous import is not permission to overwrite, erase or blindly rerun it.
This suppresses confirmed legacy identities within the bounded migration scope;
it is not a receiver upsert or global exactly-once guarantee.

## Safe operational evidence and recovery

Application logs are fixed
`durable outcome=<outcome> key=<hashed-key> count=1 reason=<internal-failure-code>`.
Failure codes distinguish size/record/candidate limits, storage failures and
contention without logging mapper/parser exception details.
Outcomes include `matched`, `deadline_missing`, `orphan_expired`, `late`, `conflict`,
`ambiguous`, `acknowledged`, `admission_failure`, `drain_failure`, and retained
`recovery_ambiguous` / `recovery_rejected`, plus admission/pending/replay/mismatch
counts. Repeated scan outcomes are operational counts, not distinct-span parity.
Never emit message bodies, raw dimensions, frozen bytes or exceptions into logs.

Example count query against Function logs in the authorized workspace (not
evidence of a live run):

```kusto
AppTraces
| where TimeGenerated > ago(1h)
| where Message startswith "durable outcome="
| parse Message with "durable outcome=" outcome " key=" ledgerKey " count=" count " reason=" reason
| summarize events=count(), distinctKeys=dcount(ledgerKey) by outcome, bin(TimeGenerated, 5m)
```

Alert on admission/drain failures, unexpected ambiguity/rejection/conflict, overdue
pending work, timer failures, orphan rates and cost. Inspect metadata/state/age only
under explicitly authorized storage access; do not list/download content for routine
logs or evidence. Container metadata/version policy review and an age/backlog
dashboard are rollout prerequisites; this implementation supplies reason logs,
not a deployed dashboard or global oldest-age aggregation.

For permanent rejection, correct routing/auth/schema under separate approval.
For ambiguity, retain state and reconcile exact destination identities/receipt
evidence before deciding whether a resend risks duplicates. There is intentionally
no blind CLI “retry ambiguous” command. A targeted recovery release/change needs
explicit authorization and immutable-byte/hash checks. No edit/delete/replay of
quarantined payloads is automatic or justified by an empty destination query.

## Offline verification

From repository root:

```powershell
python -m pip install -e ".\src\telemetry-pipeline[test]"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONPATH = (Resolve-Path .\src\telemetry-pipeline).Path
python -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests tests\telemetry-mapping tests\export\test_otlp_export_conformance.py
az bicep build --file infra\main.bicep --stdout | Out-Null
az bicep build --file infra\modules\function-app.bicep --stdout | Out-Null
```

Package test dependencies include the optional durable dependencies; the production
requirements also include them. Base installs can select `[durable]` explicitly.
Tests use synthetic messages, clocks, single-attempt transport outcomes, real OTLP
protobuf encoding, and the real Blob adapter against a conditional fake client.
The bounded-download regression also exercises the real Blob SDK's range and
conditional-ETag request construction through a blocked HTTP transport. A length
requires explicit `offset=0`; omitting it fails SDK validation before HTTP.
They cover batch/order/restart/races, precedence/isolation/conflict, receipt clocks,
cleanup/tombstones, immutable retries/stale-claim ambiguity, atomic admission,
capacity limits, scan cursor fairness and compiled infrastructure restrictions.
No Azure/Arize service calls, real settings reads, cloud what-if or live delivery
validation are part of that evidence. Infrastructure contract tests skip if Azure
CLI is absent; local compilation must still be run before release.

Preparation verification on 2026-10-19: the exact pytest command above **passed
232 tests** (17.98s); both Bicep compile commands **passed**. The main-template
compile reports pre-existing nullable-resource warnings BCP318 in
`app-insights.bicep:165`, BCP422 in `event-hub.bicep:207`, and BCP318 in
`event-hub.bicep:231`; the Function module compile adds no warning.
`.\infra\scripts\validate-naming.ps1` **passed for six modules**.
That initial preparation included no cloud what-if/deployment or live delivery
validation. Subsequent scoped ARM validation, what-if and deployment succeeded;
positive durable-path delivery acceptance remains a separate release gate.
