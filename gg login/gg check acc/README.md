# GPM Google Login Automation

Script tự động đăng nhập Google sử dụng Puppeteer với Stealth Plugin.

## Cài đặt

```bash
npm install
```

## Cấu hình

Chỉnh sửa file `accounts.json`:

```json
{
  "accounts": [
    {
      "email": "your-email@gmail.com",
      "password": "your-password"
    }
  ]
}
```

## Chạy Script

```bash
npm start
```

hoặc

```bash
node google_login.js
```

## Tính năng

- ✅ Sử dụng Stealth Plugin để tránh bị phát hiện là bot
- ✅ Gõ phím ngẫu nhiên giống người thật
- ✅ Lưu cookies để đăng nhập nhanh lần sau
- ✅ Screenshot tự động khi gặp lỗi
- ✅ Hỗ trợ xử lý thủ công khi gặp CAPTCHA/2FA

## Lưu ý

⚠️ **Quan trọng:**
- Google có cơ chế chống bot mạnh
- Nếu gặp CAPTCHA hoặc 2FA, script sẽ giữ browser mở 60s để bạn xử lý thủ công
- Không nên chạy automation quá nhiều lần liên tiếp
- Sử dụng tài khoản test có bảo mật thấp để thử nghiệm
