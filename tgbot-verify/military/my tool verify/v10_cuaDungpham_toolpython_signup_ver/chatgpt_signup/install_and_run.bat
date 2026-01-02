@echo off
chcp 65001 >nul
echo ========================================
echo ChatGPT Auto Signup - Setup and Run
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/
    echo.
    echo After installing Python:
    echo 1. Make sure to check "Add Python to PATH" during installation
    echo 2. Restart this script
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Python found!
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        echo Make sure you have permissions to create folders in this directory.
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

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --quiet --upgrade pip
echo.

REM Install dependencies
echo [INFO] Installing dependencies...
echo This may take a few minutes on first run...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo.
    echo Troubleshooting:
    echo 1. Make sure you have internet connection
    echo 2. Try running as Administrator
    echo 3. Check if antivirus is blocking pip
    echo.
    pause
    exit /b 1
)
echo.
echo [SUCCESS] All dependencies installed!
echo.

REM Show installed packages
echo [INFO] Installed packages:
pip list | findstr /i "selenium requests PyQt6 undetected"
echo.

REM Run the application
echo ========================================
echo Starting ChatGPT Auto Signup GUI...
echo ========================================
echo.
python chatgpt_signup_gui.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error!
    echo Check the error messages above for details.
    echo.
    pause
) else (
    echo.
    echo [INFO] Application closed successfully.
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat
