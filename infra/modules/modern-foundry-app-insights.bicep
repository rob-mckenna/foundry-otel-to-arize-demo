@description('Existing AIServices account. No parent, network, identity or RBAC properties are changed.')
@minLength(2)
param accountName string

@description('Existing modern Foundry project.')
@minLength(2)
param projectName string

@description('Exact manual name when adopting; preflight must reject a different existing AppInsights connection.')
@minLength(3)
@maxLength(33)
param connectionName string

@description('Full ARM ID of the intended existing Application Insights component.')
@minLength(1)
param appInsightsResourceId string

@description('ApiKey preserves existing ingestion authentication; ProjectManagedIdentity is separately approved.')
@allowed(['ApiKey', 'ProjectManagedIdentity'])
param connectionAuthType string

@description('Required reviewed sharing setting. Never infer sharing from the auth type.')
@allowed(['private', 'projectShared'])
param connectionSharing string

@description('Positive acknowledgement of reviewed writable properties and equivalent secure material. Zero fails validation.')
@minValue(1)
param reviewedProperties int

@description('ApiKey credentials.key or MI routing metadata following Microsoft samples. Use a version-pinned Key Vault deployment reference.')
@secure()
@minLength(1)
param appInsightsConnectionString string

resource account 'Microsoft.CognitiveServices/accounts@2025-09-01' existing = {
  name: accountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-09-01' existing = {
  parent: account
  name: projectName
}

var apiKeyProperties = {
  category: 'AppInsights'
  target: appInsightsResourceId
  authType: 'ApiKey'
  isSharedToAll: connectionSharing == 'projectShared'
  useWorkspaceManagedIdentity: false
  credentials: {
    key: appInsightsConnectionString
  }
  metadata: {
    ApiType: 'Azure'
    ResourceId: appInsightsResourceId
  }
}

var managedIdentityProperties = {
  category: 'AppInsights'
  target: appInsightsResourceId
  authType: 'ProjectManagedIdentity'
  isSharedToAll: connectionSharing == 'projectShared'
  metadata: {
    ApiType: 'Azure'
    ResourceId: appInsightsResourceId
    ApplicationInsightsConnectionString: appInsightsConnectionString
  }
}

// Microsoft's pinned sample supports this discriminator despite stale ARM type definitions.
resource connection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-09-01' = {
  parent: project
  name: connectionName
  #disable-next-line BCP036
  properties: connectionAuthType == 'ApiKey' ? apiKeyProperties : managedIdentityProperties
}

output connectionResourceId string = connection.id
output connectionPropertiesReviewAcknowledged bool = reviewedProperties == 1
