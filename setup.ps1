# XClipboard Backend Setup Script for Windows PowerShell
# Installs all necessary dependencies for the project

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "XClipboard Backend Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementsFile = Join-Path $scriptDir "requirements.txt"

if (-not (Test-Path $requirementsFile)) {
    Write-Host "ERROR: requirements.txt not found at $requirementsFile" -ForegroundColor Red
    exit 1
}

Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host ""

try {
    & python -m pip install -r $requirementsFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "✓ All dependencies installed successfully!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run the backend with:" -ForegroundColor Cyan
        Write-Host "  python back/ClipBackend.py" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "ERROR: Installation failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
