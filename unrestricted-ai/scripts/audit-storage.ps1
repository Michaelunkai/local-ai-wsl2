$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
$registered=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\*' | Where-Object DistributionName -eq 'UnrestrictedAi'
if($registered.BasePath.TrimEnd('\') -ne "$StackRoot\runtime\wsl"){throw 'WSL disk is not stored inside the project'}
$ids=& wsl -d UnrestrictedAi -u root -- docker ps -aq --filter label=com.docker.compose.project=unrestricted-ai
if($LASTEXITCODE -ne 0 -or -not $ids){throw 'Project containers not found'}
$containers=(& wsl -d UnrestrictedAi -u root -- docker inspect @ids | ConvertFrom-Json)
$linuxRoot=(& wsl -d UnrestrictedAi -u root -- wslpath -a $StackRoot.Replace('\','/')).Trim()
$dockerRoot=(& wsl -d UnrestrictedAi -u root -- docker info --format '{{.DockerRootDir}}').Trim()
$inventory=@()
foreach($container in $containers) {
 foreach($mount in $container.Mounts) {
  if($mount.Type -eq 'bind' -and -not $mount.Source.StartsWith($linuxRoot+'/') -and $mount.Source -ne $linuxRoot){throw "Unexpected bind mount: $($mount.Source)"}
  if($mount.Type -eq 'volume' -and -not $mount.Source.StartsWith($dockerRoot+'/volumes/')){throw 'Unexpected Docker volume location'}
 }
 $inventory+=@{name=$container.Name;running=$container.State.Running;image=$container.Image;mounts=@($container.Mounts | Select-Object Type,Source,Destination,RW);readonlyRoot=$container.HostConfig.ReadonlyRootfs}
}
$inventory | ConvertTo-Json -Depth 7 | Set-Content "$StackRoot\logs\storage-inventory.json"
$links=@('.ollama','.wslconfig') | ForEach-Object {Get-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('UserProfile')) $_) -Force | Select-Object FullName,LinkType,Target}
foreach($link in $links){if(-not $link.LinkType -or -not ([string]$link.Target).StartsWith($StackRoot)){throw "Storage redirect missing: $($link.FullName)"}}
@{timestamp=(Get-Date).ToString('o');passed=$true;wslBasePath=$registered.BasePath;dockerRoot=$dockerRoot;redirects=$links;containers=$inventory.Count} | ConvertTo-Json -Depth 5 | Set-Content "$StackRoot\logs\storage-audit.json"
Write-Output 'Storage audit passed: project mounts, runtime disk and Windows redirects are on F:'
