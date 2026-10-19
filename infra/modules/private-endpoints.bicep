import { buildResourceName, buildRequiredTags, resourceTypeTokens } from 'naming.bicep'

type privateEndpointTarget = {
  name: string
  targetResourceId: string
  groupId: string
  @minLength(1)
  privateDnsZoneResourceIds: string[]
}

param projectToken string
param environment string
param location string
param regionToken string
param ownerTag string
param costCenterTag string
@minLength(1)
param subnetResourceId string
param targets privateEndpointTarget[]

var endpointNames = [for target in targets: buildResourceName(projectToken, environment, '${resourceTypeTokens.privateEndpoint}-${target.name}', regionToken)]

resource endpoints 'Microsoft.Network/privateEndpoints@2023-11-01' = [for (target, i) in targets: {
  name: endpointNames[i]
  location: location
  tags: buildRequiredTags(environment, ownerTag, costCenterTag, 'synthetic')
  properties: {
    subnet: {
      id: subnetResourceId
    }
    privateLinkServiceConnections: [
      {
        name: '${target.name}-connection'
        properties: {
          privateLinkServiceId: target.targetResourceId
          groupIds: [
            target.groupId
          ]
        }
      }
    ]
  }
}]

resource zoneGroups 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = [for (target, i) in targets: {
  parent: endpoints[i]
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [for (zoneId, j) in target.privateDnsZoneResourceIds: {
      name: 'zone-${j}'
      properties: {
        privateDnsZoneId: zoneId
      }
    }]
  }
}]

output privateEndpointResourceIds array = [for (target, i) in targets: endpoints[i].id]
output privateEndpointsEnabled bool = true
