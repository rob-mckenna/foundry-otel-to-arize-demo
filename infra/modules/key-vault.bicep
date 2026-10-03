// =============================================================================
// key-vault.bicep
// Provisions a Key Vault using RBAC authorization (not legacy access
// policies), with purge protection and soft-delete enabled, and grants
// least-privilege RBAC role assignments to the managed identities of
// compute resources that need to read secrets (Foundry project, Function
// App, and any future compute).
//
// SEQUENCING (two-phase deploy - see issue #18 and .squad/decisions.md
// "Function App <-> Key Vault sequencing"):
//   Phase 1 - provision this Key Vault shell independently. It does not
//             depend on the Function App or any other compute resource
//             existing.
//   Phase 2 - cross-wire: pass the principal ID(s) of already-provisioned
//             compute managed identities into `readerPrincipalIds` (or
//             call this module again / add role-assignment resources in a
//             follow-up deployment) once those resources exist.
//
// GRANTING A NEW COMPUTE RESOURCE ACCESS TO THIS VAULT (reusable pattern):
//   1. Provision the compute resource with `identity: { type: 'SystemAssigned' }`.
//   2. Capture its `identity.principalId` as a module/resource output.
//   3. Add that principal ID to the `readerPrincipalIds` array parameter
//      passed to this module (or append a new
//      `Microsoft.Authorization/roleAssignments` resource scoped to this
//      vault, assigning role `4633458b-17de-408a-b874-0445c86b69e6`
//      - "Key Vault Secrets User" - to the principal).
//   4. The compute resource reads secrets via
//      `https://<vault-name>.vault.azure.net/secrets/<name>` using its
//      managed identity token. No key material is ever configured in app
//      settings, parameters, or source.
//   Never grant the broader "Key Vault Administrator" role to a reader
//   identity - only the identities that manage the vault itself (break-
//   glass/operator access) should receive that role, and that grant is
//   intentionally NOT automated here.
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

@description('Azure AD tenant ID that owns this Key Vault.')
param tenantId string = subscription().tenantId

@description('SKU for the Key Vault: standard or premium (HSM-backed).')
@allowed([
  'standard'
  'premium'
])
param skuName string = 'standard'

@description('Soft-delete retention period in days. Must be >= 7; 90 is the Azure default.')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 90

@description('Array of managed identity principal IDs (system- or user-assigned) to grant the least-privilege "Key Vault Secrets User" role to - e.g. the Foundry project and Function App managed identities. Leave empty on first (shell) deploy and populate once those resources exist (phase 2 cross-wiring).')
param readerPrincipalIds array = []

@description('Array of managed identity principal IDs to grant the "Key Vault Secrets Officer" role to (can create/update/delete secrets, but not manage the vault itself). Use sparingly - most compute identities only need read access via readerPrincipalIds.')
param writerPrincipalIds array = []

var keyVaultName = buildResourceName(projectToken, environment, resourceTypeTokens.keyVault, regionToken)
var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, dataClassificationTag)

// Built-in Azure RBAC role definition IDs (stable GUIDs, safe to reference directly).
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
var keyVaultSecretsOfficerRoleId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: requiredTags
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: skuName
    }
    // RBAC authorization mode per acceptance criteria - no legacy access policies.
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Least-privilege reader role assignments - one per supplied principal ID.
// `Key Vault Secrets User` only permits reading secret values, not managing
// the vault or other secret types.
resource secretsUserRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for principalId in readerPrincipalIds: {
    name: guid(keyVault.id, principalId, keyVaultSecretsUserRoleId)
    scope: keyVault
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
      principalId: principalId
      principalType: 'ServicePrincipal'
    }
  }
]

resource secretsOfficerRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for principalId in writerPrincipalIds: {
    name: guid(keyVault.id, principalId, keyVaultSecretsOfficerRoleId)
    scope: keyVault
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsOfficerRoleId)
      principalId: principalId
      principalType: 'ServicePrincipal'
    }
  }
]

@description('Resource ID of the Key Vault.')
output keyVaultResourceId string = keyVault.id

@description('Name of the Key Vault - pass this to other modules (e.g. app-insights.bicep keyVaultName, foundry-project.bicep keyVaultResourceId) to wire secret storage.')
output keyVaultName string = keyVault.name

@description('URI of the Key Vault, e.g. https://<name>.vault.azure.net/')
output keyVaultUri string = keyVault.properties.vaultUri
