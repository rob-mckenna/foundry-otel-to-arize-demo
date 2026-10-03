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
//
// Naming/tagging: every module below imports and uses the shared helpers in
// modules/naming.bicep (buildResourceName/buildRequiredTags), enforced via
// infra/scripts/validate-naming.ps1 (issue #20) - do not add a new module
// that re-derives the naming/tag pattern locally.
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

@description('Log Analytics data retention in days (demo cost control).')
@minValue(30)
@maxValue(730)
param logAnalyticsRetentionInDays int = 30

@description('Daily data ingestion cap in GB for the Log Analytics workspace (demo cost control). -1 disables the cap.')
param logAnalyticsDailyQuotaGb int = 1

@description('Key Vault SKU: standard or premium (HSM-backed).')
@allowed([
  'standard'
  'premium'
])
param keyVaultSkuName string = 'standard'

@description('Key Vault soft-delete retention period in days (minimum 7, Azure default 90).')
@minValue(7)
@maxValue(90)
param keyVaultSoftDeleteRetentionInDays int = 90

@description('Optional private-endpoint upgrade path (issue #21). Defaults to false - the demo baseline posture is public access + Azure AD/RBAC auth. Set true to additionally deploy private endpoints for the Key Vault and Foundry project into a scratch VNet (or an existing subnet via networkExistingSubnetResourceId).')
param enablePrivateEndpoints bool = false

@description('When enablePrivateEndpoints is true: if true, provisions a scratch VNet+subnet for the private endpoints; if false, networkExistingSubnetResourceId must be supplied instead.')
param networkCreateVirtualNetwork bool = true

@description('Resource ID of an existing subnet to deploy private endpoints into, used only when enablePrivateEndpoints is true and networkCreateVirtualNetwork is false.')
param networkExistingSubnetResourceId string = ''

@description('Event Hub namespace SKU (issue #17). Standard is required for consumer groups.')
@allowed([
  'Basic'
  'Standard'
])
param eventHubSkuName string = 'Standard'

@description('Event Hub namespace throughput units, sized for demo-scale load (issue #17).')
@minValue(1)
@maxValue(20)
param eventHubThroughputUnits int = 1

@description('Event Hub partition count, sized for a single-Function-App demo consumer (issue #17).')
@minValue(1)
@maxValue(32)
param eventHubPartitionCount int = 2

@description('Function App hosting plan tier (issue #19). "Consumption" (cold-start tolerant, near-zero idle cost) is the demo default; "Premium" is a single-parameter upgrade for POCs needing no cold start/VNet integration.')
@allowed([
  'Consumption'
  'Premium'
])
param functionHostingPlanTier string = 'Consumption'

@description('Python runtime version for the Function App telemetry transform pipeline (issue #19).')
@allowed([
  '3.10'
  '3.11'
  '3.12'
])
param functionPythonVersion string = '3.11'

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

module appInsights 'modules/app-insights.bicep' = {
  name: 'app-insights-deployment'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    retentionInDays: logAnalyticsRetentionInDays
    dailyQuotaGb: logAnalyticsDailyQuotaGb
    foundryProjectName: foundryProject.outputs.projectName
    // Key Vault now exists (issue #18) - wire the connection string into it
    // as a secret instead of emitting it as a plaintext output.
    keyVaultName: keyVault.outputs.keyVaultName
  }
}

// Key Vault shell + phase-2 cross-wiring: the Foundry project's
// system-assigned managed identity is granted "Key Vault Secrets User" so it
// can read secrets (e.g. the Arize API key, entered manually post-deploy).
// The Function App module (issue #19, below) grants itself "Key Vault
// Secrets User" directly via its own keyVaultName-scoped role assignment,
// so no readerPrincipalIds cross-wire is needed here for it.
module keyVault 'modules/key-vault.bicep' = {
  name: 'key-vault-deployment'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    skuName: keyVaultSkuName
    softDeleteRetentionInDays: keyVaultSoftDeleteRetentionInDays
    readerPrincipalIds: [
      foundryProject.outputs.projectPrincipalId
    ]
  }
}

// Event Hub namespace + hub (issue #17): sits between Application
// Insights/Log Analytics (export source) and the Azure Function transform
// pipeline (issue #19). RBAC-only by default - the Function App module
// below grants itself "Azure Event Hubs Data Receiver" on this namespace
// directly (via its own eventHubNamespaceResourceId-scoped role
// assignment), so no receiverPrincipalIds cross-wire is needed here.
module eventHub 'modules/event-hub.bicep' = {
  name: 'event-hub-deployment'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    skuName: eventHubSkuName
    throughputUnits: eventHubThroughputUnits
    partitionCount: eventHubPartitionCount
  }
}

// Azure Function App telemetry transform pipeline (issue #19): consumes
// from the Event Hub above and transforms/forwards telemetry on toward
// Arize (transform code deployed separately by Telemetry, Milestone 2).
// Identity-based bindings only - the module grants itself "Azure Event Hubs
// Data Receiver" on eventHub (via eventHubNamespaceResourceId) and "Key
// Vault Secrets User" on keyVault (via keyVaultName) directly, so the whole
// chain is RBAC-wired in this single deployment with no follow-up required.
module functionApp 'modules/function-app.bicep' = {
  name: 'function-app-deployment'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    hostingPlanTier: functionHostingPlanTier
    pythonVersion: functionPythonVersion
    keyVaultName: keyVault.outputs.keyVaultName
    eventHubNamespaceFqdn: eventHub.outputs.eventHubNamespaceFqdn
    eventHubNamespaceResourceId: eventHub.outputs.eventHubNamespaceResourceId
  }
}

@description('Resource ID of the Foundry project - the entry point the Prompt Agent is deployed into.')
output foundryProjectResourceId string = foundryProject.outputs.projectResourceId

@description('Foundry project discovery/API endpoint.')
output foundryProjectEndpoint string = foundryProject.outputs.projectEndpoint

@description('Foundry project system-assigned managed identity principal ID, for downstream Key Vault RBAC wiring.')
output foundryProjectPrincipalId string = foundryProject.outputs.projectPrincipalId

@description('Resource ID of the Log Analytics workspace.')
output logAnalyticsWorkspaceId string = appInsights.outputs.logAnalyticsWorkspaceId

@description('Resource ID of the Application Insights resource.')
output appInsightsResourceId string = appInsights.outputs.appInsightsResourceId

@description('Resource ID of the Key Vault.')
output keyVaultResourceId string = keyVault.outputs.keyVaultResourceId

@description('Name of the Key Vault - needed by downstream modules (e.g. a future Function App) to wire additional RBAC role assignments.')
output keyVaultName string = keyVault.outputs.keyVaultName

@description('Name of the Event Hub namespace (issue #17) - needed by the Azure Function transform pipeline (issue #19) to bind via identity-based RBAC.')
output eventHubNamespaceName string = eventHub.outputs.eventHubNamespaceName

@description('Name of the Event Hub (within the namespace) that the transform pipeline should consume from.')
output eventHubName string = eventHub.outputs.eventHubName

@description('Name of the consumer group provisioned for the Azure Function transform pipeline (issue #19).')
output eventHubFunctionConsumerGroupName string = eventHub.outputs.functionConsumerGroupName

@description('Name of the Function App telemetry transform pipeline (issue #19).')
output functionAppName string = functionApp.outputs.functionAppName

@description('Default host name of the Function App, e.g. <name>.azurewebsites.net.')
output functionAppDefaultHostName string = functionApp.outputs.functionAppDefaultHostName

@description('System-assigned managed identity principal ID of the Function App.')
output functionAppPrincipalId string = functionApp.outputs.functionAppPrincipalId

@description('True if the Function App is on the Premium (EP1) hosting plan instead of the Consumption (Y1) default.')
output functionAppIsPremiumHostingPlan bool = functionApp.outputs.isPremiumHostingPlan

// Optional private-endpoint upgrade path (issue #21) - disabled by default.
// See infra/README.md "Network posture" for the baseline-vs-private-endpoint
// rationale and infra/modules/networking.bicep for implementation notes.
module networking 'modules/networking.bicep' = {
  name: 'networking-deployment'
  params: {
    enablePrivateEndpoints: enablePrivateEndpoints
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    createVirtualNetwork: networkCreateVirtualNetwork
    existingSubnetResourceId: networkExistingSubnetResourceId
    privateEndpointTargets: enablePrivateEndpoints ? [
      {
        name: 'kv'
        targetResourceId: keyVault.outputs.keyVaultResourceId
        groupId: 'vault'
      }
      {
        name: 'aiproj'
        targetResourceId: foundryProject.outputs.projectResourceId
        groupId: 'amlworkspace'
      }
    ] : []
  }
}

@description('True if this deployment provisioned private endpoints (issue #21 upgrade path) rather than the public-access demo baseline.')
output privateEndpointsEnabled bool = networking.outputs.privateEndpointsEnabled
