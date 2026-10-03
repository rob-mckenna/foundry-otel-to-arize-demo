// =============================================================================
// app-insights.bicep
// Provisions a Log Analytics workspace and a workspace-based Application
// Insights resource to receive OTel/OpenInference traces from the Foundry
// Prompt Agent. Retention and daily data cap are parameterized to keep demo
// costs bounded. Optionally wires:
//   - Diagnostic settings from an existing Foundry project to this workspace
//     (managed-identity/diagnostic-settings based, not instrumentation key)
//   - The Application Insights connection string into an existing Key Vault
//     secret, so the plaintext connection string is never emitted as a
//     deployment output (see acceptance criteria on issue #16).
//
// Naming/tagging: {project}-{env}-{resourceType}-{region}, e.g.
//   fotoa-demo-law-eastus2 / fotoa-demo-appi-eastus2
// Issue #20 will retrofit this module onto the shared naming.bicep helper.
// =============================================================================

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

@description('Data classification tag. Must be "synthetic" for all demo resources in this repo.')
@allowed([
  'synthetic'
])
param dataClassificationTag string = 'synthetic'

@description('Log Analytics data retention in days. Defaults to 30 for demo cost control.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('Daily data ingestion cap in GB for the Log Analytics workspace, to prevent runaway demo costs. -1 disables the cap.')
param dailyQuotaGb int = 1

@description('Optional name of an existing Foundry project workspace (same resource group) to wire diagnostic settings from, forwarding its logs/metrics to this Log Analytics workspace. Leave empty to skip - diagnostic wiring can be added in a later deployment once the Foundry project exists.')
param foundryProjectName string = ''

@description('Optional name of an existing Key Vault (same resource group) to store the Application Insights connection string in as a secret. Leave empty to skip - the connection string is never emitted as a plaintext output regardless.')
param keyVaultName string = ''

@description('Name of the Key Vault secret used to store the Application Insights connection string, when keyVaultName is provided.')
param connectionStringSecretName string = 'appinsights-connection-string'

var namingSuffix = '${projectToken}-${environment}'
var workspaceName = '${namingSuffix}-law-${regionToken}'
var appInsightsName = '${namingSuffix}-appi-${regionToken}'

var requiredTags = {
  environment: environment
  owner: ownerTag
  project: 'foundry-otel-to-arize-demo'
  costCenter: costCenterTag
  dataClassification: dataClassificationTag
}

var storeConnectionStringInKeyVault = !empty(keyVaultName)
var wireFoundryDiagnostics = !empty(foundryProjectName)

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: requiredTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    workspaceCapping: {
      dailyQuotaGb: dailyQuotaGb
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: requiredTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Reference to the existing Foundry project (issue #15) to wire diagnostic
// settings from, when the caller provides a name. Assumes same resource
// group - cross-resource-group wiring should pass a fully qualified scope
// via a separate cross-wiring deployment.
resource existingFoundryProject 'Microsoft.MachineLearningServices/workspaces@2024-10-01' existing = if (wireFoundryDiagnostics) {
  name: foundryProjectName
}

resource foundryDiagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (wireFoundryDiagnostics) {
  name: '${namingSuffix}-diag-to-law'
  scope: existingFoundryProject
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// Reference to an existing Key Vault (issue #18) to store the connection
// string in, when the caller provides a name. This keeps the Application
// Insights connection string out of plaintext deployment outputs entirely.
resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (storeConnectionStringInKeyVault) {
  name: keyVaultName
}

resource connectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (storeConnectionStringInKeyVault) {
  parent: existingKeyVault
  name: connectionStringSecretName
  properties: {
    value: appInsights.properties.ConnectionString
    contentType: 'text/plain'
  }
}

@description('Resource ID of the Log Analytics workspace.')
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id

@description('Resource ID of the Application Insights resource.')
output appInsightsResourceId string = appInsights.id

@description('Application Insights resource name.')
output appInsightsName string = appInsights.name

@description('True if the connection string was stored in Key Vault as part of this deployment.')
output connectionStringStoredInKeyVault bool = storeConnectionStringInKeyVault

@description('Key Vault secret URI for the Application Insights connection string, when keyVaultName was supplied. Empty string otherwise - callers must not expect a plaintext connection string output from this module.')
output connectionStringSecretUri string = storeConnectionStringInKeyVault ? connectionStringSecret.properties.secretUri : ''
