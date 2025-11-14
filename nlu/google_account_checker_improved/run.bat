@echo off
echo ============================================================
echo   GOOGLE ACCOUNT CHECKER - IMPROVED VERSION
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

echo [INFO] Starting checker...
echo.

python checker.py

echo.
echo ============================================================
echo   COMPLETED! Check results folder for output.
echo ============================================================
pause
