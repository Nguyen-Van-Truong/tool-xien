from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time, string, random, re, threading, queue, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from modules.TempMailClient import TempMailClient
from faker import Faker

BASE_URL = "https://member.bro.game/member/dashboard"
SELECTORS = {
    "email_input": ("css", "input[type='email']"),
    "password_input": ("css", "input[type='password']"),
    "login_button": ("css", "button[type='submit']")
}

class Bot:
    def __init__(self, token, chromedriver: str ="driver/chromedriver.exe", wait_sec=2, timeout=30, headless_mode: bool=False):
        self.token = token
        self.chromedriver = chromedriver
        self.WAIT_SEC = wait_sec
        self.TIMEOUT = timeout
        self.headless_mode = headless_mode
        self.is_email_used = None
        self.add_used_email = None
        self._setup_driver()

    def _setup_driver(self):
        opts = webdriver.ChromeOptions()
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-web-security')
        opts.add_argument('--allow-running-insecure-content')
        opts.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        if self.headless_mode:
            opts.add_argument('--headless=new')
            opts.add_argument('--window-size=1920,1080')
        else:
            opts.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(service=Service(str(self.chromedriver)), options=opts)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)
        self.client = TempMailClient(self.token)

    def _loc(self, key):
        try:
            by, sel = SELECTORS[key]
            return (By.CSS_SELECTOR, sel) if by == "css" else (By.XPATH, sel)
        except Exception as e:
            print(f"Lỗi selector {key}: {str(e)}")
            raise

    def click(self, key):
        try:
            el = self.wait.until(EC.element_to_be_clickable(self._loc(key)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
            try: el.click()
            except: self.driver.execute_script("arguments[0].click();", el)
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
        if not timeout: timeout = self.TIMEOUT
        el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(self._loc(key)))
        sel = Select(el)
        time.sleep(self.WAIT_SEC)
        if by_value is not None: sel.select_by_value(by_value)
        elif by_text is not None: sel.select_by_visible_text(by_text)
        elif by_index is not None: sel.select_by_index(by_index)

    def wait_for(self, key, timeout=None):
        if not timeout: timeout = self.TIMEOUT
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(self._loc(key)))

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
            "last_name": f.last_name(),
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
        for _ in range(tries):
            j = self.client.create_temp_email(user)
            if j:
                email = j["email"]
                if self.is_email_used and self.is_email_used(email):
                    print(f"Email {email} đã tồn tại, thử tạo email khác...")
                    continue
                if self.add_used_email:
                    self.add_used_email(email)
                return j
        return {}

    def switch_to_frame_with(self, css_selector: str) -> bool:
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            self.driver.switch_to.frame(frame)
            if self.driver.find_elements(By.CSS_SELECTOR, css_selector):
                return True
            self.driver.switch_to.default_content()
        return False

    def check_account(self, email, password):
        try:
            self.driver.get(BASE_URL)
            time.sleep(2)
            
            # Kiểm tra xem các element có tồn tại không
            try:
                self.wait_for("email_input")
                self.wait_for("password_input")
                self.wait_for("login_button")
            except Exception as e:
                print(f"Không tìm thấy element: {str(e)}")
                self.driver.save_screenshot("error_elements.png")
                return False

            self.type("email_input", email)
            self.type("password_input", password)
            self.click("login_button")
            
            time.sleep(10)  # Đợi chuyển hướng
            current_url = self.driver.current_url
            
            if "member.bro.game/member/dashboard" in current_url:
                return True
            else:
                # Lưu tài khoản không hợp lệ
                with open("acc_invalid.txt", "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password}\n")
                return False
                
        except Exception as e:
            print(f"Lỗi khi check tài khoản {email}: {str(e)}")
            self.driver.save_screenshot(f"error_{email}.png")
            return False
        finally:
            self.driver.delete_all_cookies()
            self.driver.get(BASE_URL)
            time.sleep(2)

    def exit(self):
        if hasattr(self, 'driver'):
            try: self.driver.quit()
            except: pass

class BotManager:
    def __init__(self, token, num_threads=10, chromedriver="driver/chromedriver.exe", headless_mode=True):
        self.token = token
        self.num_threads = min(num_threads, 10)  # Giới hạn tối đa 10 luồng
        self.chromedriver = chromedriver
        self.results = []
        self.lock = threading.Lock()
        self.headless_mode = bool(headless_mode)
        self.bots = []
        self.account_queue = queue.Queue()
        self.valid_accounts = set()  # Lưu các tài khoản hợp lệ
        self.load_accounts()
        
    def load_accounts(self):
        try:
            with open("acc.txt", "r", encoding="utf-8") as f:
                accounts = [line.strip().split(":") for line in f if line.strip()]
                for account in accounts:
                    self.account_queue.put(account)
            print(f"Đã load {len(accounts)} tài khoản vào queue")
        except Exception as e:
            print(f"Lỗi khi load tài khoản: {str(e)}")

    def save_valid_accounts(self):
        try:
            # Lưu tài khoản hợp lệ vào acc_valid.txt
            with open("acc_valid.txt", "w", encoding="utf-8") as f:
                for email, password in self.valid_accounts:
                    f.write(f"{email}:{password}\n")
            
            # Cập nhật lại acc.txt chỉ với tài khoản hợp lệ
            with open("acc.txt", "w", encoding="utf-8") as f:
                for email, password in self.valid_accounts:
                    f.write(f"{email}:{password}\n")
                    
            print(f"\nĐã lưu {len(self.valid_accounts)} tài khoản hợp lệ")
            print(f"Đã xóa {self.account_queue.qsize()} tài khoản không hợp lệ khỏi acc.txt")
        except Exception as e:
            print(f"Lỗi khi lưu tài khoản: {str(e)}")

    def run_bot(self, thread_index):
        try:
            bot = Bot(self.token, self.chromedriver, headless_mode=self.headless_mode)
            with self.lock: self.bots.append(bot)
            
            while not self.account_queue.empty():
                try:
                    email, password = self.account_queue.get()
                    print(f"Luồng {thread_index + 1} đang xử lý tài khoản: {email}")
                    
                    success = bot.check_account(email, password)
                    if success:
                        print(f"✅ Luồng {thread_index + 1}: Tài khoản {email} hợp lệ")
                        with self.lock:
                            self.valid_accounts.add((email, password))
                    else:
                        print(f"❌ Luồng {thread_index + 1}: Tài khoản {email} không hợp lệ")
                        
                except Exception as e:
                    print(f"Lỗi khi xử lý tài khoản trong luồng {thread_index + 1}: {str(e)}")
                    continue
                finally:
                    self.account_queue.task_done()
            
            bot.exit()
            
        except Exception as e:
            print(f"Lỗi chi tiết trong luồng {thread_index + 1}: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def start(self):
        print(f"Bắt đầu chạy {self.num_threads} luồng...")
        if self.num_threads == 1:
            self.run_bot(0)
        else:
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                executor.map(self.run_bot, range(self.num_threads))
        
        # Sau khi tất cả các luồng hoàn thành, lưu kết quả
        self.save_valid_accounts()
        print("Hoàn thành kiểm tra tài khoản!")
        return True

    def exit(self):
        for bot in self.bots:
            try: bot.exit()
            except: pass
        self.bots.clear()
        self.results.clear()
