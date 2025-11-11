# build.ps1
# Rebuilds FPD & QR generator v3.0.0.exe with PyInstaller

# Stop on errors
$ErrorActionPreference = "Stop"

# Make sure venv is active (optional: remove if you don't use one)
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..."
    . .\venv\Scripts\Activate.ps1
}

# Clean old builds
if (Test-Path "dist")  { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "*.spec") { Remove-Item "*.spec" -Force }

# Run PyInstaller
Write-Host "Building executable..."
pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "FPD & QR generator v3.0.0" `
  --collect-data customtkinter `
  --collect-submodules customtkinter `
  main.py

Write-Host ""
Write-Host "✅ Build complete!"
Write-Host "Find your exe at: dist\FPD & QR generator v3.0.0.exe"
Write-Host "Remember to place config.yaml next to it."
