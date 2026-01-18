# 🔗 Payment Link Converter

Công cụ chuyển đổi link thanh toán từ `chatgpt.com/checkout` sang `pay.openai.com`.

## 📋 Mô tả

Module này chứa logic chuyển đổi link thanh toán ChatGPT sang định dạng pay.openai.com. Hỗ trợ nhiều môi trường:
- **JavaScript** - Dùng trong browser hoặc Node.js
- **PowerShell** - Dùng trên Windows
- **Batch** - Dùng trên Windows CMD

## 🎯 Tính năng

✅ Chuyển đổi URL checkout sang pay URL  
✅ Hỗ trợ cả URL đầy đủ hoặc chỉ token  
✅ Validate token hợp lệ  
✅ Export cho cả browser và Node.js  
✅ Tự động copy vào clipboard (PowerShell/Batch)  
✅ Tùy chọn mở link trong trình duyệt

---

## 🚀 Cách sử dụng

### 1️⃣ JavaScript (Browser)

```html
<!DOCTYPE html>
<html>
<head>
    <script src="converter.js"></script>
</head>
<body>
    <script>
        // Sử dụng từ URL
        const result1 = PaymentLinkConverter.convertCheckoutLink(
            'https://chatgpt.com/checkout/openai_llc/cs_live_abc123...'
        );
        console.log(result1.url); // https://pay.openai.com/c/pay/cs_live_abc123...

        // Sử dụng từ token
        const result2 = PaymentLinkConverter.convertCheckoutLink('cs_live_abc123...');
        console.log(result2.url);
    </script>
</body>
</html>
```

**Demo page:** Mở file `demo.html` trong trình duyệt để test trực tiếp.

### 2️⃣ JavaScript (Node.js)

```javascript
const { convertCheckoutLink } = require('./converter.js');

// Chuyển đổi
const result = convertCheckoutLink('cs_live_abc123...');

if (result.success) {
    console.log('Token:', result.token);
    console.log('Pay URL:', result.url);
} else {
    console.error('Lỗi:', result.error);
}
```

### 3️⃣ PowerShell

```powershell
# Từ URL đầy đủ
.\converter.ps1 "https://chatgpt.com/checkout/openai_llc/cs_live_abc123..."

# Từ token
.\converter.ps1 "cs_live_abc123..."

# Từ clipboard
.\converter.ps1 (Get-Clipboard)
```

### 4️⃣ Batch (CMD)

```cmd
REM Từ URL đầy đủ
converter.bat "https://chatgpt.com/checkout/openai_llc/cs_live_abc123..."

REM Từ token
converter.bat "cs_live_abc123..."
```

---

## 📚 API Documentation

### JavaScript Functions

#### `convertCheckoutLink(input)`
Hàm chính để chuyển đổi link.

**Parameters:**
- `input` (string): URL checkout hoặc token

**Returns:**
```javascript
{
    success: true,
    url: "https://pay.openai.com/c/pay/cs_live_...",
    token: "cs_live_..."
}
// hoặc
{
    success: false,
    error: "Mô tả lỗi"
}
```

#### `extractToken(input)`
Extract token từ URL hoặc string.

**Parameters:**
- `input` (string): URL hoặc token

**Returns:**
- `string|null` - Token hoặc null nếu không tìm thấy

#### `validateToken(token)`
Kiểm tra token có hợp lệ không.

**Parameters:**
- `token` (string): Token cần validate

**Returns:**
- `boolean` - true nếu token hợp lệ

#### `convertTokenToPayURL(token)`
Chuyển token thành pay URL.

**Parameters:**
- `token` (string): Token cs_live_xxx

**Returns:**
- `string` - URL pay.openai.com đầy đủ

**Throws:**
- `Error` - Nếu token không hợp lệ

---

## 📝 Ví dụ

### Input
```
https://chatgpt.com/checkout/openai_llc/cs_live_a16oz4K0IOSjCshbxoxqojU3dSa34e9t9v2KBYagzhZT834mEPLscVl9y7
```

### Output
```
https://pay.openai.com/c/pay/cs_live_a16oz4K0IOSjCshbxoxqojU3dSa34e9t9v2KBYagzhZT834mEPLscVl9y7#fidnandhYHdWcXxpYCc%2FJ2FgY2RwaXEnKSdpamZkaWAnPydgaycpJ3ZwZ3Zmd2x1cWxqa1BrbHRwYGtgdnZAa2RnaWBhJz9jZGl2YCknZHVsTmB8Jz8ndW5aaWxzYFowNE1Kd1ZyRjNtNGt9QmpMNmlRRGJXb1xTd38xYVA2Y1NKZGd8RmZOVzZ1Z0BPYnBGU0RpdEZ9YX1GUHNqV200XVJyV2RmU2xqc1A2bklOc3Vub20yTHRuUjU1bF1Udm9qNmsnKSdjd2poVmB3c2B3Jz9xd3BgKSdnZGZuYW5qcGthRmppancnPycmY2NjY2NjJyknaWR8anBxUXx1YCc%2FJ3Zsa2JpYFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl
```

---

## 🔧 Logic chuyển đổi

### Quy trình:

1. **Extract token** từ input:
   - Nếu là URL: tìm pattern `cs_live_[a-zA-Z0-9]+`
   - Nếu là token: sử dụng trực tiếp

2. **Validate token**:
   - Token phải match pattern: `^cs_live_[a-zA-Z0-9]+$`

3. **Tạo Pay URL**:
   ```
   Base URL: https://pay.openai.com/c/pay/
   Format: {base_url}{token}{suffix}
   ```

### Constants:

```javascript
PAY_BASE_URL = 'https://pay.openai.com/c/pay/'
CHECKOUT_SUFFIX = '#fidnandhYHdWcXxpYCc%2FJ2FgY2RwaXEnKSdpamZkaWAnPydgaycpJ3ZwZ3Zmd2x1cWxqa1BrbHRwYGtgdnZAa2RnaWBhJz9jZGl2YCknZHVsTmB8Jz8ndW5aaWxzYFowNE1Kd1ZyRjNtNGt9QmpMNmlRRGJXb1xTd38xYVA2Y1NKZGd8RmZOVzZ1Z0BPYnBGU0RpdEZ9YX1GUHNqV200XVJyV2RmU2xqc1A2bklOc3Vub20yTHRuUjU1bF1Udm9qNmsnKSdjd2poVmB3c2B3Jz9xd3BgKSdnZGZuYW5qcGthRmppancnPycmY2NjY2NjJyknaWR8anBxUXx1YCc%2FJ3Zsa2JpYFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl'
```

---

## 🔐 Bảo mật

⚠️ **Cảnh báo quan trọng:**

- Token `cs_live_` là thông tin nhạy cảm
- KHÔNG chia sẻ token công khai
- KHÔNG commit token vào Git
- KHÔNG gửi token qua email
- Chỉ sử dụng trong môi trường riêng tư

---

## 🐛 Troubleshooting

### PowerShell: "cannot be loaded because running scripts is disabled"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Token không hợp lệ
- Kiểm tra token bắt đầu bằng `cs_live_`
- Không có khoảng trắng thừa
- Sử dụng dấu ngoặc kép khi truyền vào script

### JavaScript: Module not found
- Đảm bảo đường dẫn đến `converter.js` đúng
- Kiểm tra file có tồn tại trong thư mục

---

## 📊 So sánh các phiên bản

| Tính năng | JavaScript | PowerShell | Batch |
|-----------|-----------|-----------|-------|
| Môi trường | Browser/Node.js | Windows PowerShell | Windows CMD |
| Regex support | ✅ Tốt | ✅ Tốt | ⚠️ Cơ bản |
| Copy clipboard | ❌ Cần code thêm | ✅ Tự động | ✅ Tự động |
| Mở browser | ❌ Cần code thêm | ✅ Có | ✅ Có |
| Dễ tích hợp | ✅✅ Rất dễ | ⚠️ Trung bình | ⚠️ Trung bình |
| Cross-platform | ✅ Có | ❌ Chỉ Windows | ❌ Chỉ Windows |

**Khuyến nghị:**
- **Web/App**: Dùng JavaScript
- **Windows Terminal**: Dùng PowerShell
- **Windows CMD**: Dùng Batch

---

## 📂 Cấu trúc thư mục

```
payment-link-converter/
├── converter.js       # JavaScript module
├── converter.ps1      # PowerShell script
├── converter.bat      # Batch script
├── demo.html          # Demo page
└── README.md          # Tài liệu này
```

---

## 🔄 Tích hợp vào project

### Vào Chrome Extension
```javascript
// content.js
const { convertCheckoutLink } = require('./payment-link-converter/converter.js');

// Sử dụng
const result = convertCheckoutLink(checkoutUrl);
if (result.success) {
    window.location.href = result.url;
}
```

### Vào Node.js Backend
```javascript
const express = require('express');
const { convertCheckoutLink } = require('./payment-link-converter/converter.js');

app.post('/convert', (req, res) => {
    const result = convertCheckoutLink(req.body.url);
    res.json(result);
});
```

### Vào React App
```javascript
import { convertCheckoutLink } from './payment-link-converter/converter.js';

function CheckoutConverter() {
    const handleConvert = (input) => {
        const result = convertCheckoutLink(input);
        if (result.success) {
            window.location.href = result.url;
        }
    };
    
    return <button onClick={() => handleConvert(url)}>Convert</button>;
}
```

---

## 📄 License

Miễn phí sử dụng cho mục đích cá nhân và thương mại.

---

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra token hợp lệ
2. Đọc phần Troubleshooting
3. Kiểm tra console/terminal để xem lỗi chi tiết

---

**Created by:** ExtensionGetLinkStripe Team  
**Last Updated:** 2025-12-27
