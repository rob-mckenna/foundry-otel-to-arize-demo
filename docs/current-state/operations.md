# Operations and recovery

**One durable path; synthetic data only.** Configuration and recovery require separately
approved scope. These notes do not authorize enabling triggers, deployment, replay,
new permissions, resource deletion or another model invocation.

## Runtime configuration

Review the [identity wiring](../../src/telemetry-pipeline/telemetry_pipeline/durable_runtime.py)
and [Function entrypoint](../../src/telemetry-pipeline/telemetry_pipeline/function_app.py).
Use placeholders when documenting configuration; never dump settings or secret values.

| Setting / resource | Contract |
| --- | --- |
| `DURABLE_ALLOWED_WORKSPACE_ID` | Exact agent workspace UUID. |
| `DURABLE_ALLOWED_COMPONENT_RESOURCE_ID` | Exact allowed agent Application Insights component ARM ID. |
| `DURABLE_ARIZE_PROJECT` | Approved destination project; frozen into the OTLP resource. |
| `ARIZE_OTLP_ENDPOINT` | HTTPS trace endpoint ending in `/v1/traces`. |
| `ARIZE_SPACE_ID`, `ARIZE_API_KEY` | Matching destination routing/authentication; secret material stays Key Vault-resolved. |
| `AzureWebJobsStorage__blobServiceUri` or `AzureWebJobsStorage__accountName` | Identity-based existing host storage; public-Azure Blob hostname with private DNS routing where needed. No connection-string/SAS/Azurite alternative. |
| `genai-correlation` | Existing private Blob container, separate from host checkpoint blobs; system-assigned Function identity needs approved data and index-tag permissions. |
| `EVENT_HUB_NAME`, `EVENT_HUB_CONSUMER_GROUP`, `EVENT_HUB_CONNECTION_SETTING_PREFIX` | Exact existing hub/group and identity-binding prefix; preserve checkpoints and provisioned names. The matching prefix uses `__fullyQualifiedNamespace` / `__credential` settings, not a connection string. |
| Function monitoring | Key Vault-resolved health connection pointing to the separate **non-exported** health workspace, not the agent workspace. |
| `PIPELINE_EXCLUDED_SERVICE_NAMES` | Optional JSON array of exact source service roles; case-sensitive; default `[]`. |
| `PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS` | Optional JSON array of exact component ARM IDs; case-insensitive; default `[]`. |

Malformed source-policy settings fail explicitly. Exclusions are not operation-name
filters, mapped fallback-service filters or whole-trace drops. Do not exclude the
shared agent component just to remove Function health. Eligible tool/HTTP/non-LLM
children remain part of the preview. Source isolation is the primary feedback defense;
the guard cannot retract previously delivered spans or identify absent roles.

## Admission and delivery

`TelemetryTransform` commits admitted records before returning; it does not send OTLP
or sleep while waiting for content. `DurableGenAIOutbox` runs every 30 seconds with
bounded due-entry scans and send budgets. Conditional Blob creates/ETag replacements
serialize ownership; persisted frozen bytes cannot change after claim.

| Outcome | State / operator meaning |
| --- | --- |
| Valid OTLP HTTP 200 response with no rejection/error | `acknowledged`; content-bearing active document replaced by a content-free tombstone. |
| Explicit HTTP 429 | Retry the identical bytes, at most five total attempts; backoff 30/60/120/240 seconds, then retained `rejected`. |
| HTTP 400/401/403/404/405/413/415 | `rejected`; correct the cause under approved scope, no automatic resend. |
| Timeout, connection error, 5xx, redirect, unexpected/malformed/oversized or partial-success response | `ambiguous`; acceptance may already have happened, so **no automatic resend**. |
| `sending` claim older than 120 seconds / uncertain acknowledgment write | Reconcile conservatively; stale sends become `ambiguous`, not ready-to-retry. |
| Storage/admission/bound failure | Invocation fails with backpressure; restore capacity/access and inspect content-free failure reasons. |

Protocol acknowledgment is not independent proof of Arize field fidelity. A bounded
destination query returning no record is not definitive proof of nonacceptance.
Existing ambiguous operational delivery must remain quarantined; do not blindly resend.

Finite host retries remain a limitation: after exhaustion, Event Hub checkpoints can
advance even for never-admitted events. The ledger cannot recover records it never
received. Preserve approved partition/sequence/identity evidence and obtain explicit
recovery authorization; neither automatic losslessness nor exactly-once delivery is promised.

## Retention and bounds

- Content-only orphans expire after **24 hours** from first receipt and never create spans.
- Acknowledged and policy-excluded identities retain content-free tombstones for
  **48 hours**, then expire. Exclusion is not a delivery acknowledgment.
  Verify that upstream retention/replay horizons fit this finite deduplication window.
- Unsent, ambiguous and rejected evidence can remain indefinitely. Do not apply
  unconditional lifecycle deletion to the container or delete it as a rollback shortcut.
- Active-payload deletion does not purge snapshots, versions, soft-delete or backups.
  Approve those storage-retention policies before admitting content.
- Local bounds include 1 MiB/event, 128 KiB/source record, four candidates/side,
  1 MiB/ledger document, 256 KiB/frozen OTLP request and 64 KiB/HTTP response.
  Timer work is bounded to 16 entries/four HTTP attempts per pass.
  These are sample safety limits, not vendor guarantees or throughput commitments.

## Minimal operator checks

1. **Before enabling:** verify exact source/destination, all three export tables, MI
   permissions including Blob index write/filter, private connectivity, synthetic
   content approval, storage retention and a reviewed cutover boundary.
   Do not run parallel consumers that export the same originals.
2. **During observation:** inspect safe admission/reason/state counts, oldest pending
   age, timer progress, index-query lag, throttling, quarantine count and storage cost.
   Avoid raw content, parser/SDK dumps, full settings or credentials.
3. **If Arize is empty:** distinguish no source original, delayed native export,
   rejected admission, pending join, storage failure and quarantined delivery.
   A successful caller or healthy Function host alone does not prove export.
4. **If enrichment is missing:** compare supported field shape and exact join keys,
   parent assertion, side precedence/conflicts and first-admission deadline.
   Do not move child content onto a parent or fabricate missing fields.
5. **Before recovery:** preserve checkpoints, ledger namespace, frozen bytes and
   ambiguous/rejected history. No reset, import, replay or blanket deletion without
   separate reconciliation and approval.

Offline suites in [setup](setup.md) exercise synthetic mapping and delivery behavior.
Live resource acceptance, native transport and independent Arize comparison are separate
checks; physical health isolation does not mean the latest source guard is deployed.
