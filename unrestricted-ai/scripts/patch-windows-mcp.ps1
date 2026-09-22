$ErrorActionPreference='Stop'
$integrationRoot=Join-Path (Split-Path $PSScriptRoot -Parent) 'integrations'
$servicePath=Join-Path $integrationRoot 'uv-tools\windows-mcp\Lib\site-packages\windows_mcp\desktop\service.py'
$source=[IO.File]::ReadAllText($servicePath)
$repairedMarker='confirm the result before the next action.'
if($source.Contains($repairedMarker)){return}

$startMarker='            case "launch":'
$endMarker='            case "resize":'
$start=$source.IndexOf($startMarker,[StringComparison]::Ordinal)
$end=$source.IndexOf($endMarker,$start,[StringComparison]::Ordinal)
if($start -lt 0 -or $end -le $start){throw 'Windows MCP launch layout changed; review the adapter before starting host tools'}
$original=$source.Substring($start,$end-$start)
if(-not $original.Contains('WindowControl') -or -not $original.Contains('maxSearchSeconds=10')) {
    throw 'Windows MCP launch behavior changed; refusing to patch an unreviewed implementation'
}

$replacement=@'
            case "launch":
                response, status, pid = self.launch_app(name)
                if status != 0:
                    return response
                return (
                    f"{name.title()} launch command sent. Inspect the desktop to "
                    "confirm the result before the next action."
                )
'@
$replacement=$replacement.Replace("`r`n","`n")+"`n"
[IO.File]::WriteAllText(
    $servicePath,
    $source.Substring(0,$start)+$replacement+$source.Substring($end),
    (New-Object Text.UTF8Encoding($false))
)
