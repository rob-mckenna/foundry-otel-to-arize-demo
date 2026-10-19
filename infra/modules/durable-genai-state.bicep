// Sole fresh state writer. The existing-resource rollout uses identical GUID
// derivation, but must never run concurrently against fresh-owned resources.
param storageAccountName string
param functionPrincipalId string

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}
resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' existing = {
  parent: storage
  name: 'default'
}
resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' existing = {
  parent: blobs
  name: 'genai-correlation'
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
output indexRoleDefinitionId string = indexRole.id
output indexRoleAssignmentId string = indexAssignment.id
