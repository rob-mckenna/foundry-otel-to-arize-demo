# src/telemetry-pipeline

**Status: CURRENT-STATE implementation with synthetic offline tests; NOT E2E VALIDATED.**
The baseline source reconciles the eight-file package published on 2026-10-16 under an explicit
user-approved package-only exception, not completed generic official validation. Independent
Arize graph/field/token parity remains **UNKNOWN**. The inline GenAI message-content
enhancement source `e2c557fa58b27f68ef4706722544df76e7b17e5b` is pushed and deployed:
deployment `3f880a64-208b-498a-8f84-d6bbcd329ecb` completed successfully/active at
`2026-10-16T23:04:08.7902273Z`. All eight active source hashes match the immutable
source ZIP `55448a28fd31f28c38c5227603982d86ba57bb09a384fc8c0af1f34aa19b2b4a`;
host Running, Event Hub trigger enabled/indexed, three references Resolved, and safe
control projections unchanged. **Arize UI not independently validated.** The ignored
operator receipt is `.azure-sandbox\genai-e2c557f-20261016-reconciled-proof.json`.
See the scoped
[native mapping and export contract](../../docs/current-state/telemetry-mapping-export-contract.md)
for provenance, source-field mappings, failure handling, binding prerequisites, and held work.

This directory holds the Azure Function transform/mapping code and Event Hub consumer logic for the
telemetry pipeline:

`Application Insights -> Log Analytics -> Event Hub -> Azure Function (transform/map) -> Arize (OTLP)`

## What exists now (issue #37 follow-on)

`telemetry_pipeline/` is a real, importable Python package implementing every mapping in
[`/docs/telemetry/field-mapping.md`](../../docs/telemetry/field-mapping.md)'s summary table and its
four detail docs (`/docs/telemetry/mapping/*.md`, issues #89–#92):

- `mapping.py` — per-record field-group transform logic (identity/correlation, token,
  LLM I/O, span kind/status), including the critical "App Insights exports every
  `customDimensions` value as a JSON string" type-coercion rule (string→int for token counts and
  `retry.attempt`/`max_attempts`, string→bool for `retry.will_retry`, bool→OTLP status code for
  `Success`), and the root-span-has-no-parent handling documented in
  [`trace-correlation-preservation.md`](../../docs/telemetry/trace-correlation-preservation.md) §1
  (an empty/absent `operation_ParentId` becomes `None`, never a zero-filled span ID).
  Inline `gen_ai.input.messages` / `gen_ai.output.messages` role/parts arrays (native or
  JSON-encoded) fill missing OpenInference `input.value` / `output.value` as JSON strings
  with `application/json` MIME. Explicit values and their MIME win independently; stale
  MIME without a value is replaced on conversion or omitted. Invalid message content
  emits a key/reason-only warning and omits that side's generated I/O, retaining the
  span. Nested parts are preserved; no new truncation, AppGenAIContent join, or copying
  content to parents is introduced.
- `batch.py` — decodes an Event Hub message batch (single record, JSON array, or the Log Analytics
  Data Export `{"records": [...]}` envelope) into OTel SDK `ReadableSpan` objects and exports the
  whole batch in one `exporter.export()` call (per §4's whole-batch-checkpointing recommendation),
  flagging malformed individual records rather than failing the entire batch.
- `exporter.py` — the OTLP-to-Arize export path is injected via a factory/DI seam
  (`get_default_exporter()` / `build_arize_otlp_exporter()`), mirroring
  `src/prompt-agent/prompt_agent/telemetry.py`'s `_CountingSpanExporter` pattern. No live network
  call to Arize is made by default or by the test suite.
- `function_app.py` — the actual `azure.functions` (Python v2 programming model) Event Hub trigger
  wiring, matching the identity-based binding app-setting prefix documented in
  `infra/modules/function-app.bicep`. This is the only module requiring the `azure-functions`
  package; the transform logic above does not depend on it and is unit-testable without it.

**Unit tests** (`tests/`) cover every field group, the type-coercion rule, the root-span-no-parent
edge case, and a synthetic 3-span batch (`prompt_agent.invoke` → `tool.lookup_plan_details` +
`llm.chat_completion`) proving one shared `trace_id` and correct parent linkage survive an in-memory
Event Hub message batch — entirely via mocked message objects, no live Azure required to run them.

## What remains open

Publication/source parity, retained native preflight delivery, source capture, and destination
parity are separate evidence gates. Publication did not establish a fresh Event Hub delivery or
OTLP acknowledgment. Full same-invocation graph/field/token parity in Arize is still unproven.
The separately authorized package-only deployment is recorded above; this document
authorizes no replay, model, registration, evaluation, settings, infrastructure, or
further deployment operation.

The future-state idea of bypassing this pipeline with a direct OTLP exporter is conceptual only and
lives under `/docs/future-state` — it must never be partially implemented here ahead of an accepted
architecture decision.

## Known gap (tracked, historical)

This README previously stated an incorrect `validated, implemented` status while this directory
held no code — surfaced by Lead during the Milestone 4 current-state/future-state separation audit
(issue #14, see `/docs/current-state/separation-audit.md` Finding 3; also reflected as a "Partial"
capability in `/docs/architecture/capability-matrix.md`, issue #60 capability #7). Corrected in
PR #121. See `.squad/decisions/inbox/lead-telemetry-pipeline-readme-drift.md` and
`.squad/decisions/inbox/telemetry-readme-drift-and-issue-37-followup.md` for that history, and
`.squad/decisions/inbox/telemetry-issue-37-function-transform.md` for this pass's follow-up.

## Known gap (tracked)

This README previously stated an incorrect `validated, implemented` status while this directory
held no code — surfaced by Lead during the Milestone 4 current-state/future-state separation audit
(issue #14, see `/docs/current-state/separation-audit.md` Finding 3; also reflected as a "Partial"
capability in `/docs/architecture/capability-matrix.md`, issue #60 capability #7). Corrected here.
See `.squad/decisions/inbox/lead-telemetry-pipeline-readme-drift.md` for the full finding and
`.squad/decisions/inbox/telemetry-readme-drift-and-issue-37-followup.md` for this fix and the
related issue #37 follow-up.
