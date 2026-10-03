// =============================================================================
// networking.bicep
// OPTIONAL private-endpoint module for the Milestone 1 compute/secret
// resources (Key Vault #18, Foundry project #15, and a future Function App).
// Disabled (`enablePrivateEndpoints: false`) by default to match this repo's
// demo baseline posture: public network access secured by Azure AD/RBAC
// auth, chosen to keep demo setup time low for prospects (see
// /infra/README.md "Network posture" section and
// .squad/decisions/inbox/infra-network-posture.md for the full rationale).
//
// When enabled, this module can optionally provision a small scratch VNet +
// subnet (private-endpoint network policies disabled, per Azure
// requirements for private endpoints) and creates one
// Microsoft.Network/privateEndpoints resource per entry in
// `privateEndpointTargets`, each with a matching private DNS zone group so
// name resolution works without extra client-side configuration.
//
// Naming/tagging: uses the shared infra/modules/naming.bicep helpers.
// =============================================================================

import { buildResourceName, buildRequiredTags, resourceTypeTokens } from 'naming.bicep'

@description('Master on/off switch for private networking. Defaults to false (public access + RBAC), the demo baseline posture. Set true to deploy the private-endpoint variant.')
param enablePrivateEndpoints bool = false

@description('Short project token used in resource names, e.g. "fotoa" for foundry-otel-to-arize-demo.')
@minLength(2)
@maxLength(10)
param projectToken string = 'fotoa'

@description('Environment token used in resource names and tags: dev, demo, or prod.')
@allowed([
  'dev'
  'demo'
  'prod'
])
param environment string = 'demo'

@description('Azure region for the deployment (full ARM location name, e.g. eastus2).')
param location string = resourceGroup().location

@description('Short region token used in resource names, e.g. "eastus2".')
param regionToken string = 'eastus2'

@description('Owner tag value (responsible team/individual) - required by repo tagging convention.')
param ownerTag string

@description('Cost center tag value - required by repo tagging convention.')
param costCenterTag string

@description('Data classification tag. Must be "synthetic" for all demo resources in this repo.')
@allowed([
  'synthetic'
])
param dataClassificationTag string = 'synthetic'

@description('When true (and enablePrivateEndpoints is true), this module provisions a small scratch VNet + subnet dedicated to private endpoints. Set false and supply existingSubnetResourceId to reuse an existing network instead - recommended for a real customer POC rather than a throwaway scratch validation.')
param createVirtualNetwork bool = true

@description('Address space for the scratch VNet, when createVirtualNetwork is true.')
param virtualNetworkAddressPrefix string = '10.20.0.0/24'

@description('Address prefix for the private-endpoints subnet, when createVirtualNetwork is true. Must be within virtualNetworkAddressPrefix.')
param privateEndpointSubnetAddressPrefix string = '10.20.0.0/26'

@description('Resource ID of an existing subnet to deploy private endpoints into, when createVirtualNetwork is false. Required in that case.')
param existingSubnetResourceId string = ''

@description('Array of private endpoint targets to provision when enablePrivateEndpoints is true. Each entry: { name: short token used in the PE resource name (e.g. "kv", "aiproj", "func"), targetResourceId: resource ID of the resource to privately link, groupId: the sub-resource group ID for that resource type (e.g. "vault" for Key Vault, "amlworkspace" for a Foundry/ML workspace, "sites" for a Function/Web App) }. Leave empty to provision the network scaffolding only.')
param privateEndpointTargets array = []

var requiredTags = buildRequiredTags(environment, ownerTag, costCenterTag, dataClassificationTag)
var vnetName = buildResourceName(projectToken, environment, resourceTypeTokens.virtualNetwork, regionToken)
var subnetName = 'private-endpoints'

resource scratchVnet 'Microsoft.Network/virtualNetworks@2023-11-01' = if (enablePrivateEndpoints && createVirtualNetwork) {
  name: vnetName
  location: location
  tags: requiredTags
  properties: {
    addressSpace: {
      addressPrefixes: [
        virtualNetworkAddressPrefix
      ]
    }
    subnets: [
      {
        name: subnetName
        properties: {
          addressPrefix: privateEndpointSubnetAddressPrefix
          // Required by Azure for subnets hosting private endpoints.
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

var resolvedSubnetResourceId = createVirtualNetwork
  ? '${scratchVnet.id}/subnets/${subnetName}'
  : existingSubnetResourceId

resource privateEndpoints 'Microsoft.Network/privateEndpoints@2023-11-01' = [
  for target in privateEndpointTargets: if (enablePrivateEndpoints) {
    name: buildResourceName(projectToken, environment, '${resourceTypeTokens.privateEndpoint}-${target.name}', regionToken)
    location: location
    tags: requiredTags
    properties: {
      subnet: {
        id: resolvedSubnetResourceId
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
  }
]

@description('True if private endpoints were deployed by this module invocation.')
output privateEndpointsEnabled bool = enablePrivateEndpoints

@description('Resource ID of the scratch VNet, when created. Empty string otherwise.')
output virtualNetworkResourceId string = (enablePrivateEndpoints && createVirtualNetwork) ? scratchVnet.id : ''

@description('Resource ID of the subnet private endpoints were deployed into (scratch or existing). Empty string when private endpoints are disabled.')
output subnetResourceId string = enablePrivateEndpoints ? resolvedSubnetResourceId : ''

@description('Resource IDs of every private endpoint created, in the same order as privateEndpointTargets.')
output privateEndpointResourceIds array = [for (target, i) in privateEndpointTargets: enablePrivateEndpoints ? privateEndpoints[i].id : '']
