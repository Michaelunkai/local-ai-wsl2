function Remove-OrphanedProjectRunners {
 param([string]$Binary)
 $modelPattern=[regex]::Escape("$StackRoot\ollama_models\")
 $runnerBinary=Join-Path (Split-Path $Binary) 'lib\ollama\llama-server.exe'
 foreach($runner in (Get-CimInstance Win32_Process -Filter "name='llama-server.exe'")) {
  if($runner.ExecutablePath -ne $runnerBinary -or $runner.CommandLine -notmatch $modelPattern){continue}
  $parent=Get-Process -Id $runner.ParentProcessId -ErrorAction SilentlyContinue
  if(-not $parent -or $parent.Path -ne $Binary -or $parent.StartTime -gt $runner.CreationDate) {
   Stop-Process -Id $runner.ProcessId -ErrorAction Stop
   Write-Output "Removed orphaned project model runner $($runner.ProcessId)"
  }
 }
}
function Stop-ProjectOllama {
 param([int]$ProcessId,[string]$Binary)
 $parent=Get-Process -Id $ProcessId -ErrorAction Stop
 if($parent.Path -ne $Binary){throw 'Ollama process identity changed'}
 $children=@(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId AND name='llama-server.exe'" | Where-Object { $_.CommandLine -match [regex]::Escape("$StackRoot\ollama_models\") })
 Stop-Process -Id $ProcessId -ErrorAction Stop
 foreach($child in $children){Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue}
}
