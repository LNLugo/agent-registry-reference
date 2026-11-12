<#
.SYNOPSIS
  Set up the environment, run all tests and produce the governance report.

.EXAMPLE
  ./scripts/run.ps1
  ./scripts/run.ps1 -AsOf 2026-11-10
#>
param(
    [string]$AsOf = "2026-11-10"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment" -ForegroundColor Cyan
    python -m venv .venv
}
$py = Join-Path ".venv" "Scripts\python.exe"
if (-not (Test-Path $py)) { $py = Join-Path ".venv" "bin/python" }

& $py -m pip install --quiet --upgrade pip
& $py -m pip install --quiet -e ".[dev]"

Write-Host "`nPython tests" -ForegroundColor Cyan
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

Write-Host "`nExport registry data for the gateway policy" -ForegroundColor Cyan
& $py -m agent_registry.cli export-opa

$opa = Get-Command opa -ErrorAction SilentlyContinue
if (-not $opa -and (Test-Path ".\opa.exe")) { $opa = ".\opa.exe" }
if ($opa) {
    Write-Host "`nPolicy tests" -ForegroundColor Cyan
    & $opa test policy/ -v
    if ($LASTEXITCODE -ne 0) { throw "opa test failed" }
} else {
    Write-Host "`nopa not found, skipping policy tests. Install with: winget install open-policy-agent.opa" -ForegroundColor Yellow
}

Write-Host "`nExport registry data for the Agent Catalog" -ForegroundColor Cyan
& $py -m agent_registry.cli export-catalog --as-of $AsOf

Write-Host "`nGovernance report as of $AsOf" -ForegroundColor Cyan
& $py -m agent_registry.cli report --as-of $AsOf
Write-Host "(exit code 1 above means critical findings exist, which is expected with the sample data)"
Get-Content "reports/governance-report-$AsOf.md" | Select-Object -First 25
