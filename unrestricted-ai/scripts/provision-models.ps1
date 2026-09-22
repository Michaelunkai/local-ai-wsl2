param([string]$Only)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\environment.ps1"
& "$PSScriptRoot\start-ollama.ps1"
$linuxRoot=(& wsl -d UnrestrictedAi -u root -- wslpath -a $StackRoot.Replace('\','/')).Trim()
& wsl -d UnrestrictedAi -u root -- env "HF_HOME=$linuxRoot/hf_cache" TMPDIR=/tmp "PIP_CACHE_DIR=$linuxRoot/pip_cache" python3 "$linuxRoot/scripts/download-models.py" --root $linuxRoot --only $Only
if($LASTEXITCODE -ne 0){throw 'Pinned model download failed'}
& "$PSScriptRoot\import-models.ps1" -Only $Only
& ollama.exe pull nomic-embed-text
if($LASTEXITCODE -ne 0){throw 'Embedding model pull failed'}
