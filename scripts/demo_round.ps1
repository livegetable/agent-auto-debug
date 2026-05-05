param(
    [ValidateSet("value_error", "zero_division", "attribute_error")]
    [string]$Bug = "value_error",
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [switch]$SkipPreflight
)

$ErrorActionPreference = "Stop"
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

try {
    Write-Step "Reset app.py to bug base: $Bug"
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "reset_bug.ps1") -Bug $Bug

    Write-Step "IMPORTANT: restart service now"
    Write-Host "Stop service terminal with Ctrl+C, then restart:" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\python.exe demo_service\app.py" -ForegroundColor Yellow
    Read-Host "Press Enter after service restart"

    Write-Step "Trigger bug: $Bug"
    Push-Location $projectRoot
    & $PythonExe "scripts/trigger_bug.py" $Bug
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to trigger bug '$Bug'. Exit code: $LASTEXITCODE"
    }
    Pop-Location

    Write-Step "Run agent once"
    Push-Location $projectRoot
    if ($SkipPreflight) {
        & $PythonExe "-m" "agent.main" "--once" "--skip-preflight"
    } else {
        & $PythonExe "-m" "agent.main" "--once"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Agent failed. Exit code: $LASTEXITCODE"
    }
    Pop-Location
}
finally {
    Write-Host ""
    Write-Host "Demo round completed. Current app.py stays as-is." -ForegroundColor Yellow
    Write-Host "If you want to recover normal mode:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\reset_bug.ps1 -Bug normal" -ForegroundColor Yellow
}
