param([string]$Model='local-qwen:27b-32k', [switch]$VerifyOnly)
$ErrorActionPreference='Stop'
. "$PSScriptRoot\environment.ps1"
$sources=Get-Content -LiteralPath "$StackRoot\models.lock.json" -Raw | ConvertFrom-Json
$verified=@()
foreach($source in $sources) {
    foreach($alias in @($source.alias, ($source.alias+'-32k'))) {
        $show=Invoke-RestMethod 'http://127.0.0.1:11434/api/show' -Method Post -ContentType 'application/json' -Body (@{model=$alias} | ConvertTo-Json) -TimeoutSec 30
        foreach($file in $source.files.PSObject.Properties) {
            if($show.modelfile -notmatch [regex]::Escape($file.Value)) {
                throw "Model provenance mismatch for $alias ($($file.Name)); refusing to substitute an unverified model"
            }
        }
        $verified+=@{model=$alias;repository=$source.repository;revision=$source.revision;verified=$true}
    }
}
@{timestamp=(Get-Date).ToString('o');models=$verified} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$StackRoot\logs\model-provenance.json"
if($VerifyOnly){return}
if($Model -notin $verified.model){throw 'Select a verified Qwen or Dolphin preset'}
Write-Host "Preparing $Model for your first message. A cold model load can take a few minutes."
$request=@{model=$Model;messages=@(@{role='user';content='Reply with READY.'});stream=$false;keep_alive=-1;options=@{num_predict=8;temperature=0}}
if($Model -like 'local-qwen:*'){$request.think=$false}
$timer=[Diagnostics.Stopwatch]::StartNew()
$reply=Invoke-RestMethod 'http://127.0.0.1:11434/api/chat' -Method Post -ContentType 'application/json' -Body ($request | ConvertTo-Json -Depth 6) -TimeoutSec 900
if(-not $reply.done -or [string]::IsNullOrWhiteSpace($reply.message.content)){throw 'Model warmup did not produce a complete text response'}
@{timestamp=(Get-Date).ToString('o');model=$Model;seconds=$timer.Elapsed.TotalSeconds;answer=$reply.message.content;passed=$true} | ConvertTo-Json | Set-Content -LiteralPath "$StackRoot\logs\chat-readiness.json"
Write-Host 'Model ready. Opening your browser.'
