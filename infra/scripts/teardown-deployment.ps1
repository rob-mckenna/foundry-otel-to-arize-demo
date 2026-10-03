<#
.SYNOPSIS
  Cleanup / teardown script for demo resources deployed by infra/main.bicep
  (issue #23).

.DESCRIPTION
  Removes everything the deployment validation script (infra/scripts/
  validate-deployment.ps1, issue #22) provisions, with explicit confirmation
  safeguards since this is destructive:
    1. Deletes the target resource group (default: the whole scratch
       resource group, since this repo's demo convention is one isolated
       resource group per demo - see -ResourceIds for the shared-group
       targeted-deletion alternative).
    2. Polls until the resource group (or targeted resources) are
       confirmed absent - does not just fire-and-forget the delete call.
    3. Purges the Key Vault's soft-deleted record (soft-delete + purge
       protection are enabled by modules/key-vault.bicep), with its own
       explicit confirmation prompt since purge is irreversible and
       independent of the resource-group delete.
    4. Lists any role assignments still scoped to the deleted resource
       IDs (Azure can leave orphaned role assignments behind after a
       resource is deleted) and reports them - these should normally
       self-clean, so any survivors are flagged for manual review rather
       than silently ignored.

  This script is written for a real Azure environment with the `az` CLI
  authenticated against a subscription. It is NOT executable in this
  automated authoring sandbox - `az` hits a PermissionError reading the
  cached profile at ~/.azure/azureProfile.json here (see
  .squad/agents/infra/history.md). It fails fast with a clear message if
  `az` is missing or not logged in rather than silently no-op'ing.

.PARAMETER ResourceGroupName
  The scratch resource group to tear down. Required - there is no default,
  so an operator cannot accidentally delete the wrong resource group by
  forgetting to pass this.

.PARAMETER ResourceIds
  Optional array of specific resource IDs to delete instead of the whole
  resource group - use this when the resource group is shared with other
  demos/resources that must not be touched (per issue #23's "targeted
  resource deletion if resources share a group with other demos"
  acceptance criteria). When supplied, the resource group itself is left
  in place and only these resources are deleted.

.PARAMETER KeyVaultName
  Name of the Key Vault to purge from its soft-deleted state after
  deletion. Required if -PurgeKeyVault is set; otherwise optional (the
  script will try to discover it from the resource group's resources if
  omitted and a full resource-group teardown is being performed).

.PARAMETER PurgeKeyVault
  If set, purges the Key Vault's soft-deleted record after the resource
  group/resource deletion completes (prompts for a separate, explicit
  "yes" confirmation since this is irreversible). If not set, the
  soft-deleted vault is left in its retention window (recoverable), which
  may be the correct choice if policy requires a retention period before
  purge - document that choice explicitly when skipping this flag.

.PARAMETER Force
  Skips the interactive confirmation prompts. Intended for CI/non-
  interactive use only - use with care, this makes the script fully
  destructive with no human-in-the-loop safeguard.

.EXAMPLE
  pwsh ./infra/scripts/teardown-deployment.ps1 -ResourceGroupName fotoa-validate-demo -PurgeKeyVault
  Deletes the whole scratch resource group (after confirmation), polls for
  its absence, then purges the Key Vault's soft-deleted record (after a
  second, separate confirmation).

.EXAMPLE
  pwsh ./infra/scripts/teardown-deployment.ps1 -ResourceGroupName shared-poc-rg `
    -ResourceIds "/subscriptions/.../resourceGroups/shared-poc-rg/providers/Microsoft.KeyVault/vaults/fotoa-demo-kv-eastus2"
  Deletes only the listed resources, leaving the shared resource group and
  any other tenants' resources in it untouched.

.EXAMPLE
  pwsh ./infra/scripts/teardown-deployment.ps1 -ResourceGroupName fotoa-validate-demo -Force -PurgeKeyVault
  Non-interactive teardown for CI - no confirmation prompts. Use only in a
  pipeline context where ResourceGroupName is already guaranteed scratch/
  disposable.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$ResourceGroupName,

  [string[]]$ResourceIds = @(),

  [string]$KeyVaultName,

  [switch]$PurgeKeyVault,

  [switch]$Force
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

function Confirm-Destructive([string]$Message) {
  if ($Force) {
    Write-Host "(-Force set) Skipping confirmation: $Message" -ForegroundColor Yellow
    return $true
  }
  $response = Read-Host "$Message Type 'yes' to continue"
  return $response -eq 'yes'
}

# Runs an `az ... --output json` command and parses its output, returning
# $null (instead of throwing) on any failure - including a non-zero exit
# code, or stdout that isn't valid JSON (e.g. az printing a Python
# traceback/error to stdout instead of stderr, which `ConvertFrom-Json`
# would otherwise turn into an unhandled terminating error under
# $ErrorActionPreference = 'Stop'). Callers treat a $null result the same
# as "az CLI unavailable/unauthenticated/resource not found" and report a
# clean FAIL via Add-Result rather than crashing with a raw exception.
function Invoke-AzJson {
  param([Parameter(Mandatory = $true)][string[]]$ArgumentList)
  # Native command stderr merged via 2>&1 arrives as ErrorRecord objects, not
  # plain strings - under the script-wide $ErrorActionPreference = 'Stop'
  # those records throw immediately instead of just being captured. Scope a
  # local 'Continue' override to this call only so az's own error output
  # (e.g. a traceback written to stderr) is captured as data, not thrown.
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $raw = & az @ArgumentList --output json 2>&1
  } finally {
    $ErrorActionPreference = $previousPreference
  }
  if ($LASTEXITCODE -ne 0) { return $null }
  try {
    return ($raw | Out-String) | ConvertFrom-Json -ErrorAction Stop
  } catch {
    return $null
  }
}

# Runs an az CLI command where the output is just for display/logging
# (deletes, purges) rather than JSON to parse. Returns $LASTEXITCODE.
# Scopes the same local 'Continue' override as Invoke-AzJson so az's own
# stderr output does not become an unhandled terminating error under this
# script's $ErrorActionPreference = 'Stop'.
function Invoke-AzCommand {
  param([Parameter(Mandatory = $true)][string[]]$ArgumentList)
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    & az @ArgumentList 2>&1 | ForEach-Object { Write-Host $_ }
  } finally {
    $ErrorActionPreference = $previousPreference
  }
  return $LASTEXITCODE
}

function Write-Summary {
  Write-Section 'Summary'
  $duration = (Get-Date) - $script:startTime
  $failed = @($script:results | Where-Object { -not $_.Pass })
  $passed = @($script:results | Where-Object { $_.Pass })
  $script:results | Format-Table Timestamp, Check, Pass, Detail -AutoSize | Out-String | Write-Host

  Write-Host "Total checks: $($script:results.Count)  Passed: $($passed.Count)  Failed: $($failed.Count)"
  Write-Host "Elapsed: $($duration.ToString('hh\:mm\:ss'))"

  if ($failed.Count -eq 0) {
    Write-Host "`nRESULT: PASS - teardown of '$ResourceGroupName' completed cleanly." -ForegroundColor Green
  } else {
    Write-Host "`nRESULT: FAIL - $($failed.Count) check(s) failed. See details above." -ForegroundColor Red
  }
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

$account = Invoke-AzJson -ArgumentList @('account', 'show')
if (-not $account) {
  Add-Result -Check 'az CLI authenticated' -Pass $false -Detail "Not logged in, or 'az account show' failed (see output above). Run 'az login' (and 'az account set --subscription <id>' if needed) before re-running."
  Write-Summary
  exit 1
}
Add-Result -Check 'az CLI authenticated' -Pass $true -Detail "Subscription: $($account.name) ($($account.id))"

$rg = Invoke-AzJson -ArgumentList @('group', 'show', '--name', $ResourceGroupName)
if (-not $rg) {
  Add-Result -Check 'Resource group exists' -Pass $false -Detail "$ResourceGroupName not found - nothing to tear down (already clean, or wrong name/subscription)."
  Write-Summary
  exit 0
}
Add-Result -Check 'Resource group exists' -Pass $true -Detail "$ResourceGroupName in $($rg.location)"

# ---------------------------------------------------------------------------
# 1. Discover Key Vault name (for purge step) before anything is deleted, if
#    not explicitly supplied and this is a whole-resource-group teardown.
# ---------------------------------------------------------------------------
if (-not $KeyVaultName -and $ResourceIds.Count -eq 0) {
  $vaults = @(Invoke-AzJson -ArgumentList @('resource', 'list', '--resource-group', $ResourceGroupName, '--resource-type', 'Microsoft.KeyVault/vaults'))
  if ($vaults.Count -gt 0 -and $vaults[0]) {
    $KeyVaultName = $vaults[0].name
    Write-Host "Discovered Key Vault '$KeyVaultName' in $ResourceGroupName for the post-teardown purge step."
  }
}

# ---------------------------------------------------------------------------
# 2. Delete - either the whole resource group, or a targeted resource list.
# ---------------------------------------------------------------------------
if ($ResourceIds.Count -gt 0) {
  Write-Section "Targeted resource deletion ($($ResourceIds.Count) resource(s))"

  $confirmMsg = "About to permanently delete $($ResourceIds.Count) resource(s) from '$ResourceGroupName':`n$($ResourceIds -join "`n")`n"
  if (-not (Confirm-Destructive $confirmMsg)) {
    Add-Result -Check 'Targeted deletion confirmed' -Pass $false -Detail 'User did not confirm - aborting, no resources deleted.'
    Write-Summary
    exit 1
  }

  $deleteExit = Invoke-AzCommand -ArgumentList (@('resource', 'delete', '--ids') + $ResourceIds)
  Add-Result -Check 'Targeted resource delete command' -Pass ($deleteExit -eq 0) -Detail "exit code $deleteExit"

  Write-Host 'Polling for deletion to complete (checking each resource ID is gone)...'
  $maxAttempts = 30
  $allGone = $false
  for ($i = 0; $i -lt $maxAttempts; $i++) {
    $stillPresent = @()
    foreach ($id in $ResourceIds) {
      $exists = Invoke-AzJson -ArgumentList @('resource', 'show', '--ids', $id)
      if ($exists) { $stillPresent += $id }
    }
    if ($stillPresent.Count -eq 0) { $allGone = $true; break }
    Start-Sleep -Seconds 10
  }
  Add-Result -Check 'Targeted resources confirmed absent' -Pass $allGone -Detail $(if ($allGone) { 'All listed resource IDs confirmed deleted.' } else { "Timed out after $($maxAttempts * 10)s waiting for deletion - check the portal/az resource show manually." })
} else {
  Write-Section "Resource group deletion: $ResourceGroupName"

  $resourceCount = (@(Invoke-AzJson -ArgumentList @('resource', 'list', '--resource-group', $ResourceGroupName))).Count
  $confirmMsg = "About to permanently delete the ENTIRE resource group '$ResourceGroupName' ($resourceCount resource(s)) in subscription '$($account.name)'.`n"
  if (-not (Confirm-Destructive $confirmMsg)) {
    Add-Result -Check 'Resource group deletion confirmed' -Pass $false -Detail 'User did not confirm - aborting, no resources deleted.'
    Write-Summary
    exit 1
  }

  Write-Host "Deleting resource group '$ResourceGroupName' (--yes, --no-wait so we can poll explicitly below)..."
  $deleteExit = Invoke-AzCommand -ArgumentList @('group', 'delete', '--name', $ResourceGroupName, '--yes', '--no-wait')
  Add-Result -Check 'Resource group delete command accepted' -Pass ($deleteExit -eq 0) -Detail "exit code $deleteExit"

  Write-Host 'Polling for the resource group to become absent (this can take several minutes)...'
  $maxAttempts = 60
  $gone = $false
  for ($i = 0; $i -lt $maxAttempts; $i++) {
    $exists = Invoke-AzJson -ArgumentList @('group', 'show', '--name', $ResourceGroupName)
    if (-not $exists) { $gone = $true; break }
    Start-Sleep -Seconds 15
  }
  Add-Result -Check 'Resource group confirmed absent' -Pass $gone -Detail $(if ($gone) { "Confirmed '$ResourceGroupName' no longer exists." } else { "Timed out after $($maxAttempts * 15)s - deletion may still be in progress; check 'az group show --name $ResourceGroupName' manually before re-deploying to this name." })
}

# ---------------------------------------------------------------------------
# 3. Purge soft-deleted Key Vault (separate, explicit confirmation - this is
#    irreversible and independent of the resource-group/resource delete
#    above, which only soft-deletes the vault per its own retention policy).
# ---------------------------------------------------------------------------
Write-Section 'Key Vault soft-delete purge'

if (-not $KeyVaultName) {
  Add-Result -Check 'Key Vault purge' -Pass $true -Detail 'No Key Vault name supplied or discovered - skipping (nothing to purge, or pass -KeyVaultName explicitly for a targeted teardown).'
} elseif (-not $PurgeKeyVault) {
  Add-Result -Check 'Key Vault purge' -Pass $true -Detail "-PurgeKeyVault not set - '$KeyVaultName' is left soft-deleted and recoverable within its retention window (see modules/key-vault.bicep softDeleteRetentionInDays). Pass -PurgeKeyVault to purge it now, or document an intentional retention-window policy instead."
} else {
  $purgeConfirmMsg = "About to PERMANENTLY PURGE soft-deleted Key Vault '$KeyVaultName' - this cannot be undone and any secrets it held become unrecoverable.`n"
  if (-not (Confirm-Destructive $purgeConfirmMsg)) {
    Add-Result -Check 'Key Vault purge confirmed' -Pass $false -Detail 'User did not confirm - vault left in its soft-deleted, recoverable state.'
  } else {
    $deletedVault = @(Invoke-AzJson -ArgumentList @('keyvault', 'list-deleted', '--query', "[?name=='$KeyVaultName']"))
    if ($deletedVault.Count -eq 0 -or -not $deletedVault[0]) {
      Add-Result -Check 'Key Vault purge' -Pass $false -Detail "'$KeyVaultName' not found in the soft-deleted vaults list yet - the resource-group/resource deletion above may still be propagating. Re-run with -PurgeKeyVault once 'az keyvault list-deleted' shows it."
    } else {
      $purgeExit = Invoke-AzCommand -ArgumentList @('keyvault', 'purge', '--name', $KeyVaultName)
      Add-Result -Check 'Key Vault purge' -Pass ($purgeExit -eq 0) -Detail "az keyvault purge --name $KeyVaultName -> exit code $purgeExit"
    }
  }
}

# ---------------------------------------------------------------------------
# 4. Orphaned role-assignment check (Azure normally cleans these up when the
#    scope resource is deleted, but this is a documented edge case worth
#    confirming rather than assuming).
# ---------------------------------------------------------------------------
Write-Section 'Orphaned role assignment check'

$targetScopes = if ($ResourceIds.Count -gt 0) { $ResourceIds } else { @("/subscriptions/$($account.id)/resourceGroups/$ResourceGroupName") }
$orphaned = @()
foreach ($scope in $targetScopes) {
  $assignments = @(Invoke-AzJson -ArgumentList @('role', 'assignment', 'list', '--scope', $scope))
  if ($assignments.Count -gt 0 -and $assignments[0]) {
    $orphaned += $assignments
  }
}

if ($orphaned.Count -eq 0) {
  Add-Result -Check 'No orphaned role assignments' -Pass $true -Detail 'No role assignments found scoped to the deleted resource(s)/group.'
} else {
  $orphanDescriptions = ($orphaned | ForEach-Object { "$($_.principalId) -> $($_.roleDefinitionName) @ $($_.scope)" }) -join '; '
  Add-Result -Check 'No orphaned role assignments' -Pass $false -Detail "$($orphaned.Count) role assignment(s) still found scoped to the deleted resource(s) - this can happen if the scope resource is gone but the assignment record lags, or if deletion did not fully complete. Review manually: $orphanDescriptions"
}

Write-Summary
exit ([int]($script:results | Where-Object { -not $_.Pass } | Measure-Object).Count -gt 0)
