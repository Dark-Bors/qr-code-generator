@echo off
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

echo [INFO] Cleaning old builds...
rmdir /s /q build dist __pycache__
del /q *.spec

echo [INFO] Running PyInstaller...
REM --onefile: Single .exe
REM --noconsole: No black window (GUI only)
REM --name: Output name
REM --add-data: Include config.example.yaml (we can't include real config safely usually, or we do)
REM Note: config.yaml is usually external for editing. We won't bundle it inside the EXE so it remains editable.
REM We just build the EXE.

pyinstaller --noconsole --onefile --name "FPD_Tool_v6.0.0" --icon=NONE main.py

echo.
echo [SUCCESS] Build complete!
echo Your EXE is in the 'dist' folder.
echo.
echo ******************************************************
echo IMPORTANT: Copy 'config.yaml' to the same folder as the EXE!
echo ******************************************************
echo.
pause
