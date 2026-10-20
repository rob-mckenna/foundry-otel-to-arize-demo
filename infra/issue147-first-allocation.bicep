// Exact fresh-application/existing-network bundle, NOT deployment authority.
// First allocation only. Repeat validation uses main, not this custody write.
targetScope = 'subscription'

import { buildRequiredTags } from 'modules/naming.bicep'

var p = loadJsonContent('main.issue147-existing-network.parameters.json').parameters

resource freshGroup 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'fotoa-demo-rg147-eastus2'
  location: p.location.value
  tags: buildRequiredTags(p.environment.value, p.ownerTag.value, p.costCenterTag.value, 'synthetic')
}

module foundation 'main.bicep' = {
  name: 'issue147-fresh-application'
  scope: freshGroup
  params: {
    projectToken: p.projectToken.value
    environment: p.environment.value
    location: p.location.value
    regionToken: p.regionToken.value
    ownerTag: p.ownerTag.value
    costCenterTag: p.costCenterTag.value
    accountName: p.accountName.value
    projectName: p.projectName.value
    customSubDomainName: p.customSubDomainName.value
    modelDeploymentName: p.modelDeploymentName.value
    modelFormat: p.modelFormat.value
    modelName: p.modelName.value
    modelVersion: p.modelVersion.value
    modelDeploymentSkuName: p.modelDeploymentSkuName.value
    modelDeploymentCapacity: p.modelDeploymentCapacity.value
    modelVersionUpgradeOption: p.modelVersionUpgradeOption.value
    modelDataResidencyApproval: p.modelDataResidencyApproval.value
    modelDeploymentApproved: p.modelDeploymentApproved.value
    network: p.network.value
    functionPackageBlobName: p.functionPackageBlobName.value
    functionPythonVersion: p.functionPythonVersion.value
    functionMaximumInstances: p.functionMaximumInstances.value
    eventHubConsumerGroupName: p.eventHubConsumerGroupName.value
    arizeProjectName: p.arizeProjectName.value
    keyVaultReferences: p.keyVaultReferences.value
    appInsightsConnectionName: p.appInsightsConnectionName.value
    tracingAssociationMode: p.tracingAssociationMode.value
    appInsightsConnectionPropertiesReviewed: p.appInsightsConnectionPropertiesReviewed.value
  }
}

module bootstrap 'issue147-app-insights-bootstrap.bicep' = {
  name: 'issue147-routing-bootstrap'
  scope: freshGroup
  dependsOn: [
    foundation
  ]
}

output secretVersionUri string = bootstrap.outputs.secretVersionUri
output componentBindingResourceId string = bootstrap.outputs.componentBindingResourceId
