# infra/terraform

**Status: CURRENT-STATE (validated, implemented) — optional alternative**

Optional Terraform alternative to `/infra/bicep`, mirroring the same module boundaries
(Application Insights, Log Analytics, Event Hub, Function App, Key Vault). Bicep is this repo's
preferred IaC tool (see `/.github/copilot-instructions.md` §5-§6); use Terraform here only where a
team already maintains Terraform elsewhere, and do not mix both tools for the same resource.

Same conventions apply as `/infra/bicep`: parameterized environment/region/naming/SKU, idempotent
deploys (validate with `terraform plan`), required tags, and no plaintext secrets.
