<#
.SYNOPSIS
  OFFLINE ONLY: compile supported Bicep entrypoints and verify modern outputs.
.DESCRIPTION
  No Azure CLI, authentication, account lookup, what-if, create or deployment.
  Use official azure-prepare -> azure-validate -> azure-deploy only after scoped
  user approval. Compilation is not provider/private-path/runtime validation.
  BICEP_CLI may identify an already installed standalone Bicep binary. Never
  installs or upgrades dependencies. Compiled JSON stays in memory.
.EXAMPLE
  ./infra/scripts/validate-deployment.ps1
#>
[CmdletBinding()]
param(
  [string]$BicepExecutable = $env:BICEP_CLI
)
$ErrorActionPreference = 'Stop'
if (-not $BicepExecutable) {
  $command = Get-Command bicep -ErrorAction SilentlyContinue
  if ($command) { $BicepExecutable = $command.Source }
}
if (-not $BicepExecutable) {
  $contained = Join-Path $PSScriptRoot '..' '..' '.azure-config' 'bin' 'bicep.exe'
  if (Test-Path $contained -PathType Leaf) { $BicepExecutable = $contained }
}
if (-not $BicepExecutable) {
  throw 'Standalone Bicep is required. Set BICEP_CLI; no installation or Azure command was attempted.'
}
$templates = @{}
foreach ($entry in @('main.bicep', 'modern-foundry-tracing.bicep', 'durable-genai-rollout.bicep')) {
  $path = Join-Path $PSScriptRoot '..' $entry
  $compiled = & $BicepExecutable build $path --stdout
  if ($LASTEXITCODE -ne 0) { throw "Offline type-check failed: $entry" }
  $templates[$entry] = ($compiled -join "`n") | ConvertFrom-Json -AsHashtable
  Write-Host "PASS offline Bicep type-check: $entry"
}
$main = $templates['main.bicep']
foreach ($name in @(
  'foundryAccountResourceId', 'foundryAccountName', 'foundryAccountPrincipalId',
  'foundryProjectResourceId', 'foundryProjectName', 'foundryProjectPrincipalId',
  'foundryProjectEndpoint', 'modelDeploymentResourceId', 'modelDeploymentName',
  'logAnalyticsWorkspaceId', 'appInsightsResourceId', 'keyVaultResourceId',
  'eventHubNamespaceResourceId', 'functionAppResourceId', 'storageAccountResourceId',
  'exportRuleResourceId', 'privateDnsZoneResourceIds'
)) {
  if (-not $main.outputs.ContainsKey($name)) { throw "Missing modern output: $name" }
}
if ($main.outputs.privateEndpointsEnabled.value -ne $true) { throw 'Private endpoints must be unconditional.' }
if ($main.outputs.consumerEnabled.value -ne $false) { throw 'Fresh consumers must remain disabled.' }
Write-Host 'PASS modern output contract; no provider, reachability, deployment, idempotence or runtime claim.'
