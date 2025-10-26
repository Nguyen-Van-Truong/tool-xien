@echo off
echo 🚀 SANTA FE COLLEGE TEST RUNNER
echo ================================
echo.

cd /d "E:\tool xien\tool no card"

echo 📂 Current directory: %CD%
echo 🐍 Running Python test...
echo.

"C:\Users\truong\AppData\Local\Programs\Python\Python312\python.exe" sf_auto_test.py

echo.
echo ✨ Test completed!
echo 📸 Check for screenshot files in current directory
echo.
pause 