@echo off
echo Starting ChatGPT Veterans Verification Tool...
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Run the main.py file
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Program exited with an error.
    pause
)

