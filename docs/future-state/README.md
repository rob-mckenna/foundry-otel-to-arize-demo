# docs/future-state

> ⚠️ **CONCEPTUAL — NOT IMPLEMENTED.** Everything in this directory describes a proposal, not
> working code. Nothing here exists in `/src` or `/infra`.

This directory holds conceptual direct-OTLP design docs, diagrams, and proposals — for example,
exporting OTLP directly from the Prompt Agent (or a lightweight sidecar) straight to Arize, bypassing
the Application Insights -> Log Analytics -> Event Hub -> Azure Function pipeline (see
`/.github/copilot-instructions.md` §3).

Every document in this directory must carry an explicit "CONCEPTUAL — NOT IMPLEMENTED" label near
the top. Do not add implementation code, stubs, or partial implementations here or anywhere under
`/src` or `/infra` for ideas described in this directory until an `architecture-decision` issue has
been accepted and `/.github/copilot-instructions.md` has been updated to describe the design as
current-state.

## Contents

- [`direct-otlp.md`](direct-otlp.md) — the direct-OTLP export design proposal, dashed-line
  diagram, assumptions, and risks (issue #63).

