@echo off
REM ============================================
REM ChatGPT Checkout Link Converter
REM Chuyển đổi link từ chatgpt.com/checkout sang pay.openai.com
REM ============================================

setlocal enabledelayedexpansion

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     ChatGPT Checkout Link Converter                        ║
echo ║     Chuyển đổi: chatgpt.com/checkout → pay.openai.com     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Kiểm tra xem có argument không
if "%~1"=="" (
    echo ❌ Lỗi: Vui lòng cung cấp link hoặc token
    echo.
    echo 📖 Cách sử dụng:
    echo    1. Dán link: converter.bat "https://chatgpt.com/checkout/openai_llc/cs_live_..."
    echo    2. Hoặc chỉ token: converter.bat "cs_live_..."
    echo.
    echo 💡 Ví dụ:
    echo    converter.bat "https://chatgpt.com/checkout/openai_llc/cs_live_a16oz4K0IOSjCshbxoxqojU3dSa34e9t9v2KBYagzhZT834mEPLscVl9y7"
    echo.
    pause
    exit /b 1
)

set "input=%~1"

REM Loại bỏ dấu ngoặc kép nếu có
set "input=!input:"=!"

echo 📥 Input: !input!
echo.

REM Kiểm tra xem input có phải là URL không
echo !input! | findstr /R "^https://" >nul
if !errorlevel! equ 0 (
    REM Là URL - extract token
    echo 🔍 Đang extract token từ URL...
    
    REM Tìm cs_live_ trong URL
    for /f "tokens=* delims=" %%A in ('powershell -NoProfile -Command "if ('!input!' -match 'cs_live_[a-zA-Z0-9]+') { $matches[0] }"') do (
        set "token=%%A"
    )
    
    if "!token!"=="" (
        echo ❌ Lỗi: Không tìm thấy token cs_live_ trong URL
        echo.
        pause
        exit /b 1
    )
) else (
    REM Không phải URL - coi như token
    echo 🔍 Coi input là token...
    set "token=!input!"
)

REM Kiểm tra token hợp lệ
echo !token! | findstr /R "^cs_live_" >nul
if !errorlevel! neq 0 (
    echo ❌ Lỗi: Token không hợp lệ (phải bắt đầu bằng cs_live_)
    echo.
    pause
    exit /b 1
)

echo ✅ Token: !token!
echo.

REM Tạo pay.openai.com URL
set "pay_base_url=https://pay.openai.com/c/pay/"
set "checkout_suffix=#fidnandhYHdWcXxpYCc%%2FJ2FgY2RwaXEnKSdpamZkaWAnPydgaycpJ3ZwZ3Zmd2x1cWxqa1BrbHRwYGtgdnZAa2RnaWBhJz9jZGl2YCknZHVsTmB8Jz8ndW5aaWxzYFowNE1Kd1ZyRjNtNGt9QmpMNmlRRGJXb1xTd38xYVA2Y1NKZGd8RmZOVzZ1Z0BPYnBGU0RpdEZ9YX1GUHNqV200XVJyV2RmU2xqc1A2bklOc3Vub20yTHRuUjU1bF1Udm9qNmsnKSdjd2poVmB3c2B3Jz9xd3BgKSdnZGZuYW5qcGthRmppancnPycmY2NjY2NjJyknaWR8anBxUXx1YCc%%2FJ3Zsa2JpYFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl"

set "output_url=!pay_base_url!!token!!checkout_suffix!"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    ✅ KẾT QUẢ                              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📤 Output URL:
echo.
echo !output_url!
echo.

REM Copy vào clipboard
echo !output_url! | clip
echo ✅ Đã copy vào clipboard!
echo.

REM Hỏi có muốn mở link không
set /p "open_link=Có muốn mở link trong trình duyệt không? (Y/N): "
if /i "!open_link!"=="Y" (
    echo 🌐 Đang mở link...
    start "" "!output_url!"
)

echo.
pause
