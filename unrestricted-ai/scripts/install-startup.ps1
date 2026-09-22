$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
$binary=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action=New-ScheduledTaskAction -Execute $binary -Argument "-NoProfile -WindowStyle Hidden -File `"$PSScriptRoot\supervise.ps1`"" -WorkingDirectory $StackRoot
$trigger=New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$existing=Get-ScheduledTask -TaskName 'UnrestrictedAi-Health' -ErrorAction SilentlyContinue
if(-not $existing -or $existing.Actions.Execute -ne $action.Execute -or $existing.Actions.Arguments -ne $action.Arguments) {
 Register-ScheduledTask -TaskName 'UnrestrictedAi-Health' -Action $action -Trigger $trigger -Settings $settings -Description 'Launch and supervise the F: local AI infrastructure; does not delete data or change model weights.' -Force -ErrorAction Stop | Out-Null
}
$task=Get-ScheduledTask -TaskName 'UnrestrictedAi-Health' -ErrorAction Stop
# An explicit setup run resumes supervision after a previous intentional stop.
if($task.State -eq 'Disabled' -or -not $task.Settings.Enabled) {
 Enable-ScheduledTask -TaskName 'UnrestrictedAi-Health' -ErrorAction Stop | Out-Null
}
if((Get-ScheduledTask -TaskName 'UnrestrictedAi-Health' -ErrorAction Stop).State -ne 'Running') {
 Start-ScheduledTask -TaskName 'UnrestrictedAi-Health' -ErrorAction Stop
}
$deadline=(Get-Date).AddSeconds(30)
do {
 $task=Get-ScheduledTask -TaskName 'UnrestrictedAi-Health' -ErrorAction Stop
 if($task.State -eq 'Running'){return}
 Start-Sleep -Milliseconds 500
} while((Get-Date) -lt $deadline)
$info=Get-ScheduledTaskInfo -TaskName 'UnrestrictedAi-Health' -ErrorAction Stop
throw "Health supervision did not start (state=$($task.State), result=$($info.LastTaskResult))."
