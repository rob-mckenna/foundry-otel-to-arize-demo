// EXISTING demo rollout: only the isolated health pair + one ARM-custodied secret.
// No Function, agent, export, diagnostic, IAM, checkpoint or ledger writes.
targetScope = 'resourceGroup'

param projectToken string
@allowed(['dev', 'demo', 'prod'])
param environment string
param location string
param regionToken string
param ownerTag string
param costCenterTag string
param keyVaultName string
param functionHealthConnectionStringSecretName string = 'function-health-connection-string'
@description('Approved future health secret expiration as UTC Unix seconds. Defaults to 90 days from deployment; pin explicitly for the existing rollout.')
@minValue(1)
@maxValue(2147483647)
param functionHealthSecretExpirationEpoch int = dateTimeToEpoch(dateTimeAdd(utcNow(), 'P90D'))
@minValue(30)
@maxValue(90)
param retentionInDays int = 30
@minValue(1)
@maxValue(10)
param dailyQuotaGb int = 1
@allowed(['PerGB2018'])
param workspaceSkuName string = 'PerGB2018'

module health 'modules/function-health.bicep' = {
  name: 'pipeline-function-health'
  params: {
    projectToken: projectToken
    environment: environment
    location: location
    regionToken: regionToken
    ownerTag: ownerTag
    costCenterTag: costCenterTag
    keyVaultName: keyVaultName
    functionHealthConnectionStringSecretName: functionHealthConnectionStringSecretName
    functionHealthSecretExpirationEpoch: functionHealthSecretExpirationEpoch
    retentionInDays: retentionInDays
    dailyQuotaGb: dailyQuotaGb
    workspaceSkuName: workspaceSkuName
  }
}

output healthWorkspaceResourceId string = health.outputs.healthWorkspaceResourceId
output healthComponentResourceId string = health.outputs.healthComponentResourceId
output functionHealthSecretUri string = health.outputs.functionHealthSecretUri
