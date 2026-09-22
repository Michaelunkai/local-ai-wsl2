$ErrorActionPreference = 'Continue'
. "$PSScriptRoot\environment.ps1"

$wsl = Join-Path $env:SystemRoot 'System32\wsl.exe'
$logPath = Join-Path $StackRoot 'logs\wsl-anchor-watchdog.log'

function Write-AnchorLog([string]$message) {
    try {
        "$(Get-Date -Format o) $message" | Add-Content -LiteralPath $logPath -Encoding UTF8
    } catch {}
}

Write-AnchorLog 'Watchdog started.'
while ($true) {
    try {
        $child = Start-Process -FilePath $wsl -ArgumentList @('-d', 'UnrestrictedAi', '-u', 'root', '--', 'sleep', 'infinity') -WorkingDirectory $StackRoot -WindowStyle Hidden -PassThru
        $child.WaitForExit()
        Write-AnchorLog "WSL anchor exited with code $($child.ExitCode); restarting after a short delay."
    } catch {
        Write-AnchorLog "WSL anchor launch failed: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds 5
}
