// One explicitly selected account-scoped deployment; no catalog/default discovery.
import { buildRequiredTags } from 'naming.bicep'

param environment string
param ownerTag string
param costCenterTag string
@minLength(2)
param accountName string
@minLength(1)
param modelDeploymentName string
@minLength(1)
param modelFormat string
@minLength(1)
param modelName string
@minLength(1)
param modelVersion string
@minLength(1)
param modelDeploymentSkuName string
@minValue(1)
param modelDeploymentCapacity int
@allowed(['NoAutoUpgrade', 'OnceCurrentVersionExpired', 'OnceNewDefaultVersionAvailable'])
param modelVersionUpgradeOption string
param raiPolicyName string = ''

resource account 'Microsoft.CognitiveServices/accounts@2025-09-01' existing = {
  name: accountName
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-09-01' = {
  parent: account
  name: modelDeploymentName
  tags: buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic')
  sku: {
    name: modelDeploymentSkuName
    capacity: modelDeploymentCapacity
  }
  properties: union({
    model: {
      format: modelFormat
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: modelVersionUpgradeOption
  }, empty(raiPolicyName) ? {} : {
    raiPolicyName: raiPolicyName
  })
}

output modelDeploymentResourceId string = modelDeployment.id
output modelDeploymentName string = modelDeployment.name
