// Modern-only FRESH composition (ADR-0004). Never apply over the mixed live RG.
// Source cleanup is not live retirement. Deployment/publication require approval.
targetScope = 'resourceGroup'
import { privateNetworkConfiguration } from 'modules/networking.bicep'

@minLength(2)
@maxLength(10)
param projectToken string
@allowed(['dev', 'demo', 'prod'])
param environment string
param location string
param regionToken string
param ownerTag string
param costCenterTag string
@minLength(2)
param accountName string
@minLength(2)
param projectName string
@minLength(2)
param customSubDomainName string
param projectDisplayName string = 'Synthetic Foundry observability'

@minLength(1)
param modelDeploymentName string
@minLength(1)
param modelFormat string
@minLength(1)
param modelName string
@minLength(1)
param modelVersion string
@minLength(1)
param modelDeploymentSkuName string
@minValue(1)
param modelDeploymentCapacity int
@allowed(['NoAutoUpgrade', 'OnceCurrentVersionExpired', 'OnceNewDefaultVersionAvailable'])
param modelVersionUpgradeOption string
param raiPolicyName string = ''
@description('Owner-approved processing residency, including Global/DataZone implications. Not an ARM residency switch.')
@minLength(1)
param modelDataResidencyApproval string
@description('Required owner attestation for exact model/version/region/SKU/capacity/upgrade, availability, quota and cost; never auto-discovered.')
@allowed([true])
param modelDeploymentApproved bool

param network privateNetworkConfiguration
@minValue(30)
@maxValue(730)
param logAnalyticsRetentionInDays int = 30
param logAnalyticsDailyQuotaGb int = 1
@allowed(['standard', 'premium'])
param keyVaultSkuName string = 'standard'
@minValue(7)
@maxValue(90)
param keyVaultSoftDeleteRetentionInDays int = 90
@minValue(1)
@maxValue(20)
param eventHubThroughputUnits int = 1
@minValue(1)
@maxValue(32)
param eventHubPartitionCount int = 2
@minLength(1)
param eventHubConsumerGroupName string = 'function-transform'
@allowed(['3.10', '3.11', '3.12'])
param functionPythonVersion string = '3.11'
@minLength(1)
param functionPackageBlobName string
@description('Approved Arize project name; endpoint/space/key remain operator-populated KV references, never plaintext.')
@minLength(1)
param arizeProjectName string
param arizeEndpointSecretName string = 'arize-otlp-endpoint'
param arizeSpaceIdSecretName string = 'arize-space-id'
param arizeApiKeySecretName string = 'arize-api-key'

@description('No connection PUT by default. Fresh tracing completion requires separately approved ApiKey association and immutable vault reference; preserveExisting is NOT configured tracing.')
@allowed(['preserveExisting', 'ApiKey'])
param tracingAssociationMode string = 'preserveExisting'
@minLength(3)
@maxLength(33)
param appInsightsConnectionName string
@allowed(['private', 'projectShared'])
param appInsightsConnectionSharing string = 'private'
@allowed(['Required', 'NotRequired', 'NotApplicable'])
param appInsightsConnectionPeRequirement string = 'NotRequired'
@allowed(['Inactive', 'Active', 'NotApplicable'])
param appInsightsConnectionPeStatus string = 'NotApplicable'
param appInsightsConnectionPropertiesReviewed bool = false
@description('Operator-supplied immutable Key Vault deployment reference ONLY. No plaintext profile, secret lookup, or output.')
@secure()
param appInsightsConnectionString string = ''

module modernFoundry 'modules/modern-foundry-foundation.bicep' = {
  name: 'modern-foundry-foundation'
  params: {
    environment: environment
    location: location
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    accountName: accountName
    projectName: projectName
    customSubDomainName: customSubDomainName
    projectDisplayName: projectDisplayName
  }
}
module modelDeployment 'modules/modern-foundry-model.bicep' = {
  name: 'modern-foundry-model'
  params: {
    environment: environment
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    accountName: modernFoundry.outputs.foundryAccountName
    modelDeploymentName: modelDeploymentName
    modelFormat: modelFormat
    modelName: modelName
    modelVersion: modelVersion
    modelDeploymentSkuName: modelDeploymentSkuName
    modelDeploymentCapacity: modelDeploymentCapacity
    modelVersionUpgradeOption: modelVersionUpgradeOption
    raiPolicyName: raiPolicyName
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
    eventHubNamespaceResourceId: eventHub.outputs.eventHubNamespaceResourceId
    eventHubName: eventHub.outputs.eventHubName
  }
}
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
  }
}
module eventHub 'modules/event-hub.bicep' = {
  name: 'event-hub-deployment'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    throughputUnits: eventHubThroughputUnits
    partitionCount: eventHubPartitionCount
    functionConsumerGroupName: eventHubConsumerGroupName
  }
}
module networking 'modules/networking.bicep' = {
  name: 'private-network'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    network: network
  }
}
module endpoints 'modules/private-endpoints.bicep' = {
  name: 'foundation-private-endpoints'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    subnetResourceId: networking.outputs.privateEndpointSubnetResourceId
    targets: [
      {
        name: 'foundry'
        targetResourceId: modernFoundry.outputs.foundryAccountResourceId
        groupId: 'account'
        privateDnsZoneResourceIds: [
          networking.outputs.privateDnsZoneResourceIds.cognitiveServices
          networking.outputs.privateDnsZoneResourceIds.openAI
          networking.outputs.privateDnsZoneResourceIds.servicesAI
        ]
      }
      {
        name: 'kv'
        targetResourceId: keyVault.outputs.keyVaultResourceId
        groupId: 'vault'
        privateDnsZoneResourceIds: [
          networking.outputs.privateDnsZoneResourceIds.vault
        ]
      }
    ]
  }
}
module functionApp 'modules/function-app.bicep' = {
  name: 'function-app-deployment'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    pythonVersion: functionPythonVersion
    functionPackageBlobName: functionPackageBlobName
    functionIntegrationSubnetResourceId: networking.outputs.functionIntegrationSubnetResourceId
    privateEndpointSubnetResourceId: networking.outputs.privateEndpointSubnetResourceId
    privateDnsZoneResourceIds: networking.outputs.privateDnsZoneResourceIds
    prepareDurableGenAIContainer: true
    keyVaultName: keyVault.outputs.keyVaultName
    eventHubNamespaceFqdn: eventHub.outputs.eventHubNamespaceFqdn
    eventHubNamespaceName: eventHub.outputs.eventHubNamespaceName
    eventHubName: eventHub.outputs.eventHubName
    eventHubConsumerGroupName: eventHub.outputs.functionConsumerGroupName
    extraKeyVaultReferenceAppSettings: [
      { settingName: 'ARIZE_OTLP_ENDPOINT', secretName: arizeEndpointSecretName }
      { settingName: 'ARIZE_SPACE_ID', secretName: arizeSpaceIdSecretName }
      { settingName: 'ARIZE_API_KEY', secretName: arizeApiKeySecretName }
    ]
  }
  dependsOn: [
    endpoints
  ]
}
module durableState 'modules/durable-genai-state.bicep' = {
  name: 'fresh-durable-state'
  params: {
    storageAccountName: functionApp.outputs.storageAccountName
    functionPrincipalId: functionApp.outputs.functionAppPrincipalId
  }
}
module tracing 'modern-foundry-tracing.bicep' = {
  name: 'fresh-tracing-association'
  params: {
    accountName: modernFoundry.outputs.foundryAccountName
    projectName: modernFoundry.outputs.foundryProjectName
    appInsightsResourceId: appInsights.outputs.appInsightsResourceId
    appInsightsConnectionName: appInsightsConnectionName
    tracingAssociationMode: tracingAssociationMode
    appInsightsConnectionSharing: appInsightsConnectionSharing
    appInsightsConnectionPeRequirement: appInsightsConnectionPeRequirement
    appInsightsConnectionPeStatus: appInsightsConnectionPeStatus
    appInsightsConnectionPropertiesReviewed: appInsightsConnectionPropertiesReviewed
    appInsightsConnectionString: appInsightsConnectionString
  }
}

output foundryAccountResourceId string = modernFoundry.outputs.foundryAccountResourceId
output foundryAccountName string = modernFoundry.outputs.foundryAccountName
output foundryAccountPrincipalId string = modernFoundry.outputs.foundryAccountPrincipalId
output foundryProjectName string = modernFoundry.outputs.foundryProjectName
output foundryProjectResourceId string = modernFoundry.outputs.foundryProjectResourceId
output foundryProjectEndpoint string = modernFoundry.outputs.foundryProjectEndpoint
output foundryProjectPrincipalId string = modernFoundry.outputs.foundryProjectPrincipalId
output modelDeploymentResourceId string = modelDeployment.outputs.modelDeploymentResourceId
output modelDeploymentName string = modelDeployment.outputs.modelDeploymentName
output modelSelectionApprovalRecorded bool = modelDeploymentApproved && !empty(modelDataResidencyApproval)
output logAnalyticsWorkspaceId string = appInsights.outputs.logAnalyticsWorkspaceId
output logAnalyticsWorkspaceName string = appInsights.outputs.logAnalyticsWorkspaceName
output appInsightsResourceId string = appInsights.outputs.appInsightsResourceId
output appInsightsName string = appInsights.outputs.appInsightsName
output keyVaultResourceId string = keyVault.outputs.keyVaultResourceId
output keyVaultName string = keyVault.outputs.keyVaultName
output eventHubNamespaceResourceId string = eventHub.outputs.eventHubNamespaceResourceId
output eventHubNamespaceName string = eventHub.outputs.eventHubNamespaceName
output eventHubName string = eventHub.outputs.eventHubName
output eventHubFunctionConsumerGroupName string = eventHub.outputs.functionConsumerGroupName
output functionAppResourceId string = functionApp.outputs.functionAppResourceId
output functionAppName string = functionApp.outputs.functionAppName
output functionAppDefaultHostName string = functionApp.outputs.functionAppDefaultHostName
output functionAppPrincipalId string = functionApp.outputs.functionAppPrincipalId
output functionAppIsPremiumHostingPlan bool = true
output storageAccountResourceId string = functionApp.outputs.storageAccountResourceId
output storageAccountName string = functionApp.outputs.storageAccountName
output genAICorrelationContainerResourceId string = functionApp.outputs.genAICorrelationContainerResourceId
output exportRuleResourceId string = appInsights.outputs.exportRuleResourceId
output privateEndpointsEnabled bool = true
output privateEndpointResourceIds array = concat(endpoints.outputs.privateEndpointResourceIds, functionApp.outputs.privateEndpointResourceIds)
output privateEndpointSubnetResourceId string = networking.outputs.privateEndpointSubnetResourceId
output functionIntegrationSubnetResourceId string = networking.outputs.functionIntegrationSubnetResourceId
output privateDnsZoneResourceIds object = networking.outputs.privateDnsZoneResourceIds
output tracingAssociationRequestedMode string = tracingAssociationMode
output arizeProjectName string = arizeProjectName
// Not a runtime/cutover readiness claim: package, credentials, durable gates and
// selected private Prompt Agent API/state prerequisites require separate proof.
output consumerEnabled bool = false
