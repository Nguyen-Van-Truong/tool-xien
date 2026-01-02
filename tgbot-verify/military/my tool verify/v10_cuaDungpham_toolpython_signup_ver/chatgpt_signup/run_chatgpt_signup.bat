@echo off
chcp 65001 >nul
echo ========================================
echo ChatGPT Auto Signup - Python GUI
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Python found!
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created!
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo [INFO] Installing/updating dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed!
echo.

REM Run the application
echo [INFO] Starting ChatGPT Auto Signup GUI...
echo.
python chatgpt_signup_gui.py

REM If error occurred
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error!
    pause
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat
