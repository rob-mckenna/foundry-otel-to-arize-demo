// Function operational telemetry must never share the exported agent workspace.
import { buildResourceName, buildRequiredTags } from 'naming.bicep'

@minLength(2)
@maxLength(10)
param projectToken string
@allowed(['dev', 'demo', 'prod'])
param environment string
param location string
param regionToken string
@minLength(1)
param ownerTag string
@minLength(1)
param costCenterTag string
@minValue(30)
@maxValue(90)
param retentionInDays int = 30
@minValue(1)
@maxValue(10)
param dailyQuotaGb int = 1
@allowed(['PerGB2018'])
param workspaceSkuName string = 'PerGB2018'
@minLength(1)
param keyVaultName string
@minLength(1)
param functionHealthConnectionStringSecretName string = 'function-health-connection-string'

var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic')

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: buildResourceName(projectToken, environment, 'funclaw', regionToken)
  location: location
  tags: requiredTags
  properties: {
    sku: {
      name: workspaceSkuName
    }
    retentionInDays: retentionInDays
    workspaceCapping: {
      dailyQuotaGb: dailyQuotaGb
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource component 'Microsoft.Insights/components@2020-02-02' = {
  name: buildResourceName(projectToken, environment, 'funcappi', regionToken)
  location: location
  tags: requiredTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource connectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: functionHealthConnectionStringSecretName
  properties: {
    value: component.properties.ConnectionString
    contentType: 'text/plain'
  }
}

output healthWorkspaceResourceId string = workspace.id
output healthWorkspaceName string = workspace.name
output healthComponentResourceId string = component.id
output healthComponentName string = component.name
output functionHealthSecretUri string = connectionStringSecret.properties.secretUriWithVersion
