targetScope = 'resourceGroup'

@description('Existing modern AIServices account. This entrypoint never redeploys its parent resources.')
@minLength(2)
param accountName string

@description('Existing modern Foundry project.')
@minLength(2)
param projectName string

@description('Exact existing manual connection name, or reviewed stable name for clean creation.')
@minLength(3)
@maxLength(33)
param appInsightsConnectionName string

@description('Full ARM ID of the intended existing Application Insights component.')
@minLength(1)
param appInsightsResourceId string

@description('Safe default emits no connection PUT. ApiKey explicitly creates/adopts without MI migration; ProjectManagedIdentity is a separate approved migration.')
@allowed(['preserveExisting', 'ApiKey', 'ProjectManagedIdentity'])
param tracingAssociationMode string = 'preserveExisting'

@description('Review exact existing isSharedToAll first: private=false, projectShared=true. This default is not a live sharing assertion.')
@allowed(['private', 'projectShared'])
param appInsightsConnectionSharing string = 'private'

@description('Reviewed connection private-endpoint requirement; must match the existing writable property when adopting.')
@allowed(['Required', 'NotRequired', 'NotApplicable'])
param appInsightsConnectionPeRequirement string = 'NotRequired'

@description('Reviewed peStatus request value accepted by API 2025-09-01. Does not prove actual private-endpoint health.')
@allowed(['Inactive', 'Active', 'NotApplicable'])
param appInsightsConnectionPeStatus string = 'NotApplicable'

@description('Leave false until exact writable properties and equivalent pinned Key Vault material have been reviewed. False fails active module validation.')
param appInsightsConnectionPropertiesReviewed bool = false

@description('Version-pinned Key Vault deployment reference only. ApiKey uses credentials.key; MI uses provider-readable routing metadata, requiring separate security approval.')
@secure()
param appInsightsConnectionString string = ''

module tracing 'modules/modern-foundry-app-insights.bicep' = if (tracingAssociationMode == 'ApiKey' || tracingAssociationMode == 'ProjectManagedIdentity') {
  name: 'modern-foundry-app-insights'
  params: {
    accountName: accountName
    projectName: projectName
    connectionName: appInsightsConnectionName
    appInsightsResourceId: appInsightsResourceId
    appInsightsConnectionString: appInsightsConnectionString
    connectionAuthType: tracingAssociationMode == 'ApiKey' ? 'ApiKey' : 'ProjectManagedIdentity'
    connectionSharing: appInsightsConnectionSharing
    connectionPeRequirement: appInsightsConnectionPeRequirement
    connectionPeStatus: appInsightsConnectionPeStatus
    // Deliberately fail nested parameter validation for an unreviewed active PUT.
    #disable-next-line BCP329
    reviewedProperties: appInsightsConnectionPropertiesReviewed ? 1 : 0
  }
}

@description('Intended ID only; does not establish live existence, health or trace delivery.')
output appInsightsConnectionResourceId string = resourceId('Microsoft.CognitiveServices/accounts/projects/connections', accountName, projectName, appInsightsConnectionName)
output tracingAssociationRequestedMode string = tracingAssociationMode
