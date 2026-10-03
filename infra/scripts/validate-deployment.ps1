<#
.SYNOPSIS
  End-to-end deployment validation for infra/main.bicep (issue #22).

.DESCRIPTION
  Runs `az deployment group what-if` and then `az deployment group create`
  against a scratch resource group, confirms every module's resource(s)
  reached provisioning state `Succeeded`, spot-checks the managed-identity
  RBAC wiring this repo relies on (Key Vault Secrets User, Event Hub Data
  Receiver), and prints a single pass/fail summary with resource names and
  timestamps that a sales engineer or CI job can run the morning of a demo.

  This script is written for a real Azure environment with the `az` CLI
  authenticated against a subscription. It is NOT executable in this
  automated authoring sandbox - `az` hits a PermissionError reading the
  cached profile at ~/.azure/azureProfile.json here (see
  .squad/agents/infra/history.md). The script fails fast with a clear
  message if `az` is missing or not logged in rather than silently no-op'ing,
  so this limitation is obvious to whoever runs it for real.

.PARAMETER ResourceGroupName
  Scratch resource group to deploy into. Defaults to a timestamped name
  (fotoa-validate-<yyyyMMddHHmmss>) so repeat runs never collide.

.PARAMETER Location
  Azure region to create the scratch resource group in if it does not
  already exist. Defaults to eastus2 (matches infra/main.parameters.json).

.PARAMETER TemplateFile
  Path to the Bicep entry point. Defaults to infra/main.bicep relative to
  this script.

.PARAMETER ParametersFile
  Path to the parameters file. Defaults to infra/main.parameters.json
  relative to this script (the public-access demo baseline - no secrets).

.PARAMETER SkipCreate
  Run `what-if` only; do not actually deploy. Useful for a fast pre-PR
  sanity check that does not spend money or wait for a full deployment.

.PARAMETER CreateResourceGroupIfMissing
  If set, creates ResourceGroupName in Location when it does not already
  exist. If not set and the resource group is missing, the script fails
  with guidance rather than silently creating billable infrastructure.

.EXAMPLE
  pwsh ./infra/scripts/validate-deployment.ps1 -ResourceGroupName fotoa-validate-demo -CreateResourceGroupIfMissing
  Deploys the full stack to a fresh scratch resource group and validates it.

.EXAMPLE
  pwsh ./infra/scripts/validate-deployment.ps1 -ResourceGroupName fotoa-validate-demo -SkipCreate
  Runs `what-if` only against an existing scratch resource group - no
  resources are created or modified.

.EXAMPLE
  # Induced-failure test (per issue #22 validation steps): pass a parameters
  # file with a bad value (e.g. an out-of-range eventHubPartitionCount) and
  # confirm the script reports the deployment failure clearly instead of a
  # false pass:
  pwsh ./infra/scripts/validate-deployment.ps1 -ResourceGroupName fotoa-validate-demo `
    -ParametersFile ./infra/main.parameters.json -CreateResourceGroupIfMissing
#>
[CmdletBinding()]
param(
  [string]$ResourceGroupName = "fotoa-validate-$(Get-Date -Format 'yyyyMMddHHmmss')",
  [string]$Location = 'eastus2',
  [string]$TemplateFile = (Join-Path $PSScriptRoot '..' 'main.bicep'),
  [string]$ParametersFile = (Join-Path $PSScriptRoot '..' 'main.parameters.json'),
  [switch]$SkipCreate,
  [switch]$CreateResourceGroupIfMissing
)

$ErrorActionPreference = 'Stop'
$script:startTime = Get-Date
$script:results = New-Object System.Collections.Generic.List[pscustomobject]

function Write-Section($title) {
  Write-Host ''
  Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Add-Result([string]$Check, [bool]$Pass, [string]$Detail) {
  $script:results.Add([pscustomobject]@{
    Timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    Check     = $Check
    Pass      = $Pass
    Detail    = $Detail
  })
  $color = if ($Pass) { 'Green' } else { 'Red' }
  $status = if ($Pass) { 'PASS' } else { 'FAIL' }
  Write-Host "[$status] $Check - $Detail" -ForegroundColor $color
}

# ---------------------------------------------------------------------------
# 0. Preconditions: az CLI present and authenticated.
# ---------------------------------------------------------------------------
Write-Section 'Preconditions'

$azCommand = Get-Command az -ErrorAction SilentlyContinue
if (-not $azCommand) {
  Add-Result -Check 'az CLI available' -Pass $false -Detail 'az CLI not found on PATH. Install https://learn.microsoft.com/cli/azure/install-azure-cli and re-run.'
  Write-Host "`nCannot continue without the az CLI. This is expected in the automated authoring sandbox (see infra README); run this script from a workstation/CI runner with az installed and `az login` completed." -ForegroundColor Yellow
  exit 1
}
Add-Result -Check 'az CLI available' -Pass $true -Detail "Found at $($azCommand.Source)"

$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
  Add-Result -Check 'az CLI authenticated' -Pass $false -Detail "Not logged in. Run 'az login' (and 'az account set --subscription <id>' if needed) before re-running."
  exit 1
}
Add-Result -Check 'az CLI authenticated' -Pass $true -Detail "Subscription: $($account.name) ($($account.id))"

if (-not (Test-Path $TemplateFile)) {
  Add-Result -Check 'Template file exists' -Pass $false -Detail "$TemplateFile not found."
  exit 1
}
if (-not (Test-Path $ParametersFile)) {
  Add-Result -Check 'Parameters file exists' -Pass $false -Detail "$ParametersFile not found."
  exit 1
}
Add-Result -Check 'Template + parameters files found' -Pass $true -Detail "$TemplateFile / $ParametersFile"

# ---------------------------------------------------------------------------
# 1. Resource group.
# ---------------------------------------------------------------------------
Write-Section "Resource group: $ResourceGroupName"

$rg = az group show --name $ResourceGroupName 2>$null | ConvertFrom-Json
if (-not $rg) {
  if ($CreateResourceGroupIfMissing) {
    Write-Host "Resource group $ResourceGroupName not found - creating in $Location (per -CreateResourceGroupIfMissing)..."
    az group create --name $ResourceGroupName --location $Location --tags project=foundry-otel-to-arize-demo dataClassification=synthetic purpose=deployment-validation | Out-Null
    $rg = az group show --name $ResourceGroupName 2>$null | ConvertFrom-Json
  } else {
    Add-Result -Check 'Resource group exists' -Pass $false -Detail "$ResourceGroupName does not exist. Re-run with -CreateResourceGroupIfMissing, or create it yourself first (az group create --name $ResourceGroupName --location $Location)."
    exit 1
  }
}
Add-Result -Check 'Resource group exists' -Pass ($null -ne $rg) -Detail "$ResourceGroupName in $($rg.location)"

# ---------------------------------------------------------------------------
# 2. what-if preview (always runs - cheap, non-destructive, dependency-order
#    aware because Bicep/ARM resolves module dependencies automatically from
#    the `module` graph in main.bicep; no separate ordering step is needed).
# ---------------------------------------------------------------------------
Write-Section 'what-if preview'

$whatIfOutput = az deployment group what-if `
  --resource-group $ResourceGroupName `
  --template-file $TemplateFile `
  --parameters "@$ParametersFile" `
  --no-pretty-print 2>&1
$whatIfExit = $LASTEXITCODE
Write-Host $whatIfOutput
Add-Result -Check 'what-if preview succeeded' -Pass ($whatIfExit -eq 0) -Detail "exit code $whatIfExit"

if ($whatIfExit -ne 0) {
  Write-Host "`nwhat-if failed - aborting before an actual deployment is attempted." -ForegroundColor Red
  Write-Summary
  exit 1
}

if ($SkipCreate) {
  Write-Host "`n-SkipCreate set: stopping after what-if (no resources were created or modified)." -ForegroundColor Yellow
  Write-Summary
  exit 0
}

# ---------------------------------------------------------------------------
# 3. Actual deployment.
# ---------------------------------------------------------------------------
Write-Section 'Deployment'

$deploymentName = "fotoa-validate-$(Get-Date -Format 'yyyyMMddHHmmss')"
Write-Host "Deploying as '$deploymentName' - this can take several minutes (Foundry project + Key Vault purge-protection-enabled create are the slowest steps)..."

$deployOutputRaw = az deployment group create `
  --resource-group $ResourceGroupName `
  --name $deploymentName `
  --template-file $TemplateFile `
  --parameters "@$ParametersFile" `
  --output json 2>&1
$deployExit = $LASTEXITCODE

if ($deployExit -ne 0) {
  Add-Result -Check 'Deployment completed' -Pass $false -Detail "exit code $deployExit. Output: $deployOutputRaw"
  Write-Summary
  exit 1
}

$deployment = $deployOutputRaw | ConvertFrom-Json
Add-Result -Check 'Deployment completed' -Pass ($deployment.properties.provisioningState -eq 'Succeeded') -Detail "Deployment '$deploymentName' state: $($deployment.properties.provisioningState)"

$outputs = $deployment.properties.outputs

# ---------------------------------------------------------------------------
# 4. Per-resource provisioning state checks.
#    Maps each main.bicep output to the az resource it identifies, so this
#    script stays in sync automatically as modules are added - no hardcoded
#    resource-name guessing.
# ---------------------------------------------------------------------------
Write-Section 'Resource provisioning states'

$resourceIdChecks = @(
  @{ Label = 'Foundry project'; IdOutput = 'foundryProjectResourceId' }
  @{ Label = 'Log Analytics workspace'; IdOutput = 'logAnalyticsWorkspaceId' }
  @{ Label = 'Application Insights'; IdOutput = 'appInsightsResourceId' }
  @{ Label = 'Key Vault'; IdOutput = 'keyVaultResourceId' }
)

foreach ($check in $resourceIdChecks) {
  $resourceId = $outputs.($check.IdOutput).value
  if (-not $resourceId) {
    Add-Result -Check $check.Label -Pass $false -Detail "Output '$($check.IdOutput)' missing from deployment outputs."
    continue
  }
  $resource = az resource show --ids $resourceId --output json 2>$null | ConvertFrom-Json
  $state = $resource.properties.provisioningState
  Add-Result -Check $check.Label -Pass ($state -eq 'Succeeded') -Detail "$resourceId -> provisioningState: $state"
}

# Event Hub namespace + Function App are only identified by name (not a full
# resource ID) in current main.bicep outputs - resolve via az resource list.
$namespaceName = $outputs.eventHubNamespaceName.value
if ($namespaceName) {
  $ehNamespace = az eventhubs namespace show --resource-group $ResourceGroupName --name $namespaceName --output json 2>$null | ConvertFrom-Json
  Add-Result -Check 'Event Hub namespace' -Pass ($ehNamespace.provisioningState -eq 'Succeeded') -Detail "$namespaceName -> provisioningState: $($ehNamespace.provisioningState)"
} else {
  Add-Result -Check 'Event Hub namespace' -Pass $false -Detail "Output 'eventHubNamespaceName' missing from deployment outputs."
}

$functionAppName = $outputs.functionAppName.value
if ($functionAppName) {
  $functionApp = az functionapp show --resource-group $ResourceGroupName --name $functionAppName --output json 2>$null | ConvertFrom-Json
  $state = $functionApp.state
  Add-Result -Check 'Function App' -Pass ($state -eq 'Running') -Detail "$functionAppName -> state: $state, defaultHostName: $($functionApp.defaultHostName)"
} else {
  Add-Result -Check 'Function App' -Pass $false -Detail "Output 'functionAppName' missing from deployment outputs (expected once issue #19 is deployed)."
}

# ---------------------------------------------------------------------------
# 5. RBAC spot checks (not exhaustive - confirms the documented cross-wiring
#    in infra/README.md actually landed, per acceptance criteria).
# ---------------------------------------------------------------------------
Write-Section 'Managed identity + RBAC spot checks'

$keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
$eventHubDataReceiverRoleId = 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde'

$functionPrincipalId = $outputs.functionAppPrincipalId.value
$keyVaultResourceId = $outputs.keyVaultResourceId.value

if ($functionPrincipalId -and $keyVaultResourceId) {
  $kvAssignments = az role assignment list --scope $keyVaultResourceId --assignee $functionPrincipalId --output json 2>$null | ConvertFrom-Json
  $hasSecretsUser = $kvAssignments | Where-Object { $_.roleDefinitionId -like "*$keyVaultSecretsUserRoleId" }
  Add-Result -Check 'Function App -> Key Vault Secrets User' -Pass ($null -ne $hasSecretsUser) -Detail "principal $functionPrincipalId on $keyVaultResourceId"
} else {
  Add-Result -Check 'Function App -> Key Vault Secrets User' -Pass $false -Detail 'functionAppPrincipalId or keyVaultResourceId output missing - cannot spot-check.'
}

if ($functionPrincipalId -and $namespaceName) {
  $ehResourceId = az eventhubs namespace show --resource-group $ResourceGroupName --name $namespaceName --query id --output tsv 2>$null
  if ($ehResourceId) {
    $ehAssignments = az role assignment list --scope $ehResourceId --assignee $functionPrincipalId --output json 2>$null | ConvertFrom-Json
    $hasDataReceiver = $ehAssignments | Where-Object { $_.roleDefinitionId -like "*$eventHubDataReceiverRoleId" }
    Add-Result -Check 'Function App -> Event Hub Data Receiver' -Pass ($null -ne $hasDataReceiver) -Detail "principal $functionPrincipalId on $ehResourceId"
  }
} else {
  Add-Result -Check 'Function App -> Event Hub Data Receiver' -Pass $false -Detail 'functionAppPrincipalId or eventHubNamespaceName output missing - cannot spot-check.'
}

$foundryPrincipalId = $outputs.foundryProjectPrincipalId.value
if ($foundryPrincipalId -and $keyVaultResourceId) {
  $foundryAssignments = az role assignment list --scope $keyVaultResourceId --assignee $foundryPrincipalId --output json 2>$null | ConvertFrom-Json
  $hasSecretsUser = $foundryAssignments | Where-Object { $_.roleDefinitionId -like "*$keyVaultSecretsUserRoleId" }
  Add-Result -Check 'Foundry project -> Key Vault Secrets User' -Pass ($null -ne $hasSecretsUser) -Detail "principal $foundryPrincipalId on $keyVaultResourceId"
}

function Write-Summary {
  Write-Section 'Summary'
  $duration = (Get-Date) - $script:startTime
  $failed = $script:results | Where-Object { -not $_.Pass }
  $script:results | Format-Table Timestamp, Check, Pass, Detail -AutoSize | Out-String | Write-Host

  Write-Host "Total checks: $($script:results.Count)  Passed: $(($script:results | Where-Object Pass).Count)  Failed: $($failed.Count)"
  Write-Host "Elapsed: $($duration.ToString('hh\:mm\:ss'))"

  if ($failed.Count -eq 0) {
    Write-Host "`nRESULT: PASS - deployment to '$ResourceGroupName' validated successfully." -ForegroundColor Green
  } else {
    Write-Host "`nRESULT: FAIL - $($failed.Count) check(s) failed. See details above." -ForegroundColor Red
  }
}

Write-Summary
exit ([int]($script:results | Where-Object { -not $_.Pass } | Measure-Object).Count -gt 0)
