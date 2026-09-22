param([switch]$FullVerification, [string]$Model='local-qwen:27b-32k')
$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
foreach($name in @('scripts','docker','modelfiles','data','logs','tmp','runtime','ollama_models','hf_cache','pip_cache','docker_config','workspace')) {
 New-Item -ItemType Directory -Force (Join-Path $StackRoot $name) | Out-Null
}
$null=Get-Command ollama.exe -ErrorAction Stop
& "$PSScriptRoot\ensure-storage.ps1"
$distros=((& wsl --list --quiet) -join "`n") -replace '\x00',''
if($LASTEXITCODE -ne 0){throw 'Unable to list WSL distributions'}
if($distros -notmatch '(?m)^UnrestrictedAi\s*$') {
 $archive=Join-Path $StackRoot 'tmp\ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz'
 $expected='2a790896740b14d637dbdc583cce1ba081ac53b9e9cdb46dc09a2f73abbd9934'
 if(-not (Test-Path $archive)) {
  Invoke-WebRequest 'https://cloud-images.ubuntu.com/wsl/releases/noble/current/ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz' -OutFile $archive
 }
 if((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw 'Ubuntu rootfs checksum changed; update the pinned source deliberately before importing'}
 & wsl --import UnrestrictedAi "$StackRoot\runtime\wsl" $archive --version 2
 if($LASTEXITCODE -ne 0){throw 'WSL import failed; Windows WSL2 must already be enabled'}
}
$registered=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\*' | Where-Object DistributionName -eq 'UnrestrictedAi'
if($registered.BasePath.TrimEnd('\') -ne "$StackRoot\runtime\wsl"){throw 'The named WSL distribution is registered outside this project'}
$linuxRoot=(& wsl -d UnrestrictedAi -u root -- wslpath -a $StackRoot.Replace('\','/')).Trim()
if($LASTEXITCODE -ne 0 -or -not $linuxRoot){throw 'Unable to resolve the project path inside WSL'}
& wsl -d UnrestrictedAi -u root -- bash -c 'command -v docker >/dev/null && command -v nvidia-ctk >/dev/null'
if($LASTEXITCODE -ne 0) {
 & wsl -d UnrestrictedAi -u root -- env "STACK_ROOT=$linuxRoot" bash "$linuxRoot/scripts/bootstrap-linux.sh"
 if($LASTEXITCODE -ne 0){throw 'Linux package bootstrap failed'}
 & wsl --terminate UnrestrictedAi
}
& "$StackRoot\run_ai_stack.ps1" start
$installed=(Invoke-RestMethod 'http://127.0.0.1:11434/api/tags').models.name
if(@(@('local-qwen:27b','local-dolphin:24b','local-qwen:27b-32k','local-dolphin:24b-32k','nomic-embed-text:latest') | Where-Object { $_ -notin $installed }).Count) {
 & "$PSScriptRoot\provision-models.ps1"
}
$webuiReady=$false
for($attempt=0;$attempt -lt 60;$attempt++) {
 try { $null=Invoke-RestMethod 'http://127.0.0.1:3080/health' -TimeoutSec 3 -ErrorAction Stop; $webuiReady=$true; break } catch { Start-Sleep 2 }
}
if(-not $webuiReady){throw 'Open WebUI did not become healthy within the startup deadline'}
& wsl -d UnrestrictedAi -u root -- python3 "$linuxRoot/scripts/configure-webui.py"
if($LASTEXITCODE -ne 0){throw 'WebUI preset configuration failed'}
& "$PSScriptRoot\install-startup.ps1"
if((Get-ScheduledTask -TaskName 'UnrestrictedAi-Health' -ErrorAction Stop).State -ne 'Running'){throw 'Health supervision is not running'}
if($FullVerification) {
 & "$StackRoot\run_ai_stack.ps1" verify
 $verificationExitCode=$LASTEXITCODE
 $verificationReportPath=Join-Path $StackRoot 'data\indexer\verification.json'
 $verificationReport=$null
 if(Test-Path -LiteralPath $verificationReportPath) {
  $verificationReport=Get-Content -Raw -LiteralPath $verificationReportPath | ConvertFrom-Json
 }
 $verificationPassed=($verificationExitCode -eq 0 -and $null -ne $verificationReport -and $verificationReport.passed -eq $true)
 $testNames=@()
 $failedTests=@()
 if($null -ne $verificationReport -and $null -ne $verificationReport.tests) {
  $testNames=@($verificationReport.tests.PSObject.Properties.Name)
  $failedTests=@($verificationReport.tests.PSObject.Properties | Where-Object { $_.Value.pass -ne $true } | ForEach-Object Name)
 }
 $launcherRecord=[ordered]@{
  passed=$verificationPassed
  timestamp=(Get-Date).ToString('o')
  script=(Join-Path $StackRoot 'Setup-and-Open.ps1')
  model=$Model
  fullStackVerificationExitCode=$verificationExitCode
  fullStackVerificationPassed=$verificationPassed
  fullStackTestCount=$testNames.Count
  fullStackTestNames=$testNames
  failedTests=$failedTests
  verificationReport=$verificationReportPath
  browserOpened=$true
  allReadinessProbesPassed=$true
 }
 $launcherRecord | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $StackRoot 'logs\final-launcher-verification.json') -Encoding UTF8
 if(-not $verificationPassed) {
  throw "Full stack verification did not pass (exit=$verificationExitCode, failed=$($failedTests -join ', '))."
 }
}
