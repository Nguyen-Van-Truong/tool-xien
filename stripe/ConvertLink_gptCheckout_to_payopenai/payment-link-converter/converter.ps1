# ============================================
# ChatGPT Checkout Link Converter (PowerShell)
# Chuyển đổi link từ chatgpt.com/checkout sang pay.openai.com
# ============================================

param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Kết hợp tất cả arguments thành 1 string
$input = $Arguments -join " "

# Hàm hiển thị header
function Show-Header {
    Clear-Host
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     ChatGPT Checkout Link Converter                        ║" -ForegroundColor Cyan
    Write-Host "║     Chuyển đổi: chatgpt.com/checkout → pay.openai.com     ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# Hàm hiển thị lỗi
function Show-Error {
    param([string]$message)
    Write-Host "❌ Lỗi: $message" -ForegroundColor Red
}

# Hàm hiển thị thành công
function Show-Success {
    param([string]$message)
    Write-Host "✅ $message" -ForegroundColor Green
}

# Hàm hiển thị info
function Show-Info {
    param([string]$message)
    Write-Host "ℹ️  $message" -ForegroundColor Cyan
}

# Hàm hiển thị warning
function Show-Warning {
    param([string]$message)
    Write-Host "⚠️  $message" -ForegroundColor Yellow
}

Show-Header

# Kiểm tra input
if ([string]::IsNullOrWhiteSpace($input)) {
    Show-Error "Vui lòng cung cấp link hoặc token"
    Write-Host ""
    Write-Host "📖 Cách sử dụng:" -ForegroundColor Yellow
    Write-Host "   1. Dán link: .\converter.ps1 `"https://chatgpt.com/checkout/openai_llc/cs_live_...`""
    Write-Host "   2. Hoặc chỉ token: .\converter.ps1 `"cs_live_...`""
    Write-Host ""
    Write-Host "💡 Ví dụ:" -ForegroundColor Yellow
    Write-Host "   .\converter.ps1 `"https://chatgpt.com/checkout/openai_llc/cs_live_a16oz4K0IOSjCshbxoxqojU3dSa34e9t9v2KBYagzhZT834mEPLscVl9y7`""
    Write-Host ""
    Read-Host "Nhấn Enter để thoát"
    exit 1
}

Write-Host "📥 Input: $input" -ForegroundColor Gray
Write-Host ""

# Extract token
$token = $null

if ($input -match "https://") {
    # Là URL - extract token
    Show-Info "Đang extract token từ URL..."
    
    if ($input -match "cs_live_[a-zA-Z0-9]+") {
        $token = $matches[0]
    }
    
    if ([string]::IsNullOrWhiteSpace($token)) {
        Show-Error "Không tìm thấy token cs_live_ trong URL"
        Write-Host ""
        Read-Host "Nhấn Enter để thoát"
        exit 1
    }
} else {
    # Không phải URL - coi như token
    Show-Info "Coi input là token..."
    $token = $input.Trim()
}

# Kiểm tra token hợp lệ
if ($token -notmatch "^cs_live_[a-zA-Z0-9]+$") {
    Show-Error "Token không hợp lệ (phải bắt đầu bằng cs_live_)"
    Write-Host ""
    Read-Host "Nhấn Enter để thoát"
    exit 1
}

Show-Success "Token: $token"
Write-Host ""

# Tạo pay.openai.com URL
$pay_base_url = "https://pay.openai.com/c/pay/"
$checkout_suffix = "#fidnandhYHdWcXxpYCc%2FJ2FgY2RwaXEnKSdpamZkaWAnPydgaycpJ3ZwZ3Zmd2x1cWxqa1BrbHRwYGtgdnZAa2RnaWBhJz9jZGl2YCknZHVsTmB8Jz8ndW5aaWxzYFowNE1Kd1ZyRjNtNGt9QmpMNmlRRGJXb1xTd38xYVA2Y1NKZGd8RmZOVzZ1Z0BPYnBGU0RpdEZ9YX1GUHNqV200XVJyV2RmU2xqc1A2bklOc3Vub20yTHRuUjU1bF1Udm9qNmsnKSdjd2poVmB3c2B3Jz9xd3BgKSdnZGZuYW5qcGthRmppancnPycmY2NjY2NjJyknaWR8anBxUXx1YCc%2FJ3Zsa2JpYFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl"

$output_url = "$pay_base_url$token$checkout_suffix"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ KẾT QUẢ                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📤 Output URL:" -ForegroundColor Yellow
Write-Host ""
Write-Host $output_url -ForegroundColor Cyan
Write-Host ""

# Copy vào clipboard
$output_url | Set-Clipboard
Show-Success "Đã copy vào clipboard!"
Write-Host ""

# Hỏi có muốn mở link không
$open_link = Read-Host "Có muốn mở link trong trình duyệt không? (Y/N)"
if ($open_link -eq "Y" -or $open_link -eq "y") {
    Write-Host "🌐 Đang mở link..." -ForegroundColor Cyan
    Start-Process $output_url
}

Write-Host ""
Read-Host "Nhấn Enter để thoát"
