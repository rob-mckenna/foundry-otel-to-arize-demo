// Fresh private Premium shell. Package publication/trigger synchronization and
// private runtime readiness are separate approved operations, not Bicep outputs.
// No Azure Files dependency: private Blob package URL + system MI.
// https://learn.microsoft.com/azure/azure-functions/storage-considerations#create-an-app-without-azure-files
import { buildResourceName, buildRequiredTags, resourceTypeTokens } from 'naming.bicep'
import { privateDnsZoneIds } from 'networking.bicep'

@export()
@discriminator('mode')
type functionSecretReferences = {
  mode: 'freshVault'
} | {
  mode: 'existing'
  applicationInsightsSecretUri: string
  arizeEndpointSecretUri: string
  arizeSpaceIdSecretUri: string
  arizeApiKeySecretUri: string
}

param projectToken string
param environment string
param location string
param regionToken string
param ownerTag string
param costCenterTag string
@allowed(['3.10', '3.11', '3.12'])
param pythonVersion string = '3.11'
@description('Single-app EP1 plan/app ceiling, including prewarmed instances. Not a billing or transient replacement-instance guarantee.')
@allowed([1])
param maximumInstances int = 1
@minLength(1)
param keyVaultName string
@minLength(1)
param eventHubNamespaceFqdn string
@minLength(6)
param eventHubNamespaceName string
@minLength(1)
param eventHubName string
@minLength(1)
param eventHubConsumerGroupName string
param eventHubConnectionSettingPrefix string = 'EventHubConnection'
@minLength(1)
param functionIntegrationSubnetResourceId string
@minLength(1)
param privateEndpointSubnetResourceId string
param privateDnsZoneResourceIds privateDnsZoneIds
@description('Immutable ZIP blob name under private function-packages in host storage. Upload separately; no SAS or remote-build fallback.')
@minLength(1)
param functionPackageBlobName string
param appInsightsConnectionStringSecretName string = 'appinsights-connection-string'
param extraKeyVaultReferenceAppSettings { settingName: string, secretName: string }[] = []
@description('Reference identifiers only. Existing custody needs separately authorized secret-scoped Secrets User grants for this NEW Function MI; this module never grants access on an external vault.')
param keyVaultReferences functionSecretReferences = { mode: 'freshVault' }
@description('Container preparation only; fresh main sets true. Never enables runtime/cutover.')
param prepareDurableGenAIContainer bool = false

var storageAccountName = toLower(replace(buildResourceName(projectToken, environment, resourceTypeTokens.storageAccount, regionToken), '-', ''))
var hostingPlanName = buildResourceName(projectToken, environment, 'plan', regionToken)
var functionAppName = buildResourceName(projectToken, environment, resourceTypeTokens.functionApp, regionToken)
var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic')

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: requiredTags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'None'
    }
  }
}

resource applicationBlobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' existing = {
  parent: storageAccount
  name: 'default'
}
resource genAICorrelationContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = if (prepareDurableGenAIContainer) {
  parent: applicationBlobService
  name: 'genai-correlation'
  properties: {
    publicAccess: 'None'
  }
}
resource packageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: applicationBlobService
  name: 'function-packages'
  properties: {
    publicAccess: 'None'
  }
}
  module storagePrivateEndpoints 'private-endpoints.bicep' = {
    name: 'host-storage-private-endpoints'
    params: {
      projectToken: projectToken
      environment: environment
      location: location
      regionToken: regionToken
      ownerTag: ownerTag
      costCenterTag: costCenterTag
      subnetResourceId: privateEndpointSubnetResourceId
      targets: [
        {
          name: 'blob'
          targetResourceId: storageAccount.id
          groupId: 'blob'
          privateDnsZoneResourceIds: [privateDnsZoneResourceIds.blob]
        }
        {
          name: 'queue'
          targetResourceId: storageAccount.id
          groupId: 'queue'
          privateDnsZoneResourceIds: [privateDnsZoneResourceIds.queue]
        }
        {
          name: 'table'
          targetResourceId: storageAccount.id
          groupId: 'table'
          privateDnsZoneResourceIds: [privateDnsZoneResourceIds.table]
        }
      ]
    }
  }
resource hostingPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: hostingPlanName
  location: location
  tags: requiredTags
  kind: 'functionapp,linux'
  sku: {
    name: 'EP1'
    tier: 'ElasticPremium'
    capacity: 1
  }
  properties: {
    reserved: true
    maximumElasticWorkerCount: maximumInstances
  }
}

var baseAppSettings = [
  { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
  { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
  { name: 'AzureWebJobsStorage__accountName', value: storageAccount.name }
  { name: 'AzureWebJobsStorage__credential', value: 'managedidentity' }
  { name: '${eventHubConnectionSettingPrefix}__fullyQualifiedNamespace', value: eventHubNamespaceFqdn }
  { name: '${eventHubConnectionSettingPrefix}__credential', value: 'managedidentity' }
  { name: 'EVENT_HUB_CONNECTION_SETTING_PREFIX', value: eventHubConnectionSettingPrefix }
  { name: 'EVENT_HUB_NAME', value: eventHubName }
  { name: 'EVENT_HUB_CONSUMER_GROUP', value: eventHubConsumerGroupName }
  { name: 'AzureWebJobs.TelemetryTransform.Disabled', value: 'true' }
  { name: 'AzureWebJobs.DurableGenAIOutbox.Disabled', value: 'true' }
  {
    name: 'WEBSITE_RUN_FROM_PACKAGE'
    value: 'https://${storageAccount.name}.blob.${az.environment().suffixes.storage}/function-packages/${functionPackageBlobName}'
  }
  { name: 'WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID', value: 'SystemAssigned' }
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    value: keyVaultReferences.mode == 'existing'
      ? '@Microsoft.KeyVault(SecretUri=${keyVaultReferences.applicationInsightsSecretUri})'
      : '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${appInsightsConnectionStringSecretName}/)'
  }
]
var localExtraAppSettings = [for setting in extraKeyVaultReferenceAppSettings: {
  name: setting.settingName
  value: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${setting.secretName}/)'
}]
var extraAppSettings = keyVaultReferences.mode == 'existing' ? [
  { name: 'ARIZE_OTLP_ENDPOINT', value: '@Microsoft.KeyVault(SecretUri=${keyVaultReferences.arizeEndpointSecretUri})' }
  { name: 'ARIZE_SPACE_ID', value: '@Microsoft.KeyVault(SecretUri=${keyVaultReferences.arizeSpaceIdSecretUri})' }
  { name: 'ARIZE_API_KEY', value: '@Microsoft.KeyVault(SecretUri=${keyVaultReferences.arizeApiKeySecretUri})' }
] : localExtraAppSettings
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  tags: requiredTags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: hostingPlan.id
    httpsOnly: true
    publicNetworkAccess: 'Disabled'
    virtualNetworkSubnetId: functionIntegrationSubnetResourceId
    vnetRouteAllEnabled: true
    keyVaultReferenceIdentity: 'SystemAssigned'
    siteConfig: {
      functionAppScaleLimit: maximumInstances
      minimumElasticInstanceCount: 1
      preWarmedInstanceCount: 1
      linuxFxVersion: 'Python|${pythonVersion}'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      appSettings: concat(baseAppSettings, extraAppSettings)
    }
  }
  dependsOn: [
    storagePrivateEndpoints
  ]
}

// Retain Blob/Queue/Table grants. Blob Data Owner is additionally required for
// identity-based host storage (distinct from application Blob Contributor).
var storageRoleIds = [
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
  '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
  'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
]
resource storageRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for roleId in storageRoleIds: {
  name: guid(storageAccount.id, functionApp.id, roleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}]
resource eventHubNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' existing = {
  name: eventHubNamespaceName
}
var eventHubsDataReceiverRoleId = 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde'
resource eventHubReceiverRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(eventHubNamespace.id, functionApp.id, eventHubsDataReceiverRoleId)
  scope: eventHubNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', eventHubsDataReceiverRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
resource keyVaultSecretsUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (keyVaultReferences.mode == 'freshVault') {
  name: guid(keyVault.id, functionApp.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
resource scmBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-12-01' = {
  parent: functionApp
  name: 'scm'
  properties: {
    allow: false
  }
}
resource ftpBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-12-01' = {
  parent: functionApp
  name: 'ftp'
  properties: {
    allow: false
  }
}

output functionAppResourceId string = functionApp.id
output functionAppName string = functionApp.name
output functionAppDefaultHostName string = functionApp.properties.defaultHostName
output functionAppPrincipalId string = functionApp.identity.principalId
output storageAccountResourceId string = storageAccount.id
output storageAccountName string = storageAccount.name
output hostingPlanResourceId string = hostingPlan.id
output isPremiumHostingPlan bool = true
output genAICorrelationContainerResourceId string = prepareDurableGenAIContainer ? genAICorrelationContainer!.id : ''
output privateEndpointResourceIds array = storagePrivateEndpoints.outputs.privateEndpointResourceIds
