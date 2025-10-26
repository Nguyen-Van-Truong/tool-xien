# 🎓 SANTA FE COLLEGE - CẤU HÌNH TEMPLATE
# Điền thông tin vào template này sau khi inspect website

# =============== CẤU HÌNH CHÍNH ===============
BASE_URL = "https://ss2.sfcollege.edu/sr/AdmissionApplication/#/"
COLLEGE_NAME = "Santa Fe College"
EMAIL_DOMAIN = "@sfcollege.edu"  # HOẶC @student.sfcollege.edu - CẦN XÁC NHẬN

# =============== SELECTORS CẦN ĐIỀN ===============
SELECTORS = {
    # === THÔNG TIN CÁ NHÂN ===
    "email":                ("css", ""),           # ← ĐIỀN SELECTOR EMAIL
    "password":             ("css", ""),           # ← ĐIỀN SELECTOR PASSWORD  
    "confirm_password":     ("css", ""),           # ← ĐIỀN SELECTOR CONFIRM PASSWORD
    "first_name":           ("css", ""),           # ← ĐIỀN SELECTOR FIRST NAME
    "last_name":            ("css", ""),           # ← ĐIỀN SELECTOR LAST NAME
    "middle_name":          ("css", ""),           # ← NẾU CÓ
    "date_of_birth":        ("css", ""),           # ← ĐIỀN SELECTOR DOB
    "phone":                ("css", ""),           # ← ĐIỀN SELECTOR PHONE
    "ssn":                  ("css", ""),           # ← ĐIỀN SELECTOR SSN/ID
    
    # === ĐỊA CHỈ ===
    "address_line1":        ("css", ""),           # ← ĐIỀN SELECTOR ADDRESS
    "address_line2":        ("css", ""),           # ← NẾU CÓ
    "city":                 ("css", ""),           # ← ĐIỀN SELECTOR CITY
    "state":                ("css", ""),           # ← ĐIỀN SELECTOR STATE
    "zip_code":             ("css", ""),           # ← ĐIỀN SELECTOR ZIP
    "country":              ("css", ""),           # ← ĐIỀN SELECTOR COUNTRY
    
    # === HỌC VẤN ===
    "previous_school":      ("css", ""),           # ← ĐIỀN SELECTOR PREVIOUS SCHOOL
    "graduation_year":      ("css", ""),           # ← ĐIỀN SELECTOR GRAD YEAR
    "gpa":                  ("css", ""),           # ← NẾU CÓ
    "program_interest":     ("css", ""),           # ← ĐIỀN SELECTOR PROGRAM/MAJOR
    
    # === BUTTONS ===
    "next_button":          ("css", ""),           # ← ĐIỀN SELECTOR NEXT BUTTON
    "submit_button":        ("css", ""),           # ← ĐIỀN SELECTOR SUBMIT
    "previous_button":      ("css", ""),           # ← NẾU CÓ
    
    # === EMAIL VERIFICATION ===
    "verification_code":    ("css", ""),           # ← ĐIỀN SELECTOR VERIFICATION CODE
    "verify_button":        ("css", ""),           # ← ĐIỀN SELECTOR VERIFY BUTTON
    "resend_code":          ("css", ""),           # ← NẾU CÓ
    
    # === CAPTCHA ===
    "captcha_iframe":       ("css", ""),           # ← ĐIỀN SELECTOR CAPTCHA IFRAME
    "captcha_checkbox":     ("css", ""),           # ← NẾU LÀ reCAPTCHA v2
    
    # === AGREEMENT/TERMS ===
    "terms_checkbox":       ("css", ""),           # ← ĐIỀN SELECTOR TERMS CHECKBOX
    "privacy_checkbox":     ("css", ""),           # ← NẾU CÓ
    "agreement_checkbox":   ("css", ""),           # ← NẾU CÓ
}

# =============== THÔNG TIN MẶC ĐỊNH ===============
DEFAULT_INFO = {
    "state": "FL",                                 # Florida
    "country": "United States",
    "phone_prefix": "+extract gg from pdf",
    "address_city": "Gainesville",                 # Thành phố của Santa Fe College
    "zip_code": "32606",                          # Zip code khu vực
    "graduation_year": "2024",
    "program_interest": "Computer Science",        # Ngành học mặc định
}

# =============== EMAIL VERIFICATION CONFIG ===============
EMAIL_CONFIG = {
    "domain": "@sfcollege.edu",                   # HOẶC @student.sfcollege.edu
    "verification_wait_time": 60,                 # Đợi extract gg from pdf phút như bạn nói
    "max_retries": 10,                           # Thử tối đa 10 lần
    "code_format": "6_digits",                    # HOẶC "4_digits", "alphanumeric"
    "email_subject_keywords": [                   # Keywords trong subject email
        "verify", "verification", "confirm", 
        "activate", "santa fe", "sfcollege"
    ]
}

# =============== CAPTCHA CONFIG ===============
CAPTCHA_CONFIG = {
    "type": "recaptcha_v2",                       # HOẶC "recaptcha_v3", "hcaptcha"
    "wait_time": 15,                             # Đợi extension giải captcha
    "manual_solve": False,                        # True nếu cần giải manual
}

# =============== FORM FLOW CONFIG ===============
FORM_FLOW = {
    "is_multi_step": True,                        # True nếu có nhiều bước
    "steps": [
        "personal_info",                          # Bước extract gg from pdf: Thông tin cá nhân
        "contact_info",                           # Bước 2: Thông tin liên lạc  
        "education_info",                         # Bước 3: Học vấn
        "program_selection",                      # Bước 4: Chọn chương trình
        "verification",                           # Bước 5: Xác thực email
        "final_submission"                        # Bước 6: Hoàn thành
    ],
    "wait_between_steps": 3,                     # Giây đợi giữa các bước
}

# =============== SUCCESS INDICATORS ===============
SUCCESS_INDICATORS = {
    "url_patterns": [
        "success", "complete", "confirmation", 
        "welcome", "dashboard", "profile"
    ],
    "text_patterns": [
        "application submitted", "registration complete",
        "welcome to santa fe", "check your email",
        "application received", "thank you"
    ]
}

# =============== HƯỚNG DẪN ĐIỀN THÔNG TIN ===============
"""
🔍 CÁCH LẤY SELECTORS:

extract gg from pdf. Mở https://ss2.sfcollege.edu/sr/AdmissionApplication/#/
2. Đợi trang load xong
3. F12 → Inspect element
4. Right-click input → Copy → Copy selector
5. Paste vào các field "" ở trên

📧 XÁC ĐỊNH EMAIL DOMAIN:
- Kiểm tra form để xem tạo email @sfcollege.edu hay @student.sfcollege.edu
- Hoặc test đăng ký extract gg from pdf acc manual để xem

🤖 KIỂM TRA CAPTCHA:
- Xem có iframe reCAPTCHA không
- Copy selector của captcha elements

📝 KIỂM TRA FORM FLOW:
- Xem có bao nhiêu bước
- Nút Next/Previous ở đâu
- Validation như thế nào

⚠️ LƯU Ý:
- Website có thể có validation phức tạp
- Cần test manual trước khi chạy tool
- Một số field có thể required/optional
""" 