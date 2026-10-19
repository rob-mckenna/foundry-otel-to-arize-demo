// =============================================================================
// app-insights.bicep
// Provisions a Log Analytics workspace and a workspace-based Application
// Insights resource to receive OTel/OpenInference traces from the Foundry
// Prompt Agent. Retention and daily data cap are parameterized to keep demo
// costs bounded. Tracing is owned by the modern connection module, not a
// diagnostic setting. Secret custody is an operator prerequisite; a private
// vault is not bootstrapped by weakening network controls.
//
// Naming/tagging: resource names and required tags are built via the shared
// infra/modules/naming.bicep helpers (buildResourceName/buildRequiredTags),
// enforced repo-wide per issue #20.
// =============================================================================

import { buildResourceName, buildRequiredTags, resourceTypeTokens } from 'naming.bicep'

@description('Short project token used in resource names, e.g. "fotoa" for foundry-otel-to-arize-demo.')
@minLength(2)
@maxLength(10)
param projectToken string

@description('Environment token used in resource names and tags: dev, demo, or prod.')
@allowed([
  'dev'
  'demo'
  'prod'
])
param environment string

@description('Azure region for the deployment (full ARM location name, e.g. eastus2).')
param location string

@description('Short region token used in resource names, e.g. "eastus2".')
param regionToken string

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

@minLength(1)
param eventHubNamespaceResourceId string
@minLength(1)
param eventHubName string

// Optional independently approved secret write, retained for component custody.
// Fresh main does not bootstrap a private vault or claim ARM can reach it.
param keyVaultName string = ''
param connectionStringSecretName string = 'appinsights-connection-string'

var workspaceName = buildResourceName(projectToken, environment, resourceTypeTokens.logAnalyticsWorkspace, regionToken)
var appInsightsName = buildResourceName(projectToken, environment, resourceTypeTokens.applicationInsights, regionToken)
var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, dataClassificationTag)

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

  resource exportRule 'Microsoft.OperationalInsights/workspaces/dataExports@2023-09-01' = {
    parent: logAnalyticsWorkspace
    name: 'telemetry-to-eventhub'
    properties: {
      destination: {
        resourceId: eventHubNamespaceResourceId
        metaData: {
          eventHubName: eventHubName
        }
      }
      tableNames: [
        'AppDependencies'
        'AppRequests'
        'AppGenAIContent'
      ]
      enable: true
    }
  }
  resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (!empty(keyVaultName)) {
    name: keyVaultName
  }
  resource connectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(keyVaultName)) {
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

output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
output exportRuleResourceId string = exportRule.id
output connectionStringStoredInKeyVault bool = !empty(keyVaultName)
output connectionStringSecretUri string = !empty(keyVaultName) ? connectionStringSecret!.properties.secretUri : ''
