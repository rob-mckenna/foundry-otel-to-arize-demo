# Export-Pipeline Execution — Validation (#54)

**Status: FUTURE-STATE dependency, fully BLOCKED. No validation possible today — see §2.**

Validation record for
[#54 Validate export-pipeline execution](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/54),
depends on #50 and #35/#36 (export pipeline documentation).

## 1. Acceptance criteria under validation

1. For each synthetic trace, confirm the corresponding Event Hub message was consumed (no messages
   left in the consumer group backlog beyond the expected processing window).
2. Azure Function execution logs show a successful run (no exceptions) for each synthetic trace
   processed.
3. Any failure is filed as a bug (`bug-report.yml`) with the Function execution ID as evidence.

## 2. Why this is fully blocked, not partially validated

Unlike #50–#53, this issue's acceptance criteria are **entirely** about infrastructure that does
not exist in this repo in any form yet:

- **No Event Hub is provisioned.** Issue #17 (Event Hub Bicep module) status was not re-verified
  as part of this doc (out of scope for Telemetry — Infra track owns it), but even if the Bicep
  module exists, there is no live, deployed Event Hub instance in this sandbox to send messages to
  or check consumer-group backlog on.
- **No Azure Function transform/consumer code exists.** Confirmed directly:
  `src/telemetry-pipeline/` contains only a `README.md` (now corrected in PR #121 to accurately
  state this) — no Function App code, no Event Hub trigger binding, no transform logic. There is
  nothing to deploy, and therefore nothing that could produce "Azure Function execution logs."
- **No Function execution ID can exist** without a deployed, invoked Function — criterion 3's
  evidence requirement is structurally impossible to satisfy right now.

This is a materially different situation from #50–#53, where this repo's own code (the Prompt
Agent's instrumentation) could be validated in-process even without live Azure resources. Export
pipeline *execution* has no equivalent "in-process, no-live-resources-needed" validation path,
because the thing being validated — the Function actually running — doesn't exist as code at all
yet, let alone as a deployed/invokable resource.

## 3. What documentation already exists for this gap (not validation, design)

- [`docs/telemetry/field-mapping.md`](./../telemetry/field-mapping.md) and the four field-group
  specs under `docs/telemetry/mapping/` (#89–#92) specify *what* the Function must do once
  written.
- [`docs/telemetry/trace-correlation-preservation.md`](./../telemetry/trace-correlation-preservation.md)
  §3–§4 specifies two concrete implementation requirements (Event Hub partition-key choice,
  whole-batch checkpointing strategy) the Function's eventual implementation must satisfy for
  correlation-ID preservation — written in advance of the code existing, as a design constraint for
  whoever implements #19's follow-on work.
- [`docs/telemetry/otlp-export-conformance.md`](./../telemetry/otlp-export-conformance.md) (#38)
  specifies the OTLP conformance the Function's *output* must meet, validated today only via a
  reference-transform test scaffold (not the real Function code).

None of the above is execution evidence — they are specs the eventual implementation must satisfy,
which is a meaningfully different (and lesser) claim than this issue's acceptance criteria ask for.

## 4. Sandbox limitation

No Event Hub, no Azure Function code/deployment, and no Python interpreter exist in this session.

## 5. Validation checklist (to run once #19's Function code is implemented and deployed)

- [ ] Send a known-count batch of synthetic trace events into the Event Hub (e.g. via the Prompt
      Agent's real App Insights export, or a direct synthetic producer script).
- [ ] Check the Event Hub consumer group's backlog/lag metric — confirm it returns to zero within
      the expected processing window for every message sent.
- [ ] Check the Function's own Application Insights instance (its execution telemetry, separate
      from the Prompt Agent's) for each invocation — confirm `Succeeded` status, no exceptions
      logged, for every synthetic trace processed.
- [ ] Record each Function execution ID alongside its corresponding synthetic trace ID in a
      `demo-validation.yml` entry.
- [ ] File a `bug-report.yml` (component: "Export pipeline (Event Hub / Azure Function)") for any
      execution that failed, citing the execution ID — never the raw payload — as evidence.

## 6. Summary

| # | Check | Status |
|---|---|---|
| 1 | Event Hub messages consumed, no backlog | ❌ Blocked — no Event Hub deployment exists to check |
| 2 | Function execution logs show success | ❌ Blocked — no Function code exists to execute, let alone log |
| 3 | Failures filed as bugs with execution ID | N/A — no execution has ever occurred, so no execution ID can exist yet |

**Overall verdict: Blocked — cannot be validated in any form in this sandbox.** This is a genuine,
structural gap (missing implementation), not a defect to file a bug against. The follow-on work
required before this issue can be attempted is: implement #19's Function transform/consumer code,
deploy both it and an Event Hub instance, then re-run §5's checklist.
