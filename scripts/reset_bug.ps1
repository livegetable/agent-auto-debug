param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("normal", "value_error", "zero_division", "attribute_error")]
    [string]$Bug
)

$ErrorActionPreference = "Stop"
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$sourceMap = @{
    "normal"          = "demo_service/bug_bases/app_normal.py"
    "value_error"     = "demo_service/bug_bases/app_bug_value_error.py"
    "zero_division"   = "demo_service/bug_bases/app_bug_zero_division.py"
    "attribute_error" = "demo_service/bug_bases/app_bug_attribute_error.py"
}

$sourceRel = $sourceMap[$Bug]
$sourceAbs = Join-Path $projectRoot $sourceRel
$targetAbs = Join-Path $projectRoot "demo_service/app.py"
$logAbs = Join-Path $projectRoot "demo_service/logs/error.log"

if (-not (Test-Path $sourceAbs)) {
    throw "Bug base not found: $sourceAbs"
}

Copy-Item -Path $sourceAbs -Destination $targetAbs -Force
Set-Content -Path $logAbs -Value ""

Write-Host "Reset completed."
Write-Host "bug = $Bug"
Write-Host "source = $sourceRel"
Write-Host "target = demo_service/app.py"
Write-Host "log cleared = demo_service/logs/error.log"
