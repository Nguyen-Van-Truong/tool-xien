# Quick Start Guide

## 5 Bước nhanh để bắt đầu

### 1️⃣ Cài đặt Selenium
```bash
pip install selenium
```

### 2️⃣ Chuẩn bị file tài khoản
Copy file `students_accounts.txt` từ thư mục `runhere` vào đây, hoặc tạo mới:
```
email1@domain.com|password1
email2@domain.com|password2
```

### 3️⃣ (Tùy chọn) Chỉnh config
Mở `config/config.json` và chỉnh:
- `threads`: Số threads (4-6 là tốt)
- `headless`: `true` để chạy ngầm (nhanh hơn)
- `max_accounts_per_minute`: Tốc độ kiểm tra

### 4️⃣ Chạy
**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

Hoặc chạy trực tiếp:
```bash
python checker.py
```

### 5️⃣ Xem kết quả
- ✅ Tài khoản tốt: `results/good_accounts.txt`
- 📊 Báo cáo: `results/report.txt`
- 📝 Logs: `logs/checker.log`

---

## Config nhanh cho các tình huống

### 🐌 An toàn, tránh phone verification (KHUYẾN NGHỊ)
```json
{
  "performance": {"threads": 4, "headless": false},
  "anti_detection": {"session_break_after": 30, "session_break_duration_seconds": 180},
  "rate_limiting": {"max_accounts_per_minute": 8}
}
```

### ⚡ Nhanh nhất (rủi ro cao)
```json
{
  "performance": {"threads": 8, "headless": true},
  "anti_detection": {"session_break_after": 100, "session_break_duration_seconds": 60},
  "rate_limiting": {"max_accounts_per_minute": 20}
}
```

### ⚖️ Cân bằng
```json
{
  "performance": {"threads": 6, "headless": false},
  "anti_detection": {"session_break_after": 50, "session_break_duration_seconds": 120},
  "rate_limiting": {"max_accounts_per_minute": 12}
}
```

---

## Xử lý nhanh sự cố

| Vấn đề | Giải pháp |
|--------|-----------|
| Bị yêu cầu phone verification | Giảm `max_accounts_per_minute` xuống 6, tăng `session_break_duration` lên 300 |
| ChromeDriver error | Cập nhật Chrome, hoặc đặt chromedriver vào `../runhere/driver/` |
| Quá chậm | Bật `headless: true`, tăng `threads` lên 8 |
| Quá nhiều captcha | Giảm tốc độ, nghỉ lâu hơn |

---

**Đọc full hướng dẫn tại README.md**
