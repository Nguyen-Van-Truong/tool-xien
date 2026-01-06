@echo off
echo Starting Gamma Promo Code Tester...
cd /d "e:\tool xien\checkpromogamma"

REM Test if Python works
python --version
if %errorlevel% neq 0 (
    echo Python not found. Installing...
    REM Try to install Python if not found
    goto :error
)

REM Install selenium if not installed
python -m pip install selenium --quiet
if %errorlevel% neq 0 (
    echo Failed to install selenium
    goto :error
)

REM Run the tester
echo Running Gamma Promo Code Tester...
python gamma_promo_tester.py

goto :end

:error
echo An error occurred. Please check Python installation.
pause

:end
echo Test completed.
pause



