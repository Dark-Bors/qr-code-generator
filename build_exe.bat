@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo   Building Fetch Production Data (FPD) EXE...
echo ==================================================
echo.

if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found!
    pause
    exit /b 1
)

call venv\Scripts\activate

REM --- Extract Version from version.py ---
set "VERSION="
for /f "tokens=3" %%a in ('findstr "VERSION" version.py') do set VERSION=%%~a
REM Clean up quotes if present
set VERSION=%VERSION:"=%
echo [INFO] Detected Version: %VERSION%

if "%VERSION%"=="" (
    echo [ERROR] Could not detect version from version.py
    pause
    exit /b 1
)

echo.
echo [INFO] Cleaning old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
del /q *.spec

echo.
echo [INFO] Running PyInstaller...
REM --onefile: Single .exe
REM --noconsole: No black window (GUI only)
REM --collect-all customtkinter: Required for CustomTkinter assets
REM --name: Output name with version

pyinstaller --noconsole --onefile --collect-all customtkinter --name "FPD_Tool_v%VERSION%" --icon=NONE main.py

echo.
if exist "dist\FPD_Tool_v%VERSION%.exe" (
    echo [SUCCESS] Build complete!
    echo Your EXE is in the 'dist' folder.
    
    echo.
    echo [INFO] Copying config.example.yaml to dist folder...
    copy config.example.yaml dist\config.example.yaml >nul
    
    echo.
    echo ******************************************************
    echo IMPORTANT: 'config.example.yaml' has been copied to 'dist'.
    echo The App will auto-create 'config.yaml' if missing.
    echo ******************************************************
) else (
    echo [ERROR] Build failed! No EXE found.
)

echo.
pause
