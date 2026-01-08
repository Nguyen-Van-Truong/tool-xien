# ChatGPT Military Verification Tool

Tool Python tự động verify hàng loạt tài khoản ChatGPT Veterans sử dụng Playwright và PyQt6.

## Tính năng

- ✅ Tự động đăng ký/đăng nhập ChatGPT (browser thật, thủ công)
- ✅ Tự động verify tư cách cựu chiến binh trên SheerID (tự động hoàn toàn)
- ✅ Giao diện đồ họa với PyQt6
- ✅ Xử lý nhiều tài khoản đồng thời (tối đa 20)
- ✅ Hỗ trợ proxy
- ✅ Đọc OTP từ email API
- ✅ Tạo email tự động cho verification
- ✅ Hiển thị trạng thái real-time
- ✅ Auto-retry khi gặp lỗi "Not Approved" hoặc "Limit Exceeded"
- ✅ Quản lý cookies tự động qua browser profiles

## Quy trình hoạt động

Tool hoạt động theo **2 bước riêng biệt**:

### Bước 1: Reg/Login (Đăng ký/Đăng nhập)

**Mục đích**: Lưu cookies đăng nhập vào browser profile riêng cho mỗi tài khoản.

**Quy trình**:
1. Tool mở browser thật (Brave/Edge/Chrome) với user data directory riêng
2. Browser tự động điều hướng đến `https://chatgpt.com`
3. **Người dùng tự thực hiện**:
   - Xử lý Cloudflare challenge (nếu có)
   - Hoàn thành đăng ký/đăng nhập thủ công
   - Khi đến bước OTP, click nút "Code" trong tool để lấy OTP từ email API
   - Nhập OTP và hoàn thành login
4. Cookies được lưu tự động trong user data directory
5. Đóng browser khi hoàn thành

**Lưu ý**: 
- Browser sẽ mở và đợi bạn hoàn thành - **KHÔNG GIỚI HẠN THỜI GIAN**
- Mỗi tài khoản có browser profile riêng để lưu cookies
- Browser profile được lưu tại `browser_profiles/profile_{row}_{email}/`

### Bước 2: Verification (Xác minh tư cách cựu chiến binh)

**Mục đích**: Tự động verify tài khoản đã đăng nhập trên SheerID.

**Quy trình**:
1. Tool mở browser thật với CDP (Chrome DevTools Protocol) để Playwright có thể điều khiển
2. Load cookies từ browser profile đã lưu ở Bước 1
3. Tự động điều hướng đến `https://chatgpt.com/veterans-claim`
4. Click nút "Verify" để bắt đầu quá trình verification
5. Chờ redirect đến SheerID và extract `verification_id` từ URL
6. Tạo email tự động từ API `tinyhost.shop`
7. Gửi thông tin verification đến SheerID API:
   - Tên, họ từ veteran data
   - Ngày sinh, ngày xuất ngũ
   - Branch (Army, Navy, Air Force, etc.)
   - Email tự động tạo
8. Chờ email verification từ SheerID
9. Tự động click link verification trong email
10. Đóng browser sau khi hoàn thành

**Tính năng đặc biệt**:
- **Auto-retry**: Nếu gặp lỗi "Not Approved" hoặc "Limit Exceeded", tool tự động thử với veteran data khác (không dừng)
- **Quản lý veteran data**: Mỗi veteran data chỉ được dùng 1 lần, tự động chuyển sang data khác khi cần
- **Error handling**: Nếu gặp Cloudflare/CAPTCHA, browser sẽ giữ mở để người dùng xử lý thủ công

## Cài đặt

1. Cài đặt Python 3.8+

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Cài đặt Playwright browsers:
```bash
playwright install chromium
```

**Lưu ý**: Tool sử dụng browser thật (Brave/Edge/Chrome) trên máy, không cần cài đặt browser riêng từ Playwright. Playwright chỉ dùng để kết nối qua CDP.

## Sử dụng

### 1. Chạy tool:
```bash
python main.py
```

### 2. Load dữ liệu:

**Load Accounts**:
- Click "Load Accounts"
- Chọn file chứa accounts (format: `email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id`)

**Load Data**:
- Click "Load Data"
- Chọn file chứa veteran data (format: `first|last|branch|month|day|year`)

**Load Proxies** (optional):
- Click "Load Proxies"
- Chọn file chứa proxies (format: `host:port:username:password` hoặc `host:port`)

### 3. Thực hiện Reg/Login:

**Cách 1: Chạy tất cả**:
- Click "Start Automation" để chạy Reg/Login cho tất cả accounts

**Cách 2: Chạy riêng lẻ**:
- Click nút "▶ Reg/Login" trên từng row để chạy riêng lẻ

**Quy trình**:
1. Browser sẽ mở cho mỗi account
2. Hoàn thành đăng ký/đăng nhập thủ công trong browser
3. Khi cần OTP, click nút "Code" trong tool để lấy OTP
4. Nhập OTP và hoàn thành login
5. Đóng browser khi xong
6. Status sẽ chuyển sang "Ready!" khi thành công

### 4. Thực hiện Verification:

**Sau khi Reg/Login thành công**, click nút "▶ Start Veri" trên từng row để bắt đầu verification.

**Quy trình tự động**:
1. Tool mở browser với CDP và load cookies
2. Tự động điều hướng và click verify button
3. Tự động submit thông tin verification
4. Tự động xử lý email verification
5. Đóng browser khi hoàn thành

**Status có thể**:
- `Verified!`: Verification thành công
- `Not Approved`: Tự động retry với veteran data khác
- `Limit Exceeded`: Tự động retry với veteran data khác
- `Cloudflare Detected`: Browser giữ mở để xử lý thủ công
- `Failed`: Lỗi khác, cần kiểm tra

## Format dữ liệu

### Accounts (accounts.txt):
```
email1@example.com|password1|email-login1@example.com|pass-email1|refresh_token1|client_id1
email2@example.com|password2|email-login2@example.com|pass-email2|refresh_token2|client_id2
```

**Giải thích các trường**:
- `email-chatgpt`: Email đăng ký ChatGPT
- `pass-chatgpt`: Password đăng ký ChatGPT
- `email-login`: Email để đăng nhập vào email API (để lấy OTP)
- `pass-email`: Password email API
- `refresh_token`: Refresh token của email API (Gmail/Outlook)
- `client_id`: Client ID của email API

### Veteran Data (data.txt):
```
John|Doe|Army|January|15|1980
Jane|Smith|Navy|February|20|1985
```

**Giải thích các trường**:
- `first`: Tên
- `last`: Họ
- `branch`: Nhánh quân đội (Army, Navy, Air Force, Marines, Coast Guard, Space Force)
- `month`: Tháng sinh (tên tháng tiếng Anh: January, February, ...)
- `day`: Ngày sinh (số)
- `year`: Năm sinh (4 chữ số)

### Proxies (proxies.txt):
```
proxy1.com:8080:user1:pass1
proxy2.com:8080:user2:pass2
proxy3.com:8080
```

**Format**: `host:port:username:password` hoặc `host:port` (nếu không cần auth)

## Cấu trúc project

```
chatgpt_veterans_tool/
├── main.py                              # Entry point
├── gui/
│   ├── __init__.py
│   └── main_window.py                    # Main window UI với table và controls
├── automation/
│   ├── __init__.py
│   ├── reg_login_automation.py           # Reg/Login automation (browser thật)
│   ├── verification_only_automation.py  # Verification automation (CDP)
│   ├── verification_flow.py              # Verification flow logic
│   ├── signup_flow.py                    # Signup flow logic (không dùng trong workflow 2 bước)
│   └── chatgpt_automation.py             # Legacy automation (không dùng)
├── utils/
│   ├── __init__.py
│   ├── file_loader.py                    # File loader (accounts, data, proxies)
│   ├── email_api.py                      # Email API để lấy OTP
│   ├── browser_fingerprint.py            # Browser fingerprint và stealth
│   └── config.py                         # Config handler
├── military/
│   ├── __init__.py
│   ├── sheerid_verifier.py               # SheerID API verification
│   ├── name_generator.py                 # Generate random names/dates
│   └── config.py                         # Military config
├── browser_profiles/                     # Browser profiles (mỗi account 1 profile)
│   └── profile_{row}_{email}/
│       └── ... (browser data, cookies, etc.)
├── data/                                 # Data files folder
│   ├── emails.txt                        # Accounts file
│   ├── data-extension.txt                # Veteran data file
│   └── proxies.txt                       # Proxies file
├── requirements.txt
└── README.md
```

## Chi tiết kỹ thuật

### Browser Management

- **Browser thật**: Tool sử dụng browser thật (Brave/Edge/Chrome) thay vì headless browser
- **Browser profiles**: Mỗi account có profile riêng tại `browser_profiles/profile_{row}_{email}/`
- **CDP (Chrome DevTools Protocol)**: Dùng để Playwright điều khiển browser thật trong bước Verification
- **Cookie persistence**: Cookies được lưu tự động trong browser profile

### Automation Flow

1. **Reg/Login Thread** (`RegLoginThread`):
   - Mở browser thật với user data dir riêng
   - Đợi người dùng hoàn thành login
   - Lưu cookies tự động
   - Đóng browser khi xong

2. **Verification Thread** (`VerificationThread`):
   - Mở browser thật với CDP port
   - Connect Playwright qua CDP
   - Load cookies từ profile
   - Chạy verification flow tự động
   - Đóng browser khi xong

### Error Handling

- **Cloudflare/CAPTCHA**: Browser giữ mở để xử lý thủ công
- **Not Approved**: Tự động retry với veteran data khác
- **Limit Exceeded**: Tự động retry với veteran data khác
- **Element not found**: Log error và giữ browser mở

### Veteran Data Management

- Mỗi veteran data chỉ được dùng 1 lần cho 1 account
- Tracking qua `veteran_data_in_use` dictionary
- Auto-retry tự động chọn veteran data chưa dùng
- Nếu hết data, status chuyển sang "Failed"

## Lưu ý quan trọng

- ✅ Tool cần kết nối internet để truy cập ChatGPT và các API
- ✅ Cần có refresh_token và client_id hợp lệ để đọc email OTP
- ✅ Tool sẽ mở browser thật để thực hiện automation (không headless)
- ✅ Đảm bảo có đủ tài khoản và data trước khi start automation
- ✅ Mỗi account cần hoàn thành Reg/Login trước khi có thể verify
- ✅ Browser profiles sẽ được tạo tự động, không cần setup thủ công
- ✅ Tool hỗ trợ tối đa 20 browsers chạy đồng thời (có thể điều chỉnh)
- ⚠️ Không đóng browser thủ công trong quá trình verification (trừ khi có lỗi)
- ⚠️ Nếu gặp Cloudflare, cần xử lý thủ công trong browser

## Troubleshooting

### Browser không mở được
- Kiểm tra xem đã cài Brave/Edge/Chrome chưa
- Tool sẽ tự động tìm browser theo thứ tự: Brave → Edge → Chrome

### Cookies không được lưu
- Kiểm tra quyền ghi vào thư mục `browser_profiles/`
- Đảm bảo đã hoàn thành login trước khi đóng browser

### Verification failed
- Kiểm tra xem đã Reg/Login thành công chưa (status = "Ready!")
- Kiểm tra veteran data có hợp lệ không
- Kiểm tra kết nối internet và proxy (nếu dùng)

### OTP không lấy được
- Kiểm tra refresh_token và client_id có hợp lệ không
- Kiểm tra email API credentials
- Thử click nút "Code" lại

## License

Private use only
