# Mapping and limitations

**Current-state contract for the durable Event Hub → Function → Arize bridge.**
This is per-span reconstruction from Azure Monitor fields, not recovery of every
original OpenTelemetry feature. See the [mapper](../../src/telemetry-pipeline/telemetry_pipeline/mapping.py)
and [correlator](../../src/telemetry-pipeline/telemetry_pipeline/durable.py).

## Fields carried into OTLP

| Source | Destination / rule |
| --- | --- |
| `OperationId` / `operation_Id` | Nonzero 32-hex trace ID, preserved. |
| `Id` / `id` | Nonzero 16-hex span ID. Strict wrapped IDs require the same embedded trace. |
| `ParentId` / `operation_ParentId` | Valid parent preserved; absent/empty root parent omitted, not replaced with zeros. Native AppDependencies' exact trace-ID root marker is handled specially. |
| `TimeGenerated` / `timestamp`, `DurationMs` / `duration` | Start/end nanoseconds; ISO fractions retained through nine digits; invalid timing is not replaced with invocation time. |
| `Name`, `Success` | Operation name and best-effort status; native AppRequests maps to SERVER. |
| `AppRoleName`, `AppRoleInstance` / legacy equivalents | Resource service name/instance; this does not restore a complete original resource block. |
| `Properties` / `customDimensions` | Native object or JSON object; supported attributes only, not arbitrary property copying. |
| `correlation.id` | String preserved if present; never inferred from trace ID or response ID. |
| `llm.model_name`, `gen_ai.response.model`, `gen_ai.request.model` | Explicit OpenInference model wins; response then request model fills a missing model. |
| `openinference.span.kind`, `gen_ai.operation.name` | Explicit kind wins; `chat` / `invoke_agent` can supply LLM / AGENT. Names alone do not classify spans. |
| `llm.token_count.prompt`, `.completion`, `.total` | Nonnegative int64, including zero. Totals are **not derived**. |
| `gen_ai.usage.input_tokens`, `.output_tokens` | Preserved and aliased to prompt/completion; disagreement with explicit usage rejects the original. |
| Supported GenAI response/conversation/provider metadata | Preserved where supplied; never invented join keys. |

Native/legacy aliases must agree when both occur. Malformed identities, conflicting
aliases or invalid authoritative values are not repaired by guessing. Missing parent,
status detail, exception events, links, source correlation, tokens or resources cannot
be recreated merely because a destination trace appears connected.

## Content joining

Only AppRequests/AppDependencies originals create spans. `AppGenAIContent` rows
supply content candidates, never standalone spans. The durable join is scoped to
the exact workspace, component and destination plus **trace ID + span ID**.
The recorded exact Agent version identifies the invocation target; the bridge's
source allowlist filters workspace/component, **not individual Agent versions**.
Content `Id` is not a span ID. A supplied content parent must match the original;
content does not override parent, timing, model, status or usage.

For each input/output side independently:

1. Explicit OpenInference `input.value` / `output.value` wins, including `""`.
2. Otherwise valid inline `gen_ai.input.messages` / `gen_ai.output.messages` wins.
3. Otherwise a unique valid content-table `InputMessages` / `OutputMessages` array fills it.

Messages require a nonempty role and a parts array; parts require a nonempty type.
Message/part order and nested JSON are preserved. Converted values are JSON strings
with `application/json` MIME. Empty arrays count as present. Invalid inline content
can fall back to content-table data; malformed content omits the affected side,
not a fabricated replacement. Identical candidates are idempotent; distinct valid
candidates conflict and are not concatenated or chosen by arrival order.

LLM/AGENT or nonempty `gen_ai.operation.name` originals can wait up to **300 seconds
from first durable original admission**. Content-first arrival does not start the
clock; duplicates do not reset it. Both sides present allows early finalization.
Ordinary eligible non-LLM spans do not wait. At deadline the original sends with
whatever valid content is available; an unresolved conflicted side is omitted.
Timer cadence, index visibility and backlog add latency, so 300 seconds is not an SLA.
Late content does not trigger an update or resend of an exported span.

## Evidence: what the preview can claim

| Observation | Scope / limitation |
| --- | --- |
| A real synthetic versioned Agent invocation reached Arize with native AGENT/LLM input/output and actual prompt/completion counts. | Valid full inline JSON won precedence; this did not demonstrate native missing-inline fallback. |
| Native AppGenAIContent rows crossed the export route alongside the originals. | Transport is observed separately from use of those rows for enrichment. All three required tables are exported. |
| Controlled generated originals lacking inline content were followed by matching content fixtures in separate Event Hub invocations; Arize had the expected joined JSON. | Demonstrates deployed missing-inline join behavior, **not native Foundry missing-inline capture**. Fixture tokens are invented, not model usage. |
| Function health moved to dedicated non-exported Azure Monitor resources, with bounded passive observation. | Does not prove all-table/permanent absence of feedback. Extra source/backlog exclusion code is offline-tested, not deployed evidence. |

These observations concern the previously deployed existing demo, not live acceptance
of every change in this simplified source. Detailed earlier evidence is preserved at
Git tag `minimal-preview-baseline-20261021`; deployment-specific IDs and raw payloads
are intentionally absent here.

## Actionable boundaries

- **Incomplete graph:** an upstream parent was unobserved in bounded source/destination
  results. Do not label this demonstrated export loss or claim a complete trace;
  compare actual source originals before diagnosing.
- **Correlation and token provenance:** native source `correlation.id` and source total
  usage were absent in that observation. The caller's request UUID and actual response
  total do not prove native span fields existed. Arize's arithmetic total is not
  source-total preservation.
- **Resources:** bounded destination readback did not expose a full OTLP resource block.
  Do not claim full resource parity from matching spans or model fields.
- **Delivery:** joins and observed duplicate suppression are not an exactly-once
  guarantee. Finite host retries can advance checkpoints after never-admitted events;
  network uncertainty can leave delivery quarantined. See [operations](operations.md).
- **Deployment:** fresh/repeat composition deployment, private Agent runtime and full
  end-to-end validation remain unverified. Use the existing-resource prerequisites,
  not a fresh-foundation promise.
