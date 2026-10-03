# infra/bicep

**Status: CURRENT-STATE (validated, implemented)**

Preferred Infrastructure-as-Code for this repo. Bicep modules provision the current-state Azure
resources backing the validated pipeline: Application Insights, Log Analytics Workspace, Event
Hub (namespace + hub), Azure Function App, and Key Vault.

Conventions (see `/.github/copilot-instructions.md` §6-§7):
- One module per resource type or tightly coupled resource group (e.g. `app-insights.bicep`,
  `event-hub.bicep`, `function-app.bicep`, `key-vault.bicep`).
- Parameterize environment, region, naming prefix, and SKU — no hardcoded names or
  environment-specific values.
- Deploys must be idempotent; validate with `az deployment ... what-if` before merge.
- Apply required tags (`environment`, `owner`, `project`, `costCenter`, `dataClassification`) and
  the `{project}-{env}-{resourceType}-{region}` naming pattern to every resource.
- No secrets as plaintext parameters — reference Key Vault via secure parameters only.
