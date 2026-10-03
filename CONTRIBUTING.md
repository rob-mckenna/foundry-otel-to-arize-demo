# Contributing

This repo is maintained using the [Squad](.squad) team framework. See
[`.github/copilot-instructions.md`](.github/copilot-instructions.md) for the full set of
architecture, security, telemetry, testing, and documentation conventions that apply to every
contribution — this file adds one specific, lightweight process on top of those: keeping docs in
sync with implementation.

## Doc-drift checklist (every PR)

**The single most common reason reusable demo repos rot is docs that silently stop matching the
code.** Treat a stale doc as a bug, not a follow-up chore — if your PR changes architecture or
behavior, update the relevant doc **in the same PR**, not afterward.

Before opening a PR, ask:

1. **Does this PR change what's implemented under `/src` or `/infra`?**
   If yes → update `/docs/current-state` (architecture diagram, field mapping, runbook, or
   whichever doc describes that behavior) in this same PR.
2. **Does this PR change a conceptual/proposed design under `/docs/future-state`?**
   If yes → update that design doc, and confirm it still carries the required
   "CONCEPTUAL — NOT IMPLEMENTED" label (per `copilot-instructions.md` §16) — never let a
   future-state doc start implying something is implemented.
3. **Does this PR change an environment variable, CLI command, file path, or setup step referenced
   anywhere in `README.md`, `demo/runbook.md`, or `docs/current-state/runbooks.md`?**
   If yes → update every doc that references the old value, not just the first one you find.
4. **Does this PR touch the Event Hub → Azure Function → Arize transform path (schema mapping,
   trace/span ID handling, token-usage fields)?**
   If yes → add/update a test under `/tests/telemetry-mapping` or `/tests/export` **and** update
   `docs/telemetry/field-mapping.md`'s mapping table if the field-level behavior changed.
5. **Did you add a new known limitation, assumption, or unvalidated behavior?**
   If yes → it must be stated explicitly in the relevant doc (per `copilot-instructions.md` §16) —
   not left for a reader to infer.

If the honest answer to all five is "no, this PR doesn't touch anything documented anywhere," state
that explicitly in the PR's **Documentation Updates** field ("None needed — reason") rather than
leaving it blank. A blank or vague "N/A" there is itself a doc-drift risk: it gives the next
reviewer no way to tell whether the box was actually considered.

This checklist is intentionally short — it is meant to be run mentally in under a minute per PR,
not as a blocking approval gate. The PR template's existing **Documentation Updates** field (see
`.github/pull_request_template.md`) is where you record the answer; this checklist is what you run
through your head (or literally paste into that field) before filling it in.

## Retroactive validation example

Applied against PR #74 ("Document and implement network requirements (optional private-endpoint
module)", issue #21, merged 2026-10-03) as a validation example for this checklist:

- **Changed:** `infra/modules/networking.bicep` (new optional module), `infra/main.bicep`,
  `infra/main.parameters*.json`.
- **Checklist item 1 (current-state docs):** `infra/README.md` was updated in the *same* PR with a
  full "Network posture" section (default public+RBAC posture, the optional private-endpoint
  upgrade path, and an explicit note on what was/wasn't validated from the authoring environment).
  ✅ Would have passed this checklist — no drift introduced.
- **Checklist item 5 (known limitations):** the PR explicitly documented that the private-endpoint
  variant was reviewed for Bicep syntax only, not deployed+torn-down against a live subscription —
  stated directly in `infra/README.md` rather than silently omitted. ✅ Passes.
- **Checklist item 2 (future-state):** not applicable — this PR implemented an optional
  current-state module, not a future-state proposal, and the architecture diagram in
  `docs/current-state/architecture.md` correctly continues to show only the default (no
  private-endpoint) posture, since that remains the validated default pipeline.

**Conclusion:** this PR would have passed the checklist above with no gaps — it is a useful
positive example of the practice this checklist is meant to enforce going forward, not a case where
a gap was caught after the fact.

## Where this is tracked

This checklist is also recorded as a team decision in
`.squad/decisions/inbox/qa-doc-drift-checklist.md` for the Scribe to merge into
`.squad/decisions.md`. Per that decision, a short reference to this file should be added to
`.github/pull_request_template.md`'s **Documentation Updates** section by whoever owns that
template (Lead/Scribe) — this PR does not edit the template directly, consistent with issue #62's
own instruction to coordinate rather than edit it unilaterally.
