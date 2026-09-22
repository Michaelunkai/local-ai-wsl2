$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
$profilePath=[Environment]::GetFolderPath('UserProfile')
$ollamaPath=Join-Path $profilePath '.ollama'
$target=Join-Path $StackRoot 'cache\original-user-ollama'
if(-not $target.StartsWith("$StackRoot\cache\",[StringComparison]::OrdinalIgnoreCase)){throw 'Invalid Ollama relocation target'}
$existing=Get-Item -LiteralPath $ollamaPath -Force -ErrorAction SilentlyContinue
if($existing -and $existing.LinkType) {
 if(-not ([string]$existing.Target).StartsWith($StackRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Existing Ollama link points outside this project'}
} else {
 if($existing) {
  if(Test-Path -LiteralPath $target){$target+='-'+(Get-Date -Format yyyyMMddHHmmss)}
  Move-Item -LiteralPath $ollamaPath -Destination $target
 } else { New-Item -ItemType Directory -Force $target | Out-Null }
 New-Item -ItemType Junction -Path $ollamaPath -Target $target | Out-Null
}
$configPath=Join-Path $profilePath '.wslconfig'
$targetConfig=Join-Path $StackRoot 'runtime\wslconfig'
$existing=Get-Item -LiteralPath $configPath -Force -ErrorAction SilentlyContinue
if($existing -and $existing.LinkType -and ([string]$existing.Target) -eq $targetConfig){return}
$content=if($existing){Get-Content -LiteralPath $configPath -Raw}else{''}
$swap='swapFile='+($StackRoot+'\runtime\wsl-swap.vhdx').Replace('\','\\')
if($content -match '(?m)^swapFile='){$content=[regex]::Replace($content,'(?m)^swapFile=.*$',[System.Text.RegularExpressions.MatchEvaluator]{param($m) $swap})}
elseif($content -match '(?m)^\[wsl2\]'){$content=$content.Replace('[wsl2]',"[wsl2]`n$swap")}
else{$content+="`n[wsl2]`n$swap`n"}
if($existing){Move-Item -LiteralPath $configPath -Destination (Join-Path $StackRoot ('runtime\wslconfig-before-'+(Get-Date -Format yyyyMMddHHmmss)))}
$content | Set-Content -LiteralPath $targetConfig -Encoding utf8
New-Item -ItemType SymbolicLink -Path $configPath -Target $targetConfig | Out-Null
