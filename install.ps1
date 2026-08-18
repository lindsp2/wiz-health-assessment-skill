# Wiz Health Assessment Installer (PowerShell)
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "     WIZ HEALTH ASSESSMENT & SKILLS INSTALLER          " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

$pythonCmd = "python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $pythonCmd = "py"
    } else {
        Write-Host "[!] Python is required but was not found in PATH." -ForegroundColor Red
        Write-Host "    Please install Python 3.9+ from https://python.org and ensure it is in PATH."
        Exit 1
    }
}

Write-Host "[*] Checking Python dependencies..." -ForegroundColor Yellow
& $pythonCmd -m pip install -r requirements.txt --quiet

Write-Host "[*] Running skills installer..." -ForegroundColor Yellow
& $pythonCmd scripts/install_skills.py
