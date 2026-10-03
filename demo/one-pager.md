# Observability for Foundry Prompt Agents — What This Demo Shows

*Illustrative synthetic data — nothing in this demo or this page uses real patient, member, or
claims information.*

## The problem

Healthcare organizations are adopting AI agents (chatbots, copilots, benefits assistants) built on
Microsoft Foundry Prompt Agents. Before trusting these agents in production, platform and
compliance teams need to answer a simple question: **"If something goes wrong — or we just need to
understand what the AI did and why — can we see it?"**

## What we show you

Using a fabricated "member services benefits chatbot" scenario, this demo shows how a Foundry
Prompt Agent can be instrumented so that **every single interaction is fully observable**:

- **What was asked, and what the agent answered** — captured automatically, with no custom logging
  code in the agent itself.
- **How much it cost** — token usage (the unit AI vendors bill on) tracked per request.
- **What happened when something failed** — if a model call times out or errors, you can see
  exactly what retried, how many times, and whether it ultimately succeeded or failed — instead of
  a black box.
- **How to trace one conversation across every system it touches** — a single ID lets you follow
  one member's request from the moment the agent received it through every downstream system,
  so "what happened with this one interaction?" has a real, traceable answer.

## Why it matters for your organization

- **Trust and accountability.** Before an AI agent touches anything near a member or patient
  workflow, your teams can demand proof it's observable — not just a vendor's word for it.
- **Operational readiness.** When (not if) something behaves unexpectedly, your support and
  engineering teams need a way to investigate it quickly, the same way they would any other
  production system.
- **Cost visibility.** Token usage is captured at the source, so usage/cost trends are visible
  without waiting on a vendor invoice.
- **A repeatable, provable approach — not a one-off.** Everything shown in this demo is backed by a
  written validation plan your own engineers can re-run against the same synthetic data, rather
  than a one-time live demo you have to take on faith.

## What's proven today vs. what's coming next

Part of this demo is already working end-to-end and reproducible on request; the remaining piece
— exporting that captured telemetry into a third-party analytics platform (Arize) for cross-system
trace visualization — is fully designed and the groundwork is in place, with the remaining
engineering work in progress. We are transparent about exactly which is which; see the technical
runbook and validation plan for the detailed breakdown.

## Want the technical details?

This page is intentionally non-technical. For the full architecture, validation evidence, and
step-by-step runbook, see:

- `docs/current-state/architecture.md` — how it works, technically
- `docs/validation/demo-validation-plan.md` — what's been proven, and how to re-check it yourself
- `demo/narrative.md` — the live demo script

---

*All data shown in this demo — member names, member IDs, plan names, claims, and conversation
content — is illustrative synthetic data, fabricated specifically for this demonstration. No real
patient, member, or claims data is used anywhere in this repository or demo.*
