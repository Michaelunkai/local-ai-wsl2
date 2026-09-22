param(
 [ValidateSet('start','stop','status','verify','update','repair')][string]$Action='start',
 [ValidateSet('open-webui','workspace-api','searxng','crawl4ai','qdrant','sandbox')][string[]]$Services=@()
)
$ErrorActionPreference='Stop'
. "$PSScriptRoot\scripts\environment.ps1"
if($Action -in @('start','update','verify','repair')) {
 & "$PSScriptRoot\scripts\start-wsl-anchor.ps1"
}
if($Action -in @('start','update','repair')) {
 & "$PSScriptRoot\scripts\start-ollama.ps1"
 & "$PSScriptRoot\scripts\start-embeddings.ps1"
}
$linuxRoot=(& wsl -d UnrestrictedAi -u root -- wslpath -a $PSScriptRoot.Replace('\','/')).Trim()
if($LASTEXITCODE -ne 0 -or -not $linuxRoot){throw 'Unable to resolve project path inside WSL'}
$ip='host-gateway'
if($Action -in @('start','update','repair')) {
 & wsl -d UnrestrictedAi -u root -- bash "$linuxRoot/scripts/install-ollama-relay.sh"
 if($LASTEXITCODE -ne 0){throw 'Unable to start the project Ollama bridge'}
}
& wsl -d UnrestrictedAi -u root -- env "OLLAMA_HOST_IP=$ip" bash "$linuxRoot/run_ai_stack.sh" $Action @Services
if($LASTEXITCODE -ne 0){throw "Stack action '$Action' failed ($LASTEXITCODE). Inspect logs/ and Docker Compose logs."}
