function Get-StackServiceHealth {
 $result=[ordered]@{}
 $endpoints=[ordered]@{
  'open-webui'='http://127.0.0.1:3080/health'
  'workspace-api'='http://127.0.0.1:8001/health'
  'qdrant'='http://127.0.0.1:6333/readyz'
  'searxng'='http://127.0.0.1:8081/healthz'
  'crawl4ai'='http://127.0.0.1:11235/health'
 }
 foreach($entry in $endpoints.GetEnumerator()) {
  try {
   $null=Invoke-WebRequest $entry.Value -UseBasicParsing -TimeoutSec 5
   $result[$entry.Key]=@{healthy=$true}
  } catch { $result[$entry.Key]=@{healthy=$false;error=$_.Exception.Message} }
 }
 try {
  & wsl -d UnrestrictedAi -u root -- bash /mnt/f/backup/UnrestrictedAi/scripts/check-network.sh 2>$null
  if($LASTEXITCODE -ne 0){throw 'Project container forwarding rules are missing'}
 } catch { $result['workspace-api']=@{healthy=$false;error=$_.Exception.Message} }
 try {
  $stateText=& wsl -d UnrestrictedAi -u root -- docker inspect unrestricted-ai-sandbox-1 --format '{{json .State}}' 2>$null
  if($LASTEXITCODE -ne 0){throw 'Sandbox container missing or Docker unavailable'}
  $state=$stateText | ConvertFrom-Json
  if(-not $state.Running){throw 'Sandbox is stopped'}
  if($state.Health.Status -ne 'healthy'){throw "Sandbox health: $($state.Health.Status)"}
  $result['sandbox']=@{healthy=$true}
 } catch { $result['sandbox']=@{healthy=$false;error=$_.Exception.Message} }
 return $result
}
