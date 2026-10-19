# ADR-0003: Opt-in durable GenAI content correlation before OTLP delivery

## Status

Accepted operating policy for implementation preparation, 2026-10-19.
Rob McKenna approved “Go with the recommendations”; numeric defaults are recorded
in [#143 approval comment](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/143#issuecomment-6263046439).
**Implementation prepared and offline-tested; NOT DEPLOYED; live acceptance remains open.**
Issue #143 is not closed by this ADR. This decision does not authorize cloud changes.

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
No Durable Task orchestration, query fallback, new storage account, or new grant
is introduced. A bounded timer handles joining and sending; the trigger never waits.

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
content-bearing ledger with a content-free acknowledged tombstone, initially 48h.
Content-only orphans are deleted observably at 24h, subject to bounded scan latency.
Verify the real upstream/Event Hub/recovery replay horizon before enabling the 48h
setting; source template retention is not live-state evidence.

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

## Consequences

- **Current-state impact:** optional enhancement inside Foundry → Application Insights /
  Log Analytics → Event Hub → Function → Arize. Feature-off batching, exporter retries,
  console fallback and checkpoint semantics remain unchanged. No new live claim.
- **Future-state impact:** None. No direct Foundry-to-Arize implementation.
- **Security considerations:** content-bearing state is a new protected surface in
  an existing account, with account-level grants still requiring scoped review.
  Only synthetic content; Key Vault-managed Arize credentials; managed-identity Blob
  auth. Verify encryption, network access, version/snapshot/soft-delete retention,
  and deletion behavior before rollout. Never apply account/container lifecycle TTL
  to unsent or ambiguous work. Container preparation adds no RBAC.
- **Observability considerations:** fixed reason/count logs plus hashed ledger IDs,
  never raw content or SDK/parser exception dumps. Original trace/span/parent,
  correlation and typed token fields are preserved, not inferred. A confirmed
  HTTP OTLP acknowledgment still is not independent destination field-parity proof.
- **Implementation trade-offs requiring rollout review:** added join/scan latency;
  unknown deliveries can remain
  quarantined indefinitely; payload-bearing recovery requires operators and cost
  monitoring. Finite host retry exhaustion can still advance Event Hub checkpoints
  after an admission failure; durable storage cannot recover never-admitted events.
- **Open questions:** actual native content-table export delivery, source shape and
  table-plan eligibility; exact existing storage grants/network/retention controls;
  destination acknowledgment/content fidelity; migration boundary for already-exported
  spans; live replay horizon and workload sizing. All are release gates, not reasons
  to silently enable query fallback, grant access, replay or invoke a model.
