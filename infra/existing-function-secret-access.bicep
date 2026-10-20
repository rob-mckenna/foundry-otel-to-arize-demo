// Separate later lease only. No vault/secret PUT or secret value access.
// Deploy at the existing custody vault's RG, never implicitly from fresh main.
targetScope = 'resourceGroup'

@minLength(3)
@maxLength(24)
param vaultName string
@description('Actual provider-generated principal of the fresh Function; never the existing Function/runner identity.')
@minLength(36)
@maxLength(36)
param functionPrincipalId string
@minLength(1)
@maxLength(4)
param secretNames string[]

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: vaultName
}
resource secrets 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = [for secretName in secretNames: {
  parent: vault
  name: secretName
}]
var secretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
resource readers 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (secretName, i) in secretNames: {
  name: guid(secrets[i].id, functionPrincipalId, secretsUserRoleId)
  scope: secrets[i]
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', secretsUserRoleId)
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}]
