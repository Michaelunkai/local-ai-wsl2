param([switch]$Restart)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\environment.ps1"
. "$PSScriptRoot\ollama-processes.ps1"
$serviceMutex=New-Object Threading.Mutex($false,'Local\UnrestrictedAiOllamaStart')
if(-not $serviceMutex.WaitOne(60000)){throw 'Another Ollama startup is still in progress'}
try {
$binary = (Get-Command ollama.exe -ErrorAction Stop).Source
Remove-OrphanedProjectRunners -Binary $binary
$owned=$false
$instancePath="$StackRoot\logs\ollama-instance.json"
if(Test-Path $instancePath) {
 try {
  $instance=Get-Content $instancePath -Raw | ConvertFrom-Json
  $process=Get-Process -Id $instance.pid -ErrorAction Stop
  $owned=$process.Path -eq $binary -and $process.StartTime.ToUniversalTime().Ticks -eq [long]$instance.startTicks
 } catch {}
}
if(-not $Restart) {
 try {
  $null=Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 10
  if($owned){return}
 } catch {}
 # Reconcile the existing Ollama installation with this project's environment.
 $Restart=$true
}
if ($Restart) {
 if($owned){Stop-ProjectOllama -ProcessId $process.Id -Binary $binary}
 else {
  $listeners=Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
  foreach($listener in $listeners) {
   $candidate=Get-Process -Id $listener.OwningProcess -ErrorAction Stop
   if($candidate.Path -ne $binary){throw 'Port 11434 belongs to a different application'}
   Stop-ProjectOllama -ProcessId $candidate.Id -Binary $binary
  }
 }
 Start-Sleep -Seconds 2
}
try { $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 3; return } catch {}
$oldProfile = $env:USERPROFILE
try {
 $env:USERPROFILE = "$StackRoot\cache\ollama-home"
 New-Item -ItemType Directory -Force $env:USERPROFILE | Out-Null
 $p = Start-Process $binary -ArgumentList 'serve' -WorkingDirectory $StackRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$StackRoot\logs\ollama.stdout.log" -RedirectStandardError "$StackRoot\logs\ollama.stderr.log"
 $p.Id | Set-Content "$StackRoot\logs\ollama.pid"
 @{pid=$p.Id;startTicks=$p.StartTime.ToUniversalTime().Ticks} | ConvertTo-Json | Set-Content $instancePath
} finally { $env:USERPROFILE = $oldProfile }
for ($i=0; $i -lt 30; $i++) {
 try { $null=Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2; return } catch { Start-Sleep 1 }
}
throw 'Ollama did not become ready; inspect logs/ollama.stderr.log'
} finally { $serviceMutex.ReleaseMutex(); $serviceMutex.Dispose() }
