// =============================================================================
// event-hub.bicep
// Provisions an Event Hub namespace + hub to sit between Application
// Insights/Log Analytics (export/diagnostic-settings source) and the Azure
// Function transform pipeline (issue #19), enabling streaming telemetry
// fan-out toward Arize.
//
// AUTH MODEL (issue #17 acceptance criteria): managed identity + RBAC is the
// primary (and default) auth path - NOT shared access keys/connection
// strings. Callers pass the managed identity principal IDs of producers
// (e.g. a Log Analytics/diagnostic-settings export identity) and consumers
// (e.g. the Function App's system-assigned identity, see
// infra/modules/function-app.bicep) and this module grants least-privilege
// data-plane RBAC roles:
//   - "Azure Event Hubs Data Sender"   -> senderPrincipalIds
//   - "Azure Event Hubs Data Receiver" -> receiverPrincipalIds
// Local/SAS-key auth (`disableLocalAuth`) is disabled by default.
//
// OPTIONAL CONNECTION-STRING FALLBACK: some tooling (local dev, consumer
// libraries without identity-based Event Hub support) still expects a
// connection string. When that is unavoidable, this module can optionally
// write the namespace's primary connection string into an *existing* Key
// Vault as a secret (never as a plaintext Bicep output) - set
// `storeConnectionStringInKeyVault: true` and supply `keyVaultName`. This
// requires `disableLocalAuth: false` (SAS auth re-enabled) and is OFF by
// default; RBAC-only is the recommended posture per repo convention
// (/.github/copilot-instructions.md section 8).
//
// Naming/tagging: resource names and required tags are built via the shared
// infra/modules/naming.bicep helpers (buildResourceName/buildRequiredTags),
// enforced repo-wide per issue #20.
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

@description('Event Hub namespace SKU. Standard is required for consumer groups and is the default demo-scale tier; Basic lacks consumer-group support needed by the transform pipeline.')
@allowed([
  'Basic'
  'Standard'
])
param skuName string = 'Standard'

@description('Throughput units (SKU capacity) for demo-scale load. 1 TU supports ~1MB/s ingress - sized for a demo, not production volume.')
@minValue(1)
@maxValue(20)
param throughputUnits int = 1

@description('Enable auto-inflate so the namespace can scale up throughput units automatically under demo load spikes, bounded by maxThroughputUnits.')
param autoInflateEnabled bool = true

@description('Maximum throughput units auto-inflate may scale to. Ignored when autoInflateEnabled is false. Kept small for demo cost control.')
@minValue(1)
@maxValue(20)
param maxThroughputUnits int = 2

@description('Name suffix for the Event Hub (within the namespace), e.g. "telemetry". The full hub name is not run through the shared resource-name helper (it is a child resource, not an ARM top-level resource name) but follows the same project-env prefix for discoverability.')
param eventHubBaseName string = 'telemetry'

@description('Number of partitions for the hub. Parameterized for demo scale - more partitions allow more parallel consumers but each is a minimum billing unit; 2 is enough for a single-Function-App demo consumer.')
@minValue(1)
@maxValue(32)
param partitionCount int = 2

@description('Message retention in days for the hub.')
@minValue(1)
@maxValue(7)
param messageRetentionInDays int = 1

@description('Name of the consumer group the Azure Function transform pipeline (issue #19) will read from, in addition to $Default.')
param functionConsumerGroupName string = 'function-transform'

@description('Disables SAS-key/connection-string based local auth on the namespace. Default true (RBAC-only) per repo security convention - only set false if storeConnectionStringInKeyVault is also true.')
param disableLocalAuth bool = true

@description('Array of managed identity principal IDs to grant "Azure Event Hubs Data Sender" (send-only) on this namespace - e.g. a Log Analytics/diagnostic-settings export identity or the Foundry project identity.')
param senderPrincipalIds array = []

@description('Array of managed identity principal IDs to grant "Azure Event Hubs Data Receiver" (receive-only) on this namespace - e.g. the Function App system-assigned identity from infra/modules/function-app.bicep.')
param receiverPrincipalIds array = []

@description('Optional: when true, writes the namespace primary connection string into an existing Key Vault as a secret, for tooling that cannot use identity-based auth. Never emitted as a plaintext output regardless of this setting. Requires disableLocalAuth to be explicitly set to false.')
param storeConnectionStringInKeyVault bool = false

@description('Name of an existing Key Vault (same resource group) to store the connection-string fallback secret in. Required only when storeConnectionStringInKeyVault is true.')
param keyVaultName string = ''

@description('Name of the Key Vault secret used to store the Event Hub namespace connection string, when storeConnectionStringInKeyVault is true.')
param connectionStringSecretName string = 'eventhub-connection-string'

var namespaceName = buildResourceName(projectToken, environment, resourceTypeTokens.eventHubNamespace, regionToken)
var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, dataClassificationTag)

// Built-in Azure RBAC role definition IDs (stable GUIDs, safe to reference directly).
var eventHubsDataSenderRoleId = '2b629674-e913-4c01-ae53-ef4638d8f975'
var eventHubsDataReceiverRoleId = 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde'

var wireConnectionStringSecret = storeConnectionStringInKeyVault && !disableLocalAuth && !empty(keyVaultName)

resource eventHubNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' = {
  name: namespaceName
  location: location
  tags: requiredTags
  sku: {
    name: skuName
    tier: skuName
    capacity: throughputUnits
  }
  properties: {
    isAutoInflateEnabled: autoInflateEnabled
    maximumThroughputUnits: autoInflateEnabled ? maxThroughputUnits : 0
    disableLocalAuth: disableLocalAuth
    publicNetworkAccess: 'Enabled'
  }
}

resource eventHub 'Microsoft.EventHub/namespaces/eventhubs@2023-01-01-preview' = {
  parent: eventHubNamespace
  name: eventHubBaseName
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

// Least-privilege data-plane RBAC - one role assignment per supplied
// principal ID, scoped to the namespace (not a specific hub), matching the
// granularity Azure RBAC supports for Event Hubs data roles.
resource senderRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for principalId in senderPrincipalIds: {
    name: guid(eventHubNamespace.id, principalId, eventHubsDataSenderRoleId)
    scope: eventHubNamespace
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', eventHubsDataSenderRoleId)
      principalId: principalId
      principalType: 'ServicePrincipal'
    }
  }
]

resource receiverRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for principalId in receiverPrincipalIds: {
    name: guid(eventHubNamespace.id, principalId, eventHubsDataReceiverRoleId)
    scope: eventHubNamespace
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', eventHubsDataReceiverRoleId)
      principalId: principalId
      principalType: 'ServicePrincipal'
    }
  }
]

// Optional connection-string fallback, written to Key Vault only - never a
// plaintext deployment output. Only materializes when the caller has
// explicitly opted in (storeConnectionStringInKeyVault: true) AND
// re-enabled local auth (disableLocalAuth: false), since a connection
// string cannot be minted while local/SAS auth is disabled on the namespace.
resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (wireConnectionStringSecret) {
  name: keyVaultName
}

resource namespaceAuthRule 'Microsoft.EventHub/namespaces/authorizationRules@2023-01-01-preview' existing = if (wireConnectionStringSecret) {
  parent: eventHubNamespace
  name: 'RootManageSharedAccessKey'
}

resource connectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (wireConnectionStringSecret) {
  parent: existingKeyVault
  name: connectionStringSecretName
  properties: {
    value: namespaceAuthRule.listKeys().primaryConnectionString
    contentType: 'text/plain'
  }
}

@description('Resource ID of the Event Hub namespace.')
output eventHubNamespaceResourceId string = eventHubNamespace.id

@description('Name of the Event Hub namespace - pass to downstream modules (e.g. function-app.bicep) for identity-based binding.')
output eventHubNamespaceName string = eventHubNamespace.name

@description('Fully qualified namespace host name, e.g. <namespace>.servicebus.windows.net - used by identity-based (RBAC) Event Hub bindings.')
output eventHubNamespaceFqdn string = '${eventHubNamespace.name}.servicebus.windows.net'

@description('Name of the Event Hub (within the namespace).')
output eventHubName string = eventHub.name

@description('Name of the consumer group provisioned for the Azure Function transform pipeline (issue #19).')
output functionConsumerGroupName string = functionConsumerGroup.name

@description('True if the connection-string fallback secret was written to Key Vault as part of this deployment.')
output connectionStringStoredInKeyVault bool = wireConnectionStringSecret

@description('Key Vault secret URI for the Event Hub connection-string fallback, when storeConnectionStringInKeyVault was requested and local auth is enabled. Empty string otherwise - callers must not expect a plaintext connection string output from this module and should prefer RBAC (senderPrincipalIds/receiverPrincipalIds) over this fallback.')
output connectionStringSecretUri string = wireConnectionStringSecret ? connectionStringSecret.properties.secretUri : ''
