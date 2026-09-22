$StackRoot = Split-Path $PSScriptRoot -Parent
$values = @{
 OLLAMA_MODELS = "$StackRoot\ollama_models"
 DOCKER_CONFIG = "$StackRoot\docker_config"
 HF_HOME = "$StackRoot\hf_cache"
 TMPDIR = "$StackRoot\tmp"
 TEMP = "$StackRoot\tmp"
 TMP = "$StackRoot\tmp"
 PIP_CACHE_DIR = "$StackRoot\pip_cache"
 OLLAMA_HOST = '0.0.0.0:11434'
 OLLAMA_ORIGINS = '*'
 OLLAMA_FLASH_ATTENTION = '1'
 OLLAMA_KV_CACHE_TYPE = 'q8_0'
 OLLAMA_KEEP_ALIVE = '-1'
 OLLAMA_MAX_LOADED_MODELS = '1'
 OLLAMA_NUM_PARALLEL = '1'
 OLLAMA_CONTEXT_LENGTH = '8192'
}
foreach ($entry in $values.GetEnumerator()) { [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, 'Process') }
