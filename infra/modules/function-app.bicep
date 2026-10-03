// =============================================================================
// function-app.bicep
// Provisions the Azure Function App "shell" for the telemetry transform
// pipeline (issue #19): Function App + dedicated storage account + App
// Service plan + Application Insights linkage, ready for Telemetry to
// deploy the Event Hub -> OTLP transform code (Milestone 2).
//
// HOSTING PLAN DECISION (Consumption vs Premium):
//   Default: **Consumption (Y1, Linux, Dynamic tier)**. This is a demo
//   pipeline invoked by manual/scripted demo runs against an Event Hub with
//   low, bursty volume - not a latency-sensitive production workload. A few
//   seconds of cold start on the first invocation after idle is an
//   acceptable trade-off for near-zero idle cost (pay-per-execution), which
//   also supports the "low operational overhead, easy to replicate in your
//   own tenant" sales message from issue #19's customer value statement.
//   Set `hostingPlanTier: 'Premium'` to switch to an Elastic Premium (EP1)
//   plan for a POC that needs no cold start and/or VNet integration with a
//   customer's own Event Hub - this is a single-parameter upgrade, no
//   template rewrite, matching the optional-upgrade-path pattern used by
//   modules/networking.bicep (issue #21).
//
// IDENTITY / SECRETS MODEL (no inline secrets, no shared keys):
//   - System-assigned managed identity enabled on the Function App.
//   - Storage: identity-based `AzureWebJobsStorage__accountName` +
//     `AzureWebJobsStorage__credential: managedidentity` app settings
//     (Azure Functions' identity-based storage connection support) instead
//     of a connection-string app setting. The Function identity is granted
//     least-privilege Storage Blob/Queue/Table Data Contributor roles on
//     the dedicated storage account (Functions' runtime bookkeeping
//     requires all three data-plane roles).
//   - Event Hub (issue #17): identity-based trigger binding via
//     `<prefix>__fullyQualifiedNamespace` + `<prefix>__credential:
//     managedidentity` app settings (the namespace host name is not a
//     secret). The Function identity is granted "Azure Event Hubs Data
//     Receiver" on the namespace when `eventHubNamespaceResourceId` is
//     supplied. A connection-string fallback app setting
//     (`eventHubConnectionSecretName`, resolved via a Key Vault reference)
//     is available for tooling that cannot use identity-based bindings -
//     it is never written inline.
//   - Application Insights: `APPLICATIONINSIGHTS_CONNECTION_STRING` is
//     wired as a Key Vault reference (`@Microsoft.KeyVault(SecretUri=...)`)
//     pointing at the secret app-insights.bicep already wrote (issue #16),
//     never as a plaintext app setting.
//   - Any other Key Vault secret (e.g. a future Arize API key) can be
//     exposed the same way via `extraKeyVaultReferenceAppSettings`.
//   - The Function App's own principal ID is exposed as an output so the
//     Key Vault module's `readerPrincipalIds` and the Event Hub module's
//     `receiverPrincipalIds` can be cross-wired to it in a follow-up
//     deployment (two-phase pattern, see modules/key-vault.bicep).
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

@description('Hosting plan tier. "Consumption" (Y1, pay-per-execution, cold-start tolerant) is the demo default; "Premium" (EP1, no cold start, VNet-capable) is an optional single-parameter upgrade for latency-sensitive or network-isolated POCs. See module header for the full rationale.')
@allowed([
  'Consumption'
  'Premium'
])
param hostingPlanTier string = 'Consumption'

@description('Python runtime version for the Function App (isolated worker model), kept consistent with the Prompt Agent/telemetry transform language choice per repo convention (/.github/copilot-instructions.md section 5).')
@allowed([
  '3.10'
  '3.11'
  '3.12'
])
param pythonVersion string = '3.11'

@description('Name of the existing Key Vault (same resource group) to resolve Key Vault reference app settings against (Application Insights connection string, optional Event Hub connection-string fallback). Leave empty to skip all Key-Vault-backed app settings - the Function App will still work with identity-based storage/Event Hub bindings alone.')
param keyVaultName string = ''

@description('Name of the Key Vault secret holding the Application Insights connection string (written by modules/app-insights.bicep, issue #16). Ignored when keyVaultName is empty.')
param appInsightsConnectionStringSecretName string = 'appinsights-connection-string'

@description('Fully qualified Event Hub namespace host name (output eventHubNamespaceFqdn from modules/event-hub.bicep, issue #17), e.g. <namespace>.servicebus.windows.net. Leave empty to skip Event Hub trigger wiring - app settings can be added in a later deployment once the Event Hub exists.')
param eventHubNamespaceFqdn string = ''

@description('Resource ID of the Event Hub namespace (modules/event-hub.bicep output eventHubNamespaceResourceId), used to scope the "Azure Event Hubs Data Receiver" RBAC role assignment. Required only when eventHubNamespaceFqdn is supplied and identity-based access should be granted in this deployment; leave empty to grant the role in a later cross-wiring deployment instead.')
param eventHubNamespaceResourceId string = ''

@description('App-setting prefix used for the identity-based Event Hub connection, e.g. settings named "<prefix>__fullyQualifiedNamespace"/"<prefix>__credential". Must match the `connection` property the transform function''s trigger binding uses.')
param eventHubConnectionSettingPrefix string = 'EventHubConnection'

@description('Optional: name of a Key Vault secret holding an Event Hub connection string, for tooling that cannot use the identity-based binding above. Resolved via a Key Vault reference app setting, never inline. Leave empty (default) to rely on identity-based access only.')
param eventHubConnectionSecretName string = ''

@description('Additional Key Vault reference app settings as an array of { settingName, secretName } objects, e.g. a future Arize API key. Each resolves to @Microsoft.KeyVault(SecretUri=.../<secretName>/) against keyVaultName. Ignored when keyVaultName is empty.')
param extraKeyVaultReferenceAppSettings array = []

var storageAccountName = toLower(replace(buildResourceName(projectToken, environment, resourceTypeTokens.storageAccount, regionToken), '-', ''))
var hostingPlanName = buildResourceName(projectToken, environment, 'plan', regionToken)
var functionAppName = buildResourceName(projectToken, environment, resourceTypeTokens.functionApp, regionToken)
var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, dataClassificationTag)

var isPremium = hostingPlanTier == 'Premium'
var wireKeyVaultReferences = !empty(keyVaultName)
var wireEventHubTrigger = !empty(eventHubNamespaceFqdn)
var wireEventHubRbac = wireEventHubTrigger && !empty(eventHubNamespaceResourceId)
var wireEventHubConnectionSecret = wireKeyVaultReferences && !empty(eventHubConnectionSecretName)

// Built-in Azure RBAC role definition IDs (stable GUIDs, safe to reference directly).
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var storageQueueDataContributorRoleId = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
var storageTableDataContributorRoleId = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
var eventHubsDataReceiverRoleId = 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde'
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

// Dedicated storage account for this Function App only (not shared with
// other demo resources per issue #19 acceptance criteria). No connection
// string is ever read from this account by the Function App - see
// AzureWebJobsStorage__* identity-based settings below.
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
    supportsHttpsTrafficOnly: true
  }
}

resource hostingPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: hostingPlanName
  location: location
  tags: requiredTags
  kind: 'functionapp,linux'
  sku: isPremium
    ? {
        name: 'EP1'
        tier: 'ElasticPremium'
      }
    : {
        name: 'Y1'
        tier: 'Dynamic'
      }
  properties: {
    reserved: true
  }
}

// appSettings is built up as plain variables (rather than inline for-loops
// nested in a concat() call) because Bicep only guarantees for-expression
// support when a loop is the entire value of a variable/property - see
// extraKeyVaultReferenceAppSettingsRaw below.
var baseAppSettings = [
  {
    name: 'FUNCTIONS_EXTENSION_VERSION'
    value: '~4'
  }
  {
    name: 'FUNCTIONS_WORKER_RUNTIME'
    value: 'python'
  }
  // Identity-based storage connection - no AzureWebJobsStorage
  // connection-string app setting is ever created.
  {
    name: 'AzureWebJobsStorage__accountName'
    value: storageAccount.name
  }
  {
    name: 'AzureWebJobsStorage__credential'
    value: 'managedidentity'
  }
]

var appInsightsAppSettingsRaw = [
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    value: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${appInsightsConnectionStringSecretName}/)'
  }
]
var appInsightsAppSettings = wireKeyVaultReferences ? appInsightsAppSettingsRaw : []

var eventHubAppSettingsRaw = [
  {
    name: '${eventHubConnectionSettingPrefix}__fullyQualifiedNamespace'
    value: eventHubNamespaceFqdn
  }
  {
    name: '${eventHubConnectionSettingPrefix}__credential'
    value: 'managedidentity'
  }
]
var eventHubAppSettings = wireEventHubTrigger ? eventHubAppSettingsRaw : []

var eventHubConnectionSecretAppSettingsRaw = [
  {
    name: '${eventHubConnectionSettingPrefix}ConnectionString'
    value: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${eventHubConnectionSecretName}/)'
  }
]
var eventHubConnectionSecretAppSettings = wireEventHubConnectionSecret ? eventHubConnectionSecretAppSettingsRaw : []

var extraKeyVaultReferenceAppSettingsRaw = [
  for setting in extraKeyVaultReferenceAppSettings: {
    name: setting.settingName
    value: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${setting.secretName}/)'
  }
]
var extraAppSettings = wireKeyVaultReferences ? extraKeyVaultReferenceAppSettingsRaw : []

var allAppSettings = concat(
  baseAppSettings,
  appInsightsAppSettings,
  eventHubAppSettings,
  eventHubConnectionSecretAppSettings,
  extraAppSettings
)

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
    keyVaultReferenceIdentity: 'SystemAssigned'
    siteConfig: {
      linuxFxVersion: 'Python|${pythonVersion}'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: allAppSettings
    }
  }
}

// Least-privilege storage data-plane RBAC for the Function runtime's own
// bookkeeping (triggers/bindings state, host lock blobs, queues, tables) -
// all three roles are required by the Functions host when using
// identity-based AzureWebJobsStorage.
resource storageBlobRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, storageBlobDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageQueueRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, storageQueueDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageQueueDataContributorRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageTableRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, storageTableDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageTableDataContributorRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Optional Event Hub "Data Receiver" RBAC, scoped to the namespace resource
// ID the caller supplies. If omitted, grant this role in a later
// cross-wiring deployment by adding the Function App's principalId output
// to modules/event-hub.bicep's receiverPrincipalIds parameter instead.
resource existingEventHubNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' existing = if (wireEventHubRbac) {
  name: last(split(eventHubNamespaceResourceId, '/'))
}

resource eventHubReceiverRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (wireEventHubRbac) {
  name: guid(eventHubNamespaceResourceId, functionApp.id, eventHubsDataReceiverRoleId)
  scope: existingEventHubNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', eventHubsDataReceiverRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Optional Key Vault "Secrets User" RBAC so the Key Vault reference app
// settings above (Application Insights connection string, optional Event
// Hub connection-string fallback, extraKeyVaultReferenceAppSettings) can
// actually resolve. If omitted, grant this role in a later cross-wiring
// deployment by adding the Function App's principalId output to
// modules/key-vault.bicep's readerPrincipalIds parameter instead.
resource existingKeyVaultForRbac 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (wireKeyVaultReferences) {
  name: keyVaultName
}

resource keyVaultSecretsUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (wireKeyVaultReferences) {
  name: guid(existingKeyVaultForRbac.id, functionApp.id, keyVaultSecretsUserRoleId)
  scope: existingKeyVaultForRbac
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Resource ID of the Function App.')
output functionAppResourceId string = functionApp.id

@description('Name of the Function App.')
output functionAppName string = functionApp.name

@description('Default host name of the Function App, e.g. <name>.azurewebsites.net.')
output functionAppDefaultHostName string = functionApp.properties.defaultHostName

@description('System-assigned managed identity principal ID of the Function App - pass this to modules/key-vault.bicep readerPrincipalIds and modules/event-hub.bicep receiverPrincipalIds in a follow-up cross-wiring deployment if it was not already supplied to this module via keyVaultName/eventHubNamespaceResourceId.')
output functionAppPrincipalId string = functionApp.identity.principalId

@description('Resource ID of the dedicated storage account.')
output storageAccountResourceId string = storageAccount.id

@description('Name of the dedicated storage account.')
output storageAccountName string = storageAccount.name

@description('Resource ID of the App Service plan (hosting plan).')
output hostingPlanResourceId string = hostingPlan.id

@description('True if the Premium (EP1) hosting plan was used instead of the Consumption (Y1) default.')
output isPremiumHostingPlan bool = isPremium
