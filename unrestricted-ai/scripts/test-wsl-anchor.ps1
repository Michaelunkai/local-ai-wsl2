$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"

& "$PSScriptRoot\start-wsl-anchor.ps1"
$task=Get-ScheduledTask -TaskName 'UnrestrictedAi-WSL-Anchor' -ErrorAction Stop
if($task.State -ne 'Running'){throw "WSL anchor state is $($task.State)"}

& wsl.exe -d UnrestrictedAi -u root -- true
if($LASTEXITCODE -ne 0){throw 'A normal WSL command failed while the anchor was active'}
Start-Sleep -Seconds 20

$task=Get-ScheduledTask -TaskName 'UnrestrictedAi-WSL-Anchor' -ErrorAction Stop
$distro=((wsl.exe -l -v) -join "`n") -replace '\x00',''
if($task.State -ne 'Running'){throw "WSL anchor stopped unexpectedly: $($task.State)"}
if($distro -notmatch '(?m)^\*?\s*UnrestrictedAi\s+Running\s+2\s*$'){throw 'UnrestrictedAi did not remain running'}

@{
 passed=$true
 timestamp=(Get-Date).ToString('o')
 taskState=$task.State.ToString()
 distroRunning=$true
} | ConvertTo-Json -Depth 4 | Set-Content "$StackRoot\logs\wsl-anchor-test.json"
Write-Output 'PASS scheduled WSL anchor remained running after client exit'
