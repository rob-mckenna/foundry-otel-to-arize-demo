# Native telemetry mapping and export contract

**CURRENT-STATE implementation; offline preparation, NOT E2E VALIDATED (2026-10-16).**

## Provenance and evidence limits

**Inline GenAI message enhancement (2026-10-16): local implementation only, not
published or live-validated.** The provenance below describes the baseline package,
not parity of the enhanced mapper with any active Function package. Offline tests
prove the enhanced mapping and protobuf encoding, not Arize UI rendering/acceptance.

The baseline changeset starts at remote main
`beb3944afd9aba93d1eed7c06fcc4ec1e8d41c69`, not the unpublished local-main stack.
It extracts the Function trigger repair from `34d844c` and exporter/Function
failure handling plus regression tests from `f65384f`, excluding their surrounding
infrastructure and operational instructions.

The baseline native mapper and batch decoder reconciled to the immutable approved source ZIP
SHA-256 `023127d9edc7ad3751a17576d1d8b6d849826d74bbd6ddb4f36fb6df8b882e5d`.
All eight original source members matched the package and retained publication
reconciliation proof. Four members have no semantic change from remote main
(root entrypoint, host configuration, requirements, and package initializer).
The baseline implementation changes were confined to mapping, batch decoding,
exporter, and Function entrypoint modules. The inline message bridge is a later,
local-only mapper change, excluded from that publication receipt.

Deployment `c06afa7a-3065-4659-afa9-67137f64b6d5` was reconciled active with
eight-source parity using an **explicit user-approved package-only exception**.
Generic official validation was **not completed**. The retained native preflight,
publication, source capture, OTLP acknowledgment, and independent Arize parity
are separate gates. Publication established no fresh delivery/acknowledgment;
independent destination graph, field, and token parity remains **UNKNOWN**.
Local protobuf tests prove encoding only, not service acceptance.

## Source-field contract

Only span rows (`AppDependencies` and `AppRequests`, plus existing legacy rows)
are accepted. AppTraces and AppExceptions are not reconstructed as spans/events.
Native/legacy aliases must agree when both appear; conflicts reject the row.
Inputs are copied, not mutated.

| Source | Destination and validation |
|---|---|
| `OperationId` / `operation_Id` | Nonzero 32-hex OTLP trace ID, preserved |
| `Id` / `id` | Nonzero 16-hex span ID; strict `\|trace.span.` wrappers unwrap only if the embedded trace matches |
| `ParentId` / `operation_ParentId` | Real 16-hex or strict same-trace wrapped parent preserved; null/empty/missing parent omitted |
| Native `AppDependencies` `ParentId == OperationId` | Observed trace-ID root marker omitted only for this exact native shape; mismatching markers, legacy-only markers, and AppRequests markers reject |
| `Properties` / `customDimensions` | Object or JSON-encoded object; non-object JSON rejects |
| `TimeGenerated` / `timestamp` | Epoch nanoseconds; ISO fractions retained through nine digits, naive ISO interpreted as UTC |
| `DurationMs` / `duration` | Finite nonnegative milliseconds added to supplied start; supplied invalid/out-of-range times reject; no invocation-time fabrication |
| `AppRoleName`, `AppRoleInstance` / legacy role fields | Resource `service.name`, `service.instance.id`; SDK resource detection retains configured `OTEL_RESOURCE_ATTRIBUTES` |
| `Name`, `Success` | Span name and best-effort OK/ERROR status; not recovery of original OTel status |
| `correlation.id`, `input.value`, `output.value`, `llm.model_name` | String passthrough only where present; invalid types reject |
| `input.mime_type`, `output.mime_type` | String passthrough alongside the corresponding explicit value; orphan MIME omitted |
| Inline `gen_ai.input.messages`, `gen_ai.output.messages` in `Properties` / `customDimensions` | JSON string or native array of role/parts messages → corresponding missing `input.value` / `output.value` JSON string and `application/json` MIME |
| `llm.token_count.prompt`, `.completion`, `.total` | Nonnegative int64, including zero; no derived total or copied non-LLM usage |
| `gen_ai.usage.input_tokens`, `.output_tokens` | Typed original attributes plus prompt/completion OpenInference aliases; disagreement with explicit usage rejects |
| `gen_ai.response.model`, `gen_ai.request.model` | Preserve both; response then request fallback for missing `llm.model_name` |
| `gen_ai.operation.name` | Preserve; `chat` / `invoke_agent` bridge missing OpenInference kind to LLM / AGENT |
| `gen_ai.response.id`, `.conversation.id`, `.provider.name` | String metadata preserved when present; no invented join keys |

Explicit OpenInference model/kind values remain authoritative. Core span kind
is best effort (native requests are SERVER); missing original status/kind,
exception events, links, upstream parents, correlation, content, and total usage
cannot be recreated unless the corresponding supported source fields are present.

### Inline GenAI message content

Each message must be an object with a nonempty string `role` and a `parts` array.
Each part must be an object with a nonempty string `type`; nested content and
additional JSON fields are preserved unchanged, not flattened or converted to
another message schema. For example, synthetic
`[{"role":"user","parts":[{"type":"text","content":"Synthetic coverage question"}]}]`
becomes the JSON-string `input.value` with `input.mime_type=application/json`.
Empty message arrays (and empty parts arrays) are valid JSON content.

Precedence is independent for input and output. An explicit OpenInference value,
including an empty string, wins and retains its matching explicit MIME when supplied;
the overridden GenAI source is not parsed. If no explicit value exists, a stale
MIME is replaced with `application/json` on successful conversion, or omitted if
there is no valid content. No MIME is invented for explicit values lacking MIME.

Missing message attributes produce no I/O. Malformed JSON, non-message shapes,
or non-JSON nested content omit only that side's generated value/MIME, not the span
or neighboring records. Warnings contain only the source attribute key and a
fixed reason, never raw message bodies or parser exception text. Operators should
investigate these warnings upstream. Existing raw GenAI message attributes remain
unexported; this bridge adds only OpenInference value/MIME attributes.

No new mapper size cap or truncation is introduced: upstream truncation may make
JSON invalid, in which case conversion is omitted rather than emitting broken JSON.
Only inline content on the original span is mapped. There are no AppGenAIContent
exports/joins, indexed `llm.input_messages` attributes, separate developer-message
or tool-definition exports, child-to-parent copies, or restored absent roots.
No source content-recording settings, model calls, deployment, or UI customization
are part of this enhancement.

## Batch, trigger, export, and recovery

The decoder accepts a single object, array, or `{"records": [...]}` compatibility
wrapper. This is not proof of the workspace's actual Event Hub wire envelope.
Malformed rows, invalid UTF-8, and malformed wrappers are observable skips;
valid neighbors export together once. Partial skips can leave graph gaps.
Operators must investigate skip warnings; skipped malformed records do not
cause host retries. An empty/all-malformed batch does not call the exporter.

The many-event trigger uses worker-compatible `typing.List[EventHubEvent]`.
`EVENT_HUB_NAME` defaults to `telemetry`; the identity binding prefix defaults
to `EventHubConnection`. The consumer-group fallback remains `$Default`.
Commit `65cb957`'s explicit hub/consumer-group settings are **HELD** because
they require infrastructure changes. This changeset does not provision a group,
wire settings, or change networking: an independently reviewed deployment must
explicitly select the provisioned hub/group (normally `function-transform`).
Do not infer that remote-main infrastructure is reconciled by this source patch.

The HTTP exporter requires an HTTPS trace URL ending in `/v1/traces`.
Actual Space ID and matching key remain Key Vault-managed configuration;
no diagnostics may print credentials. Project routing uses the SDK resource
detector (`OTEL_RESOURCE_ATTRIBUTES`), not a new span attribute. This changeset
does not add the infrastructure routing settings from `f65384f`.

Function logs distinguish mapped/exported/failed/skipped counts and
`success`, `failure`, or `no_export`. Only exporter SUCCESS counts as exported;
console fallback success is not Arize ingestion. Export FAILURE raises, and
the owned exporter always shuts down without masking a primary failure.
The host policy requests three exponential retries after the initial attempt,
5 seconds to 1 minute; SDK network retries remain separate. Host retry counts
are best effort across restarts, and checkpoints can advance after exhaustion.
Whole-batch retry can duplicate accepted identities; destination deduplication
and count parity must not be assumed.

Persistent auth/routing/endpoint failures require operator correction; malformed
rows require source/schema investigation. Preserve affected synthetic IDs and
partition/sequence evidence. Recovery needs a separate explicitly approved plan:
do not delete checkpoints, replay events, or infer another invocation allowance
from this documentation.

## Offline checks

From repository root in the isolated candidate:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONPATH = (Resolve-Path .\src\telemetry-pipeline).Path
python -m pytest -q -p no:cacheprovider src\telemetry-pipeline\tests tests\telemetry-mapping tests\export\test_otlp_export_conformance.py
```

The existing pytest runner covers legacy and native mapping, Function decorator
metadata/failure cleanup, and real protobuf graph/token/resource encoding using
synthetic inputs. No runtime receipts or live services are test prerequisites.
No separate linter/type checker is configured for this package.

## Work explicitly held

Infrastructure/settings/routing, casting/framework migration, Prompt Agent,
evaluation, release tooling, content joins beyond the inline bridge, and unrelated dirty
documentation are excluded. Issue #139 is QA-approved locally **not deployed**.
Runtime submissions remain **CLOSED 3/3**; both historical creation intents are
consumed, only v1 accepted. Evaluation pending-upload HTTP 403 remains
**PARTIAL_OR_UNKNOWN_DO_NOT_RETRY**; a dataset GET 404 does not clear that state.
No deployment, replay, model, registration, evaluation, permissions, or
networking operation is authorized by this preparation.
