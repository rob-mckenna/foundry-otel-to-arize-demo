// Native LAW export -> explicit telemetry hub/consumer. No SAS/key fallback.
// Public service ingestion is intentionally retained (ADR-0004), not a Foundry
// public fallback. Enterprise denial requires a separately approved design.
import { buildResourceName, buildRequiredTags, resourceTypeTokens } from 'naming.bicep'

param projectToken string
param environment string
param location string
param regionToken string
param ownerTag string
param costCenterTag string
@minValue(1)
@maxValue(20)
param throughputUnits int = 1
@minValue(1)
@maxValue(32)
param partitionCount int = 2
@minValue(1)
@maxValue(7)
param messageRetentionInDays int = 1
@minLength(1)
param functionConsumerGroupName string = 'function-transform'

resource eventHubNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' = {
  name: buildResourceName(projectToken, environment, resourceTypeTokens.eventHubNamespace, regionToken)
  location: location
  tags: buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic')
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: throughputUnits
  }
  properties: {
    isAutoInflateEnabled: false
    maximumThroughputUnits: 0
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}
resource eventHub 'Microsoft.EventHub/namespaces/eventhubs@2023-01-01-preview' = {
  parent: eventHubNamespace
  name: 'telemetry'
  properties: {
    partitionCount: partitionCount
    messageRetentionInDays: messageRetentionInDays
  }
}
resource functionConsumerGroup 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2023-01-01-preview' = {
  parent: eventHub
  name: functionConsumerGroupName
  properties: {}
}

output eventHubNamespaceResourceId string = eventHubNamespace.id
output eventHubNamespaceName string = eventHubNamespace.name
output eventHubNamespaceFqdn string = '${eventHubNamespace.name}.servicebus.windows.net'
output eventHubName string = eventHub.name
output functionConsumerGroupName string = functionConsumerGroup.name
