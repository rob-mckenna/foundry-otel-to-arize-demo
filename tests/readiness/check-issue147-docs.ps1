$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$docs = Join-Path $root 'docs\current-state'
$count = 0
foreach ($name in @('fresh-foundation-acceptance.md', 'issue147-cost-estimate.md', 'issue147-workflow-gates.md')) {
    $content = Get-Content (Join-Path $docs $name) -Raw
    foreach ($match in [regex]::Matches($content, '(?s)```powershell\s*\r?\n(.*?)```')) {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseInput(
            $match.Groups[1].Value, [ref]$tokens, [ref]$errors
        ) | Out-Null
        if ($errors.Count) { throw "$name contains invalid PowerShell: $errors" }
        $count++
    }
}
Write-Output "PASS: $count PowerShell documentation examples parse; none executed."

$teamRoot = $root
if ((Split-Path (Split-Path $root) -Leaf) -eq '.worktrees') {
    $teamRoot = Split-Path (Split-Path $root)
}
$cache = Join-Path $teamRoot '.azure-sandbox\issue147-workflow\qa-followup-20261019'
if (Test-Path $cache) {
    foreach ($relative in @(
        'azure-validate\references\scripts\workflow.ps1',
        'azure-validate\references\recipes\scripts\validate-deployment.ps1'
    )) {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile(
            (Join-Path $cache $relative), [ref]$tokens, [ref]$errors
        ) | Out-Null
        if ($errors.Count) { throw "$relative contains invalid PowerShell: $errors" }
    }
    Write-Output 'PASS: 2 pinned official scripts parse; neither executed.'
} else {
    Write-Output 'Optional ignored public cache absent; pinned-script parser check not run.'
}
