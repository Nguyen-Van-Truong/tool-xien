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

def load_cards(card_file="cards.txt"):
    cards = []
    try:
        with open(card_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('|')
                if len(parts) >= 3:
                    # Xử lý ngày hết hạn
                    expiry = parts[1]
                    if len(expiry) == 4:  # Nếu là định dạng MMYY
                        month = expiry[:2]
                        year = expiry[2:]
                        expiry = f"{month}/{year}"
                    
                    card = {
                        'number': parts[0],
                        'expiry': expiry,
                        'cvc': parts[2],
                        'name': parts[3] if len(parts) > 3 else None
                    }
                    cards.append(card)
    except Exception as e:
        print(f"Lỗi khi đọc file thẻ: {str(e)}")
    return cards

def get_random_card(card_file="cards.txt"):
    cards = load_cards(card_file)
    if not cards:
        raise Exception("Không có thẻ nào trong file cards.txt")
    return random.choice(cards)

BASE_URL = "https://member.bro.game/"
SELECTORS = {
    "refcode":      ("css", "input.refcode-input"),
    "submit_code":  ("css", "button.refcode-btn"),
    "email":        ("css", "input#email"),
    "register":     ("xpath", "//button[contains(@class, 'interface-button-primary')]//span[text()='สมัครสมาชิก']/.."),
    "first_name":   ("css", "input#firstname"),
    "last_name":    ("css", "input#lastname"),
    "country":      ("xpath", "//div[contains(@class, 'ant-select-item-option-content') and contains(text(), 'Thailand')]"),
    "tel":          ("css", "input#tel"),
    "password":     ("css", "input#password"),
    "confirm_password": ("css", "input#confirmPassword"),
    "confirm": (
        "xpath",
        "//button[@type='submit' and .//div[text()='ยืนยัน']]"
    ),
    "card_name": ("css", "input#name"),
    "stripe_iframe": ("css", "iframe[name^='__privateStripeFrame']"),
    "card_number":   ("css", "input#Field-numberInput"),
    "expiry_iframe": ("css", "iframe[name^='__privateStripeFrame'][src*='expiry']"),
    "cvc_iframe":    ("css", "iframe[name^='__privateStripeFrame'][src*='cvc']"),
    "expiry_input": ("css", "input#Field-expiryInput"),
    "cvc_input":    ("css", "input#Field-cvcInput"),
    "country": ("css", "select#Field-countryInput"),
    "confirm_payment": (
        "xpath",
        "//button[@type='button' and .//span[text()='ยืนยันการชำระเงิน']]"
    ),
    "dashboard": (
        "xpath",
        "//button[@type='button' and .//span[text()='เข้าสู่ Dashboard']]"
    ),
}

class Bot:
    def __init__(self, token, chromedriver: str ="driver/chromedriver.exe", wait_sec=2, timeout=30, headless_mode: bool=False):
        self.token = token
        self.chromedriver = chromedriver
        self.WAIT_SEC = wait_sec
        self.TIMEOUT = timeout
        self.headless_mode = headless_mode
        self.is_email_used = None  # Sẽ được set từ BotManager
        self.add_used_email = None  # Sẽ được set từ BotManager

    def _setup_driver(self):
        print(f"Debug - headless_mode value: {self.headless_mode}")
        opts = webdriver.ChromeOptions()
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_extension("driver/captchasolver.crx")
        opts.add_extension("driver/extract gg from pdf.crx")
        opts.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        # Thêm các options cho VPN
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-web-security')
        opts.add_argument('--allow-running-insecure-content')
        opts.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Xử lý chế độ hiển thị
        if self.headless_mode:
            print("Debug - Setting up headless mode")
            opts.add_argument('--headless=new')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--window-size=1920,1080')
        else:
            print("Debug - Setting up normal mode")
            # Tất cả các tab đều chạy full màn hình khi không chọn chạy ngầm
            opts.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(service=Service(str(self.chromedriver)), options=opts)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)
        self.client = TempMailClient(self.token)

    def _loc(self, key):
        by, sel = SELECTORS[key]
        return (By.CSS_SELECTOR, sel) if by == "css" else (By.XPATH, sel)

    def click(self, key):
        try:
            # Kiểm tra element có tồn tại không
            el = self.wait.until(EC.presence_of_element_located(self._loc(key)))
            print(f"Element {key} tồn tại")
            
            # Kiểm tra element có thể click được không
            el = self.wait.until(EC.element_to_be_clickable(self._loc(key)))
            print(f"Element {key} có thể click được")
            
            # Scroll và click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
            try:
                el.click()
            except:
                # Thử click bằng JavaScript nếu click thông thường thất bại
                print(f"Thử click bằng JavaScript cho {key}")
                self.driver.execute_script("arguments[0].click();", el)
            time.sleep(self.WAIT_SEC)
        except Exception as e:
            print(f"Lỗi khi click {key}: {str(e)}")
            # Chụp ảnh màn hình để debug
            self.driver.save_screenshot(f"error_{key}.png")
            raise

    def type(self, key, txt):
        try:
            el = self.wait.until(EC.element_to_be_clickable(self._loc(key)))
            el.clear()
            time.sleep(0.5)  # Thêm delay sau khi clear
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

    def wait_for(self, key, timeout=None):
        if not timeout:
            timeout = self.TIMEOUT
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(self._loc(key))
        )

    def switch_to_frame(self, key):
        try:
            frame = self.wait.until(EC.frame_to_be_available_and_switch_to_it(self._loc(key)))
            time.sleep(self.WAIT_SEC)
            return frame
        except Exception as e:
            print(f"Lỗi khi chuyển frame {key}: {str(e)}")
            self.driver.save_screenshot(f"error_frame_{key}.png")
            raise

    def switch_to_default_content(self):
        self.driver.switch_to.default_content()
        time.sleep(self.WAIT_SEC)

    def fake_profile(self):
        f = Faker()
        return {
            "first_name": f.first_name(),
            "last_name":  f.last_name(),
        }

    def generate_username(self, length=9):
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def generate_password(self):
        chars = string.ascii_letters + string.digits
        random_chars = "".join(random.choices(chars, k=5))
        special_chars = "!#%@"
        special_char = random.choice(special_chars)
        return f"DevBot{random_chars}{special_char}"

    def create_email(self, user, tries=5):
        """Tạo email mới với kiểm tra trùng"""
        for _ in range(tries):
            j = self.client.create_temp_email(user)
            if j:
                email = j["email"]
                # Kiểm tra email đã tồn tại trong file acc.txt chưa
                if self.is_email_used(email):
                    print(f"Email {email} đã tồn tại trong acc.txt, dừng luồng hiện tại")
                    return None  # Trả về None để dừng luồng
                return j
        return None

    def switch_to_frame_with(self, css_selector: str) -> bool:
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            self.driver.switch_to.frame(frame)
            if self.driver.find_elements(By.CSS_SELECTOR, css_selector):
                return True
            self.driver.switch_to.default_content()
        return False

    def check_success(self):
        """Kiểm tra xem đã chuyển đến trang thành công chưa và lưu tài khoản nếu thành công"""
        try:
            current_url = self.driver.current_url
            if "member.bro.game/sign-up/success" in current_url:
                print("Đăng ký thành công!")
                return True
            return False
        except:
            return False

    def save_account_immediately(self, email, password):
        """Lưu tài khoản ngay lập tức vào file"""
        try:
            with open("acc.txt", "a", encoding="utf-8") as f:
                f.write(f"{email}|{password}\n")
            print("\n" + "="*50)
            print(f"🎉 TẠO TÀI KHOẢN THÀNH CÔNG!")
            print(f"📧 Email: {email}")
            print(f"🔑 Password: {password}")
            print("="*50 + "\n")
            return True
        except Exception as e:
            print(f"Lỗi khi lưu tài khoản: {str(e)}")
            # Thử lưu vào file backup
            try:
                with open("acc_backup.txt", "a", encoding="utf-8") as f:
                    f.write(f"{email}|{password}\n")
                print(f"Đã lưu tài khoản vào file backup: {email}")
                return True
            except:
                print("Không thể lưu vào cả file chính và file backup!")
                return False

    def wait_for_verification_email(self, mail_id, timeout=60):
        """Đợi và lấy email xác minh"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Lấy danh sách email mới
                messages = self.client.get_message_list(mail_id)
                if not messages or not messages.get("items"):
                    time.sleep(2)
                    continue
                
                # Tìm email xác minh
                for msg in messages["items"]:
                    if msg.get("from") == "no-reply@auth0user.net" and "Verify Your Account" in msg.get("subject", ""):
                        print("Đã tìm thấy email xác minh!")
                        # Đọc nội dung email để lấy link
                        message_id = msg.get("id")
                        if message_id:
                            email_content = self.client.read_message(message_id)
                            if email_content:
                                return email_content
                
                time.sleep(2)
            except Exception as e:
                print(f"Lỗi khi kiểm tra email: {str(e)}")
                time.sleep(2)
        
        print("Không tìm thấy email xác minh sau thời gian chờ")
        return None

    def verify_email(self, verification_url):
        """Xác minh email bằng cách mở link trong email"""
        try:
            # Mở link xác minh trong tab mới
            self.driver.execute_script(f"window.open('{verification_url}', '_blank');")
            time.sleep(2)
            
            # Chuyển sang tab mới
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(5)
            
            # Kiểm tra xác minh thành công
            if "success" in self.driver.current_url.lower():
                print("Xác minh email thành công!")
                return True
            else:
                print("Xác minh email không thành công")
                return False
                
        except Exception as e:
            print(f"Lỗi khi xác minh email: {str(e)}")
            return False
        finally:
            # Đóng tab xác minh và quay lại tab chính
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

    def move_mouse_human_like(self):
        """Di chuyển chuột giống người thật trên trang web"""
        try:
            # Lấy kích thước cửa sổ trình duyệt
            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']
            
            # Tạo các điểm di chuyển ngẫu nhiên
            num_points = random.randint(3, 6)  # Số điểm di chuyển ngẫu nhiên
            points = []
            for _ in range(num_points):
                x = random.randint(0, width)
                y = random.randint(0, height)
                points.append((x, y))
            
            # Di chuyển chuột qua các điểm với tốc độ và đường cong tự nhiên
            actions = ActionChains(self.driver)
            for i, (x, y) in enumerate(points):
                # Thêm độ trễ ngẫu nhiên giữa các chuyển động
                delay = random.uniform(0.1, 0.3)
                actions.pause(delay)
                
                # Di chuyển với tốc độ không đều
                if i == 0:
                    actions.move_by_offset(x, y)
                else:
                    # Tạo đường cong Bezier đơn giản
                    prev_x, prev_y = points[i-1]
                    control_x = (prev_x + x) / 2 + random.randint(-50, 50)
                    control_y = (prev_y + y) / 2 + random.randint(-50, 50)
                    
                    # Di chuyển theo đường cong
                    steps = random.randint(10, 20)
                    for step in range(steps):
                        t = step / steps
                        # Công thức Bezier bậc 2
                        current_x = (1-t)**2 * prev_x + 2*(1-t)*t * control_x + t**2 * x
                        current_y = (1-t)**2 * prev_y + 2*(1-t)*t * control_y + t**2 * y
                        actions.move_by_offset(current_x - prev_x, current_y - prev_y)
                        prev_x, prev_y = current_x, current_y
                
                # Thêm độ trễ ngẫu nhiên sau mỗi chuyển động
                actions.pause(random.uniform(0.05, 0.15))
            
            actions.perform()
            time.sleep(random.uniform(0.5, 1.0))  # Dừng ngẫu nhiên sau khi di chuyển
            
        except Exception as e:
            print(f"Lỗi khi di chuyển chuột: {str(e)}")

    def run(self):
        try:
            self._setup_driver()
            drv = self.driver
            drv.get(BASE_URL)

            profile = self.fake_profile()
            email_info = self.create_email(self.generate_username())
            
            if not email_info:
                print("Email đã tồn tại hoặc không thể tạo email mới")
                return None
            
            email = email_info["email"]
            mail_id = email_info["id"]
            pwd = self.generate_password()

            print(f"\nĐang tạo tài khoản với email: {email}")

            # --- Refcode ---
            self.type("refcode", "brogame")
            self.click("submit_code")
            
            #---- Email -----
            self.wait_for("register")
            self.type("email", email)
            self.click("register")
            
            # --- Personal Info ---
            try:
                self.type("first_name", profile["first_name"])
                self.type("last_name", profile["last_name"])
                
                # Click vào country dropdown
                country_dropdown = self.driver.find_element(By.CSS_SELECTOR, "div.ant-select-selector")
                country_dropdown.click()
                time.sleep(1)
                
                # Chọn Thailand
                thailand = self.driver.find_element(By.XPATH, "//div[contains(@class, 'ant-select-item-option-content') and contains(text(), 'Thailand')]")
                thailand.click()
                time.sleep(1)
                
                phone = "816" + str(random.randint(100000, 999999))
                self.type("tel", phone)
                
                self.type("password", pwd)
                self.type("confirm_password", pwd)
                
                self.click("confirm")
            except Exception as e:
                print(f"Lỗi khi nhập thông tin cá nhân: {str(e)}")
                self.driver.save_screenshot("error_personal_info.png")
                raise
            
            #---- Add thẻ -----
            try:
                # Di chuyển chuột ngẫu nhiên trước khi nhập thông tin thẻ
                self.move_mouse_human_like()
                
                # Lấy thẻ ngẫu nhiên từ file
                card = get_random_card("cards.txt")
                if card["name"]:
                    full_name = card["name"]
                else:
                    full_name = f"{profile['first_name']} {profile['last_name']}"
                
                self.type("card_name", full_name)
                
                # Di chuyển chuột ngẫu nhiên trước khi nhập số thẻ
                self.move_mouse_human_like()
                
                # Chuyển sang iframe của Stripe
                self.switch_to_frame("stripe_iframe")
                time.sleep(1)
                
                # Nhập số thẻ
                card_number = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#Field-numberInput")))
                card_number.clear()
                time.sleep(0.5)
                
                for digit in card["number"]:
                    card_number.send_keys(digit)
                    time.sleep(0.1)
                
                # Chuyển về main frame
                self.driver.switch_to.default_content()
                time.sleep(1)
                
                # Di chuyển chuột ngẫu nhiên trước khi nhập ngày hết hạn
                self.move_mouse_human_like()
                
                # Tìm và thử từng iframe để nhập ngày hết hạn
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                found_expiry = False
                for idx, frame in enumerate(iframes):
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(frame)
                    try:
                        expiry_input = self.driver.find_element(By.CSS_SELECTOR, "input#Field-expiryInput")
                        expiry_input.clear()
                        time.sleep(0.5)
                        for digit in card["expiry"]:
                            expiry_input.send_keys(digit)
                            time.sleep(0.3)
                        print(f"Đã nhập ngày hết hạn ở iframe số {idx}")
                        found_expiry = True
                        break
                    except Exception as e:
                        continue

                self.driver.switch_to.default_content()
                time.sleep(1)

                if not found_expiry:
                    print("Không tìm thấy input ngày hết hạn trong bất kỳ iframe nào!")
                    self.driver.save_screenshot("error_expiry_input.png")
                    raise Exception("Không tìm thấy input ngày hết hạn")
                
                # Di chuyển chuột ngẫu nhiên trước khi nhập CVC
                self.move_mouse_human_like()
                
                # Tìm và thử từng iframe để nhập CVC
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                found_cvc = False
                for idx, frame in enumerate(iframes):
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(frame)
                    try:
                        cvc_input = self.driver.find_element(By.CSS_SELECTOR, "input#Field-cvcInput")
                        cvc_input.clear()
                        time.sleep(0.5)
                        for digit in card["cvc"]:
                            cvc_input.send_keys(digit)
                            time.sleep(0.2)
                        print(f"Đã nhập CVC ở iframe số {idx}")
                        found_cvc = True
                        break
                    except Exception as e:
                        continue

                self.driver.switch_to.default_content()
                time.sleep(1)

                if not found_cvc:
                    print("Không tìm thấy input CVC trong bất kỳ iframe nào!")
                    self.driver.save_screenshot("error_cvc_input.png")
                    raise Exception("Không tìm thấy input CVC")
                
                # Di chuyển chuột ngẫu nhiên trước khi xác nhận thanh toán
                self.move_mouse_human_like()
                
                time.sleep(2)
                self.click("confirm_payment")
                
                # Tăng thời gian chờ URL thành công lên 10s
                start_time = time.time()
                while time.time() - start_time < 10:
                    current_url = self.driver.current_url
                    if "member.bro.game/sign-up/success" in current_url:
                        # Lưu tài khoản ngay khi phát hiện URL thành công
                        if self.save_account_immediately(email, pwd):
                            result = {
                                "Email": email,
                                "Password": pwd
                            }
                            drv.quit()
                            return result
                        else:
                            print("Không thể lưu tài khoản, đóng driver")
                            drv.quit()
                            return None
                    time.sleep(0.5)
                
                print(f"\n❌ Tạo tài khoản thất bại cho email: {email}")
                drv.quit()
                return None
                
            except Exception as e:
                print(f"Lỗi chi tiết khi xử lý thanh toán: {str(e)}")
                self.driver.save_screenshot("error_payment.png")
                if hasattr(self, 'driver'):
                    self.driver.quit()
                return None
            
        except Exception as e:
            print(f"Lỗi trong quá trình chạy bot: {str(e)}")
            if hasattr(self, 'driver'):
                try:
                    self.driver.save_screenshot("error_bot_run.png")
                    self.driver.quit()
                except:
                    pass
            return None

    def exit(self):
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass

    def save_result(self, result):
        """Lưu kết quả với lock để tránh ghi đè"""
        if not result:
            return
            
        with self.lock:
            try:
                # Đọc toàn bộ nội dung file hiện tại
                existing_accounts = set()
                if os.path.exists("acc.txt"):
                    with open("acc.txt", "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                existing_accounts.add(line.strip())
                
                # Thêm tài khoản mới
                new_account = f"{result['Email']}|{result['Password']}"
                if new_account not in existing_accounts:
                    # Ghi lại toàn bộ nội dung cũ và thêm mới
                    with open("acc.txt", "w", encoding="utf-8") as f:
                        for acc in existing_accounts:
                            f.write(f"{acc}\n")
                        f.write(f"{new_account}\n")
                    
                    print("\n" + "="*50)
                    print(f"🎉 TẠO TÀI KHOẢN THÀNH CÔNG!")
                    print(f"📧 Email: {result['Email']}")
                    print(f"🔑 Password: {result['Password']}")
                    print("="*50 + "\n")
                    
                    # Thêm vào danh sách đã sử dụng
                    self.add_used_email(result["Email"])
                    
                    # Thêm vào kết quả
                    self.results.append(result)
                else:
                    print(f"\n⚠️ Tài khoản {result['Email']} đã tồn tại trong file")
            except Exception as e:
                print(f"Lỗi khi lưu file: {str(e)}")
                # Thử lưu vào file backup nếu lưu chính thất bại
                try:
                    with open("acc_backup.txt", "a", encoding="utf-8") as f:
                        f.write(f"{result['Email']}|{result['Password']}\n")
                    print(f"Đã lưu tài khoản vào file backup: {result['Email']}")
                except:
                    print("Không thể lưu vào cả file chính và file backup!")

class BotManager:
    def __init__(self, token, num_threads=1, chromedriver="driver/chromedriver.exe", headless_mode=False):
        self.token = token
        self.num_threads = num_threads
        self.chromedriver = chromedriver
        self.results = []
        self.lock = threading.Lock()
        self.headless_mode = bool(headless_mode)
        self.bots = []
        
        # Thêm các biến để quản lý email
        self.email_lock = threading.Lock()
        self.used_emails = set()
        self.email_queue = queue.Queue()
        self.load_used_emails()
        
    def load_used_emails(self):
        """Load danh sách email đã sử dụng từ file acc.txt"""
        try:
            if Path("acc.txt").exists():
                with open("acc.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            email = line.split("|")[0].strip()
                            self.used_emails.add(email)
                print(f"Đã load {len(self.used_emails)} email đã sử dụng")
        except Exception as e:
            print(f"Lỗi khi load email: {str(e)}")

    def is_email_used(self, email):
        """Kiểm tra email đã được sử dụng chưa"""
        with self.email_lock:
            is_used = email in self.used_emails
            print(f"Kiểm tra email {email}: {'đã tồn tại' if is_used else 'chưa tồn tại'}")
            return is_used

    def add_used_email(self, email):
        """Thêm email vào danh sách đã sử dụng"""
        with self.email_lock:
            print(f"Thêm email {email} vào danh sách đã sử dụng")
            self.used_emails.add(email)

    def run_bot(self, thread_index):
        try:
            print(f"Debug - Creating bot with headless_mode: {self.headless_mode}")
            print(f"Khởi tạo bot mới (luồng {thread_index + 1})...")
            bot = Bot(self.token, self.chromedriver, headless_mode=self.headless_mode)
            bot.thread_index = thread_index
            bot.num_threads = self.num_threads
            
            # Thêm các hàm kiểm tra email cho bot
            bot.is_email_used = self.is_email_used
            bot.add_used_email = self.add_used_email
            
            with self.lock:
                self.bots.append(bot)
            print(f"Bắt đầu chạy bot (luồng {thread_index + 1})...")
            result = bot.run()
            if result:
                # Không cần gọi save_result ở đây nữa vì đã lưu trong run()
                pass
            else:
                print(f"Bot (luồng {thread_index + 1}) tạo tài khoản thất bại")
                # Tạo luồng mới thay thế
                print(f"Tạo luồng mới thay thế cho luồng {thread_index + 1}")
                self.run_bot(thread_index)
            bot.exit()
        except Exception as e:
            print(f"Lỗi chi tiết trong luồng {thread_index + 1}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            # Tạo luồng mới thay thế khi có lỗi
            print(f"Tạo luồng mới thay thế cho luồng {thread_index + 1} do lỗi")
            self.run_bot(thread_index)

    def start(self):
        print(f"Bắt đầu chạy {self.num_threads} luồng...")
        if self.num_threads == 1:
            self.run_bot(0)
        else:
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                executor.map(self.run_bot, range(self.num_threads))
        
        print(f"Hoàn thành! Đã tạo {len(self.results)} tài khoản thành công.")
        return self.results

    def exit(self):
        for bot in self.bots:
            try:
                bot.exit()
            except:
                pass
        self.bots.clear()
        self.results.clear()
