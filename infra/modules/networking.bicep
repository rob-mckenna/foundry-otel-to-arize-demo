// Network ownership only: fresh VNet/DNS OR existing, externally linked topology.
// Private endpoints live in a separate module to avoid Function/network cycles.
import { buildResourceName, buildRequiredTags, resourceTypeTokens } from 'naming.bicep'

@export()
type privateDnsZoneIds = {
  cognitiveServices: string
  openAI: string
  servicesAI: string
  vault: string
  blob: string
  queue: string
  table: string
}

@export()
@discriminator('mode')
type privateNetworkConfiguration = {
  mode: 'fresh'
  virtualNetworkAddressPrefix: string
  privateEndpointSubnetAddressPrefix: string
  functionIntegrationSubnetAddressPrefix: string
} | {
  mode: 'existing'
  privateEndpointSubnetResourceId: string
  functionIntegrationSubnetResourceId: string
  // External owner maintains VNet links/forwarders. No zone or VNet PUT here.
  privateDnsZoneIds: privateDnsZoneIds
  dnsLinksManagedExternally: true
}

param projectToken string
param environment string
param location string
param regionToken string
param ownerTag string
param costCenterTag string
param network privateNetworkConfiguration

var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic')
var fresh = network.mode == 'fresh'
var zoneNames = [
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  'privatelink.services.ai.azure.com'
  'privatelink.vaultcore.azure.net'
  // ADR-0004 certifies only Azure public cloud; do not substitute other clouds.
  #disable-next-line no-hardcoded-env-urls
  'privatelink.blob.core.windows.net'
  #disable-next-line no-hardcoded-env-urls
  'privatelink.queue.core.windows.net'
  #disable-next-line no-hardcoded-env-urls
  'privatelink.table.core.windows.net'
]

resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-11-01' = if (network.mode == 'fresh') {
  name: buildResourceName(projectToken, environment, resourceTypeTokens.virtualNetwork, regionToken)
  location: location
  tags: requiredTags
  properties: {
    addressSpace: {
      addressPrefixes: [
        network.virtualNetworkAddressPrefix
      ]
    }
    // Authoritative list ONLY on a new VNet; never truncate a reused VNet.
    subnets: [
      {
        name: 'private-endpoints'
        properties: {
          addressPrefix: network.privateEndpointSubnetAddressPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'function-integration'
        properties: {
          addressPrefix: network.functionIntegrationSubnetAddressPrefix
          delegations: [
            {
              name: 'web-serverfarms'
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ]
        }
      }
    ]
  }
}

resource zones 'Microsoft.Network/privateDnsZones@2020-06-01' = [for zoneName in zoneNames: if (fresh) {
  name: zoneName
  location: 'global'
  tags: requiredTags
}]

resource links 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = [for (zoneName, i) in zoneNames: if (fresh) {
  parent: zones[i]
  name: buildResourceName(projectToken, environment, 'dnslink', regionToken)
  location: 'global'
  tags: requiredTags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetwork!.id
    }
  }
}]

output privateEndpointSubnetResourceId string = network.mode == 'fresh'
  ? '${virtualNetwork!.id}/subnets/private-endpoints'
  : network.privateEndpointSubnetResourceId
output functionIntegrationSubnetResourceId string = network.mode == 'fresh'
  ? '${virtualNetwork!.id}/subnets/function-integration'
  : network.functionIntegrationSubnetResourceId
output privateDnsZoneResourceIds privateDnsZoneIds = network.mode == 'fresh' ? {
  cognitiveServices: zones[0].id
  openAI: zones[1].id
  servicesAI: zones[2].id
  vault: zones[3].id
  blob: zones[4].id
  queue: zones[5].id
  table: zones[6].id
} : network.privateDnsZoneIds
output virtualNetworkResourceId string = fresh ? virtualNetwork!.id : ''
output dnsLinkOwnership string = fresh ? 'freshComposition' : 'externalOwner'
