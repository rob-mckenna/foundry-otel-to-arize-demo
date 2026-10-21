# Telemetry pipeline

**CURRENT-STATE source; this simplification has not been deployed or live-validated.**
Only synthetic data is supported. Full same-invocation graph/field/token parity
in Arize remains unproven; no whole-trace or exactly-once guarantee is made.

One runtime path:

`AppRequests + AppDependencies + AppGenAIContent → Event Hub → TelemetryTransform
→ Blob correlation ledger → DurableGenAIOutbox → StrictSender → Arize OTLP`

`TelemetryTransform` returns after durable admission, not destination delivery.
Admission errors propagate for three bounded exponential host retries (5–60s).
Checkpoints can advance after exhaustion; persistent failures need operator recovery.
`DurableGenAIOutbox` runs every 30 seconds (`*/30 * * * * *`), never on startup.
Both functions require valid live source/destination and managed-identity storage
configuration. There is no runtime mode selector, immediate exporter, or console
fallback; obsolete `DURABLE_GENAI_ENABLED` values have no effect.

## Settings contract

Secrets must be Key Vault references, never source/local committed values.

| Setting | Required / default | Meaning |
|---|---|---|
| `DURABLE_ALLOWED_WORKSPACE_ID` | Required | Source workspace UUID (`TenantId` in rows), not its ARM resource ID |
| `DURABLE_ALLOWED_COMPONENT_RESOURCE_ID` | Required | Source agent Application Insights component ARM ID |
| `DURABLE_ARIZE_PROJECT` | Required | Explicit `openinference.project.name` destination |
| `ARIZE_OTLP_ENDPOINT` | Required, Key Vault reference | Full HTTPS trace URL ending `/v1/traces`; no userinfo/query/fragment |
| `ARIZE_SPACE_ID` | Required, Key Vault reference | Actual destination Space ID |
| `ARIZE_API_KEY` | Required, Key Vault reference | Arize credential; no managed-identity alternative |
| `AzureWebJobsStorage__blobServiceUri` | Required unless account name supplied | HTTPS public-Azure Blob URI (private routing may resolve the same hostname) |
| `AzureWebJobsStorage__accountName` | Alternative to Blob URI | Storage account name; derives `https://<account>.blob.core.windows.net` |
| `AzureWebJobsStorage__credential` | Host identity configuration: `managedidentity` | Keyless Functions host storage; ledger uses system-assigned managed identity |
| `EVENT_HUB_CONNECTION_SETTING_PREFIX` | `EventHubConnection` | Identity-based binding setting prefix |
| `<prefix>__fullyQualifiedNamespace` | Required by Functions host | Event Hub namespace FQDN |
| `<prefix>__credential` | `managedidentity` in infrastructure | System-assigned Event Hub receiver identity |
| `EVENT_HUB_NAME` | `telemetry` | Event Hub name |
| `EVENT_HUB_CONSUMER_GROUP` | `$Default` | Consumer group |
| `PIPELINE_EXCLUDED_SERVICE_NAMES` | `[]` | JSON array of exact, case-sensitive source roles |
| `PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS` | `[]` | JSON array of exact, case-insensitive component ARM IDs |
| `AzureWebJobs.TelemetryTransform.Disabled` | Host switch | Infra preparation keeps `true` |
| `AzureWebJobs.DurableGenAIOutbox.Disabled` | Host switch | Infra preparation keeps `true` |

The private `genai-correlation` container must already exist. Identity needs
conditional Blob read/write/delete and Blob tag write/filter access; host storage,
Event Hub receiver and Key Vault resolution permissions are separate prerequisites.
Health monitoring must use its physically separate Application Insights/workspace,
not the exported agent component. SourcePolicy guard source is merged but **not
deployed**; separate health monitoring is live. Publication does not enable triggers.

## Retained semantics and limits

- Original trace/span/parent IDs, timing, status, model, available source correlation,
  and available token counts are preserved by `mapping.py`; missing facts are not invented.
- Each side independently prefers explicit OpenInference I/O, then inline GenAI
  messages, then unique eligible content-table messages. No child content is copied
  to parents. Incomplete GenAI originals wait up to 300s from durable receipt;
  complete inline and non-GenAI originals need no content wait.
- `durable.py` / `durable_store.py` retain source/destination scoping, conditional
  writes, duplicate suppression, receipt deadlines, frozen payloads, bounded scans
  (16 entries, at most 4 sends/drain), 8 CAS attempts, and per-side candidate cap 4.
  Bounds: 1 MiB/message, 256 records/message, 1024 records/batch, 128 KiB/record,
  256 KiB OTLP payload, bounded ledger reads.
- `strict_sender.py` performs one HTTP attempt. Only explicit 429 rejection gets
  bounded retry (at most 5 attempts). Ambiguous delivery, including uncertain ack,
  is quarantined, never automatically resent. Orphans expire after 24h;
  acknowledged/excluded content-free tombstones remain 48h. No automatic recovery
  of quarantined/rejected work or exactly-once destination claim.
- `envelope.py` reuses the former batch parser: single row, array, or synthetic
  compatibility `{"records": [...]}` wrapper. Invalid admission is an explicit
  failure, not a success-shaped skipped/exported count.

## Offline validation (repository root, PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".\src\telemetry-pipeline[test]"
.\.venv\Scripts\python.exe -m pytest src\telemetry-pipeline\tests tests\telemetry-mapping tests\export -q
```

`opentelemetry-exporter-otlp-proto-common` supplies protobuf encoding, **not**
the SDK's retrying HTTP exporter; no `otlp` or `durable` install extra is needed.
Tests use synthetic records, fake Blob responses and injected connections only.
See [setup](../../docs/current-state/setup.md),
[mapping and limitations](../../docs/current-state/mapping-and-limitations.md),
and [operations](../../docs/current-state/operations.md).
