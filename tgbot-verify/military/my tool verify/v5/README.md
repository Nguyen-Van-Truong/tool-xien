# Military Auto Verify V2 - Chrome Extension

## Features
- 📂 **Import Veterans**: Load từ file .txt (format: FirstName|LastName|Branch|...)
- 🤖 **Auto-Fill Form**: Tự động điền form SheerID
- 🔄 **Auto-Retry**: Tự động thử veteran tiếp theo khi Not Approved
- ⚠️ **VPN Error Detection**: Dừng và thông báo khi cần đổi VPN

## Installation

1. Mở Chrome → `chrome://extensions/`
2. Bật **Developer mode** (góc phải trên)
3. Click **Load unpacked**
4. Chọn folder `v5`

## Usage

### Step 1: Import Veterans
1. Click icon extension
2. Click **Import** → Chọn file .txt
3. File format:
   ```
   JOHN|DOE|Army|January|15|1970|December|1|2025|johndoe@email.com
   ```

### Step 2: Open SheerID Page
- Mở link SheerID verification trong tab mới
- Extension sẽ tự động fill form

### Step 3: Start
1. Click **▶ Start**
2. Extension sẽ:
   - Điền form với thông tin veteran hiện tại
   - Submit form
   - Đọc kết quả
   - Nếu **Verified** → Xóa veteran, thông báo thành công
   - Nếu **Not Approved** → Xóa veteran, thử người tiếp theo
   - Nếu **Error** → Dừng, yêu cầu đổi VPN

## File Structure
```
v5/
├── manifest.json         # Extension config
├── popup/
│   ├── popup.html       # UI
│   ├── popup.css        # Styles
│   └── popup.js         # Logic
├── background/
│   └── background.js    # Main controller
├── content/
│   ├── veterans-claim.js   # ChatGPT page
│   ├── sheerid-form.js     # Form auto-fill
│   └── sheerid-verify.js   # Status detection
└── icons/
```

## Tips
- 💡 Mở DevTools (F12) để xem logs chi tiết
- 💡 Dùng VPN để tránh bị block
- 💡 Nên test với 1-2 veterans trước khi chạy nhiều
