// =============================================================================
// main.bicep
// Deployment entry point for the foundry-otel-to-arize-demo infrastructure.
//
// Modules are added incrementally (see /infra/README.md and Milestone 1:
// Foundation issues #15/#16/#18/#20/#21). Each module is independently
// parameterized and idempotent - re-running this deployment with the same
// parameters must not fail or duplicate resources.
//
// Scope: resource group. Deploy with:
//   az deployment group create -g <rg> -f infra/main.bicep -p infra/main.parameters.json
//   az deployment group what-if -g <rg> -f infra/main.bicep -p infra/main.parameters.json
// =============================================================================

targetScope = 'resourceGroup'

@description('Short project token used in resource names, e.g. "fotoa" for foundry-otel-to-arize-demo.')
@minLength(2)
@maxLength(10)
param projectToken string = 'fotoa'

@description('Environment token used in resource names and tags: dev, demo, or prod.')
@allowed([
  'dev'
  'demo'
  'prod'
])
param environment string = 'demo'

@description('Azure region for the deployment (full ARM location name, e.g. eastus2).')
param location string = resourceGroup().location

@description('Short region token used in resource names, e.g. "eastus2".')
param regionToken string = 'eastus2'

@description('Owner tag value (responsible team/individual) - required by repo tagging convention.')
param ownerTag string

@description('Cost center tag value - required by repo tagging convention.')
param costCenterTag string

@description('SKU name for the Foundry hub/project workspaces.')
@allowed([
  'Basic'
  'Free'
  'Standard'
  'Premium'
])
param foundrySkuName string = 'Basic'

@description('Friendly display name for the Foundry project.')
param projectDisplayName string = 'Foundry OTel to Arize Demo'

module foundryProject 'modules/foundry-project.bicep' = {
  name: 'foundry-project-deployment'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    skuName: foundrySkuName
    projectDisplayName: projectDisplayName
    ownerTag: ownerTag
    costCenterTag: costCenterTag
  }
}

@description('Resource ID of the Foundry project - the entry point the Prompt Agent is deployed into.')
output foundryProjectResourceId string = foundryProject.outputs.projectResourceId

@description('Foundry project discovery/API endpoint.')
output foundryProjectEndpoint string = foundryProject.outputs.projectEndpoint

@description('Foundry project system-assigned managed identity principal ID, for downstream Key Vault RBAC wiring.')
output foundryProjectPrincipalId string = foundryProject.outputs.projectPrincipalId
