param([switch]$FullVerification, [string]$Model='local-qwen:27b-32k')
$ErrorActionPreference = 'Stop'
try {
    $reviewPath=Join-Path $PSScriptRoot 'implementation-review.json'
    if(Test-Path -LiteralPath $reviewPath) {
        $review=Get-Content -Raw -LiteralPath $reviewPath | ConvertFrom-Json
        if($review.status -ne 'complete') {
            throw 'Capability implementation review is still in progress. Startup is held at your request; see CAPABILITIES.md.'
        }
    }
    & "$PSScriptRoot\scripts\start-host-tools.ps1"
    & "$PSScriptRoot\scripts\bootstrap-windows.ps1" -FullVerification:$FullVerification
    $required = @('local-qwen:27b', 'local-dolphin:24b', 'local-qwen:27b-32k', 'local-dolphin:24b-32k', 'nomic-embed-text:latest')
    $installed = (Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 15).models.name
    $missing = @($required | Where-Object { $_ -notin $installed })
    if ($missing.Count) { throw "Required models are missing: $($missing -join ', ')" }
    & "$PSScriptRoot\scripts\prepare-chat.ps1" -Model $Model
    $ready=$false
    for($attempt=1; $attempt -le 5; $attempt++) {
        try {
            $health=Invoke-RestMethod 'http://127.0.0.1:3080/health' -TimeoutSec 15 -ErrorAction Stop
            if(-not $health.status){throw 'Open WebUI reported unhealthy'}
            $ready=$true
            break
        } catch {
            if($attempt -eq 5){throw}
            Start-Sleep -Seconds 2
        }
    }
    if(-not $ready){throw 'Open WebUI is not ready'}
    Start-Process 'http://localhost:3080/' -ErrorAction Stop
} catch {
    Write-Error "Setup did not finish: $($_.Exception.Message)" -ErrorAction Continue
    exit 1
}
