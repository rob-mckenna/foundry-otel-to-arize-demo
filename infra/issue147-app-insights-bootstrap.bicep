// First-allocation routing custody only; never a general secret transfer tool.
targetScope = 'resourceGroup'

resource component 'Microsoft.Insights/components@2020-02-02' existing = {
  name: 'fotoa147-demo-appi-eastus2'
}

module custody 'modules/app-insights-secret.bicep' = {
  name: 'issue147-new-routing-custody'
  scope: resourceGroup('fotoa-demo-rg')
  params: {
    vaultName: 'fotoa-demo-kv-eastus2'
    secretName: 'fotoa147-appinsights-connection-string'
    componentResourceId: component.id
    // Auditable first-allocation expiry: 2026-11-20T10:15:00Z.
    expirationEpochSeconds: 1795169700
    environment: 'demo'
    ownerTag: 'infra-team'
    costCenterTag: 'demo-engineering'
    // ARM resolves this after component creation; no credential output/CLI parameter.
    connectionString: component.properties.ConnectionString
  }
}

output secretVersionUri string = custody.outputs.secretVersionUri
output componentBindingResourceId string = custody.outputs.componentBindingResourceId
