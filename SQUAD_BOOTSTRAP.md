# SQUAD_BOOTSTRAP.md

## Squad Team Roster

This repo is built and maintained by a Squad team (see `.squad/team.md` for the authoritative roster). Each
member owns a track of the GitHub backlog (10 epics, ~65 issues — see Issue Routing below) and works in
their own voice per their charter under `.squad/agents/{member}/charter.md`.

| Member | Role | Owns |
|---|---|---|
| **Lead** | Architect / Tech Lead | Architecture & Design, Demo Experience narrative, Future-State Architecture, label/milestone/project strategy, backlog execution |
| **Infra** | Infrastructure / DevOps Engineer | Infrastructure Deployment (Bicep/Terraform, Key Vault, managed identity, networking) |
| **Agent** | Prompt Agent Developer | Prompt Agent Implementation (Foundry Prompt Agent, OpenTelemetry/OpenInference instrumentation, retries) |
| **Telemetry** | Observability / Telemetry Pipeline Engineer | Application Insights Instrumentation, Telemetry Export Pipeline, Arize Integration, Dashboarding and Queries |
| **QA** | Tester / Technical Writer | Documentation epic, Demo Experience testing/validation issues |
| **Scribe** | Scribe | Merges decisions into `.squad/decisions.md`, keeps team state current — runs after substantial work, never blocks |
| **Ralph** | Work Monitor | Watches for stalled/blocked work |
| **Rai** | RAI Reviewer | Responsible-AI review gate |
| **Fact Checker** | Verifier | Spot-checks current-state vs. future-state claims for accuracy |
| **@copilot** | Coding Agent | Picks up `squad:{member}`-labeled issues autonomously per capability profile in `.squad/team.md` |

## Repository Structure Convention

```
/src/prompt-agent/        Foundry Prompt Agent implementation (current-state, shippable)
/src/telemetry-pipeline/  Azure Function transform pipeline (current-state, shippable)
/infra/bicep/             Bicep IaC modules
/infra/terraform/         Terraform IaC modules (if used as an alternative)
/docs/current-state/      Implemented, demo-validated architecture and diagrams
/docs/future-state/       Conceptual, NOT IMPLEMENTED — every file must carry "CONCEPTUAL — NOT IMPLEMENTED"
/docs/telemetry/          Field mapping docs, KQL query packs, custom-dimensions schema reference
/docs/validation/         Demo Validation Plan and capability matrix
/tests/telemetry-mapping/ Tests proving Azure Monitor → OTLP field mapping correctness
/tests/export/            Export-pipeline tests
/demo/                    Demo narrative, runbook, fallback guidance, one-pager, sample prompts
.squad/                   Squad team configuration, charters, decisions, routing
.github/                  Issue templates, PR template, workflows
```

**Current-state vs. future-state discipline:** nothing under `/src` or `/infra` may represent conceptual/unbuilt
capability, and nothing under `/docs/future-state` may be presented as already working. See Epic: Architecture
and Design (issue #1) and Epic: Future-State Architecture (issue #10).

## How to Pick Up Work

1. Browse open issues by **label** — each of the 19 labels maps to a track (`Architecture`, `Infrastructure`,
   `PromptAgent`, `ApplicationInsights`, `Observability`, `OpenTelemetry`, `OpenInference`, `Arize`,
   `Documentation`, `Demo`, `Security`, `Healthcare`, `CurrentState`, `FutureState`, `GoodFirstIssue`, `Blocked`,
   `Priority-High/Medium/Low`).
2. Issues also carry a **Milestone** (1–5, Foundation → Telemetry Pipeline → Arize Integration → Customer Demo
   Readiness → Future-State Design) showing where they sit in the overall sequencing.
3. For squad-routed work, apply a `squad:{member}` label per `.squad/routing.md` — the named member (or
   `@copilot` for 🟢/🟡-rated work) picks it up next session.
4. Every epic issue (#1–#10) has a child-issue checklist (`- [ ] #N`) so you can see full scope and
   dependencies at a glance before starting.
5. Read `.squad/decisions.md` before starting architecture-affecting work — it's the durable record of past
   team decisions (including the Key Vault / Function App sequencing resolution).

See also: `.github/copilot-instructions.md` (coding agent instructions and architecture conventions),
`.github/ISSUE_TEMPLATE/` (structured issue forms: bug-report, feature, infrastructure, telemetry-mapping,
demo-validation, architecture-decision, future-state-proposal), and `.github/pull_request_template.md`
(required PR sections: architecture track, security impact, telemetry impact, demo validation).

## Getting Started (Microsoft Field Engineer)

1. **Clone** the repo and read this file plus `/docs/current-state/architecture.md` to understand what's
   actually running today vs. what's conceptual (`/docs/future-state/`).
2. **Read the architecture** — start with the current-state Mermaid diagram (issue #11) and the capability
   matrix (issue #60) to see implementation status per demo capability.
3. **Deploy infra** — follow `/infra` deployment docs and run the deployment validation script (issue #22) to
   provision Foundry project, Application Insights/Log Analytics, Event Hub, Function App, and Key Vault in
   dependency order.
4. **Run the demo** — follow `/demo/runbook.md` (issue #45) to trigger the synthetic scenario end-to-end.
5. **Run demo validation** — follow `/docs/demo-validation-plan.md` (this repo root) to confirm all 11
   pipeline capabilities check out with real evidence before presenting to a customer.
6. **Tear down** — run the teardown script (issue #23) to leave a clean subscription afterward.

## GitHub Project Board

A GitHub Project (v2) board titled **"Foundry OTel to Arize Demo"** is live at
**https://github.com/users/rob-mckenna/projects/7** and tracks all 65 issues (#1–#65) through the following
**Status** columns, in order:

`Backlog` → `Ready` → `In Progress` → `Review` → `Demo Validation` → `Complete`

All 65 issues were added and currently sit in **Backlog** (the starting column) as of 2026-10-02. The board
was created and configured via `gh project create` + `gh api graphql` (`updateProjectV2Field` mutation on
the single-select `Status` field) once the `gh` CLI token's `project`/`read:project` scopes were restored —
the prior scope limitation documented here previously is resolved.

## Project Name (legacy)

foundry-prompt-agent-appinsights-arize-demo

---

## Business Objective

Build a demonstration showing how telemetry generated by a Microsoft Foundry Prompt Agent can be captured in Azure Application Insights and exported into Arize for observability, tracing, prompt inspection, token analysis, and agent workflow monitoring.

The demonstration should emulate the customer scenario discussed with UnitedHealth Group (UHG), where Prompt Agents emit telemetry into Azure Monitor / Application Insights and an integration layer forwards telemetry into Arize.

---

## Target Audience

- Enterprise Architects
- AI Platform Engineers
- Observability Teams
- Security & Compliance Reviewers
- Healthcare Customers
- Microsoft Field Teams

---

## Demonstration Goals

Demonstrate:

1. Microsoft Foundry Prompt Agent execution
2. Prompt Agent trace generation
3. Application Insights telemetry capture
4. Token usage visibility
5. Trace correlation IDs
6. Custom telemetry export
7. Arize ingestion
8. Arize trace visualization
9. End-to-end observability architecture

---

## Success Criteria

A successful demo must show:

- Prompt Agent invocation
- Trace visible in Application Insights
- Prompt and completion metadata visible
- Token metrics collected
- Correlation identifiers preserved
- Export pipeline successfully executed
- Trace viewable within Arize
- Demo repeatable in customer environments

---

## Repository Deliverables

### Documentation

README.md

docs/

- architecture.md
- deployment.md
- telemetry-flow.md
- app-insights-queries.md
- arize-configuration.md
- troubleshooting.md

---

### Infrastructure

infra/

- bicep/
- terraform/

Provision:

- Azure AI Foundry Project
- Prompt Agent
- Application Insights
- Log Analytics Workspace
- Event Hub
- Azure Function
- Storage Account
- Key Vault

---

### Demo Assets

demo/

- sample-prompts/
- walkthrough/
- screenshots/
- recordings/

---

### Code

src/

function-exporter/

Responsibilities:

- Read exported telemetry
- Transform data
- Map Application Insights records to OpenInference attributes
- Forward telemetry to Arize

---

## Technical Architecture

Prompt Agent
    ↓
Application Insights
    ↓
Log Analytics
    ↓
Event Hub
    ↓
Azure Function
    ↓
Arize OTLP Endpoint
    ↓
Arize UI

Document this architecture using Mermaid diagrams.

---

## Telemetry Requirements

Capture:

### Trace Metadata

- trace_id
- span_id
- parent_span_id

### Request Metadata

- prompt
- completion
- model
- agent

### Usage Metrics

- prompt_tokens
- completion_tokens
- total_tokens

### Timing

- start_time
- duration
- latency

### Operational Metadata

- project_name
- environment
- workflow_id
- correlation_id

---

## Arize Requirements

Use Arize paid tier.

Secrets stored in Key Vault:

- ARIZE_SPACE_ID
- ARIZE_API_KEY

No secrets committed to source control.

---

## Documentation Requirements

Provide:

### Executive Diagram

Simple architecture

### Engineering Diagram

Detailed telemetry flow

### Operations Guide

How to:

- Troubleshoot telemetry
- Validate ingestion
- Verify token metrics
- Verify trace hierarchy

---

## Demonstration Walkthrough

Storyline:

1. User invokes Prompt Agent
2. Prompt Agent generates response
3. Trace appears in Application Insights
4. Queries show token usage
5. Export pipeline executes
6. Arize receives telemetry
7. Arize displays trace
8. Demonstrate investigation of execution details

---

## Stretch Goals

If time permits:

- OpenTelemetry Collector alternative
- Azure Monitor Pipeline evaluation
- Direct OTLP export comparison
- Hosted Agent vs Prompt Agent comparison
- Cost model analysis

---

## Expected Outputs

- Working demo environment
- Repeatable deployment scripts
- Customer-facing diagrams
- Architecture documentation
- Demo walkthrough guide
- Validation checklist

The end state should be a Microsoft field-ready demonstration that can be reused for UHG, CVS, Elevance, and other enterprise customers evaluating observability for Foundry Prompt Agents.