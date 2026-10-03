# OpenInference attribute mapping — validation evidence (#28)

Captured by running `python -m prompt_agent.main --scenarios` locally with
`PYTHONPATH` pointed at a worktree-local `.deps` install (see `README.md`).
Console span exporter output is JSON; excerpt below is from the first
scenario (`SYN-00042`, deductible question) with a tool lookup + model call.

Attribute names come from `openinference-semantic-conventions==0.1.39`
(`openinference.semconv.trace.SpanAttributes` /
`OpenInferenceSpanKindValues`), pinned in `pyproject.toml` to the `0.1.x`
OpenInference trace spec.

## `tool.lookup_plan_details` span attributes

```json
"openinference.span.kind": "TOOL",
"input.value": "Acme Synthetic PPO",
"output.value": "Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible."
```

## `llm.chat_completion` span attributes

```json
"openinference.span.kind": "LLM",
"input.value": "What is my synthetic deductible under Acme Synthetic PPO?\n\n[Synthetic plan lookup result: Acme Synthetic PPO — $500/$1,000 deductible, $25 PCP copay, in-network only after deductible.]",
"output.value": "Your synthetic deductible under Acme Synthetic PPO is $500 individual / $1,000 family for this benefit year.",
"llm.model_name": "synthetic-gpt-demo",
"llm.token_count.prompt": 26,
"llm.token_count.completion": 17,
"llm.token_count.total": 43
```

Verified `llm.token_count.total == llm.token_count.prompt + llm.token_count.completion`
(26 + 17 = 43) for every scenario run — confirms the attribute values are
internally consistent, not just present.

## `prompt_agent.invoke` span attributes

```json
"openinference.span.kind": "CHAIN",
"input.value": "What is my synthetic deductible under Acme Synthetic PPO?",
"output.value": "Your synthetic deductible under Acme Synthetic PPO is $500 individual / $1,000 family for this benefit year."
```

Note `input.value` on the top-level `CHAIN` span is the **original** user
prompt (before the synthetic tool-lookup context was appended), while
`input.value` on the child `LLM` span is the **effective** prompt actually
sent to the model (original + appended tool context) — this distinction is
intentional and lets a trace viewer show both "what the user asked" and
"what the model actually saw".

All 5 synthetic scenarios produced the same attribute shape; no missing or
empty attribute values observed in any run.
