// =============================================================================
// foundry-project.bicep
// Provisions an Azure AI Foundry hub + project (Microsoft.MachineLearningServices
// workspaces, kind 'Hub' and 'Project'). This is the root resource the Prompt
// Agent is deployed into and the source of OTel/OpenInference traces for the
// demo pipeline.
//
// Naming/tagging: resource names and required tags are built via the shared
// infra/modules/naming.bicep helpers (buildResourceName/buildRequiredTags),
// enforced repo-wide per issue #20. See /.github/copilot-instructions.md
// section 7 for the authoritative convention definition.
// =============================================================================

import { buildResourceName, buildRequiredTags, resourceTypeTokens } from 'naming.bicep'

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

@description('Short region token used in resource names, e.g. "eastus2". Kept separate from `location` so naming stays stable even if the ARM location string format changes.')
param regionToken string = 'eastus2'

@description('SKU name for the underlying Foundry hub/project workspaces. Maps to the Azure AI Foundry workspace SKU.')
@allowed([
  'Basic'
  'Free'
  'Standard'
  'Premium'
])
param skuName string = 'Basic'

@description('Friendly display name for the Foundry project, shown in the Foundry portal. Must not contain customer/tenant-identifying values.')
param projectDisplayName string = 'Foundry OTel to Arize Demo'

@description('Owner tag value (responsible team/individual) - required by repo tagging convention.')
param ownerTag string

@description('Cost center tag value - required by repo tagging convention.')
param costCenterTag string

@description('Data classification tag. Must be "synthetic" for all demo resources in this repo - never phi/pii.')
@allowed([
  'synthetic'
])
param dataClassificationTag string = 'synthetic'

@description('Optional resource ID of an existing Application Insights resource to associate with the Foundry hub for diagnostics (wired by the app-insights module, issue #16). Leave empty to skip association at hub-creation time.')
param applicationInsightsResourceId string = ''

@description('Optional resource ID of an existing Key Vault to associate with the Foundry hub (wired by the key-vault module, issue #18). Leave empty to skip association at hub-creation time.')
param keyVaultResourceId string = ''

@description('Optional resource ID of an existing Storage Account to associate with the Foundry hub. Leave empty to let Azure provision a managed default.')
param storageAccountResourceId string = ''

var hubName = buildResourceName(projectToken, environment, resourceTypeTokens.foundryHub, regionToken)
var projectName = buildResourceName(projectToken, environment, resourceTypeTokens.foundryProject, regionToken)
var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, dataClassificationTag)

// Azure AI Foundry hub - the parent workspace that owns shared dependencies
// (Key Vault, storage, App Insights) for one or more Foundry projects.
resource foundryHub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: hubName
  location: location
  tags: requiredTags
  sku: {
    name: skuName
    tier: skuName
  }
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: '${projectDisplayName} Hub'
    publicNetworkAccess: 'Enabled'
    keyVault: empty(keyVaultResourceId) ? null : keyVaultResourceId
    applicationInsights: empty(applicationInsightsResourceId) ? null : applicationInsightsResourceId
    storageAccount: empty(storageAccountResourceId) ? null : storageAccountResourceId
  }
}

// Azure AI Foundry project - the entity the Prompt Agent is deployed into and
// the source of the OTel/OpenInference traces consumed downstream.
resource foundryProject 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: projectName
  location: location
  tags: requiredTags
  sku: {
    name: skuName
    tier: skuName
  }
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: projectDisplayName
    hubResourceId: foundryHub.id
    publicNetworkAccess: 'Enabled'
  }
}

@description('Resource ID of the Foundry hub, needed by downstream modules (Key Vault role assignment scope, diagnostic settings, etc.).')
output hubResourceId string = foundryHub.id

@description('Resource ID of the Foundry project, the primary resource downstream Prompt Agent deployment and wiring should reference.')
output projectResourceId string = foundryProject.id

@description('Name of the Foundry project resource.')
output projectName string = foundryProject.name

@description('Discovery/API endpoint for the Foundry project, used by the Prompt Agent SDK and for downstream Application Insights/Key Vault wiring.')
output projectEndpoint string = foundryProject.properties.discoveryUrl

@description('System-assigned managed identity principal ID for the Foundry project. Placeholder for downstream RBAC role assignments (e.g. Key Vault Secrets User) - grant roles to this principal ID, do not embed credentials.')
output projectPrincipalId string = foundryProject.identity.principalId

@description('Tenant ID of the Foundry project system-assigned identity.')
output projectTenantId string = foundryProject.identity.tenantId
