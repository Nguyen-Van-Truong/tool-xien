# 📚 HƯỚNG DẪN SỬ DỤNG TOOL ĐĂNG KÝ EMAIL EDU

## 🎯 TỔNG QUAN
Tool này được tạo từ tool gốc để đăng ký email edu tự động. Bạn cần tùy chỉnh theo website edu cụ thể mà bạn muốn đăng ký.

## 📁 CẤU TRÚC FILE MỚI
```
tool no card/
├── modules/
│   ├── Bot_edu.py          # Bot logic cho edu (MỚI)
│   └── ... (các file khác)
├── main_edu.py             # Giao diện chính cho edu (MỚI)
├── HUONG_DAN_EDU.md        # File này
└── ... (các file khác)
```

## 🚀 CÁCH CHẠY TOOL EDU

### Bước 1: Chạy tool
```bash
python main_edu.py
```

### Bước 2: Cấu hình trong giao diện
- **Token TempMail**: Đã tự động load từ `token.txt`
- **Data File**: Mặc định `edu_accounts.txt` 
- **Số lượng**: Số tài khoản muốn tạo
- **Threads**: Số luồng chạy song song

## ⚙️ TÙY CHỈNH CHO WEBSITE CỤ THỂ

### 1. Thay đổi URL và thông tin cơ bản
Mở file `modules/Bot_edu.py` và sửa:

```python
# =============== CẤU HÌNH CHÍNH - THAY ĐỔI THEO WEBSITE CỦA BẠN ===============
BASE_URL = "https://your-edu-website.edu.vn/register"  # THAY ĐỔI URL

# =============== THÔNG TIN MẶC ĐỊNH ===============
DEFAULT_INFO = {
    "department": "Công nghệ thông tin",  # Khoa mặc định
    "major": "Khoa học máy tính",         # Ngành mặc định  
    "year": "2024",                       # Năm học
    "phone_prefix": "09",                 # Đầu số điện thoại
}
```

### 2. Cấu hình Selectors
Bạn cần inspect website để lấy selectors chính xác:

```python
SELECTORS = {
    # Email input field - THAY ĐỔI THEO WEBSITE
    "email":            ("css", "input[name='email']"),           
    "username":         ("css", "input[name='username']"),        
    "password":         ("css", "input[name='password']"),        
    "confirm_password": ("css", "input[name='confirm_password']"), 
    
    # Thông tin cá nhân - THAY ĐỔI THEO FORM
    "first_name":       ("css", "input[name='first_name']"),      
    "last_name":        ("css", "input[name='last_name']"),       
    "full_name":        ("css", "input[name='full_name']"),       
    "student_id":       ("css", "input[name='student_id']"),      
    "phone":            ("css", "input[name='phone']"),           
    "birthday":         ("css", "input[name='birthday']"),        
    
    # Buttons - THAY ĐỔI THEO WEBSITE
    "register_button":  ("css", "button[type='submit']"),         
    "verify_button":    ("css", "button.verify-btn"),             
    
    # Captcha và xác thực - NẾU CÓ
    "captcha_input":    ("css", "input[name='captcha']"),         
    "verification_code": ("css", "input[name='verification_code']"), 
    
    # Agreement/Terms - NẾU CÓ
    "agree_checkbox":   ("css", "input[type='checkbox'][name='agree']"), 
    "terms_checkbox":   ("css", "input[type='checkbox'][name='terms']"), 
}
```

### 3. Cách lấy Selectors từ website
1. **Mở website đăng ký** trong Chrome
2. **Right-click** trên input field → **Inspect** 
3. **Copy selector** từ DevTools:
   - CSS Selector: Copy → Copy selector
   - XPath: Copy → Copy XPath

**Ví dụ:**
```html
<input type="email" name="user_email" id="email" class="form-control">
```
→ Selector: `("css", "input[name='user_email']")` hoặc `("css", "#email")`

### 4. Chỉnh sửa flow đăng ký
Trong hàm `register_edu_account()`, sửa theo flow của website:

```python
def register_edu_account(self):
    try:
        # extract gg from pdf. Mở trang đăng ký
        self.driver.get(BASE_URL)
        time.sleep(3)

        # 2. Tạo thông tin
        student_info = self.generate_student_info()
        username = self.generate_edu_email_username()
        password = self.generate_password()

        # 3. Điền form - CHỈNH SỬA THEO FORM CỦA BẠN
        # Thay đổi domain email edu ở đây
        if "email" in SELECTORS:
            self.type("email", f"{username}@edu.sf.vn")  # ← THAY ĐỔI DOMAIN
        
        # ... tiếp tục theo form của website
```

### 5. Xử lý các trường hợp đặc biệt

#### A. Website có nhiều bước đăng ký:
```python
# Bước extract gg from pdf: Điền thông tin cơ bản
self.type("email", email)
self.type("password", password)
self.click("next_button")

# Bước 2: Điền thông tin chi tiết  
self.type("full_name", student_info["full_name"])
self.type("phone", student_info["phone"])
self.click("register_button")
```

#### B. Website có dropdown phức tạp:
```python
# Dropdown đơn giản
self.select("department", by_text="Công nghệ thông tin")

# Dropdown phức tạp (click để mở)
self.click("department_dropdown")
self.click("department_option_it")
```

#### C. Website có CAPTCHA:
```python
if "captcha_input" in SELECTORS:
    print("Đợi giải captcha...")
    time.sleep(10)  # Đợi extension tự động giải
    # Hoặc manual input nếu cần
```

### 6. Kiểm tra thành công
Sửa hàm `check_success()` theo website:

```python
def check_success(self):
    try:
        current_url = self.driver.current_url
        
        # Kiểm tra URL chuyển hướng
        success_urls = [
            "success", "dashboard", "profile", 
            "welcome", "verify-email", "complete"
        ]
        
        for url_part in success_urls:
            if url_part in current_url:
                return True
        
        # Kiểm tra text trên trang
        page_text = self.driver.page_source.lower()
        success_messages = [
            "đăng ký thành công",
            "registration successful", 
            "account created",
            "check your email"
        ]
        
        for msg in success_messages:
            if msg in page_text:
                return True
        
        return False
    except Exception:
        return False
```

## 🔧 DEBUGGING & TROUBLESHOOTING

### 1. Khi gặp lỗi selector
- Kiểm tra lại selector trên website
- Thử dùng XPath thay vì CSS
- Kiểm tra element có động hay không

### 2. Khi không tìm thấy element
- Thêm `time.sleep()` để đợi trang load
- Kiểm tra có popup/overlay che element không
- Sử dụng `wait_for()` thay vì click trực tiếp

### 3. Debug mode
Bật chế độ debug để xem browser:
```python
# Trong giao diện, bỏ tick "Headless Mode"
headless_mode=False
```

### 4. Chụp ảnh lỗi
Tool tự động chụp ảnh khi lỗi:
- `error_[selector].png`: Lỗi click/type
- `error_register.png`: Lỗi đăng ký

## 📝 VÍ DỤ CỤ THỂ

### Ví dụ 1: Website edu đơn giản
```python
BASE_URL = "https://student.university.edu.vn/register"

SELECTORS = {
    "email": ("css", "#email"),
    "password": ("css", "#password"), 
    "full_name": ("css", "#fullName"),
    "student_id": ("css", "#studentId"),
    "register_button": ("css", ".btn-register"),
}

# Trong register_edu_account():
self.type("email", f"{username}@student.university.edu.vn")
self.type("password", password)
self.type("full_name", student_info["full_name"])
self.type("student_id", student_info["student_id"])
self.click("register_button")
```

### Ví dụ 2: Website có xác thực email
```python
def handle_email_verification(self, username):
    # Tạo email tạm
    temp_email = self.create_temp_email(username)
    
    # Đợi email xác thực
    for i in range(10):
        time.sleep(10)
        messages = self.client.get_message_list(temp_email['email_id'])
        if messages:
            code = self.extract_verification_code(messages[0])
            if code:
                self.type("verification_code", code)
                self.click("verify_button")
                return True
    return False
```

## ⚡ TIPS & TRICKS

1. **Test từng bước**: Comment code để test từng phần một
2. **Sử dụng browser developer tools**: F12 để inspect elements
3. **Thêm delay**: Một số website cần thời gian load
4. **Backup selectors**: Chuẩn bị nhiều selector cho 1 element
5. **Error handling**: Wrap code trong try-catch

## 🎯 CHECKLIST TRƯỚC KHI CHẠY

- [ ] Đã thay đổi `BASE_URL` 
- [ ] Đã cập nhật tất cả `SELECTORS`
- [ ] Đã test selector trên website thật
- [ ] Đã cấu hình domain email đúng
- [ ] Đã test flow đăng ký manual trước
- [ ] Đã cài đủ dependencies (PyQt6, selenium, etc.)
- [ ] ChromeDriver version đúng với Chrome

## 🚨 LƯU Ý QUAN TRỌNG

1. **Tuân thủ điều khoản**: Chỉ sử dụng cho mục đích học tập/test
2. **Rate limiting**: Không spam quá nhiều request
3. **Legal compliance**: Đảm bảo tuân thủ quy định của website
4. **Backup data**: Luôn backup file accounts
5. **Update tool**: Website có thể thay đổi, cần update selectors

---
💡 **Need help?** Kiểm tra lại từng bước trong hướng dẫn này hoặc debug bằng cách chạy không headless để xem trực tiếp. 