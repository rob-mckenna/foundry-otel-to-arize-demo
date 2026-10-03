# Span Instrumentation Validation (#27)

Captured while validating #27's acceptance criteria. All prompts/plan names
below are synthetic demo content.

## 1. Normal run — span tree nesting

`python -m prompt_agent.main --scenarios`, one scenario's span tree
(trace_id redacted-equal across all three spans):

```
name: tool.lookup_plan_details   parent_id: 0x13232c1d05d6c0e7   status: OK
name: llm.chat_completion        parent_id: 0x13232c1d05d6c0e7   status: OK
name: prompt_agent.invoke        span_id:   0x13232c1d05d6c0e7   status: OK
```

`tool.lookup_plan_details` and `llm.chat_completion` are both direct
children of `prompt_agent.invoke` (same `parent_id` == `prompt_agent.invoke`'s
`span_id`), and all three share the same `trace_id` — confirming correct
parent-child nesting for a full request.

## 2. Forced failure — ERROR status propagation

Ran `PromptAgent.invoke()` with a model client that deliberately raises
`RuntimeError("synthetic forced failure for span ERROR validation")`:

```
name: tool.lookup_plan_details   status: OK      (unaffected — ran first, succeeded)
name: llm.chat_completion        status: ERROR   (+ exception event recorded)
name: prompt_agent.invoke        status: ERROR   (+ exception event recorded)
```

Confirms: a failing model call marks its own span `ERROR` (with the
exception captured as a span event, via OpenTelemetry's default
`record_exception=True`/`set_status_on_exception=True` behavior on
`start_as_current_span`), and the error propagates up to mark the parent
`prompt_agent.invoke` span `ERROR` too — nothing is silently swallowed.
