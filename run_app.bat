@echo off
echo ==================================================
echo   Starting Fetch Production Data (FPD) App...
echo ==================================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please ensure you have set up the environment first.
    pause
    exit /b 1
)

REM Activate venv and run
call venv\Scripts\activate
python main.py

echo.
echo App closed.
pause
