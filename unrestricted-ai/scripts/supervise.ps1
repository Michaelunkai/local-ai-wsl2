param([switch]$Once)
$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
. "$PSScriptRoot\check-health.ps1"
$mutex=New-Object Threading.Mutex($false,'Local\UnrestrictedAiSupervisor')
if(-not $mutex.WaitOne(0)){exit 0}
try {
 do {
  $record=@{timestamp=(Get-Date).ToString('o');healthy=$false}
  try {
   & "$PSScriptRoot\start-ollama.ps1"
   & "$PSScriptRoot\start-embeddings.ps1"
   & "$PSScriptRoot\start-host-tools.ps1"
   $record.hostTools='ready'
   & wsl -d UnrestrictedAi -u root -- bash /mnt/f/backup/UnrestrictedAi/scripts/repair-network.sh *> "$StackRoot\logs\network-reconcile.log"
   if($LASTEXITCODE -ne 0){$record.networkReconciliation='Deferred until service repair'}
   $services=Get-StackServiceHealth
   $failed=@($services.Keys | Where-Object { -not $services[$_].healthy })
   if($failed.Count) {
    & "$StackRoot\run_ai_stack.ps1" repair -Services $failed *> "$StackRoot\logs\supervisor-repair.log"
    $record.repairedServices=$failed
    for($attempt=0;$attempt -lt 10;$attempt++) {
     Start-Sleep 3
     $services=Get-StackServiceHealth
     $failed=@($services.Keys | Where-Object { -not $services[$_].healthy })
     if(-not $failed.Count){break}
    }
   }
   $record.services=$services
   $record.healthy=$failed.Count -eq 0
   if($services['workspace-api'].healthy) {
    $workspace=Invoke-RestMethod 'http://127.0.0.1:8001/health' -TimeoutSec 5
    $record.index=$workspace.index
   }
   $models=(Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5).models.name
   $record.missingModels=@(@('local-qwen:27b','local-dolphin:24b') | Where-Object { $_ -notin $models })
   $record.fullyReady=$record.healthy -and $record.missingModels.Count -eq 0 -and $record.index.error -eq $null
  } catch {
   $record.error=$_.Exception.Message
  }
  $record | ConvertTo-Json -Depth 8 | Set-Content "$StackRoot\logs\supervisor-status.json"
  if(-not $Once){Start-Sleep 60}
 } while(-not $Once)
} finally { $mutex.ReleaseMutex(); $mutex.Dispose() }
