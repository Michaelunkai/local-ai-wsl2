# Keep tool-owned state on F: without changing the Windows user's identity/home.
$ErrorActionPreference='Stop'
$integrationRoot=Join-Path (Split-Path $PSScriptRoot -Parent) 'integrations'
$configPath=Join-Path $integrationRoot 'node_modules\@wonderwhy-er\desktop-commander\dist\config.js'
$original="const CONFIG_DIR = path.join(USER_HOME, '.claude-server-commander');"
$replacement="const CONFIG_DIR = process.env.DESKTOP_COMMANDER_CONFIG_DIR || path.join(USER_HOME, '.claude-server-commander');"
$source=[IO.File]::ReadAllText($configPath)
if($source.Contains($original)) {
    # Pinned 0.2.51 has no config-directory option; retain its ordinary default
    # and add only a project-scoped override. Reapplied after npm ci if needed.
    [IO.File]::WriteAllText($configPath,$source.Replace($original,$replacement),(New-Object Text.UTF8Encoding($false)))
} elseif(-not $source.Contains($replacement)) {
    throw 'Desktop Commander config layout changed; review the storage adapter before starting it'
}
