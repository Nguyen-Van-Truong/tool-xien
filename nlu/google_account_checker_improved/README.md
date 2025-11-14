# Google Account Checker - Improved Version

Tool kiểm tra tài khoản Google Workspace domain nội bộ với tính năng anti-detection và tối ưu hóa hiệu suất.

## Tính năng chính

### 1. Anti-Detection (Tránh bị phát hiện)
- ✅ **Random User Agents**: Xoay vòng user agents để tránh fingerprinting
- ✅ **Random Delays**: Delay ngẫu nhiên giữa các hành động (giống con người)
- ✅ **Stealth Mode**: Ẩn các dấu hiệu automation (webdriver flag)
- ✅ **Human-like Typing**: Gõ từng ký tự với delay ngẫu nhiên
- ✅ **Session Breaks**: Nghỉ giữa các session để tránh detection

### 2. Rate Limiting (Tránh Phone Verification)
- ✅ **Giới hạn số lượng/phút**: Mặc định 12 accounts/phút
- ✅ **Session breaks**: Nghỉ sau mỗi 50 accounts
- ✅ **Cooldown mechanism**: Tự động nghỉ khi phát hiện captcha

### 3. Performance Optimization
- ✅ **Multi-threading**: Chạy song song nhiều threads
- ✅ **Headless mode**: Tùy chọn chạy không hiển thị browser
- ✅ **Disable images**: Tắt load hình ảnh để tăng tốc
- ✅ **Optimized timeouts**: Timeout được tối ưu

### 4. Better Error Handling
- ✅ **Phân loại lỗi chi tiết**: Wrong password, Captcha, Phone verification, Technical error
- ✅ **Retry logic**: Tự động retry khi gặp lỗi
- ✅ **Detailed logging**: Log chi tiết vào file
- ✅ **Auto backup**: Tự động backup kết quả

## Cấu trúc thư mục

```
google_account_checker_improved/
├── checker.py              # File chính để chạy
├── config/
│   └── config.json        # File cấu hình
├── utils/
│   ├── __init__.py
│   ├── browser_manager.py # Quản lý browser
│   ├── account_validator.py # Logic kiểm tra
│   └── logger.py          # Logging system
├── logs/
│   └── checker.log        # Log file
├── results/
│   ├── good_accounts.txt  # Tài khoản tốt
│   ├── failed_accounts.txt # Tài khoản lỗi
│   └── report.txt         # Báo cáo chi tiết
└── README.md
```

## Cài đặt

### 1. Yêu cầu
```bash
pip install selenium
```

### 2. ChromeDriver
Tool sẽ tự động tải ChromeDriver phù hợp với Chrome của bạn (Selenium Manager).

Hoặc bạn có thể đặt chromedriver vào thư mục `../runhere/driver/`

## Sử dụng

### 1. Chuẩn bị file tài khoản

Tạo file `students_accounts.txt` (hoặc copy từ thư mục runhere):
```
email1@domain.com|password1
email2@domain.com|password2
email3@domain.com|password3
```

### 2. Cấu hình (Tùy chọn)

Chỉnh sửa `config/config.json` để tùy chỉnh:

```json
{
  "performance": {
    "threads": 4,          // Số threads (4-8 tốt nhất)
    "headless": false,     // true = không hiện browser (nhanh hơn)
    "disable_images": true // Tắt load ảnh để nhanh hơn
  },

  "anti_detection": {
    "random_delays": true,           // Random delay
    "min_delay_seconds": 1.5,        // Delay tối thiểu
    "max_delay_seconds": 3.5,        // Delay tối đa
    "session_break_after": 50,       // Nghỉ sau bao nhiêu accounts
    "session_break_duration_seconds": 120  // Nghỉ bao lâu (giây)
  },

  "rate_limiting": {
    "enabled": true,              // Bật rate limiting
    "max_accounts_per_minute": 12 // Tối đa accounts/phút
  }
}
```

### 3. Chạy tool

```bash
cd nlu/google_account_checker_improved
python checker.py
```

### 4. Xem kết quả

- **Good accounts**: `results/good_accounts.txt`
- **Failed accounts**: `results/failed_accounts.txt`
- **Report**: `results/report.txt`
- **Logs**: `logs/checker.log`

## Cấu hình tối ưu

### Để tránh Phone Verification:
```json
{
  "performance": {
    "threads": 4  // KHÔNG dùng quá nhiều threads
  },
  "anti_detection": {
    "random_delays": true,
    "min_delay_seconds": 2.0,  // Tăng delay
    "max_delay_seconds": 4.0,
    "session_break_after": 30,  // Nghỉ sớm hơn
    "session_break_duration_seconds": 180  // Nghỉ lâu hơn
  },
  "rate_limiting": {
    "max_accounts_per_minute": 8  // Giảm tốc độ
  }
}
```

### Để chạy nhanh nhất (rủi ro cao hơn):
```json
{
  "performance": {
    "threads": 8,
    "headless": true,  // Chạy ngầm
    "disable_images": true
  },
  "anti_detection": {
    "session_break_after": 100,  // Ít nghỉ hơn
    "session_break_duration_seconds": 60
  },
  "rate_limiting": {
    "max_accounts_per_minute": 20  // Nhanh hơn
  }
}
```

### Cân bằng (Khuyến nghị):
```json
{
  "performance": {
    "threads": 6,
    "headless": false,
    "disable_images": true
  },
  "anti_detection": {
    "random_delays": true,
    "min_delay_seconds": 1.5,
    "max_delay_seconds": 3.0,
    "session_break_after": 50,
    "session_break_duration_seconds": 120
  },
  "rate_limiting": {
    "max_accounts_per_minute": 12
  }
}
```

## Phân loại kết quả

Tool phân loại tài khoản thành các loại:

1. **SUCCESS**: Login thành công ✅
2. **WRONG_PASSWORD**: Sai mật khẩu (mặc định KHÔNG lưu) ❌
3. **CAPTCHA**: Yêu cầu captcha (mặc định LƯU) ⚠️
4. **PHONE_VERIFICATION**: Yêu cầu xác minh số điện thoại (mặc định LƯU) ⚠️
5. **ERROR**: Lỗi kỹ thuật (mặc định LƯU) ⚠️

### Tùy chỉnh lưu/không lưu:
```json
{
  "validation": {
    "save_wrong_password": false,     // Không lưu sai mật khẩu
    "save_technical_errors": true,    // Lưu lỗi kỹ thuật
    "save_captcha_required": true,    // Lưu yêu cầu captcha
    "save_phone_verification": true   // Lưu yêu cầu phone
  }
}
```

## So sánh với phiên bản cũ

| Tính năng | Phiên bản cũ | Improved Version |
|-----------|--------------|------------------|
| Anti-detection | ❌ Không | ✅ Đầy đủ |
| Rate limiting | ❌ Không | ✅ Có |
| Session breaks | ❌ Không | ✅ Có |
| Random delays | ⚠️ Cố định | ✅ Random |
| User agent rotation | ❌ Không | ✅ Có |
| Stealth mode | ❌ Không | ✅ Có |
| Detailed logging | ⚠️ Cơ bản | ✅ Chi tiết |
| Config file | ❌ Không | ✅ Có |
| Error classification | ⚠️ Đơn giản | ✅ Chi tiết |
| Backup | ✅ Có | ✅ Có + tốt hơn |

## Xử lý sự cố

### 1. Bị yêu cầu phone verification nhiều:
- Giảm `max_accounts_per_minute` xuống 6-8
- Tăng `session_break_after` thành 20-30
- Tăng `session_break_duration_seconds` thành 300
- Giảm số `threads` xuống 2-3

### 2. Chạy quá chậm:
- Bật `headless: true`
- Tăng `threads` lên 8-10
- Giảm `min_delay_seconds` và `max_delay_seconds`

### 3. ChromeDriver error:
- Cập nhật Chrome lên phiên bản mới nhất
- Hoặc tải chromedriver tương thích đặt vào `../runhere/driver/`

### 4. Quá nhiều captcha:
- Giảm tốc độ (giống case 1)
- Tắt headless mode
- Nghỉ lâu hơn giữa các session

## Lưu ý quan trọng

⚠️ **QUAN TRỌNG**: Tool này chỉ dành cho:
- Quản trị viên IT kiểm tra tài khoản Google Workspace nội bộ
- Có đầy đủ quyền quản lý domain
- Mục đích quản trị hợp pháp

❌ **KHÔNG sử dụng** để:
- Kiểm tra tài khoản không thuộc quyền quản lý
- Brute force attack
- Unauthorized access

## Tips tăng hiệu quả

1. **Chạy vào giờ thấp điểm**: Google ít strict hơn vào ban đêm
2. **Chia nhỏ batch**: Thay vì 1000 accounts, chia thành 10 batch x 100
3. **Sử dụng proxy**: Nếu có nhiều IP, xoay IP để tránh rate limit
4. **Monitor logs**: Theo dõi logs để điều chỉnh config phù hợp

## Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
1. File log: `logs/checker.log`
2. Config file có đúng format JSON không
3. File input có đúng format `email|password` không
4. ChromeDriver có tương thích với Chrome không

---

**Version**: 1.0.0 Improved
**Last Updated**: 2024
**License**: Internal Use Only
