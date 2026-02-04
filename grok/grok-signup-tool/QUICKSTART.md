# 🚀 Quick Start Guide - Grok Signup Tool

## Bước 1: Cài đặt (1 lần duy nhất)

```bash
cd e:\tool xien\grok-signup-tool
pip install -r requirements.txt
playwright install chromium
```

## Bước 2: Chạy tool

```bash
python gui.py
```

## Bước 3: Sử dụng

### Cách 1: Generate Random
1. Click nút "🎲 Generate Random"
2. Nhập số lượng accounts (ví dụ: 5)
3. Click "▶️ START"

### Cách 2: Nhập thủ công
1. Gõ vào ô text, mỗi dòng 1 account:
   ```
   user1@gmail.com|Password123
   user2@gmail.com|SecurePass456|John|Doe
   ```
2. Click "▶️ START"

### Cách 3: Load từ file
1. Tạo file .txt với format như trên
2. Click "📂 Load File"
3. Chọn file
4. Click "▶️ START"

## Kết quả

- File thành công: `output/success.txt`
- File thất bại: `output/failed.txt`
- Logs chi tiết: `output/logs/`

## Lưu ý

⚠️ **Email verification**: Hiện tại phần đọc email chưa hoàn thiện. Tool sẽ fail ở bước lấy mã verification. Cần implement API đọc email trong `utils/email_service.py`

## Screenshots

GUI có 2 panel:

**Left Panel:**
- Text area để nhập accounts
- Buttons: Load File, Generate, Clear, Start, Stop

**Right Panel:**
- Statistics: Total / Success / Failed
- Progress bar
- Activity log (màu xanh lá trên nền đen)
