// =============================================================================
// naming.bicep
// Shared naming and tagging helpers enforcing the repo convention:
//   {project}-{env}-{resourceType}-{region}
// and the required tag set: environment, owner, project, costCenter,
// dataClassification (see /.github/copilot-instructions.md section 7).
//
// Other modules import these functions instead of re-declaring their own
// naming/tag `var`s, so the convention is defined exactly once and cannot
// silently drift between modules. Requires Bicep's compile-time imports
// feature (enabled via bicepconfig.json at the repo/infra root - see that
// file for the experimentalFeaturesEnabled flag some Bicep CLI versions
// still require).
//
// Usage from another module:
//   import { buildResourceName, buildRequiredTags } from 'naming.bicep'
//   var myName = buildResourceName(projectToken, environment, 'kv', regionToken)
//   var myTags = buildRequiredTags(environment, ownerTag, costCenterTag, dataClassificationTag)
// =============================================================================

@description('Builds a resource name following the {project}-{env}-{resourceType}-{region} convention.')
@export()
func buildResourceName(projectToken string, environment string, resourceType string, regionToken string) string =>
  '${projectToken}-${environment}-${resourceType}-${regionToken}'

@description('Builds the required tag object (environment, owner, project, costCenter, dataClassification) applied to every provisioned resource in this repo. `project` is always the fixed repo identifier; `dataClassification` must stay "synthetic" for every demo resource.')
@export()
func buildRequiredTags(environment string, ownerTag string, costCenterTag string, dataClassificationTag string) object => {
  environment: environment
  owner: ownerTag
  project: 'foundry-otel-to-arize-demo'
  costCenter: costCenterTag
  dataClassification: dataClassificationTag
}

@description('Canonical list of required tag keys, used by validation tooling (infra/scripts/validate-naming.ps1) to confirm every module applies the full required set.')
@export()
var requiredTagKeys = [
  'environment'
  'owner'
  'project'
  'costCenter'
  'dataClassification'
]

@description('Short resource-type tokens used across modules, kept here so every module author pulls from the same abbreviation list instead of inventing new ones.')
@export()
var resourceTypeTokens = {
  foundryHub: 'aihub'
  foundryProject: 'aiproj'
  logAnalyticsWorkspace: 'law'
  applicationInsights: 'appi'
  keyVault: 'kv'
  functionApp: 'func'
  eventHubNamespace: 'ehns'
  storageAccount: 'st'
  privateEndpoint: 'pe'
  virtualNetwork: 'vnet'
}
