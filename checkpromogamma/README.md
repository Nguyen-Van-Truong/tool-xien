# Gamma Promo Code Checker

Tool để kiểm tra mã khuyến mãi của Gamma.app sử dụng Stripe API.

## Tổng quan

Đã tạo folder `checkpromogamma` với các file tool tương tự như `checkpromogpt3m` nhưng được adapt cho Gamma/Stripe API.

## Files đã tạo

- `rapid_hunter.py` - Hunter chính với multi-threading
- `simple_checker.py` - Checker đơn giản
- `check_promo_v2.py` - Checker nâng cao với error handling
- `promocode.txt` - 20 mã mẫu format 7 ký tự

## Kết quả Testing

### Từ Browser Testing:
- Mã "RZZKK46F" (được cung cấp) trả về "This code is invalid"
- Điều này cho thấy API có hoạt động nhưng mã không hợp lệ

### Vấn đề gặp phải:
1. **Python đã được cài đặt** ✅ (version 3.11.9)
2. **Chrome driver có sẵn** ✅ (từ thư mục `../nlu/driver/`)
3. **API Authentication** - Có thể cần secret key thay vì publishable key
4. **API Endpoint** - Có thể Gamma sử dụng hệ thống promo riêng

## Các Tool đã tạo

### 1. Python Scripts (dùng command line)
- `rapid_hunter.py` - Hunter đa luồng cho brute force
- `simple_checker.py` - Checker đơn giản
- `check_promo_v2.py` - Checker nâng cao với error handling
- `gamma_promo_tester.py` - **MỚI**: Sử dụng Selenium + Chrome driver

### 2. Browser Testing Tools
- `test_chrome.html` - Test trực tiếp trong Chrome browser
- `test_gamma_api.html` - Test batch codes trong browser

### 3. Helper Scripts
- `run_gamma_test.bat` - Batch file để chạy test
- `test_api_ps.ps1` - PowerShell script để test API

## Cách sử dụng

### Option 1: Browser Testing (Đơn giản nhất)
```bash
# Mở file HTML trong Chrome
start chrome.exe "test_chrome.html"
```
- Click "Test Single Code" để test một code
- Click "Test All Sample Codes" để test tất cả 20 codes

### Option 2: Selenium Testing (Tự động)
```bash
# Chạy với Chrome driver
py gamma_promo_tester.py
```
- Tự động mở Chrome và test từng code
- Lưu kết quả vào file

### Option 3: Command Line Testing
```bash
# Simple checker
py simple_checker.py

# Advanced checker
py check_promo_v2.py

# Rapid hunter
py rapid_hunter.py
```

## Kết luận

Đã tạo đầy đủ toolset cho Gamma promo code testing:

1. **Browser-based testing** - Dễ sử dụng, trực quan
2. **Selenium automation** - Tự động, có thể chạy hàng loạt
3. **API direct testing** - Nhanh, nhưng có thể cần authentication khác

## Khuyến nghị tiếp theo

1. **Test với Browser** - Dùng `test_chrome.html` để xem hoạt động
2. **Kiểm tra API keys** - Có thể cần Stripe secret key thay vì publishable key
3. **Nghiên cứu thêm** về Gamma API qua network inspection trong DevTools
4. **Test với endpoint khác** như checkout session API thay vì promotion_codes

