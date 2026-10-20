<#
Runs the unmodified pinned official five-check helper through a metadata-only
transport adapter. No deployment execution, registration, login or account set.
#>
param([Parameter(Mandatory)][string]$ReceiptDirectory)
$ErrorActionPreference = 'Stop'
$worktree = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$teamRoot = (Resolve-Path (Join-Path $worktree '..\..')).Path
$helper = Join-Path $teamRoot '.azure-sandbox\issue147-workflow\qa-followup-20261019\azure-validate\references\recipes\scripts\validate-deployment.ps1'
if ((Get-FileHash $helper -Algorithm SHA256).Hash -ne 'AC49678E5941F2946D8B216370E30DBD8B3451CB15652F8042BB9FAD77BCB9BB') {
    throw 'Pinned official helper hash mismatch'
}
$env:ISSUE147_VALIDATE_ADAPTER = Join-Path $PSScriptRoot 'issue147-validation-adapter.py'
$env:ISSUE147_VALIDATE_RECEIPTS = $ReceiptDirectory
function az {
    & python -B $env:ISSUE147_VALIDATE_ADAPTER --receipts $env:ISSUE147_VALIDATE_RECEIPTS -- @args
    $global:LASTEXITCODE = $LASTEXITCODE
}
& $helper -Scope sub -Location eastus2 `
    -Template (Join-Path $worktree 'infra\issue147-first-allocation.bicep') `
    -Parameters (Join-Path $worktree 'infra\issue147-first-allocation.parameters.json') `
    -Subscription 'c81fda52-936e-4f14-8af4-951c0dbb92d2'
exit $LASTEXITCODE
