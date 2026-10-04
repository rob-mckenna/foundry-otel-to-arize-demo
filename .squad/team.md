# Squad Team

> foundry-otel-to-arize-demo

## Coordinator

| Name | Role | Notes |
|------|------|-------|
| Squad | Coordinator | Routes work, enforces handoffs and reviewer gates. |

## Members

| Name | Role | Charter | Status |
|------|------|---------|--------|
| Lead | Architect / Tech Lead | .squad/agents/lead/charter.md | 🏗️ Active |
| Infra | Infrastructure / DevOps Engineer | .squad/agents/infra/charter.md | ⚙️ Active |
| Agent | Prompt Agent Developer | .squad/agents/agent/charter.md | 🔧 Active |
| Telemetry | Observability / Telemetry Pipeline Engineer | .squad/agents/telemetry/charter.md | 📊 Active |
| QA | Tester / Technical Writer | .squad/agents/qa/charter.md | 🧪 Active |
| Scribe | Scribe | .squad/agents/scribe/charter.md | 📋 Scribe |
| Ralph | Work Monitor | .squad/agents/ralph/charter.md | 🔄 Ralph |
| Rai | RAI Reviewer | .squad/agents/Rai/charter.md | 🛡️ RAI |
| Fact Checker | Fact Checker | .squad/agents/fact-checker/charter.md | 🔍 Verifier |


## Coding Agent

<!-- copilot-auto-assign: false -->

| Name | Role | Charter | Status |
|------|------|---------|--------|
| @copilot | Coding Agent | — | 🤖 Coding Agent |

### Capabilities

**🟢 Good fit — auto-route when enabled:**
- Bug fixes with clear reproduction steps
- Test coverage (adding missing tests, fixing flaky tests)
- Lint/format fixes and code style cleanup
- Dependency updates and version bumps
- Small isolated features with clear specs
- Boilerplate/scaffolding generation
- Documentation fixes and README updates

**🟡 Needs review — route to @copilot but flag for squad member PR review:**
- Medium features with clear specs and acceptance criteria
- Refactoring with existing test coverage
- API endpoint additions following established patterns
- Migration scripts with well-defined schemas

**🔴 Not suitable — route to squad member instead:**
- Architecture decisions and system design
- Multi-system integration requiring coordination
- Ambiguous requirements needing clarification
- Security-critical changes (auth, encryption, access control)
- Performance-critical paths requiring benchmarking
- Changes requiring cross-team discussion

## Project Context

- **Owner:** Rob McKenna
- **Project:** foundry-otel-to-arize-demo — reusable observability demo for Microsoft Foundry Prompt Agents (OpenTelemetry/OpenInference → Application Insights → Arize), targeted at enterprise healthcare customers (UnitedHealth Group, CVS Health, Elevance Health, etc.)
- **Created:** 2026-10-03
- **Naming:** Descriptive (no themed universe)
