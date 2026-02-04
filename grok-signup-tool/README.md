# Grok Account Signup Automation Tool

Tự động đăng ký tài khoản Grok (https://accounts.x.ai) sử dụng Python + Playwright.

## ✨ Tính năng

- ✅ Tự động bypass Cloudflare Turnstile challenge
- ✅ Generate email tạm để nhận mã verification (sử dụng tinyhost.shop)
- ✅ Tự động điền form và submit thông tin
- ✅ Đọc email và lấy mã verification
- ✅ Batch processing - xử lý nhiều tài khoản
- ✅ **GUI đồ họa đẹp, dễ dùng** (Tkinter)
- ✅ Logging chi tiết với màu sắc
- ✅ Lưu kết quả vào file

## 📋 Yêu cầu

- Python 3.8+
- Windows/Linux/Mac

## 🚀 Cài đặt

### 1. Clone/Download project

```bash
cd e:\tool xien\grok-signup-tool
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cài đặt Playwright browsers

```bash
playwright install chromium
```

## 📖 Cách sử dụng

### 🎨 GUI Version (Khuyến nghị)

Chạy giao diện đồ họa:

```bash
python gui.py
```

**Hướng dẫn sử dụng GUI:**

1. **Nhập accounts** vào ô text bên trái:
   - Gõ trực tiếp: `email|password|first_name|last_name`
   - Hoặc click "📂 Load File" để load từ file
   - Hoặc click "🎲 Generate Random" để tạo ngẫu nhiên

2. **Click "▶️ START"** để bắt đầu

3. **Theo dõi progress**:
   - Statistics panel hiển thị Total/Success/Failed
   - Progress bar hiển thị tiến trình
   - Activity Log hiển thị chi tiết từng bước

4. **Click "⏹️ STOP"** nếu muốn dừng

**Screenshot UI:**
- Panel trái: Input accounts + control buttons
- Panel phải: Statistics + Activity log
- Footer: Status bar

---

### 💻 CLI Version (Command Line)

1. Tạo file `input/accounts.txt` với format:

```
email|password
hoặc
email|password|first_name|last_name
```

Ví dụ:
```
user1@gmail.com|MyPassword123
user2@gmail.com|SecurePass456|John|Doe
```

2. Chạy tool:

```bash
python main.py
```

3. Chọn option `1` khi được hỏi

### Mode 2: Auto-generate

1. Chạy tool:

```bash
python main.py
```

2. Chọn option `2` và nhập số lượng accounts muốn tạo

## 📁 Cấu trúc file

```
grok-signup-tool/
├── main.py                 # Entry point
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── utils/
│   ├── email_service.py   # Email generation & retrieval
│   ├── browser_handler.py # Playwright automation
│   └── logger.py         # Logging utilities
├── input/
│   └── accounts.txt      # Input accounts (format: email|password)
└── output/
    ├── success.txt       # Successful signups
    ├── failed.txt        # Failed signups
    └── logs/            # Detailed logs & screenshots
```

## ⚙️ Cấu hình

Chỉnh sửa `config.py` để thay đổi:

- `BROWSER_HEADLESS`: Chạy browser ẩn (True/False)
- `BROWSER_SLOW_MO`: Tốc độ automation (ms)
- `DELAY_BETWEEN_ACCOUNTS`: Delay giữa các account (giây)
- `EMAIL_CHECK_MAX_RETRIES`: Số lần thử đọc email
- Và nhiều settings khác...

## 📊 Output Format

### success.txt
```
email|password|temp_email|verification_code|timestamp
```

### failed.txt
```
email|error_message|timestamp
```

## 🔧 Troubleshooting

### Cloudflare challenge không pass

- Tắt headless mode: `BROWSER_HEADLESS = False` trong config.py
- Tăng `BROWSER_SLOW_MO` để chậm hơn
- Kiểm tra internet connection

### Không nhận được mã verification

- ⚠️ **Quan trọng**: Hiện tại phần đọc email chưa được implement đầy đủ
- Cần implement API của service email bạn sử dụng trong `utils/email_service.py`
- Xem hàm `check_email_for_code()` để thêm logic đọc email

### Browser không khởi động

```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

## ⚠️ Lưu ý

1. **Email Service**: Tool hiện tại sử dụng tinyhost.shop để lấy domain ngẫu nhiên, nhưng **chưa implement API đọc email**. Bạn cần:
   - Implement API của mail.gddp2018.edu.vn trong `utils/email_service.py`
   - Hoặc sử dụng service khác như temp-mail.org, guerrillamail.com

2. **Rate Limiting**: Để tránh bị detect:
   - Không chạy quá nhiều accounts cùng lúc
   - Tăng `DELAY_BETWEEN_ACCOUNTS` nếu cần

3. **Headless Mode**: Nên test với `BROWSER_HEADLESS = False` trước, sau khi ổn định mới bật True

## 🐛 Debug

- Logs được lưu tại: `output/logs/grok_signup_*.log`
- Screenshots lỗi: `output/logs/failed_*.png`
- Console output có màu sắc để dễ theo dõi

## 📝 License

MIT License - Sử dụng tự do cho mục đích cá nhân và thương mại.

## 👨‍💻 Support

Nếu gặp vấn đề, check:
1. Log files
2. Screenshots
3. Console output

---

**Made with ❤️ for automation**
