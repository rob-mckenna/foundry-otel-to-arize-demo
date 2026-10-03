# docs/current-state

**Status: CURRENT-STATE (validated, implemented)**

Architecture docs, runbooks, and diagrams describing what is actually implemented and validated
today: the Foundry Prompt Agent -> Application Insights -> Log Analytics -> Event Hub -> Azure
Function (transform) -> Arize pipeline (see `/.github/copilot-instructions.md` §2).

Start here: [`architecture.md`](architecture.md) — the authoritative current-state Mermaid
diagram set (end-to-end pipeline + zoomed Event Hub → Azure Function transform view).

See [`prompt-agent-execution-validation.md`](prompt-agent-execution-validation.md) for the
Prompt Agent execution validation procedure, checklist, and evidence record (#49), including an
explicit breakdown of what is proven by static tests/code review versus what still requires a
live Foundry deployment.

Operational runbooks for standing up, tearing down, and troubleshooting a demo environment:
[`runbooks.md`](runbooks.md).

Only describe behavior that has been implemented under `/src` and `/infra` and verified. Known
limitations, unvalidated assumptions, and schema-mapping gaps must be called out explicitly here
rather than silently omitted (see `/.github/copilot-instructions.md` §16).

Conceptual/proposed designs do not belong here — see `/docs/future-state`.
