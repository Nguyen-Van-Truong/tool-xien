@echo off
echo ========================================
echo V11 Multi-Profile Login Tool
echo ========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Run the tool
echo Starting tool...
python multi_login_tool.py

pause
