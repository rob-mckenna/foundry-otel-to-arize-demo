targetScope = 'resourceGroup'

@description('Invocation target recorded only; never deploys or updates Foundry resources. Agent version must be exact, not latest.')
param existingAgent {
  accountResourceId: string
  projectResourceId: string
  modelDeploymentName: string
  agentName: string
  agentVersion: string
}
@description('Bounded attachment only. All referenced base resources must already exist in this resource group.')
@minLength(1)
param functionAppName string
@description('Existing system-assigned Function identity object ID, independently attested by the resource owner.')
param functionPrincipalId string
param storageAccountName string
param workspaceName string
@description('Existing agent LAW customerId GUID (WorkspaceId in exported rows), NOT its ARM resource ID.')
@minLength(36)
@maxLength(36)
param workspaceCustomerId string
param agentComponentResourceId string
param functionHealthComponentResourceId string
param functionHealthWorkspaceResourceId string
param keyVaultName string
param functionHealthConnectionStringSecretName string
param arizeEndpointSecretName string
param arizeSpaceSecretName string
param arizeApiKeySecretName string
param arizeProjectName string
param eventHubNamespaceName string
param eventHubName string
param eventHubConsumerGroupName string
@description('Exact existing rule. This is a full child-resource PUT; preserve every current table and its enabled state.')
param exportRuleName string
param existingExportTableNames string[]
param existingExportEnabled bool
@description('Complete reviewed current settings, including private immutable package URL and MI host-storage settings. Never supply raw secrets.')
param existingFunctionAppSettings object

resource functionApp 'Microsoft.Web/sites@2023-12-01' existing = {
  name: functionAppName
}
resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: workspaceName
}
resource eventHubNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' existing = {
  name: eventHubNamespaceName
}
resource exportRule 'Microsoft.OperationalInsights/workspaces/dataExports@2023-09-01' = {
  parent: workspace
  name: exportRuleName
  properties: {
    destination: {
      resourceId: eventHubNamespace.id
      metaData: {
        eventHubName: eventHubName
      }
    }
    tableNames: union(existingExportTableNames, [
      'AppRequests'
      'AppDependencies'
      'AppGenAIContent'
    ])
    enable: existingExportEnabled
  }
}

var runtimeSettings = {
  FUNCTIONS_EXTENSION_VERSION: '~4'
  FUNCTIONS_WORKER_RUNTIME: 'python'
  AzureWebJobsStorage__accountName: storageAccountName
  AzureWebJobsStorage__credential: 'managedidentity'
  EventHubConnection__fullyQualifiedNamespace: '${eventHubNamespaceName}.servicebus.windows.net'
  EventHubConnection__credential: 'managedidentity'
  EVENT_HUB_CONNECTION_SETTING_PREFIX: 'EventHubConnection'
  EVENT_HUB_NAME: eventHubName
  EVENT_HUB_CONSUMER_GROUP: eventHubConsumerGroupName
  DURABLE_ALLOWED_WORKSPACE_ID: workspaceCustomerId
  DURABLE_ALLOWED_COMPONENT_RESOURCE_ID: agentComponentResourceId
  DURABLE_ARIZE_PROJECT: arizeProjectName
  APPLICATIONINSIGHTS_CONNECTION_STRING: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${functionHealthConnectionStringSecretName}/)'
  ARIZE_OTLP_ENDPOINT: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${arizeEndpointSecretName}/)'
  ARIZE_SPACE_ID: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${arizeSpaceSecretName}/)'
  ARIZE_API_KEY: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${arizeApiKeySecretName}/)'
  PIPELINE_EXCLUDED_SERVICE_NAMES: string(union(
    contains(existingFunctionAppSettings, 'PIPELINE_EXCLUDED_SERVICE_NAMES') ? json(existingFunctionAppSettings.PIPELINE_EXCLUDED_SERVICE_NAMES) : [],
    [functionAppName]
  ))
  PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS: string(union(
    contains(existingFunctionAppSettings, 'PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS') ? json(existingFunctionAppSettings.PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS) : [],
    [functionHealthComponentResourceId]
  ))
  'AzureWebJobs.TelemetryTransform.Disabled': 'true'
  'AzureWebJobs.DurableGenAIOutbox.Disabled': 'true'
}

resource functionSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: union(existingFunctionAppSettings, runtimeSettings)
}
module durableState 'modules/durable-genai-state.bicep' = {
  name: 'durable-genai-state'
  params: {
    storageAccountName: storageAccountName
    functionPrincipalId: functionPrincipalId
  }
}

output exportRuleResourceId string = exportRule.id
output durableContainerResourceId string = durableState.outputs.containerResourceId
output healthWorkspaceResourceId string = functionHealthWorkspaceResourceId
output agentTarget object = existingAgent
output preparationOnly bool = true
