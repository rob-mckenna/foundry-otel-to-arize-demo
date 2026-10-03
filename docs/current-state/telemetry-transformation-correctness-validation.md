# Telemetry Transformation Correctness — Validation (#55)

**Status: FUTURE-STATE dependency for the real Function; reference-transform logic validated
against spec, real Function code not implemented — see §2–§3.**

Validation record for
[#55 Validate telemetry transformation correctness](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/55),
depends on #36 (field-mapping doc).

## 1. Acceptance criteria under validation

1. For a sample of synthetic spans, the transformed OTLP output is compared field-by-field against
   the mapping doc's spec.
2. Any field mismatch (wrong value, wrong type, missing field) is filed as a bug referencing the
   specific mapping-doc row.
3. At least one edge case (e.g., a span with no tool calls vs. one with multiple tool calls) is
   tested to confirm the transformation handles structural variation.

## 2. What exists and was reviewed: a reference-transform test scaffold, not the real Function

[`tests/export/test_otlp_export_conformance.py`](./../../tests/export/test_otlp_export_conformance.py)
(#38) implements a **reference transform** — a synthetic 50-span batch generator plus assertions
proving the field-mapping specs (#89–#92, #36) are internally self-consistent (span-count parity,
resource-attribute presence, ID round-tripping, root-span parent handling, token-count typing).
Critically, **this is explicitly documented in that file's own header as not a test of production
code** — it exists to prove the *specs* are coherent and testable, since there is no real Azure
Function transform implementation to test against (`src/telemetry-pipeline` contains no code — see
corrected README in PR #121).

This means #55's criterion 1 ("the transformed OTLP output is compared... against the mapping
doc's spec") is satisfied today **only in the sense that the mapping doc's own spec has been
proven internally consistent and mechanically checkable** — not in the sense the issue actually
asks for, which is comparing a *real Function's* output against the spec. These are different
claims, and conflating them would be exactly the kind of current-state/future-state drift this
repo's conventions (and the #37/README finding from this same validation pass) exist to prevent.

## 3. What is NOT validated — the real transformation does not exist to test

- **No Azure Function code exists to transform anything.** There is no `(input Azure Monitor
  record) -> (actual OTLP output)` pair this repo can produce today — only
  `(synthetic Azure Monitor-shaped record) -> (spec says it should map to X)`, which is a design
  claim, not an execution result.
- **Criterion 3's structural-variation edge case is partially covered by the reference scaffold**
  (the 50-span generator includes spans with and without tool-call children per
  `otlp-export-conformance.md`), but again only as an internal-consistency check on the spec, not
  as a test of real transform code handling that variation correctly.
- **No field mismatch has been found** against a real transform (criterion 2), because there is no
  real transform output to compare — not because everything passed.

## 4. Sandbox limitation

No Azure Function implementation and no Python interpreter exist in this session — the reference
scaffold in #38 was written and reasoned about by static code review, consistent with every other
doc in this validation batch, and was not executed this session.

## 5. Validation checklist (to run once #19's Function transform code is implemented)

- [ ] Capture a sample of real Azure Monitor records (synthetic data only) flowing through the
      live Function.
- [ ] Capture the Function's actual OTLP output for that same sample.
- [ ] For each field listed in the mapping specs (`docs/telemetry/mapping/*.md`, #89–#92), build a
      diff table: field name | expected (per spec) | actual (from real output) | match/no-match.
- [ ] Include at least one span with no tool calls and one with multiple tool calls in the sample,
      per criterion 3.
- [ ] File a `bug-report.yml` for any mismatch found, referencing the specific mapping-doc row
      (e.g. "identity-correlation-fields.md, row: operation_ParentId → parent_span_id").
- [ ] Record the full diff table as the `demo-validation.yml` evidence for this issue.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | Transformed output vs. mapping spec, field-by-field | ⚠️ Spec proven internally consistent (reference scaffold, #38) — not validated against real Function output, which doesn't exist |
| 2 | Mismatches filed as bugs referencing mapping-doc rows | N/A — no real output exists to diff against the spec yet |
| 3 | Structural-variation edge case tested | ⚠️ Covered in the reference scaffold's synthetic data generator only, not against real transform code |

**Overall verdict: Blocked (for the issue's actual claim) / Spec-validated (for the lesser claim
that the mapping doc itself is coherent)** — this distinction is the core finding of this doc: the
mapping specs are solid and testable, but "the Function matches the spec" cannot be claimed until
the Function exists to check.
