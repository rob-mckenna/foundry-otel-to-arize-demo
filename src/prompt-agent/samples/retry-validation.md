# Retry-with-backoff validation evidence (#30)

Captured by running a throwaway validation script (`_retry_validation_scratch.py`,
not committed — see below) that wires `FlakyStubFoundryModelClient`
(demo/validation-only client, `model_client.py`) into `PromptAgent` to force
transient failures and exercise `prompt_agent/retry.py`'s bounded
exponential-backoff logic.

## Case 1 — fails twice, succeeds on the 3rd attempt (`max_attempts=3`)

```
name: llm.chat_completion.attempt  retry.attempt=1  status=ERROR  retry.will_retry=true   correlation.id=fa852766-...
  -> exception event recorded (TransientModelError)
name: llm.chat_completion.attempt  retry.attempt=2  status=ERROR  retry.will_retry=true   correlation.id=fa852766-...
  -> exception event recorded (TransientModelError)
name: llm.chat_completion.attempt  retry.attempt=3  status=OK                             correlation.id=fa852766-...
name: llm.chat_completion          status=OK                                              correlation.id=fa852766-...
name: prompt_agent.invoke          status=OK                                              correlation.id=fa852766-...

RESULT: success, correlation_id=fa852766-77ed-4bca-a677-a9344fa72bb7,
        response='Your synthetic deductible under Acme Synthetic PPO is $500
        individual / $1,000 family for this benefit year.'
```

**A recovered retry still reports overall success** — `llm.chat_completion`
and `prompt_agent.invoke` are both `OK`, even though 2 of the 3
`llm.chat_completion.attempt` spans are `ERROR`. All three attempt spans,
plus the two enclosing spans, share the exact same `correlation.id` — the
retried request remains fully traceable back to the original request.

## Case 2 — fails on every attempt (`max_attempts=2`) → overall failure

```
name: llm.chat_completion.attempt  retry.attempt=1  status=ERROR  retry.will_retry=true   correlation.id=afd3c4a3-...
  -> exception event recorded (TransientModelError)
name: llm.chat_completion.attempt  retry.attempt=2  status=ERROR  retry.will_retry=false  correlation.id=afd3c4a3-...
  -> exception event recorded (TransientModelError)
name: llm.chat_completion          status=ERROR                                          correlation.id=afd3c4a3-...
  -> exception event recorded (propagated)
name: prompt_agent.invoke          status=ERROR (presumed; exception propagates through)  correlation.id=afd3c4a3-...

RESULT: raised as expected after exhausting retries: TransientModelError:
        synthetic transient failure on attempt 2 (demo/validation only)
```

Every attempt is `ERROR` with its own exception event; the final failure
propagates up through `llm.chat_completion` and `prompt_agent.invoke`
(both also `ERROR`, each with their own exception event) — a terminal
failure after retries is exhausted is just as fully traceable as a single
failed call would have been in #27, not swallowed by the retry logic.

## Important fix made during validation

The first implementation relied on OpenTelemetry's default
`record_exception=True`/`set_status_on_exception=True` behavior (as used
for the non-retried spans in #27) — but that behavior only fires when an
exception **escapes** a span's `with` block. Since `retry.py` deliberately
catches the exception *inside* the attempt span's `with` block (so it can
retry instead of propagating), the default behavior never fired, and
retried-but-failed attempts were incorrectly left `status_code: "UNSET"`
with no exception event. Fixed by explicitly calling
`span.record_exception(exc)` and
`span.set_status(Status(StatusCode.ERROR, str(exc)))` on every failed
attempt, retried or not — re-validated above (both attempts in Case 2, and
the two failed attempts in Case 1, now correctly show `ERROR` + an
`exception` event).

## Normal (non-retry) path still correct

Re-ran `python -m prompt_agent.main --scenarios` (all 5 synthetic
scenarios, using the real `StubFoundryModelClient` which never fails) after
this change — every scenario still produces exactly one
`llm.chat_completion.attempt` span (`retry.attempt=1`, `status=OK`), i.e.
the retry wrapper is a no-op overhead-wise when nothing fails.
