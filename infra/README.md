# Infrastructure (`/infra`)

Bicep is the preferred Infrastructure-as-Code tool for this repo (see
`/.github/copilot-instructions.md` sections 5-7). This directory contains the
current-state infrastructure for `foundry-otel-to-arize-demo` - the resources
needed to run the demo pipeline described in the repo root README.

## Layout

```
infra/
├── bicepconfig.json            # Enables Bicep compile-time imports (needed by naming.bicep)
├── main.bicep                 # Deployment entry point, wires modules together
├── main.parameters.json       # Example/default parameter values (no secrets)
├── scripts/
│   └── validate-naming.ps1    # CI/pre-merge lint: fails if a module skips the shared naming/tagging helpers (issue #20)
└── modules/
    ├── naming.bicep           # Shared naming/tagging helpers (issue #20) ✅ - import this from every new module
    ├── foundry-project.bicep  # Azure AI Foundry hub + project (issue #15) ✅
    ├── app-insights.bicep     # Log Analytics + Application Insights (issue #16) ✅
    ├── key-vault.bicep        # Key Vault (RBAC) + managed identity wiring pattern (issue #18) ✅
    └── networking.bicep       # Optional private endpoint module (issue #21)
```

Each module is independently parameterized (no hardcoded names, regions, or
environment-specific values) and idempotent - re-running a deployment with
the same parameters must not fail or duplicate resources.

## Naming convention

Resource names follow: `{project}-{env}-{resourceType}-{region}`

Example: `fotoa-demo-aiproj-eastus2`, `fotoa-dev-kv-eastus2`.

- `{project}`: short project token (`fotoa` for foundry-otel-to-arize-demo)
- `{env}`: `dev`, `demo`, or `prod`
- `{resourceType}`: abbreviated resource type (e.g. `aihub`, `aiproj`, `appi`, `law`, `kv`, `func`)
- `{region}`: short Azure region token (e.g. `eastus2`)

See `modules/naming.bicep` (issue #20) for the shared Bicep implementation of
this pattern, and `/.github/copilot-instructions.md` section 7 for the
authoritative definition. Every module **must** `import { buildResourceName,
buildRequiredTags, resourceTypeTokens } from 'naming.bicep'` and use those
functions to build its resource name(s) and `tags:` object - do not re-derive
the pattern or the tag keys locally. `infra/bicepconfig.json` enables Bicep's
`compileTimeImports` experimental feature flag that some Bicep CLI versions
still require for cross-file `import { ... } from '...'` statements.

### Enforcing the convention (issue #20)

`infra/scripts/validate-naming.ps1` is a lightweight static check (no Azure
or Bicep-compiler dependency) that fails if any module under `infra/modules`
(other than `naming.bicep` itself) does not import and call
`buildResourceName`/`buildRequiredTags`. Run it locally:

```
pwsh ./infra/scripts/validate-naming.ps1
```

**CI wiring status:** a `.github/workflows/infra-validate.yml` workflow
(running this script plus `az bicep build` on every PR touching `infra/**`)
was authored and verified locally, but could not be pushed in this pass -
the `gh`/git credential in this automated environment lacks the `workflow`
OAuth scope required to create or update workflow files
(`refusing to allow an OAuth App to create or update workflow ... without
'workflow' scope`). **Manual pre-merge step until that workflow is added:**
run `pwsh ./infra/scripts/validate-naming.ps1` and `az bicep build`/
`az deployment group what-if` locally before merging any `infra/**` PR. A
team member with `workflow` scope should add the CI workflow as a fast
follow-up (the script itself is already committed and ready to wire in).

## Required tags

Every provisioned resource must carry:

| Tag | Purpose |
|---|---|
| `environment` | dev / demo / prod |
| `owner` | responsible team/individual |
| `project` | `foundry-otel-to-arize-demo` |
| `costCenter` | cost allocation tag |
| `dataClassification` | must be `synthetic` for every resource in this repo |

## Secrets and managed identity pattern

- **No secrets are ever passed as Bicep parameters or stored in source.** Every
  secret-capable resource (Foundry project, Function App, any future compute)
  is wired with a **system-assigned managed identity** and granted
  least-privilege RBAC access to Key Vault (`Key Vault Secrets User` for
  readers) rather than embedding keys/connection strings.
- Application Insights connection strings are stored in Key Vault as a secret
  by the `app-insights.bicep` module's wiring step - never emitted as a plain
  Bicep output.
- Actual third-party secrets (e.g. the Arize API key) are entered into Key
  Vault manually post-deploy by an operator and are never committed to this
  repository.

### Granting a compute resource access to Key Vault

Pattern used by every module that needs to read secrets (see
`modules/key-vault.bicep` for the reusable role-assignment resource):

1. Provision the compute resource with `identity: { type: 'SystemAssigned' }`.
2. Capture its `identity.principalId` as a module output.
3. In the Key Vault module (or a cross-wiring deployment that runs after both
   resources exist), create a `Microsoft.Authorization/roleAssignments`
   resource scoped to the Key Vault, assigning the
   `Key Vault Secrets User` role (`4633458b-17de-408a-b874-0445c86b69e6`) to
   that principal ID.
4. The compute resource reads secrets via `https://<vault-name>.vault.azure.net/secrets/<name>`
   using its managed identity token - no key material is ever configured in
   app settings or source.

This is a **two-phase deploy**: provision resource shells independently, then
run a follow-up wiring deployment (or a second `module` block in `main.bicep`)
that cross-references principal IDs once both sides exist. See
`.squad/decisions.md` ("Function App ↔ Key Vault sequencing") for the
reasoning behind this split.

## Network posture

**Default (demo) posture: public network access, secured by Azure AD/RBAC
auth** - no private endpoints are deployed by default, to keep demo setup
time low for prospects evaluating the pipeline. See `modules/networking.bicep`
(issue #21) for the optional, parameterized private-endpoint variant and the
full rationale/validation notes.

## Validating a deployment

```
az deployment group what-if -g <resource-group> -f infra/main.bicep -p infra/main.parameters.json
az deployment group create  -g <resource-group> -f infra/main.bicep -p infra/main.parameters.json
```

> **Note:** `what-if`/`az bicep build` validation for the modules in this
> directory could not be executed from the automated environment that
> authored them (no Azure subscription context / `az` CLI profile access
> available in that sandbox). Templates were manually reviewed for Bicep
> syntax correctness. Run `az bicep build` and `az deployment group what-if`
> against a real/scratch resource group before merging or demoing.
