# ADR-0003: Opt-in durable GenAI content correlation before OTLP delivery

## Status

**Accepted operating policy, 2026-10-19; separately approved scoped rollout.**
Rob McKenna approved “Go with the recommendations”; numeric defaults are recorded
in [#143 approval comment](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/143#issuecomment-6263046439).
The later [rollout approval/progress record](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/143#issuecomment-6268074540)
records explicit requester approval of the bounded cloud, retention and migration
scope below, separately from acceptance of the architecture.
**Source and four-resource scoped infrastructure deployed; durable admission
ENABLED; native content transport verified; live fallback acceptance PENDING.**
Corrected source `f650fed983a687eb97211b634af3d99e7286d6e1` is deployed,
the 35-identity ACK migration is verified and both temporary VM grants are removed.
After actual outbox readiness, incoming processing resumed at `13:52:44Z`.
One native synthetic call verified independent content arrival and unchanged full
inline delivery to Arize, but did not exercise content fallback. The
[durable runbook](../current-state/durable-genai-correlation.md) records precise
evidence and remaining limits. These are coordinator-reconciled rollout facts,
not Lead live verification. Issue #143 remains open. This ADR records existing approval;
it does not itself grant new authority or waive acceptance gates.

## Context

The working inline bridge cannot correlate independently arriving `AppGenAIContent`
across Function batches, partitions, restarts or instances. The original
`AppDependencies`/`AppRequests` row is the only source of span identity, timing,
parent, status, tokens and resource metadata. Content rows are not spans.

The bounded synthetic same-ID OTLP investigation observed separate destination
records, not merging. Therefore baseline export followed by enriched retransmission
is not a supported solution. Exactly-once acceptance cannot be established across
the storage/receiver transaction boundary.

## Decision

Keep the existing architecture and inline-only path unchanged by default. Under
explicit `DURABLE_GENAI_ENABLED=true`, admit records to a private application Blob
container in existing Function storage before Event Hub checkpoint success.
Use managed identity and conditional ETags for atomic admission and send claims.
Atomic uploads maintain content-free due-work Blob index tags, preventing retained
tombstones from delaying pending work. Verify eventual index visibility and exact
tag-write/filter permissions separately; no extra grant is silently introduced.
Select native `AppGenAIContent` export through the existing Application Insights /
Log Analytics → Event Hub → Function route, with no query fallback. No Durable Task
orchestration or new storage account is introduced. Runtime introduces no grant;
the separately approved additive index permissions are bounded below.
A bounded timer handles joining and sending; the trigger never waits.

Wait up to 300 seconds from the first durable **original** admission for missing
input/output of relevant GenAI/LLM/agent spans. Duplicates do not reset the deadline.
Complete I/O and non-GenAI spans need not wait for that deadline. Per-side precedence
is explicit OpenInference (including empty strings), then valid inline role/parts
messages, then a unique valid content-table candidate. Reuse the existing validator.
Do not attach conflicting or mismatched-parent/provenance content, invent fields,
or emit content-only spans. At deadline, finalize the original with valid available
enrichment. Timer/scan latency is additional to the join interval.

Namespace state by allowed workspace/component, destination project/endpoint/space,
and validated original trace/span IDs. Ignore content `Id` as an identity source.
Freeze actual protobuf request bytes before sending. Late arrivals cannot change
those bytes or cause another export. On a confirmed OTLP success, replace the
content-bearing ledger with a content-free acknowledged tombstone for 48h.
Content-only orphans are deleted observably at 24h, subject to bounded scan latency.
The accepted replay budget uses actual Event Hub retention of 24h, upstream export
retry of 12h and at most 6h additional recovery: 42h, leaving 6h nominal margin
within the 48h ACK window. Longer replays require reconciliation, not an assumption
of deduplication after expiry. Source template retention alone is not live evidence.
Logical deletion of the active Blob payload and existing 90-day LAW retention are
accepted; this is not certified physical purge of versions, snapshots, soft-deleted
data or backups. Do not disable account protections.

**Selected implementation policy: conservative ambiguous-send quarantine.** Use a
single-attempt HTTP sender rather than the retrying OTLP exporter SDK in this mode.
Timeouts, connection errors, unexpected responses, partial success, stale sending
claims, and uncertain acknowledgment remain ambiguous; retain frozen content for
operator reconciliation without automatic resend. Explicit throttling rejection
may retry with bounded exponential backoff; definitive permanent rejection and
retry exhaustion enter retained recovery state. Unsent/recovery work never expires
automatically. This trades automatic delivery completion for reduced duplicate risk;
it is neither an Arize idempotency guarantee nor lossless/exactly-once delivery.

Protective application bounds, states, response classifications, recovery and
rollout gates are specified in the [durable runbook](../current-state/durable-genai-correlation.md).
Bounds fail with backpressure rather than silent truncation or original-span drop.

### Separately approved scoped rollout authority

The requester approved a bounded rollout in the existing pipeline, not general
cloud authority. The four writable resources in the scoped template have been
deployed: the private `genai-correlation` container in existing Function storage,
the custom two-action index role, its container-scoped Function MI assignment,
and the existing LAW export-rule update adding `AppGenAIContent`. Preserve that
rule's identity, destination and existing tables. Retain existing Function MI
Blob/Queue/Table grants; the additive role contains only
`Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write`
and `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action`,
assigned at the new container. No broad baseline deployment or unrelated IAM/auth
change is authorized.

Approved execution also covers reviewed Function-source publication and exact
source/destination configuration, with activation gated on actual active-source,
host readiness, receipt and effective-permission proof. Up to three synthetic
invocations of the named existing agent are approved, plus temporary start of the
existing private validation VM followed by restoration to its deallocated state.
Approval is not evidence that these calls or live acceptance have occurred.

The separately approved first-cutover migration is ACK-only: with incoming events
paused and existing consumer group/checkpoints preserved, use the complete bounded
snapshot of 35 confirmed Arize trace/span identities. Create only indexed,
content-free `acknowledged` records with 48h expiry in the **actual runtime
namespace**. Verify snapshot completeness, every receipt and the complete due-index
identity set before activation. Do not overwrite pending work; existing work,
incomplete evidence or ambiguous import requires reconciliation, not a blind rerun.
No historical span replay, prompt/response import or fabricated ACK is approved.

For that migration only, the VM is approved temporary Blob Data Contributor and
the same two-action index role, both scoped solely to `genai-correlation`.
Remove **both temporary assignments before new traffic**. No credential forwarding,
checkpoint-container access, Event Hub receiver grant or permanent operator access
is authorized. Failure to prove the safe cutover boundary is a stop, not authority
to widen access or change the architecture.

## Consequences

- **Current-state impact:** optional enhancement inside Foundry → Application Insights /
  Log Analytics → Event Hub → Function → Arize. Feature-off batching, exporter retries,
  console fallback and checkpoint semantics remain unchanged. Deployment is not
  proof that durable admission or native content fallback is active.
- **Future-state impact:** None. No direct Foundry-to-Arize implementation.
- **Security considerations:** content-bearing state is a new protected surface in
  an existing account, with account-level grants still requiring scoped review.
  Only synthetic content; Key Vault-managed Arize credentials; managed-identity Blob
  auth. Verify encryption, network access, version/snapshot/soft-delete retention,
  and deletion behavior within the accepted logical-deletion boundary. Never apply
  account/container lifecycle TTL to unsent or ambiguous work. Container preparation
  alone adds no RBAC; only the separate scoped approvals above cover added grants.
- **Observability considerations:** fixed reason/count logs plus hashed ledger IDs,
  never raw content or SDK/parser exception dumps. Original trace/span/parent,
  correlation and typed token fields are preserved, not inferred. A confirmed
  HTTP OTLP acknowledgment still is not independent destination field-parity proof.
- **Implementation trade-offs requiring rollout review:** added join/scan latency;
  unknown deliveries can remain
  quarantined indefinitely; payload-bearing recovery requires operators and cost
  monitoring. Finite host retry exhaustion can still advance Event Hub checkpoints
  after an admission failure; durable storage cannot recover never-admitted events.
- **Remaining acceptance gates:** active source, actual host readiness, ACK-only
  migration, grant removal and activation are verified. Native content transport
  and unchanged inline I/O have independent source/Arize evidence, but the first
  call retained valid inline input/output and therefore did not exercise fallback.
  Prove fallback selection and destination fidelity within the observable fields;
  retain explicit limits for missing source parents/correlation/totals and unexposed
  resources, capacity/timer lag and ambiguous-send reconciliation. The coordinator owns final
  positive evidence in the durable runbook; offline tests, CI and ARM deployment do
  not establish it. These gates do not authorize query fallback, historical replay,
  broader grants or calls beyond the approved synthetic budget.
