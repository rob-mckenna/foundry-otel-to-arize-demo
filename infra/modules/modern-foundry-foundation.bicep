// Fresh foundation only. Never use this module to adopt the mixed live RG.
import { buildRequiredTags } from 'naming.bicep'

param environment string
param location string
param ownerTag string
param costCenterTag string
@minLength(2)
@maxLength(64)
param accountName string
@minLength(2)
@maxLength(64)
param projectName string
@minLength(2)
param customSubDomainName string
param projectDisplayName string

var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic')

resource account 'Microsoft.CognitiveServices/accounts@2025-09-01' = {
  name: accountName
  location: location
  tags: requiredTags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: customSubDomainName
    disableLocalAuth: true
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'None'
    }
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-09-01' = {
  parent: account
  name: projectName
  location: location
  tags: requiredTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: projectDisplayName
    description: 'Synthetic Prompt Agent observability project; agent publication is separate.'
  }
}

// Published Foundry User (formerly Azure AI User); never substitute ML Developer.
// https://learn.microsoft.com/azure/role-based-access-control/built-in-roles/ai-machine-learning#foundry-user
var foundryUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
resource projectAccountAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(account.id, project.id, foundryUserRoleId)
  scope: account
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
  }
}

output foundryAccountResourceId string = account.id
output foundryAccountName string = account.name
output foundryAccountPrincipalId string = account.identity.principalId
output foundryProjectName string = project.name
output foundryProjectResourceId string = project.id
output foundryProjectPrincipalId string = project.identity.principalId
// Azure public cloud only. This is not an OpenAI endpoint or runtime readiness proof.
output foundryProjectEndpoint string = 'https://${customSubDomainName}.services.ai.azure.com/api/projects/${projectName}'
