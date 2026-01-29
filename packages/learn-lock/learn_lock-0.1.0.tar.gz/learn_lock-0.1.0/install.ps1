# LearnLock Windows Installer
$ErrorActionPreference = "Stop"

Write-Host "Installing LearnLock..." -ForegroundColor Cyan

# Check Python
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -notmatch "3\.(1[1-9]|[2-9][0-9])") {
        Write-Host "Python 3.11+ required. Found: $pyVersion" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Python not found. Install from python.org" -ForegroundColor Red
    exit 1
}

# Install
pip install --upgrade learnlock

Write-Host "`nLearnLock installed!" -ForegroundColor Green
Write-Host "Run: learnlock" -ForegroundColor Yellow
