# OTLP Export Conformance — Azure Function → Arize

> Spec + test scaffold for issue [#38](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/38).

**Status: CURRENT-STATE DESIGN, pending Azure Function transform implementation.** No Function
transform code exists in this repo yet (`src/telemetry-pipeline/` is still a placeholder) and no
live Arize space is provisioned in this sandbox. This doc specifies what "conformant OTLP export"
means for this pipeline and gives a reference test that proves the *shape* of the transform logic
against that spec using synthetic data — it does not (and cannot, in this sandbox) prove a live
Function sending to a live Arize endpoint actually behaves this way. See §4 for the explicit
validated-via-review / requires-live-environment split.

## 1. What "conformant" means here

Per issue #38's acceptance criteria, the Function's OTLP export to Arize must satisfy all three:

1. **No silent drops.** Span count in (Event Hub events received by the Function in one invocation)
   == span count out (spans successfully accepted by Arize's OTLP endpoint) for a 50+ span
   synthetic batch — no partial-success response silently treated as success.
2. **Correct resource attributes.** Every exported `ResourceSpans` message sets:
   - `service.name` = `foundry-prompt-agent-demo` — a fixed, demo-specific value so this tenant's
     traffic is distinguishable from any other tenant/environment inside a shared Arize space.
   - `deployment.environment` = the deploying environment name (e.g. `demo`, `dev`) — parameterized,
     not hardcoded, consistent with this repo's naming/tagging convention (#20) of never baking a
     single customer's environment name into shared code.
3. **Spec-compliant protocol, not a custom shim.** The Function must emit actual OTLP (protobuf over
   gRPC, or OTLP/HTTP+protobuf — Arize's documented ingestion endpoint accepts both; this repo
   defaults to **OTLP/gRPC**, matching Arize's primary documented SDK path) — not a hand-rolled JSON
   shape that merely resembles OTLP. This directly answers the customer question flagged in the
   issue: "is this real OTel or a custom shim?"

## 2. Export request shape

Each Function invocation processes one Event Hub batch and emits one
`ExportTraceServiceRequest` (the standard OTLP trace export protobuf message) containing:

```
ExportTraceServiceRequest
└── resource_spans[]
    └── ResourceSpans
        ├── resource.attributes: [service.name, deployment.environment]
        └── scope_spans[]
            └── ScopeSpans
                └── spans[]  (one Span per Event Hub event/Log Analytics row in the batch)
```

Each `Span` is populated per the field-by-field mapping specs:

- [`docs/telemetry/mapping/identity-correlation-fields.md`](./mapping/identity-correlation-fields.md) (#89) — `trace_id`/`span_id`/`parent_span_id`/`correlation.id`
- [`docs/telemetry/mapping/token-fields.md`](./mapping/token-fields.md) (#90) — token-count attributes
- [`docs/telemetry/mapping/llm-io-fields.md`](./mapping/llm-io-fields.md) (#91) — I/O/model-name attributes
- [`docs/telemetry/mapping/span-kind-status-fields.md`](./mapping/span-kind-status-fields.md) (#92) — name/status/span-kind/retry attributes

## 3. Arize OTLP endpoint expectations

- Arize's OTLP ingestion endpoint requires two headers on every export call: `space_id` and
  `api_key` (or `arize-space-id`/`arize-interface-key`, depending on SDK version — **the exact
  header names must be confirmed against the live Arize tenant's docs/dashboard once one is
  provisioned**; this is flagged as an open item, not assumed).
- A successful export returns no `ExportTracePartialSuccess` field (or one with
  `rejected_spans == 0`) in the `ExportTraceServiceResponse`. The Function must treat a non-zero
  `rejected_spans` count as a failure requiring retry/alerting, not a silently-accepted partial
  success — this is the same "treat correlation/data loss as a blocking defect" posture as
  `trace-correlation-preservation.md` (#37) applies to Event Hub/Function hops.

## 4. Validation

### Synthetic batch test (this PR)

`tests/export/test_otlp_export_conformance.py` builds a 50-span synthetic batch (10 synthetic
traces × 5 spans each: `prompt_agent.invoke` → `tool.lookup_plan_details` + `llm.chat_completion` →
`llm.chat_completion.attempt` × 2, modeled on the same span tree shape as
`src/prompt-agent/tests/test_agent_spans.py`) and a minimal **reference transform** function that
implements the mapping specs above, then asserts:

1. Span count in (50) == span count out (no span dropped by the reference transform).
2. Every exported `ResourceSpans` has `service.name` == `foundry-prompt-agent-demo` and a non-empty
   `deployment.environment`.
3. Every span's `trace_id`/`span_id`/`parent_span_id` round-trips unchanged from the synthetic input
   row's `operation_Id`/`id`/`operation_ParentId`.

**This reference transform is a test fixture proving the spec is internally consistent and
implementable — it is explicitly not the production Azure Function implementation**, which does not
exist yet in this repo. Once #19's Function code implements this mapping for real, this test (or an
equivalent one living alongside that code) should be run against the actual Function logic instead
of the reference transform.

### Expected evidence (from issue #38, requires a live Arize space)

```
query {
  spans(filter: { resourceAttribute: "service.name", value: "foundry-prompt-agent-demo" },
        timeRange: last_1h) {
    spanId
    traceId
    parentSpanId
  }
}
```

Expected: 50 spans returned, matching the synthetic batch's 10 traces × 5 spans, each with
`parentSpanId` matching the synthetic tree structure.

### Validated-via-review vs. requires live-environment re-verification

- **Validated-via-review:** the OTLP request shape (§2), the mapping-spec cross-references, and the
  reference-transform test logic (§4) are reasoned through and written to the same conventions as
  the already-reviewed `test_agent_spans.py`/`test_token_usage_validation.py` suites. **No Python
  interpreter is available in this sandbox** (consistent with Telemetry's Milestone 2 history note),
  so `test_otlp_export_conformance.py` could not actually be executed here — it must be re-run with
  a working Python 3.10+ environment before being relied on as passing CI evidence.
- **Requires live-environment re-verification:** the actual Arize OTLP endpoint header names/auth
  flow (§3), the real Function's export behavior, and the "span count in == span count out" claim
  against a live Arize space are all open items blocked on #19 (Function implementation) and a
  provisioned Arize tenant. None of this is claimed as passing today.

## Related

- [`field-mapping.md`](./field-mapping.md) (#36)
- [`trace-correlation-preservation.md`](./trace-correlation-preservation.md) (#37)
- [#39 Trace/span correlation preserved into Arize (cross-system join test)](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/39)
- [#40 Token analysis views in Arize](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/40)
