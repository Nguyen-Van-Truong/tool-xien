@echo off
chcp 65001 >nul
title ChatGPT Auto Signup

REM Activate venv and run
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python chatgpt_signup_gui.py
    call venv\Scripts\deactivate.bat
) else (
    echo Virtual environment not found! Please run install_and_run.bat first.
    pause
)

