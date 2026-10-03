<#
.SYNOPSIS
  Validates that every Bicep module in infra/modules (excluding the shared
  naming.bicep helper itself) uses the shared naming/tagging helpers instead
  of re-declaring ad hoc resource names or tag objects.

.DESCRIPTION
  Issue #20 requires a lint/validation step that fails when a module is
  missing required tags or violates the naming pattern. Full semantic
  validation of Bicep requires the Bicep compiler (not guaranteed to be
  available in every CI runner), so this script performs a pragmatic static
  check: every module must call `buildResourceName(...)` for its resource
  name(s) and `buildRequiredTags(...)` for its tags, rather than hand-rolling
  the `{project}-{env}-{resourceType}-{region}` pattern or the five required
  tag keys inline. This catches the most common drift (a new module author
  forgetting to import the shared helpers) with no external dependencies.

.PARAMETER ModulesPath
  Path to the directory containing *.bicep modules to validate. Defaults to
  infra/modules relative to this script.

.EXAMPLE
  pwsh ./infra/scripts/validate-naming.ps1
  Runs validation and exits 0 on success, 1 on any violation (with details).
#>
[CmdletBinding()]
param(
  [string]$ModulesPath = (Join-Path $PSScriptRoot '..' 'modules')
)

$ErrorActionPreference = 'Stop'

$ModulesPath = (Resolve-Path $ModulesPath).Path
$violations = New-Object System.Collections.Generic.List[string]

$moduleFiles = Get-ChildItem -Path $ModulesPath -Filter '*.bicep' -File |
  Where-Object { $_.Name -ne 'naming.bicep' }

if ($moduleFiles.Count -eq 0) {
  Write-Warning "No .bicep modules found under $ModulesPath (excluding naming.bicep) - nothing to validate."
  exit 0
}

foreach ($file in $moduleFiles) {
  $content = Get-Content -Path $file.FullName -Raw

  $usesNamingImport = $content -match "import\s*\{[^}]*buildResourceName[^}]*\}\s*from\s*'naming\.bicep'"
  $usesBuildResourceName = $content -match 'buildResourceName\('
  $usesBuildRequiredTags = $content -match 'buildRequiredTags\('

  if (-not $usesNamingImport) {
    $violations.Add("$($file.Name): does not import buildResourceName/buildRequiredTags from naming.bicep")
  }
  if (-not $usesBuildResourceName) {
    $violations.Add("$($file.Name): does not call buildResourceName(...) - resource name(s) may not follow the {project}-{env}-{resourceType}-{region} convention")
  }
  if (-not $usesBuildRequiredTags) {
    $violations.Add("$($file.Name): does not call buildRequiredTags(...) - resource(s) may be missing the required tag set (environment, owner, project, costCenter, dataClassification)")
  }
}

if ($violations.Count -gt 0) {
  Write-Host "Naming/tagging convention validation FAILED:" -ForegroundColor Red
  foreach ($v in $violations) {
    Write-Host "  - $v" -ForegroundColor Red
  }
  exit 1
}

Write-Host "Naming/tagging convention validation PASSED for $($moduleFiles.Count) module(s):" -ForegroundColor Green
foreach ($file in $moduleFiles) {
  Write-Host "  - $($file.Name)" -ForegroundColor Green
}
exit 0
