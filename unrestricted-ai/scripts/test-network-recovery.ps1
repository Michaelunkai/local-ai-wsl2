$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
$task=Get-ScheduledTask -TaskName 'UnrestrictedAi-Health'
if($task.State -ne 'Running'){throw 'The supervisor must be running for this controlled recovery test'}
$before=(& wsl -d UnrestrictedAi -u root -- docker network inspect unrestricted-ai_default --format '{{.Id}}').Trim()
if($before -notmatch '^[0-9a-f]{64}$'){throw 'Cannot identify the project network'}
$file="$StackRoot\workspace\ui-code-check.txt"
$hash=(Get-FileHash -LiteralPath $file).Hash
$bridge='br-'+$before.Substring(0,12)
& wsl -d UnrestrictedAi -u root -- iptables -C DOCKER-FORWARD -i $bridge -j ACCEPT
if($LASTEXITCODE -ne 0){throw 'Expected project forwarding rule not present'}
$started=Get-Date
& wsl -d UnrestrictedAi -u root -- iptables -D DOCKER-FORWARD -i $bridge -j ACCEPT
if($LASTEXITCODE -ne 0){throw 'Unable to inject the scoped network fault'}
Write-Output "Injected network fault only for $bridge; waiting for the running supervisor"
for($attempt=0;$attempt -lt 40;$attempt++) {
 Start-Sleep 5
 $state=Get-Content "$StackRoot\logs\supervisor-status.json" -Raw | ConvertFrom-Json
 $after=(& wsl -d UnrestrictedAi -u root -- docker network inspect unrestricted-ai_default --format '{{.Id}}' 2>$null) -join ''
 if($after -and $after -ne $before -and $state.healthy -and [datetime]$state.timestamp -gt $started) {
  if((Get-FileHash -LiteralPath $file).Hash -ne $hash){throw 'Persistent workspace changed during recovery'}
  $collections=Invoke-RestMethod 'http://127.0.0.1:6333/collections'
  if('local_workspace' -notin $collections.result.collections.name){throw 'Qdrant collection did not persist'}
  @{passed=$true;timestamp=(Get-Date).ToString('o');seconds=((Get-Date)-$started).TotalSeconds;networkBefore=$before;networkAfter=$after;workspaceHash=$hash;supervisor=$state} | ConvertTo-Json -Depth 9 | Set-Content "$StackRoot\logs\network-recovery-test.json"
  Write-Output 'PASS automatic network recovery and persistent workspace/Qdrant data'
  exit 0
 }
}
throw 'Supervisor did not recover the scoped network fault within the test deadline'
