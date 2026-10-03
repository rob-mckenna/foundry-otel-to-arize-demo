# Pull Request

## Related Issue

Closes #51

## Summary of Changes

Adds `docs/current-state/prompt-response-telemetry-validation.md`, the validation record for #51.
Proves (via existing exact-match unit test assertions in `test_agent_spans.py`) that
`input.value`/`output.value` are captured character-for-character pre-export, documents that no
truncation logic exists in this repo's instrumentation code, and — honestly — flags that the
long-prompt/truncation test case (acceptance criterion 3) does not exist yet. Provides the concrete
test code to add once a Python interpreter is available, plus the Azure Monitor 8,192-character
property-size-limit context needed to design it correctly.

## Architecture Track Affected

ApplicationInsights, Documentation

## Security Impact

None — documentation-only change; the proposed test uses only synthetic filler text.

## Telemetry Impact

None to code/span behavior. Documents the existing prompt/response capture path.

## Documentation Updates

- `docs/current-state/prompt-response-telemetry-validation.md` (new)

## Tests Performed

No new tests added in this PR (no Python interpreter available in this sandbox to write-and-run
one). §5 of the new doc specifies the exact test to add for criterion 3 as a follow-up.

## Demo Validation Performed

None — no live Application Insights instance exists to confirm post-export truncation behavior.

## Current Limitations

- Criterion 3 (long-prompt truncation) has **no test yet** — flagged as a real gap, not silently
  assumed to pass. §5 is the concrete follow-up.
- Post-export (live App Insights) confirmation of criteria 1–2 is blocked on the same missing live
  instance as #50.

## Screenshots or Trace Evidence

N/A.

---

## Checklist

- [x] No secrets, credentials, or connection strings committed
- [x] No sensitive healthcare or personal data (PII/PHI) added — synthetic data only
- [x] Tests pass (N/A — no new tests added this PR; existing suite referenced by inspection only)
- [x] Documentation updated (or explicitly noted as not needed, with reason)
- [x] Current-state vs. future-state claims are correctly labeled (no conceptual work presented as implemented, or vice versa)
- [x] New dependencies reviewed (license, maintenance status, security posture) — N/A, none added
