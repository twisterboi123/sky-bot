$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyVenv = Join-Path $root ".venv\Scripts\python.exe"
$bot = Join-Path $root "bot.py"

if (Test-Path $pyVenv) {
    & $pyVenv $bot
} else {
    Write-Host "Virtual env not found; using system Python" -ForegroundColor Yellow
    & python $bot
}
