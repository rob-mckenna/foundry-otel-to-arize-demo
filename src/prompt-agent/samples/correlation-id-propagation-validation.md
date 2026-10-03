# Correlation ID propagation — validation evidence (#29)

Captured by running `python -m prompt_agent.main --scenarios` locally (5
synthetic scenarios, one `PromptAgent.invoke()` call per scenario).

## Example trace for one request (scenario `SYN-00042`, deductible question)

```
correlation_id: 172be31b-9691-445c-9ec7-de20e3444c65

name: prompt_agent.invoke          span_id: 0x5f62cd1ab14d5a64  parent_id: 0x3be85e00d7185d8c  correlation.id: 172be31b-...
  name: tool.lookup_plan_details   span_id: 0xfd740c452ba422c1  parent_id: 0x5f62cd1ab14d5a64  correlation.id: 172be31b-...
  name: llm.chat_completion        span_id: 0x958294a5d779c177  parent_id: 0x5f62cd1ab14d5a64  correlation.id: 172be31b-...
```

All three spans carry the identical `correlation.id` attribute value and
share the same `trace_id`; `tool.lookup_plan_details` and
`llm.chat_completion` both have `parent_id` equal to
`prompt_agent.invoke`'s `span_id` — correct parent-child nesting
end-to-end for this request.

## Cross-request isolation

Each of the 5 scenarios in the demo CLI run gets its **own**,
independently-generated `correlation.id` (`PromptAgent.invoke()` generates a
new one per call when the caller doesn't supply one — see
`correlation.py`):

```
correlation_id: 172be31b-9691-445c-9ec7-de20e3444c65   (scenario 1)
correlation_id: d63ffb88-b974-41b5-9354-ee612edea7f3   (scenario 2)
correlation_id: c1f41072-3805-4866-9d0c-a7b9cc488eae   (scenario 3)
correlation_id: 6fb5eda8-d733-4809-82f4-fbc832a6e679   (scenario 4)
correlation_id: a5aa634f-8866-4023-ac93-927859bf5f14   (scenario 5)
```

Verified: every span belonging to scenario *N* carries exactly scenario
*N*'s correlation ID — no cross-contamination between concurrent/sequential
requests observed across all 5 runs.

## Note on `trace_id` vs `correlation.id` in this CLI demo

All spans in the capture above share **one `trace_id`**
(`0x7132cc2e566dd349a340da25b3625c62`). This is expected and not a bug: the
CLI entry point (`main.py`) wraps the whole `--scenarios` run in one
`prompt_agent.startup` span, so every per-scenario `prompt_agent.invoke`
call becomes a nested child of that single root span/trace — this demo
process never starts a new root trace per request.

This is exactly why `correlation.id` exists as a distinct, caller-suppliable
attribute independent of `trace_id`: in a real deployment (e.g. one HTTP
request = one trace), `trace_id` would also vary per request and
`correlation.id` would be redundant with it. In *any* topology — including
this single-process demo, and including a future multi-hop/async topology
where a request's work might legitimately span more than one trace —
`correlation.id` remains the one attribute guaranteed to uniquely identify
"this logical request" and nothing else.

## `AgentResult.correlation_id`

`PromptAgent.invoke()` returns the correlation ID (whether caller-supplied
or generated) on `AgentResult`, so a calling layer (e.g. a future HTTP
handler) can log it or return it to the caller (e.g. as a response header)
without needing to inspect span data.
