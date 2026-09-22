param([string]$Only)
$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
$models=Get-Content "$StackRoot\models.lock.json" -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force "$env:OLLAMA_MODELS\blobs" | Out-Null
foreach($model in $models) {
 if($Only -and $model.directory -ne $Only){continue}
 $files=@{}
 foreach($entry in $model.files.PSObject.Properties) {
  $source=Join-Path "$StackRoot\data\model-sources\$($model.directory)" $entry.Name
  if(-not (Test-Path -LiteralPath $source)){throw "Model source not yet available: $source"}
  $actual=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
  if($actual -ne $entry.Value){throw "Checksum mismatch for $($entry.Name)"}
  $blob=Join-Path "$env:OLLAMA_MODELS\blobs" "sha256-$actual"
  if(-not (Test-Path -LiteralPath $blob)) {
   New-Item -ItemType HardLink -Path $blob -Target $source | Out-Null
  }
  $files[$entry.Name]="sha256:$actual"
 }
 $context=8192
 if(Test-Path "$StackRoot\tuning.json") {
  $tuning=Get-Content "$StackRoot\tuning.json" -Raw | ConvertFrom-Json
  if($tuning.models.$($model.alias).num_ctx){$context=$tuning.models.$($model.alias).num_ctx}
 }
 $body=@{
  model=$model.alias; files=$files; stream=$false
  parameters=@{temperature=0.7;top_p=0.9;repeat_penalty=1.1;num_ctx=$context;num_thread=8}
 } | ConvertTo-Json -Depth 8
 $result=Invoke-RestMethod 'http://127.0.0.1:11434/api/create' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 1800
 if($result.status -ne 'success'){throw "Model import did not succeed: $($model.alias)"}
 $extended=@{model="$($model.alias)-32k";from=$model.alias;parameters=@{num_ctx=32768};stream=$false} | ConvertTo-Json -Depth 5
 $null=Invoke-RestMethod 'http://127.0.0.1:11434/api/create' -Method Post -ContentType 'application/json' -Body $extended -TimeoutSec 180
 & ollama.exe show $model.alias --modelfile | Set-Content "$StackRoot\modelfiles\$($model.directory).Modelfile"
 if($LASTEXITCODE -ne 0){throw 'Could not export Modelfile'}
 Write-Output "Verified and imported $($model.alias)"
}
