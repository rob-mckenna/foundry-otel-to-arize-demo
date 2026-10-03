# Next Actions

Prioritized list of what to do first, referencing real issue numbers and milestones. Work top to bottom —
later items generally depend on earlier ones.

1. **Scaffold the repo structure** — [#12 Scaffold repo structure](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/12)
   (`/src`, `/infra`, `/docs`, `/tests`, current/future-state boundary). *Milestone 1: Foundation.*
2. **Provision the Foundry project + base resource group** — [#15 Provision Foundry project](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/15).
   *Milestone 1: Foundation.*
3. **Provision Application Insights + Log Analytics workspace** — [#16](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/16).
   *Milestone 1: Foundation.*
4. **Provision Key Vault (RBAC mode) and wire managed identities** — [#18](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/18)
   (resolves the Key Vault/Function App sequencing question — provision shells first, cross-wire RBAC
   second, not a circular blocker). *Milestone 1: Foundation.*
5. **Provision the Azure Function App shell** — [#19](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/19),
   immediately after #18 so RBAC wiring in the same deploy has a target identity. *Milestone 1: Foundation.*
6. **Enforce naming/tagging convention across all IaC** — [#20](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/20),
   do this early so every subsequent resource follows it. *Milestone 1: Foundation.*
7. **Scaffold the Prompt Agent project and OTel SDK bootstrap** — [#24](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/24),
   [#26 OTel SDK setup](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/26). *Milestone 1: Foundation.*
8. **Implement the core prompt/response flow with synthetic scenarios** — [#25](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/25),
   the critical-path deliverable all demo steps depend on. *Milestone 1: Foundation.*
9. **Instrument every call with OpenInference-compliant spans** — [#27](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/27),
   [#28 OpenInference attribute mapping](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/28).
   *Milestone 1: Foundation.*
10. **Provision Event Hub and define the Log Analytics export baseline** — [#17](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/17),
    [#35](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/35). *Milestone 2: Telemetry Pipeline.*
11. **Write the Azure Monitor → OTLP field-mapping doc, then implement the Function's transform** — [#36](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/36),
    required before any export-pipeline validation can run. *Milestone 2: Telemetry Pipeline.*
12. **Implement OTLP export conformance to Arize** — [#38](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/38).
    *Milestone 3: Arize Integration.*
13. **Run the Demo Validation Plan steps 1–6** (Prompt Agent execution through export-pipeline execution) —
    [#49](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/49)–[#54](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/54),
    see [`docs/demo-validation-plan.md`](./demo-validation-plan.md). *Milestone 3: Arize Integration.*
14. **Run the remaining validation steps (transformation, Arize ingestion/visualization, error/retry)** —
    [#55](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/55)–[#58](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/58),
    then write the end-to-end demo runbook — [#45](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/45).
    *Milestone 4: Customer Demo Readiness.*
15. **Finish documentation and the Future-State design doc in parallel** — [#59 README accuracy pass](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/59),
    [#63 Future-state direct-OTLP design doc](https://github.com/rob-mckenna/foundry-otel-to-arize-demo/issues/63).
    *Milestone 4: Customer Demo Readiness / Milestone 5: Future-State Design.*

**Known manual step before item 1 is fully demo-ready:** the GitHub Project (v2) board could not be created
by this automation (missing `project` OAuth scope) — see `SQUAD_BOOTSTRAP.md` for the 2-minute manual setup
steps. Do this once, early, so issues can be triaged visually as work starts.
