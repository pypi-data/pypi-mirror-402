# ACS CLI Installer for Windows
# Run with: irm https://raw.githubusercontent.com/Alaa-Taieb/agentic-std/main/install.ps1 | iex

& {
    Write-Host ""
    Write-Host "  Installing Agentic Coding Standard CLI..." -ForegroundColor Cyan
    Write-Host ""

    # Install the package from PyPI
    Write-Host "  Installing package via pip..." -ForegroundColor Gray
    pip install agentic-std
    
    # Verify installation by checking if acs command exists after install
    Start-Sleep -Milliseconds 500
    
    Write-Host "  [OK] Package installed" -ForegroundColor Green

    # Get the Python Scripts directory
    $pythonPath = $null
    try {
        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    } catch { }
    
    if (-not $pythonPath) {
        Write-Host "  [WARN] Could not find Python installation" -ForegroundColor Yellow
        Write-Host ""
        return
    }
    
    $pythonDir = Split-Path $pythonPath
    $scriptsDir = Join-Path $pythonDir "Scripts"

    # Check if it's a user install (different path)
    $userScriptsDirs = Get-ChildItem (Join-Path $env:APPDATA "Python") -Directory -ErrorAction SilentlyContinue
    foreach ($dir in $userScriptsDirs) {
        $testPath = Join-Path $dir.FullName "Scripts\acs.exe"
        if (Test-Path $testPath) {
            $scriptsDir = Join-Path $dir.FullName "Scripts"
            break
        }
    }

    # Check if acs.exe exists
    $acsPath = Join-Path $scriptsDir "acs.exe"
    if (-not (Test-Path $acsPath)) {
        Write-Host "  [WARN] Could not locate acs.exe at $scriptsDir" -ForegroundColor Yellow
        Write-Host "  You may need to add Python Scripts to your PATH manually." -ForegroundColor Yellow
        Write-Host ""
        return
    }

    # Check if Scripts dir is already in PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$scriptsDir*") {
        Write-Host "  Adding $scriptsDir to PATH..." -ForegroundColor Cyan
        
        try {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$scriptsDir", "User")
            Write-Host "  [OK] Added to PATH" -ForegroundColor Green
            Write-Host ""
            Write-Host "  NOTE: Restart your terminal for PATH changes to take effect." -ForegroundColor Yellow
        } catch {
            Write-Host "  [WARN] Could not modify PATH automatically." -ForegroundColor Yellow
            Write-Host "  Please add this to your PATH manually: $scriptsDir" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [OK] Scripts directory already in PATH" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "  Installation complete!" -ForegroundColor Green
    Write-Host "  Run 'acs init' in any project to get started." -ForegroundColor Cyan
    Write-Host ""
}
