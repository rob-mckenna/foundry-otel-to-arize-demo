$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\invoke-health-command.ps1"

$result = Invoke-HealthCommand -Operation Test -Command {
    python -c "print('synthetic safe count=3')"
}
if ($result -ne 'synthetic safe count=3') { throw 'Success output was not retained' }

$message = ''
try {
    Invoke-HealthCommand -Operation ReadTopology -Command {
        python -c "import sys; print('synthetic-private-body'); sys.stderr.write('ERROR: (AuthorizationFailed) HTTP 403 synthetic-secret-never-print\n'); sys.exit(7)"
    }
    throw 'Expected process failure'
} catch { $message = $_.Exception.Message }
if ($message -notmatch 'operation=ReadTopology exit=7' -or
    $message -notmatch 'codes=AuthorizationFailed status=403' -or
    $message -match 'synthetic-private|synthetic-secret') {
    throw 'Failure diagnostics were missing or leaked raw text'
}

$message = ''
try {
    Invoke-HealthCommand -Operation Test -Command { python -c "print('x'*70000)" }
    throw 'Expected bounded-output failure'
} catch { $message = $_.Exception.Message }
if ($message -notmatch 'reason=OutputLimitExceeded') { throw 'Output bound was not enforced' }

$continued = $false
try {
    Invoke-HealthCommand -Operation Test -Command { python -c "raise SystemExit(9)" }
    $continued = $true
} catch {
    if ($_.Exception.Message -notmatch 'exit=9') { throw 'Exit status was not retained' }
}
if ($continued) { throw 'Failed process did not stop sequence' }

$message = ''
try {
    Invoke-HealthCommand -Operation ReadReferences -Command {
        python -c "import sys; sys.stderr.write('synthetic-unknown-private-error\n'); sys.exit(4)"
    }
    throw 'Expected unknown process failure'
} catch { $message = $_.Exception.Message }
if ($message -notmatch 'exit=4 reason=ProcessFailed codes=Unclassified status=Unavailable' -or
    $message -match 'synthetic-unknown') { throw 'Unknown failure was not safely classified' }

$message = ''
try {
    Invoke-HealthCommand -Operation Test -Command { & 'synthetic-command-that-does-not-exist-153' }
    throw 'Expected invocation failure'
} catch { $message = $_.Exception.Message }
if ($message -notmatch 'operation=Test exit=Unavailable' -or
    $message -match 'synthetic-command-that') { throw 'Invocation failure leaked or used stale exit status' }
'PASS: success, redacted diagnostics, output bound, fail-stop, unknown and invocation failures'
