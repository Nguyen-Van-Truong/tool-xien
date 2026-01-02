# V11 Multi-Profile Login Tool

Tool Python tự động đăng ký/đăng nhập ChatGPT với đa profile browser.

## Tính năng

- ✅ Multi-profile: Mỗi account có browser riêng với profile độc lập
- ✅ Không đóng browser: Browser giữ nguyên sau khi hoàn thành
- ✅ Log riêng biệt: Mỗi session có log file riêng
- ✅ Anti-bot: Sử dụng undetected-chromedriver
- ✅ GUI đẹp: Dark theme với PyQt6
- ✅ Tham số tùy chỉnh: Max browsers, timeout, browser path...

## Cài đặt

Double-click `install_and_run.bat` hoặc chạy thủ công:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python multi_login_tool.py
```

## Sử dụng

1. **Load File**: Click "📂 Load File" và chọn file accounts
2. **Settings**: Điều chỉnh số browser tối đa, browser path nếu cần
3. **Start**: Click "▶ START" để bắt đầu
4. **Monitor**: Theo dõi tiến độ trong bảng Accounts và Log
5. **Save**: Click "💾 Save Results" để lưu kết quả

## Format file accounts

```
email|password|emailLogin|passEmail|refreshToken|clientId
```

Hoặc format ngắn (4 fields):
```
email|password|refreshToken|clientId
```

## Cấu hình

Chỉnh sửa `config.py` để thay đổi các tham số:

- `MAX_CONCURRENT_BROWSERS`: Số browser tối đa (mặc định: 3)
- `KEEP_BROWSER_OPEN`: Giữ browser mở (mặc định: True)
- `ELEMENT_TIMEOUT`: Timeout tìm element (mặc định: 10s)
- `OTP_TIMEOUT`: Timeout chờ OTP (mặc định: 60s)

## Thư mục

- `logs/`: Chứa log files
- `profiles/`: Chứa Chrome profiles (tạm thời)
- `success_*.txt`: Accounts đăng ký thành công
- `exists_*.txt`: Accounts đã tồn tại
- `failed_*.txt`: Accounts thất bại

## Yêu cầu

- Python 3.8+
- Chrome/Brave/Edge browser
- Windows OS
