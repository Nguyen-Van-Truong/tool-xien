from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import string
import random
import re
from modules.TempMailClient import TempMailClient
from faker import Faker
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path

# =============== CẤU HÌNH CHÍNH - THAY ĐỔI THEO WEBSITE CỦA BẠN ===============
BASE_URL = "https://your-edu-website.edu.vn/register"  # THAY ĐỔI URL ĐĂNG KÝ EDU

# =============== SELECTORS - THAY ĐỔI THEO FORM CỦA WEBSITE ===============
SELECTORS = {
    # Email input field
    "email":            ("css", "input[name='email']"),           # Thay đổi selector
    "username":         ("css", "input[name='username']"),        # Nếu có username riêng
    "password":         ("css", "input[name='password']"),        # Password field
    "confirm_password": ("css", "input[name='confirm_password']"), # Confirm password
    
    # Thông tin cá nhân
    "first_name":       ("css", "input[name='first_name']"),      # Họ
    "last_name":        ("css", "input[name='last_name']"),       # Tên
    "full_name":        ("css", "input[name='full_name']"),       # Họ tên đầy đủ
    "student_id":       ("css", "input[name='student_id']"),      # Mã sinh viên
    "phone":            ("css", "input[name='phone']"),           # Số điện thoại
    "birthday":         ("css", "input[name='birthday']"),        # Ngày sinh
    
    # Dropdown/Select fields
    "department":       ("css", "select[name='department']"),     # Khoa
    "major":            ("css", "select[name='major']"),          # Ngành học
    "year":             ("css", "select[name='year']"),           # Năm học
    "class":            ("css", "select[name='class']"),          # Lớp
    
    # Buttons
    "register_button":  ("css", "button[type='submit']"),         # Nút đăng ký
    "verify_button":    ("css", "button.verify-btn"),             # Nút xác thực
    "next_button":      ("css", "button.next-btn"),               # Nút tiếp theo
    
    # Captcha và xác thực
    "captcha_input":    ("css", "input[name='captcha']"),         # Captcha input
    "captcha_image":    ("css", "img.captcha-image"),             # Captcha image
    "verification_code": ("css", "input[name='verification_code']"), # Mã xác thực email
    
    # Agreement/Terms
    "agree_checkbox":   ("css", "input[type='checkbox'][name='agree']"), # Checkbox đồng ý
    "terms_checkbox":   ("css", "input[type='checkbox'][name='terms']"), # Checkbox điều khoản
}

# =============== THÔNG TIN MẶC ĐỊNH ===============
DEFAULT_INFO = {
    "department": "Công nghệ thông tin",  # Khoa mặc định
    "major": "Khoa học máy tính",         # Ngành mặc định
    "year": "2024",                       # Năm học mặc định
    "phone_prefix": "09",                 # Đầu số điện thoại
}

class BotEdu:
    def __init__(self, token, chromedriver: str ="driver/chromedriver.exe", wait_sec=2, timeout=30, headless_mode: bool=False):
        self.token = token
        self.chromedriver = chromedriver
        self.WAIT_SEC = wait_sec
        self.TIMEOUT = timeout
        self.headless_mode = headless_mode
        self.is_email_used = None
        self.add_used_email = None

    def _setup_driver(self):
        opts = webdriver.ChromeOptions()
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        # Thêm extensions nếu cần
        if os.path.exists("driver/captchasolver.crx"):
            opts.add_extension("driver/captchasolver.crx")
        if os.path.exists("driver/extract gg from pdf.crx"):
            opts.add_extension("driver/extract gg from pdf.crx")
            
        opts.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        
        if self.headless_mode:
            opts.add_argument('--headless=new')
            opts.add_argument('--window-size=1920,1080')
        else:
            opts.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(service=Service(str(self.chromedriver)), options=opts)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)
        self.client = TempMailClient(self.token)

    def _loc(self, key):
        by, sel = SELECTORS[key]
        return (By.CSS_SELECTOR, sel) if by == "css" else (By.XPATH, sel)

    def click(self, key):
        try:
            el = self.wait.until(EC.element_to_be_clickable(self._loc(key)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
            try:
                el.click()
            except:
                self.driver.execute_script("arguments[0].click();", el)
            time.sleep(self.WAIT_SEC)
        except Exception as e:
            print(f"Lỗi khi click {key}: {str(e)}")
            self.driver.save_screenshot(f"error_{key}.png")
            raise

    def type(self, key, txt):
        try:
            el = self.wait.until(EC.element_to_be_clickable(self._loc(key)))
            el.clear()
            time.sleep(0.5)
            el.send_keys(txt)
            time.sleep(self.WAIT_SEC)
        except Exception as e:
            print(f"Lỗi khi nhập text cho {key}: {str(e)}")
            self.driver.save_screenshot(f"error_type_{key}.png")
            raise

    def select(self, key, *, by_value=None, by_text=None, by_index=None, timeout=None):
        if not timeout:
            timeout = self.TIMEOUT
        el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(self._loc(key)))
        sel = Select(el)
        time.sleep(self.WAIT_SEC)
        if by_value is not None:
            sel.select_by_value(by_value)
        elif by_text is not None:
            sel.select_by_visible_text(by_text)
        elif by_index is not None:
            sel.select_by_index(by_index)

    def generate_student_info(self):
        """Tạo thông tin sinh viên giả"""
        f = Faker('vi_VN')  # Sử dụng locale Việt Nam
        
        return {
            "first_name": f.first_name(),
            "last_name": f.last_name(),
            "full_name": f.name(),
            "phone": f"09{random.randint(10000000, 99999999)}",  # SĐT Việt Nam
            "birthday": f.date_of_birth(minimum_age=18, maximum_age=25).strftime("%d/%m/%Y"),
            "student_id": f"SV{random.randint(100000, 999999)}",  # Mã sinh viên giả
            "address": f.address(),
        }

    def generate_edu_email_username(self, length=8):
        """Tạo username cho email edu"""
        # Định dạng thường dùng: firstname.lastname.year hoặc số
        chars = string.ascii_lowercase + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def generate_password(self):
        """Tạo mật khẩu mạnh"""
        chars = string.ascii_letters + string.digits
        random_chars = "".join(random.choices(chars, k=6))
        special_chars = "!@#$"
        special_char = random.choice(special_chars)
        return f"EduPass{random_chars}{special_char}"

    def create_temp_email(self, username, tries=5):
        """Tạo email tạm để nhận mã xác thực"""
        for _ in range(tries):
            j = self.client.create_temp_email(username)
            if j:
                return j
        return None

    def register_edu_account(self):
        """Đăng ký tài khoản edu - CHỈNH SỬA THEO FLOW CỦA WEBSITE"""
        try:
            # extract gg from pdf. Mở trang đăng ký
            print("Mở trang đăng ký edu...")
            self.driver.get(BASE_URL)
            time.sleep(3)

            # 2. Tạo thông tin sinh viên
            student_info = self.generate_student_info()
            username = self.generate_edu_email_username()
            password = self.generate_password()
            
            print(f"Thông tin sinh viên: {student_info}")
            print(f"Username: {username}")

            # 3. Điền form đăng ký (CHỈNH SỬA THEO FORM CỦA BẊN)
            # Email/Username
            if "email" in SELECTORS:
                self.type("email", f"{username}@edu.sf.vn")  # Hoặc domain khác
            
            if "username" in SELECTORS:
                self.type("username", username)

            # Mật khẩu
            self.type("password", password)
            if "confirm_password" in SELECTORS:
                self.type("confirm_password", password)

            # Thông tin cá nhân
            if "full_name" in SELECTORS:
                self.type("full_name", student_info["full_name"])
            elif "first_name" in SELECTORS and "last_name" in SELECTORS:
                self.type("first_name", student_info["first_name"])
                self.type("last_name", student_info["last_name"])

            if "phone" in SELECTORS:
                self.type("phone", student_info["phone"])

            if "student_id" in SELECTORS:
                self.type("student_id", student_info["student_id"])

            if "birthday" in SELECTORS:
                self.type("birthday", student_info["birthday"])

            # Dropdown selections
            if "department" in SELECTORS:
                self.select("department", by_text=DEFAULT_INFO["department"])
            
            if "major" in SELECTORS:
                self.select("major", by_text=DEFAULT_INFO["major"])

            # Checkbox đồng ý
            if "agree_checkbox" in SELECTORS:
                self.click("agree_checkbox")
            
            if "terms_checkbox" in SELECTORS:
                self.click("terms_checkbox")

            # 4. Xử lý Captcha (nếu có)
            if "captcha_input" in SELECTORS:
                print("Đợi giải captcha...")
                time.sleep(10)  # Đợi extension tự động giải

            # 5. Submit form
            print("Nhấn nút đăng ký...")
            self.click("register_button")
            time.sleep(5)

            # 6. Xử lý xác thực email (nếu cần)
            if self.handle_email_verification(username):
                print("Xác thực email thành công!")
            
            # 7. Kiểm tra kết quả
            if self.check_success():
                account_info = {
                    "email": f"{username}@edu.sf.vn",  # Hoặc domain khác
                    "password": password,
                    "student_info": student_info
                }
                self.save_account(account_info)
                return account_info
            else:
                print("Đăng ký thất bại!")
                return None

        except Exception as e:
            print(f"Lỗi trong quá trình đăng ký: {str(e)}")
            self.driver.save_screenshot("error_register.png")
            return None

    def handle_email_verification(self, username):
        """Xử lý xác thực email - CHỈNH SỬA THEO WEBSITE"""
        try:
            # Tạo email tạm để nhận mã
            temp_email = self.create_temp_email(username)
            if not temp_email:
                return False

            print(f"Đợi email xác thực tại: {temp_email['email']}")
            
            # Đợi và lấy email xác thực
            for i in range(10):  # Thử 10 lần
                time.sleep(10)
                messages = self.client.get_message_list(temp_email['email_id'])
                if messages:
                    # Tìm email xác thực
                    verification_email = self.find_verification_email(messages)
                    if verification_email:
                        code = self.extract_verification_code(verification_email)
                        if code:
                            self.type("verification_code", code)
                            self.click("verify_button")
                            return True
            
            return False
        except Exception as e:
            print(f"Lỗi xác thực email: {str(e)}")
            return False

    def find_verification_email(self, messages):
        """Tìm email xác thực - CHỈNH SỬA THEO ĐỊNH DẠNG EMAIL"""
        for msg in messages:
            subject = msg.get("subject", "").lower()
            if "verify" in subject or "xác thực" in subject or "confirm" in subject:
                return msg
        return None

    def extract_verification_code(self, email_data):
        """Trích xuất mã xác thực từ email - CHỈNH SỬA THEO ĐỊNH DẠNG"""
        try:
            email_content = self.client.read_message(email_data["id"])
            if not email_content:
                return None
            
            content = email_content.get("content", "")
            # Tìm mã 6 số
            code_match = re.search(r'\b\d{6}\b', content)
            if code_match:
                return code_match.group()
            
            # Tìm mã 4 số
            code_match = re.search(r'\b\d{4}\b', content)
            if code_match:
                return code_match.group()
                
            return None
        except Exception as e:
            print(f"Lỗi trích xuất mã: {str(e)}")
            return None

    def check_success(self):
        """Kiểm tra đăng ký thành công - CHỈNH SỬA THEO WEBSITE"""
        try:
            current_url = self.driver.current_url
            # Kiểm tra URL sau khi đăng ký
            if "success" in current_url or "dashboard" in current_url or "profile" in current_url:
                return True
            
            # Kiểm tra thông báo thành công
            success_messages = [
                "đăng ký thành công",
                "registration successful", 
                "account created",
                "welcome"
            ]
            
            page_text = self.driver.page_source.lower()
            for msg in success_messages:
                if msg in page_text:
                    return True
            
            return False
        except Exception:
            return False

    def save_account(self, account_info):
        """Lưu thông tin tài khoản"""
        try:
            with open("edu_accounts.txt", "a", encoding="utf-8") as f:
                f.write(f"{account_info['email']}:{account_info['password']}\n")
            
            # Lưu thông tin chi tiết
            with open("edu_accounts_detail.txt", "a", encoding="utf-8") as f:
                f.write(f"Email: {account_info['email']}\n")
                f.write(f"Password: {account_info['password']}\n")
                f.write(f"Họ tên: {account_info['student_info']['full_name']}\n")
                f.write(f"SĐT: {account_info['student_info']['phone']}\n")
                f.write(f"MSSV: {account_info['student_info']['student_id']}\n")
                f.write("="*50 + "\n")
                
        except Exception as e:
            print(f"Lỗi lưu file: {str(e)}")

    def exit(self):
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass

class BotManagerEdu:
    def __init__(self, token, num_threads=1, chromedriver="driver/chromedriver.exe", headless_mode=False):
        self.token = token
        self.num_threads = num_threads
        self.chromedriver = chromedriver
        self.headless_mode = headless_mode
        self.results = []

    def run_bot(self, thread_index):
        """Chạy một bot"""
        try:
            print(f"Bắt đầu chạy bot (luồng {thread_index})...")
            bot = BotEdu(
                token=self.token,
                chromedriver=self.chromedriver,
                headless_mode=self.headless_mode
            )
            bot._setup_driver()
            
            result = bot.register_edu_account()
            if result:
                self.results.append(result)
                print(f"Bot (luồng {thread_index}) tạo tài khoản thành công!")
            else:
                print(f"Bot (luồng {thread_index}) tạo tài khoản thất bại!")
            
            bot.exit()
            return result
            
        except Exception as e:
            print(f"Lỗi trong quá trình chạy bot: {str(e)}")
            return None

    def start(self):
        """Bắt đầu chạy tất cả bots"""
        print(f"Bắt đầu chạy {self.num_threads} luồng...")
        
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            for i in range(1, self.num_threads + 1):
                future = executor.submit(self.run_bot, i)
                futures.append(future)
            
            # Đợi tất cả hoàn thành
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Lỗi trong luồng: {str(e)}")
        
        return self.results

    def exit(self):
        pass 