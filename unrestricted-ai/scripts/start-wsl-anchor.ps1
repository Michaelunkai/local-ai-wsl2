$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"

$taskName='UnrestrictedAi-WSL-Anchor'
$powershell=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$watchdog=Join-Path $PSScriptRoot 'wsl-anchor-watchdog.ps1'
$arguments="-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$watchdog`""
$action=New-ScheduledTaskAction -Execute $powershell -Argument $arguments -WorkingDirectory $StackRoot
$trigger=New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$existing=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
$needsRegistration=-not $existing -or $existing.Actions.Execute -ne $action.Execute -or $existing.Actions.Arguments -ne $action.Arguments -or $existing.Actions.WorkingDirectory -ne $action.WorkingDirectory
if($needsRegistration) {
 Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Keep the dedicated UnrestrictedAi WSL2 VM active while local AI services are available.' -Force -ErrorAction Stop | Out-Null
}
$task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
if($task.State -eq 'Disabled' -or -not $task.Settings.Enabled) {
 Enable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
}
if((Get-ScheduledTask -TaskName $taskName -ErrorAction Stop).State -ne 'Running') {
 Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
}
$deadline=(Get-Date).AddSeconds(45)
do {
 $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
 if($task.State -eq 'Running'){return}
 Start-Sleep -Milliseconds 500
} while((Get-Date) -lt $deadline)
$info=Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction Stop
throw "WSL anchor did not start (state=$($task.State), result=$($info.LastTaskResult))."
