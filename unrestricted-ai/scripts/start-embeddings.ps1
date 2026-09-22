$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
. "$PSScriptRoot\ollama-processes.ps1"
$serviceMutex=New-Object Threading.Mutex($false,'Local\UnrestrictedAiEmbeddingStart')
if(-not $serviceMutex.WaitOne(60000)){throw 'Another embedding startup is still in progress'}
try {
$binary=(Get-Command ollama.exe -ErrorAction Stop).Source
$instancePath="$StackRoot\logs\embedding-instance.json"
if(Test-Path $instancePath) {
 try {
  $instance=Get-Content $instancePath -Raw | ConvertFrom-Json
  $process=Get-Process -Id $instance.pid -ErrorAction Stop
  if($process.Path -eq $binary -and $process.StartTime.ToUniversalTime().Ticks -eq [long]$instance.startTicks) {
   try {
    $null=Invoke-RestMethod 'http://127.0.0.1:11436/api/version' -TimeoutSec 10
    return
   } catch { Stop-ProjectOllama -ProcessId $process.Id -Binary $binary }
  }
 } catch {}
}
$listener=Get-NetTCPConnection -LocalPort 11436 -State Listen -ErrorAction SilentlyContinue
if($listener){throw 'Port 11436 is occupied by a process not owned by this embedding service'}
$override=@{OLLAMA_HOST='127.0.0.1:11436';OLLAMA_CONTEXT_LENGTH='2048';OLLAMA_KEEP_ALIVE='-1';CUDA_VISIBLE_DEVICES='-1';OLLAMA_VULKAN='0';USERPROFILE="$StackRoot\cache\embedding-home"}
$previous=@{}
try {
 foreach($entry in $override.GetEnumerator()) {
  $previous[$entry.Key]=[Environment]::GetEnvironmentVariable($entry.Key,'Process')
  [Environment]::SetEnvironmentVariable($entry.Key,$entry.Value,'Process')
 }
 New-Item -ItemType Directory -Force $env:USERPROFILE | Out-Null
 $p=Start-Process $binary -ArgumentList 'serve' -WorkingDirectory $StackRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$StackRoot\logs\embedding.stdout.log" -RedirectStandardError "$StackRoot\logs\embedding.stderr.log"
 @{pid=$p.Id;startTicks=$p.StartTime.ToUniversalTime().Ticks} | ConvertTo-Json | Set-Content $instancePath
} finally {
 foreach($entry in $previous.GetEnumerator()){[Environment]::SetEnvironmentVariable($entry.Key,$entry.Value,'Process')}
}
for($i=0;$i -lt 30;$i++) {
 try { $null=Invoke-RestMethod 'http://127.0.0.1:11436/api/version' -TimeoutSec 2; return } catch { Start-Sleep 1 }
}
throw 'Embedding server did not become ready'
} finally { $serviceMutex.ReleaseMutex(); $serviceMutex.Dispose() }
