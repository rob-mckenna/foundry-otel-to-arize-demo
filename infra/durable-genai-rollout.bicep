targetScope = 'resourceGroup'

@description('Existing Function storage account in the deployment resource group. No account properties are written.')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Object ID of the existing Function system-assigned managed identity; not an application/client ID.')
@minLength(36)
@maxLength(36)
param functionPrincipalId string

@description('Existing Log Analytics workspace in the deployment resource group.')
@minLength(1)
param workspaceName string

@description('Exact existing export-rule name. Review a fresh GET before deployment; this template performs a full child-resource PUT.')
@minLength(1)
param exportRuleName string

@description('Complete current export table list from the reviewed existing rule. Every entry is preserved.')
@minLength(2)
param existingExportTableNames string[]

@description('Current enabled state of the existing rule; preserve the reviewed value.')
param existingExportEnabled bool

@description('Exact current Event Hub namespace ARM resource ID from the existing export destination. No destination resources are written.')
@minLength(1)
param eventHubNamespaceResourceId string

@description('Exact current destination Event Hub name. Required to avoid creating per-table hubs.')
@minLength(1)
param eventHubName string

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' existing = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobs
  name: 'genai-correlation'
  properties: {
    publicAccess: 'None'
  }
}

resource indexRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(resourceGroup().id, container.id, 'durable-genai-index-v1')
  properties: {
    roleName: '${storageAccountName}-genai-correlation-index'
    description: 'Additive index-tag write and container-local due-work search for the durable GenAI ledger.'
    type: 'CustomRole'
    assignableScopes: [
      resourceGroup().id
    ]
    permissions: [
      {
        actions: []
        notActions: []
        dataActions: [
          'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write'
          'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action'
        ]
        notDataActions: []
      }
    ]
  }
}

resource indexAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container.id, functionPrincipalId, indexRole.id)
  scope: container
  properties: {
    roleDefinitionId: indexRole.id
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: workspaceName
}

resource exportRule 'Microsoft.OperationalInsights/workspaces/dataExports@2023-09-01' = {
  parent: workspace
  name: exportRuleName
  properties: {
    destination: {
      resourceId: eventHubNamespaceResourceId
      metaData: {
        eventHubName: eventHubName
      }
    }
    tableNames: union(existingExportTableNames, [
      'AppDependencies'
      'AppRequests'
      'AppGenAIContent'
    ])
    enable: existingExportEnabled
  }
}

output containerResourceId string = container.id
output indexRoleDefinitionId string = indexRole.id
output indexRoleAssignmentId string = indexAssignment.id
output exportRuleResourceId string = exportRule.id
