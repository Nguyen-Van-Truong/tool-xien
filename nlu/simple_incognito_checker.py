#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class SimpleIncognitoChecker:
    def __init__(self):
        self.driver = None
        self.screenshot_counter = 0
        self.account_results = []
        
    def log(self, message, level="INFO"):
        """Log với timestamp và level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "🔵",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "STEP": "🎯"
        }
        icon = colors.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")
    
    def setup_incognito_driver(self):
        """Thiết lập Chrome driver ẩn danh"""
        self.log("🔧 Thiết lập Chrome driver ẩn danh...", "STEP")
        
        try:
            chrome_options = Options()
            # Chế độ ẩn danh
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            # Tắt thông báo save password
            chrome_options.add_argument('--disable-save-password-bubble')
            # Tắt các thông báo khác
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-infobars')
            
            # Load extensions nếu có
            if os.path.exists('driver/1.crx'):
                chrome_options.add_extension('driver/1.crx')
            if os.path.exists('driver/captchasolver.crx'):
                chrome_options.add_extension('driver/captchasolver.crx')
            
            chrome_service = Service('driver/chromedriver.exe')
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            
            # Ẩn automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.log("✅ Chrome driver ẩn danh đã sẵn sàng", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi khởi tạo Chrome driver: {e}", "ERROR")
            return False
    
    def close_driver(self):
        """Đóng driver"""
        try:
            if self.driver:
                self.log("🔒 Đóng trình duyệt...", "INFO")
                self.driver.quit()
                self.driver = None
                self.log("✅ Đã đóng trình duyệt", "SUCCESS")
        except Exception as e:
            self.log(f"Lỗi đóng trình duyệt: {e}", "ERROR")
    
    def take_screenshot_and_analyze(self, step_name, analyze=True):
        """Chụp ảnh màn hình và tự đánh giá tình huống"""
        try:
            self.screenshot_counter += 1
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f"screenshot_{self.screenshot_counter:02d}_{step_name}_{timestamp}.png"
            
            # Chụp ảnh
            self.driver.save_screenshot(filename)
            self.log(f"📸 Screenshot saved: {filename}")
            
            if not analyze:
                return filename
                
            # Tự đánh giá tình huống
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.log(f"🔍 URL hiện tại: {current_url}")
            self.log(f"📄 Tiêu đề trang: {page_title}")
            
            # Phân tích các elements có mặt
            analysis = self.analyze_page_elements()
            self.log(f"🧠 Phân tích trang: {analysis}")
            
            return filename, analysis
            
        except Exception as e:
            self.log(f"Lỗi chụp ảnh: {e}", "ERROR")
            return None
    
    def analyze_page_elements(self):
        """Phân tích các elements trên trang để xác định chính xác tình trạng"""
        try:
            analysis = {
                "login_success": False,
                "new_account_need_password_change": False,
                "wrong_password": False,
                "email_field": False,
                "password_field": False,
                "error_messages": [],
                "special_elements": []
            }
            
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url
            
            # 1. Kiểm tra ĐĂNG NHẬP THÀNH CÔNG - có popup "Your organization will manage this profile"
            try:
                org_manage_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Your organization will manage this profile')]")
                if org_manage_elements:
                    analysis["login_success"] = True
                    analysis["special_elements"].append("organization_manage_popup")
                    self.log("🎉 PHÁT HIỆN ĐĂNG NHẬP THÀNH CÔNG: Popup organization manage", "SUCCESS")
                    return analysis
            except:
                pass
            
            # Kiểm tra URL thành công khác
            success_urls = ["myaccount.google.com", "accounts.google.com/b/", "/ManageAccount", "accounts.google.com/signin/oauth"]
            if any(url in current_url for url in success_urls):
                analysis["login_success"] = True
                analysis["special_elements"].append("success_url")
                self.log("🎉 PHÁT HIỆN ĐĂNG NHẬP THÀNH CÔNG: URL", "SUCCESS")
                return analysis
            
            # 2. Kiểm tra TÀI KHOẢN MỚI CẦN ĐỔI PASSWORD
            # Các từ khóa và patterns cho tài khoản mới
            new_account_keywords = [
                "change your password", "update your password", "set up your account",
                "first time signing in", "account setup", "password requirements", 
                "create a new password", "password policy", "choose a password",
                "welcome to your google account", "set up", "getting started",
                "security check", "verify", "phone number"
            ]
            
            for keyword in new_account_keywords:
                if keyword in page_source:
                    analysis["new_account_need_password_change"] = True
                    analysis["special_elements"].append(f"new_account_keyword: {keyword}")
                    self.log(f"🆕 PHÁT HIỆN TÀI KHOẢN MỚI: {keyword}", "WARNING")
                    return analysis
            
            # Kiểm tra URL cho tài khoản mới/cần xác minh
            new_account_urls = ["challenge", "setup", "welcome", "first", "recovery", "verify"]
            if any(url in current_url for url in new_account_urls):
                analysis["new_account_need_password_change"] = True
                analysis["special_elements"].append(f"new_account_url")
                self.log(f"🆕 PHÁT HIỆN TÀI KHOẢN MỚI: URL pattern", "WARNING")
                return analysis
            
            # 3. Kiểm tra SAI PASSWORD
            wrong_password_keywords = [
                "wrong password", "incorrect password", "try again", 
                "forgot password", "password incorrect", "invalid password",
                "couldn't sign you in", "password didn't match",
                "enter a correct password", "sign-in failed"
            ]
            
            for keyword in wrong_password_keywords:
                if keyword in page_source:
                    analysis["wrong_password"] = True
                    analysis["error_messages"].append(f"wrong_password: {keyword}")
                    self.log(f"❌ PHÁT HIỆN SAI PASSWORD: {keyword}", "ERROR")
                    return analysis
            
            # Kiểm tra elements cho sai password
            try:
                error_selectors = [
                    "[role='alert']",
                    ".error-message", 
                    ".Ekjuhf",  # Google error class
                    "[data-error='true']",
                    "//div[contains(@class, 'error')]",
                    "//div[contains(@class, 'LXRPh')]"  # Google error class khác
                ]
                
                for selector in error_selectors:
                    try:
                        if selector.startswith("//"):
                            errors = self.driver.find_elements(By.XPATH, selector)
                        else:
                            errors = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for error in errors:
                            if error.text and error.text.strip():
                                error_text = error.text.strip().lower()
                                if any(keyword in error_text for keyword in ["wrong", "incorrect", "try again", "password"]):
                                    analysis["wrong_password"] = True
                                    analysis["error_messages"].append(error_text)
                                    self.log(f"❌ PHÁT HIỆN SAI PASSWORD: {error_text}", "ERROR")
                                    return analysis
                    except:
                        continue
            except:
                pass
            
            # Kiểm tra các fields cơ bản
            try:
                email_field = self.driver.find_element(By.ID, "identifierId")
                analysis["email_field"] = True
            except:
                pass
            
            try:
                password_fields = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
                if password_fields:
                    analysis["password_field"] = True
            except:
                pass
            
            return analysis
            
        except Exception as e:
            self.log(f"Lỗi phân tích trang: {e}", "ERROR")
            return {}
    
    def handle_success_popup(self):
        """Xử lý popup khi đăng nhập thành công - bấm Cancel để tiếp tục"""
        try:
            self.log("🎯 Tìm và xử lý popup đăng nhập thành công...", "STEP")
            
            # Tìm nút Cancel
            cancel_selectors = [
                "//button[contains(text(), 'Cancel')]",
                "//button[contains(text(), 'Hủy')]", 
                "//button[@id='cancel']",
                "//*[@role='button' and contains(text(), 'Cancel')]",
                "//span[contains(text(), 'Cancel')]//parent::button"
            ]
            
            for selector in cancel_selectors:
                try:
                    wait = WebDriverWait(self.driver, 5)
                    cancel_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if cancel_button:
                        self.log(f"🖱️ Tìm thấy nút Cancel, đang click...", "INFO")
                        cancel_button.click()
                        time.sleep(2)
                        self.log("✅ Đã click Cancel thành công", "SUCCESS")
                        return True
                except:
                    continue
            
            self.log("⚠️ Không tìm thấy nút Cancel", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Lỗi xử lý popup: {e}", "ERROR")
            return False
    
    def load_first_3_accounts(self):
        """Tải 3 tài khoản đầu tiên"""
        self.log("📚 Tải 3 tài khoản đầu tiên...", "STEP")
        
        try:
            with open("students_accounts.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            accounts = []
            for i, line in enumerate(lines[:3]):
                line = line.strip()
                if '|' in line:
                    username, password = line.split('|', 1)
                    accounts.append((username.strip(), password.strip(), i+1))
            
            self.log(f"Đã tải {len(accounts)} tài khoản đầu tiên", "SUCCESS")
            for i, (username, password, index) in enumerate(accounts):
                self.log(f"TK {index}: {username}", "INFO")
            
            return accounts
            
        except Exception as e:
            self.log(f"Lỗi tải tài khoản: {e}", "ERROR")
            return []
    
    def smart_wait_and_find(self, selectors, timeout=20, description="element"):
        """Tìm element thông minh"""
        for by, selector in selectors:
            try:
                self.log(f"Tìm {description} với: {selector}")
                wait = WebDriverWait(self.driver, timeout // len(selectors))
                element = wait.until(EC.presence_of_element_located((by, selector)))
                if element and element.is_displayed():
                    self.log(f"✅ Tìm thấy {description}", "SUCCESS")
                    return element
            except TimeoutException:
                continue
            except Exception as e:
                self.log(f"Lỗi tìm {description}: {e}", "WARNING")
                continue
        
        self.log(f"❌ Không tìm thấy {description}", "ERROR")
        return None
    
    def smart_input_text(self, element, text, description="text"):
        """Nhập text thông minh"""
        self.log(f"📝 Nhập {description}...")
        
        methods = [
            ("Clear và type", self._method_clear_and_type),
            ("JS clear và type", self._method_js_clear_and_type),
            ("Select all và type", self._method_select_all_and_type),
            ("Action chains", self._method_action_chains)
        ]
        
        for method_name, method_func in methods:
            try:
                self.log(f"Thử phương pháp: {method_name}")
                if method_func(element, text):
                    self.log(f"✅ Nhập {description} thành công với {method_name}", "SUCCESS")
                    return True
            except Exception as e:
                self.log(f"Phương pháp {method_name} thất bại: {e}", "WARNING")
                continue
        
        self.log(f"❌ Tất cả phương pháp nhập {description} đều thất bại", "ERROR")
        return False
    
    def _method_clear_and_type(self, element, text):
        element.clear()
        time.sleep(0.5)
        element.send_keys(text)
        return element.get_attribute('value') == text
    
    def _method_js_clear_and_type(self, element, text):
        self.driver.execute_script("arguments[0].value = '';", element)
        time.sleep(0.5)
        element.send_keys(text)
        return element.get_attribute('value') == text
    
    def _method_select_all_and_type(self, element, text):
        element.click()
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.2)
        element.send_keys(text)
        return element.get_attribute('value') == text
    
    def _method_action_chains(self, element, text):
        actions = ActionChains(self.driver)
        actions.click(element)
        actions.key_down(Keys.CONTROL)
        actions.send_keys("a")
        actions.key_up(Keys.CONTROL)
        actions.send_keys(text)
        actions.perform()
        time.sleep(0.5)
        return element.get_attribute('value') == text
    
    def smart_click(self, element, description="element"):
        """Click thông minh"""
        self.log(f"🖱️ Click {description}...")
        
        methods = [
            ("Normal click", lambda el: el.click()),
            ("JS click", lambda el: self.driver.execute_script("arguments[0].click();", el)),
            ("Action chains click", lambda el: ActionChains(self.driver).click(el).perform()),
            ("Scroll và click", self._method_scroll_and_click)
        ]
        
        for method_name, method_func in methods:
            try:
                self.log(f"Thử click với: {method_name}")
                method_func(element)
                time.sleep(1)
                self.log(f"✅ Click {description} thành công với {method_name}", "SUCCESS")
                return True
            except Exception as e:
                self.log(f"Click {method_name} thất bại: {e}", "WARNING")
                continue
        
        self.log(f"❌ Tất cả phương pháp click {description} đều thất bại", "ERROR")
        return False
    
    def _method_scroll_and_click(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        element.click()
    
    def test_single_account(self, username, password, account_index):
        """Test một tài khoản"""
        print("\n" + "="*120)
        self.log(f"🧪 BẮT ĐẦU TEST TÀI KHOẢN {account_index}: {username}", "STEP")
        print("="*120)
        
        account_result = {
            "index": account_index,
            "username": username, 
            "password": password,
            "status": "unknown",
            "description": "Chưa xác định được tình trạng"
        }
        
        try:
            # Bước 1: Mở trang đăng nhập
            self.log("🌐 Mở trang đăng nhập Google...", "STEP")
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(3)
            
            self.take_screenshot_and_analyze(f"01_login_page_acc{account_index}")
            
            # Bước 2: Nhập email
            self.log("📧 Tìm và nhập email...", "STEP")
            
            email_selectors = [
                (By.ID, "identifierId"),
                (By.NAME, "identifier"),
                (By.CSS_SELECTOR, 'input[type="email"]')
            ]
            
            email_input = self.smart_wait_and_find(email_selectors, description="ô email")
            if not email_input:
                self.take_screenshot_and_analyze(f"02_email_not_found_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không tìm thấy ô nhập email"
                return account_result
            
            if not self.smart_input_text(email_input, username, f"email {username}"):
                self.take_screenshot_and_analyze(f"03_email_input_failed_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không thể nhập email"
                return account_result
            
            self.take_screenshot_and_analyze(f"04_email_entered_acc{account_index}")
            
            # Bước 3: Click Next email
            self.log("➡️ Click Next email...", "STEP")
            
            next_selectors = [
                (By.ID, "identifierNext"),
                (By.CSS_SELECTOR, '[data-id="identifierNext"]'),
                (By.XPATH, "//span[text()='Next']//parent::button"),
                (By.XPATH, "//span[text()='Tiếp theo']//parent::button")
            ]
            
            next_button = self.smart_wait_and_find(next_selectors, description="nút Next email")
            if not next_button:
                self.take_screenshot_and_analyze(f"05_next_button_not_found_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không tìm thấy nút Next"
                return account_result
            
            if not self.smart_click(next_button, "Next email"):
                self.take_screenshot_and_analyze(f"06_next_click_failed_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không thể click nút Next"
                return account_result
            
            # Chờ và kiểm tra trang password
            self.log("⏳ Chờ trang password...", "INFO")
            time.sleep(5)
            
            self.take_screenshot_and_analyze(f"07_after_email_next_acc{account_index}")
            
            # Bước 4: Tìm và nhập password
            self.log("🔐 Tìm và nhập password...", "STEP")
            
            password_selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.XPATH, "//input[@name='password']"),
                (By.XPATH, "//input[@type='password']"),
                (By.ID, "password")
            ]
            
            password_input = self.smart_wait_and_find(password_selectors, timeout=15, description="ô password")
            if not password_input:
                self.take_screenshot_and_analyze(f"08_password_not_found_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không tìm thấy ô nhập password"
                return account_result
            
            if not self.smart_input_text(password_input, password, f"password"):
                self.take_screenshot_and_analyze(f"09_password_input_failed_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không thể nhập password"
                return account_result
            
            self.take_screenshot_and_analyze(f"10_password_entered_acc{account_index}")
            
            # Bước 5: Click Next password
            self.log("➡️ Click Next password...", "STEP")
            
            password_next_selectors = [
                (By.ID, "passwordNext"),
                (By.CSS_SELECTOR, '[data-id="passwordNext"]'),
                (By.XPATH, "//span[text()='Next']//parent::button"),
                (By.XPATH, "//span[text()='Tiếp theo']//parent::button")
            ]
            
            password_next = self.smart_wait_and_find(password_next_selectors, description="nút Next password")
            if not password_next:
                self.take_screenshot_and_analyze(f"11_password_next_not_found_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không tìm thấy nút Next password"
                return account_result
            
            if not self.smart_click(password_next, "Next password"):
                self.take_screenshot_and_analyze(f"12_password_next_failed_acc{account_index}")
                account_result["status"] = "error"
                account_result["description"] = "Không thể click nút Next password"
                return account_result
            
            # Bước 6: Phân tích kết quả
            self.log("⏳ Chờ và phân tích kết quả...", "STEP")
            time.sleep(8)
            
            filename, analysis = self.take_screenshot_and_analyze(f"13_final_result_acc{account_index}", analyze=True)
            
            # Xác định trạng thái
            if analysis.get("login_success"):
                self.log("🎉 ĐĂNG NHẬP THÀNH CÔNG!", "SUCCESS")
                account_result["status"] = "login_success"
                account_result["description"] = "Đăng nhập thành công - Tài khoản hoạt động bình thường"
                
                # Xử lý popup thành công
                self.handle_success_popup()
                
            elif analysis.get("new_account_need_password_change"):
                self.log("🆕 TÀI KHOẢN MỚI CẦN ĐỔI PASSWORD!", "WARNING")
                account_result["status"] = "new_account"
                account_result["description"] = "Tài khoản mới chưa kích hoạt - Cần đổi mật khẩu lần đầu"
                
            elif analysis.get("wrong_password"):
                self.log("❌ SAI PASSWORD!", "ERROR")
                account_result["status"] = "wrong_password"
                account_result["description"] = "Sai mật khẩu - Cần kiểm tra lại thông tin đăng nhập"
                
            else:
                # Fallback analysis
                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()
                
                if any(indicator in current_url for indicator in ["myaccount", "oauth", "ManageAccount"]):
                    account_result["status"] = "login_success"
                    account_result["description"] = "Đăng nhập thành công (xác định qua URL)"
                elif any(keyword in page_source for keyword in ["wrong", "incorrect", "try again"]):
                    account_result["status"] = "wrong_password"
                    account_result["description"] = "Sai mật khẩu (xác định qua page source)"
                elif "challenge" in current_url or "setup" in current_url or "verify" in current_url:
                    account_result["status"] = "new_account"
                    account_result["description"] = "Tài khoản mới cần xác minh (xác định qua URL)"
                else:
                    account_result["status"] = "unknown"
                    account_result["description"] = "Không thể xác định được tình trạng cụ thể"
            
            return account_result
            
        except Exception as e:
            self.log(f"❌ LỖI TỔNG QUÁT: {e}", "ERROR")
            self.take_screenshot_and_analyze(f"14_general_error_acc{account_index}")
            account_result["status"] = "error"
            account_result["description"] = f"Lỗi hệ thống: {str(e)}"
            return account_result
    
    def run_simple_incognito_test(self):
        """Chạy test với Chrome driver ẩn danh, đóng mở trình duyệt giữa các tài khoản"""
        print("🚀 TEST 3 TÀI KHOẢN - CHROME DRIVER ẨN DANH")
        print("="*80)
        print("🕵️ Sử dụng Chrome driver ẩn danh (incognito)")
        print("🔄 Đóng và mở lại trình duyệt giữa các tài khoản")
        print("⏱️ Thời gian nghỉ giữa các tài khoản: 5s")
        print("✅ Đăng nhập thành công | 🆕 Tài khoản mới | ❌ Sai password")
        print("="*80)
        
        accounts = self.load_first_3_accounts()
        if not accounts:
            return
        
        try:
            for username, password, account_index in accounts:
                print(f"\n{'='*120}")
                self.log(f"🎯 BẮT ĐẦU TEST TÀI KHOẢN {account_index}/3: {username}", "STEP")
                print("="*120)
                
                # Tạo driver mới cho mỗi tài khoản
                if not self.setup_incognito_driver():
                    account_result = {
                        "index": account_index,
                        "username": username,
                        "password": password,
                        "status": "error",
                        "description": "Không thể tạo trình duyệt ẩn danh"
                    }
                    self.account_results.append(account_result)
                    continue
                
                # Test tài khoản
                account_result = self.test_single_account(username, password, account_index)
                self.account_results.append(account_result)
                
                # Đóng driver sau mỗi tài khoản
                self.close_driver()
                
                status_icon = {
                    "login_success": "✅",
                    "new_account": "🆕",
                    "wrong_password": "❌",
                    "error": "💥",
                    "unknown": "❓"
                }.get(account_result["status"], "❓")
                
                print(f"\n{status_icon} KẾT QUẢ TÀI KHOẢN {account_index}:")
                print(f"   📧 Email: {username}")
                print(f"   📊 Trạng thái: {account_result['status']}")
                print(f"   📝 Mô tả: {account_result['description']}")
                
                # Nghỉ giữa các tài khoản
                if account_index < 3:
                    self.log(f"⏸️ Nghỉ 5s trước tài khoản {account_index+1}...", "INFO")
                    time.sleep(5)
            
            self.create_final_accstatus_report()
            input("\n⏸️ Nhấn Enter để thoát...")
            
        except KeyboardInterrupt:
            self.log("⚠️ Dừng test bởi người dùng", "WARNING")
            self.close_driver()
            self.create_final_accstatus_report()
        except Exception as e:
            self.log(f"❌ Lỗi tổng quát: {e}", "ERROR")
            self.close_driver()
    
    def create_final_accstatus_report(self):
        """Tạo file accstatus.txt cuối cùng với kết quả chính xác"""
        self.log("📄 Tạo file accstatus.txt cuối cùng...", "STEP")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Tạo file accstatus.txt
            with open("accstatus.txt", "w", encoding="utf-8") as f:
                f.write("# TÌNH TRẠNG 3 TÀI KHOẢN ĐẦU TIÊN - CHROME DRIVER ẨN DANH\n")
                f.write(f"# Thời gian kiểm tra: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Tool: simple_incognito_checker.py\n")
                f.write(f"# Phương pháp: Chrome driver ẩn danh, đóng mở giữa tài khoản\n\n")
                
                login_success_count = 0
                new_account_count = 0
                wrong_password_count = 0
                error_count = 0
                
                for account in self.account_results:
                    f.write(f"TÀI KHOẢN {account['index']}: {account['username']}\n")
                    f.write(f"Password: {account['password']}\n")
                    
                    if account['status'] == 'login_success':
                        f.write("Trạng thái: ĐĂNG NHẬP THÀNH CÔNG ✅\n")
                        f.write("Mô tả: Tài khoản hoạt động bình thường, đã đăng nhập được\n")
                        login_success_count += 1
                    elif account['status'] == 'new_account':
                        f.write("Trạng thái: TÀI KHOẢN MỚI CHƯA KÍCH HOẠT 🆕\n")
                        f.write("Mô tả: Tài khoản mới cần đổi mật khẩu lần đầu hoặc xác minh\n")
                        new_account_count += 1
                    elif account['status'] == 'wrong_password':
                        f.write("Trạng thái: SAI MẬT KHẨU ❌\n")
                        f.write("Mô tả: Mật khẩu không đúng, cần kiểm tra lại\n")
                        wrong_password_count += 1
                    else:
                        f.write(f"Trạng thái: LỖI ⚠️\n")
                        f.write(f"Mô tả: {account['description']}\n")
                        error_count += 1
                    
                    f.write("-" * 60 + "\n")
                
                f.write(f"\n## TỔNG KẾT CUỐI CÙNG:\n")
                f.write(f"- Đăng nhập thành công: {login_success_count}/3\n")
                f.write(f"- Tài khoản mới chưa kích hoạt: {new_account_count}/3\n")
                f.write(f"- Sai mật khẩu: {wrong_password_count}/3\n")
                f.write(f"- Lỗi kỹ thuật: {error_count}/3\n")
                
                f.write(f"\n## KHUYẾN NGHỊ:\n")
                if login_success_count > 0:
                    f.write(f"- {login_success_count} tài khoản có thể sử dụng ngay\n")
                if new_account_count > 0:
                    f.write(f"- {new_account_count} tài khoản cần đổi mật khẩu để kích hoạt\n")
                if wrong_password_count > 0:
                    f.write(f"- {wrong_password_count} tài khoản cần kiểm tra lại thông tin đăng nhập\n")
                if error_count > 0:
                    f.write(f"- {error_count} tài khoản gặp lỗi kỹ thuật, có thể thử lại sau\n")
                    
                f.write(f"\n## CHI TIẾT TỪNG TÀI KHOẢN:\n")
                for account in self.account_results:
                    f.write(f"TK{account['index']}: {account['username']} | {account['status'].upper()}\n")
            
            self.log("✅ Đã tạo file accstatus.txt cuối cùng", "SUCCESS")
            
            # In tổng kết ra console
            print(f"\n{'='*120}")
            self.log("📊 TỔNG KẾT CUỐI CÙNG - CHROME DRIVER ẨN DANH", "STEP")
            print("="*120)
            
            for account in self.account_results:
                status_icon = {
                    "login_success": "✅ ĐĂNG NHẬP THÀNH CÔNG",
                    "new_account": "🆕 TÀI KHOẢN MỚI CHƯA KÍCH HOẠT",
                    "wrong_password": "❌ SAI MẬT KHẨU",
                    "error": "💥 LỖI KỸ THUẬT",
                    "unknown": "❓ KHÔNG XÁC ĐỊNH"
                }.get(account["status"], "❓ KHÔNG XÁC ĐỊNH")
                
                print(f"TK{account['index']}: {account['username']} → {status_icon}")
            
            print("="*120)
            self.log(f"📄 Kết quả đã lưu vào file accstatus.txt", "SUCCESS")
            self.log(f"📸 Tổng cộng {self.screenshot_counter} ảnh chụp màn hình", "INFO")
            self.log(f"🕵️ Đã sử dụng Chrome driver ẩn danh an toàn", "SUCCESS")
            
        except Exception as e:
            self.log(f"Lỗi tạo báo cáo: {e}", "ERROR")

def main():
    checker = SimpleIncognitoChecker()
    checker.run_simple_incognito_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 