@description('Existing custody vault. No vault properties, policies or roles are changed.')
param vaultName string

@description('New routing secret name; execution must reject an existing name before first allocation.')
param secretName string

@description('Exact source component binding, not its connection material.')
param componentResourceId string

@description('Required fixed expiration as Unix epoch seconds; supplied by the allocation owner.')
@minValue(1)
param expirationEpochSeconds int

@secure()
@minLength(1)
param connectionString string

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: vaultName
}

resource routingSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: secretName
  tags: union(buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic'), {
    sourceComponentResourceId: componentResourceId
  })
  properties: {
    value: connectionString
    contentType: 'application/x-application-insights-connection-string'
    attributes: {
      enabled: true
      exp: expirationEpochSeconds
    }
  }
}

output secretVersionUri string = routingSecret.properties.secretUriWithVersion
output componentBindingResourceId string = componentResourceId
import { buildRequiredTags } from 'naming.bicep'

@allowed(['dev', 'demo', 'prod'])
param environment string
param ownerTag string
param costCenterTag string
