function Invoke-HealthCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('ReadReferences', 'BuildPackage', 'PublishPackage', 'PauseTriggers',
            'SetGuard', 'CreateHealth', 'ReadTopology', 'SetHealth', 'RemoveLegacyKey',
            'RestoreOutbox', 'ResumeIncoming', 'QueryCounts', 'Compile', 'Test', 'Diff')]
        [string]$Operation,
        [Parameter(Mandatory)][scriptblock]$Command,
        [switch]$DiscardOutput
    )

    # One native process per block. Never surface its arguments or raw failure text.
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $PSNativeCommandUseErrorActionPreference = $false
    $previousExitCode = $global:LASTEXITCODE
    $global:LASTEXITCODE = $null
    $output = [System.Text.StringBuilder]::new()
    $codes = [System.Collections.Generic.HashSet[string]]::new()
    $statuses = [System.Collections.Generic.HashSet[string]]::new()
    $overflow = $false
    $failedToInvoke = $false
    $codePattern = '\b(AuthorizationFailed|Forbidden|RequestDisallowedByPolicy|InvalidTemplateDeployment|DeploymentFailed|ResourceNotFound|BadRequest|InvalidAuthenticationTokenTenant|AuthenticationFailed|ConnectionError|KeyVaultAccessForbidden|NotFound|InvalidParameterValue|TooManyRequests|ServiceUnavailable|BCP[0-9]{3})\b'
    try {
        . $Command 2>&1 | ForEach-Object {
            $line = [string]$_
            $bounded = $line.Substring(0, [Math]::Min(4096, $line.Length))
            foreach ($match in [regex]::Matches($bounded, $codePattern)) {
                if ($codes.Count -lt 4) { [void]$codes.Add($match.Value) }
            }
            foreach ($match in [regex]::Matches($bounded, '\b(400|401|403|404|409|429|500|502|503|504)\b')) {
                if ($statuses.Count -lt 4) { [void]$statuses.Add($match.Value) }
            }
            if (-not $DiscardOutput -and $_ -isnot [System.Management.Automation.ErrorRecord]) {
                if ($output.Length + $line.Length + 2 -le 65536) {
                    [void]$output.AppendLine($line)
                } else {
                    $overflow = $true
                }
            }
        }
        $exitCode = $global:LASTEXITCODE
    } catch {
        $failedToInvoke = $true
        $exitCode = $null
    } finally {
        $ErrorActionPreference = $previousPreference
        $global:LASTEXITCODE = $previousExitCode
    }
    if ($failedToInvoke -or $null -eq $exitCode -or $exitCode -ne 0 -or $overflow) {
        $exitLabel = if ($null -eq $exitCode) { 'Unavailable' } else { [string][int]$exitCode }
        $reason = if ($overflow) { 'OutputLimitExceeded' } elseif ($failedToInvoke) { 'InvocationFailed' } else { 'ProcessFailed' }
        $codeLabel = if ($codes.Count) { (@($codes | Sort-Object) -join ',') } else { 'Unclassified' }
        $statusLabel = if ($statuses.Count) { (@($statuses | Sort-Object) -join ',') } else { 'Unavailable' }
        throw "operation=$Operation exit=$exitLabel reason=$reason codes=$codeLabel status=$statusLabel"
    }
    if (-not $DiscardOutput) { $output.ToString().TrimEnd() }
}
