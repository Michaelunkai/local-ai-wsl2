$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
$reviewPath=Join-Path $StackRoot 'implementation-review.json'
if(Test-Path -LiteralPath $reviewPath) {
 $review=Get-Content -Raw -LiteralPath $reviewPath | ConvertFrom-Json
 if($review.status -ne 'complete'){throw 'Host tool restarts are held until the capability implementation review is complete'}
}
function Start-ProjectHostTools {
$folder=Join-Path $StackRoot 'integrations'
$node=(Get-Command node.exe -ErrorAction Stop).Source
$dependencies=(Get-Content -Raw -LiteralPath "$folder\package.json" | ConvertFrom-Json).dependencies
$installRequired=$false
foreach($dependency in $dependencies.PSObject.Properties) {
 $manifest=Join-Path "$folder\node_modules" ($dependency.Name+'/package.json')
 if(-not (Test-Path -LiteralPath $manifest)){$installRequired=$true;break}
 try {$version=(Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json).version}catch{$installRequired=$true;break}
 if($version -ne $dependency.Value){$installRequired=$true;break}
}
if($installRequired) {
 & npm.cmd ci --prefix $folder --cache "$StackRoot\cache\npm"
 if($LASTEXITCODE -ne 0){throw 'Host integration dependency installation failed'}
}
if(-not (Test-Path "$folder\bin\windows-mcp.exe")) {
 $env:UV_CACHE_DIR="$StackRoot\cache\uv"
 $env:UV_PYTHON_INSTALL_DIR="$StackRoot\runtime\python"
 $env:UV_TOOL_DIR="$folder\uv-tools"
 $env:UV_TOOL_BIN_DIR="$folder\bin"
 & uv.exe tool install --python 3.13 'windows-mcp==0.8.5'
 if($LASTEXITCODE -ne 0){throw 'Windows UI integration installation failed'}
}
& "$PSScriptRoot\patch-windows-mcp.ps1"
& "$PSScriptRoot\configure-integration-storage.ps1"
if(-not (Test-Path "$folder\bridge.key")) {
 $bytes=New-Object byte[] 32
 $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
 try {$rng.GetBytes($bytes)} finally {$rng.Dispose()}
 [IO.File]::WriteAllText("$folder\bridge.key",[Convert]::ToBase64String($bytes))
}
$headers=@{Authorization='Bearer '+([IO.File]::ReadAllText("$folder\bridge.key").Trim())}
$revision=(& $node "$folder\integration-revision.mjs" $folder | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $revision -notmatch '^[a-f0-9]{64}$'){throw 'Could not determine the host integration configuration revision'}
$ready=$null
try { $ready=Invoke-RestMethod 'http://127.0.0.1:19381/health' -Headers $headers -TimeoutSec 3 } catch {}
if($ready -and $ready.status -eq 'ok') {
 if($ready.revision -eq $revision){return}
 $owned=Get-CimInstance Win32_Process -Filter "ProcessId=$($ready.pid)"
 if($owned.CommandLine -notlike ('*'+$folder+'\host-bridge.mjs*')){throw 'Unexpected owner of the Windows tools port'}
 Stop-Process -Id $ready.pid -ErrorAction Stop
}
$process=Start-Process -FilePath $node -ArgumentList ('"'+$folder+'\host-bridge.mjs"') -WorkingDirectory $folder -WindowStyle Hidden -PassThru -RedirectStandardOutput "$StackRoot\logs\host-tools.stdout.log" -RedirectStandardError "$StackRoot\logs\host-tools.stderr.log"
for($attempt=0;$attempt -lt 30;$attempt++) {
 if($process.HasExited){throw 'Windows host tools exited; inspect logs/host-tools.stderr.log'}
 try {$ready=Invoke-RestMethod 'http://127.0.0.1:19381/health' -Headers $headers -TimeoutSec 2; if($ready.status -eq 'ok'){return}}catch{}
 Start-Sleep -Seconds 1
}
throw 'Windows host tools did not become ready'
}
$hostToolsMutex=New-Object Threading.Mutex($false,'Local\UnrestrictedAiHostTools')
$acquired=$false
try {
 try {$acquired=$hostToolsMutex.WaitOne(120000)}catch [Threading.AbandonedMutexException]{$acquired=$true}
 if(-not $acquired){throw 'Another host tools startup is still running'}
 Start-ProjectHostTools
} finally {
 if($acquired){$hostToolsMutex.ReleaseMutex()}
 $hostToolsMutex.Dispose()
}
