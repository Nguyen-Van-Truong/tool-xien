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

class SmartGoogleLogin:
    def __init__(self):
        self.driver = None
        self.successful_accounts = []
        self.failed_accounts = []
        self.screenshot_counter = 0
        
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
        """Phân tích các elements trên trang để hiểu tình huống"""
        try:
            analysis = {
                "email_field": False,
                "password_field": False,
                "next_button": False,
                "signin_button": False,
                "error_messages": [],
                "success_indicators": [],
                "special_elements": []
            }
            
            # Kiểm tra email field
            try:
                email_field = self.driver.find_element(By.ID, "identifierId")
                analysis["email_field"] = True
                self.log("Phát hiện ô email", "INFO")
            except:
                pass
            
            # Kiểm tra password field với nhiều cách
            password_selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.XPATH, "//input[@name='password']"),
                (By.XPATH, "//input[@type='password']")
            ]
            
            for by, selector in password_selectors:
                try:
                    password_fields = self.driver.find_elements(by, selector)
                    if password_fields:
                        analysis["password_field"] = True
                        self.log(f"Phát hiện {len(password_fields)} ô password", "INFO")
                        break
                except:
                    continue
            
            # Kiểm tra các nút
            button_selectors = [
                (By.ID, "identifierNext"),
                (By.ID, "passwordNext"),
                (By.CSS_SELECTOR, '[data-id="identifierNext"]'),
                (By.CSS_SELECTOR, '[data-id="passwordNext"]')
            ]
            
            for by, selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(by, selector)
                    if buttons:
                        analysis["next_button"] = True
                        self.log(f"Phát hiện nút: {selector}", "INFO")
                except:
                    continue
            
            # Kiểm tra lỗi
            error_selectors = [
                '[role="alert"]',
                '.error-message',
                '.Ekjuhf',  # Google error class
                '[data-error="true"]'
            ]
            
            for selector in error_selectors:
                try:
                    errors = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for error in errors:
                        if error.text and error.text.strip():
                            analysis["error_messages"].append(error.text.strip())
                            self.log(f"Phát hiện lỗi: {error.text.strip()}", "WARNING")
                except:
                    continue
            
            # Kiểm tra thành công
            current_url = self.driver.current_url
            if any(indicator in current_url for indicator in ["myaccount.google.com", "oauth", "ManageAccount"]):
                analysis["success_indicators"].append("success_url")
                self.log("Phát hiện URL thành công", "SUCCESS")
            
            return analysis
            
        except Exception as e:
            self.log(f"Lỗi phân tích trang: {e}", "ERROR")
            return {}
    
    def setup_driver(self):
        """Thiết lập Chrome driver"""
        self.log("🔧 Thiết lập Chrome driver...", "STEP")
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Load extensions
            if os.path.exists('driver/extract gg from pdf.crx'):
                chrome_options.add_extension('driver/extract gg from pdf.crx')
            if os.path.exists('driver/captchasolver.crx'):
                chrome_options.add_extension('driver/captchasolver.crx')
            
            chrome_service = Service('driver/chromedriver.exe')
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            
            # Ẩn automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.log("Chrome driver đã sẵn sàng", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Lỗi khởi tạo driver: {e}", "ERROR")
            return False
    
    def load_accounts(self, count=2):
        """Tải tài khoản"""
        self.log(f"📚 Tải {count} tài khoản...", "STEP")
        
        try:
            with open("students_accounts.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            accounts = []
            for line in lines[:count]:
                line = line.strip()
                if '|' in line:
                    username, password = line.split('|', 1)
                    accounts.append((username.strip(), password.strip()))
            
            self.log(f"Đã tải {len(accounts)} tài khoản", "SUCCESS")
            return accounts
            
        except Exception as e:
            self.log(f"Lỗi đọc file: {e}", "ERROR")
            return []
    
    def smart_wait_and_find(self, selectors, timeout=20, description="element"):
        """Tìm element thông minh với nhiều selector"""
        self.log(f"🔍 Tìm {description}...", "INFO")
        
        if isinstance(selectors, tuple):
            selectors = [selectors]
        
        for by, selector in selectors:
            try:
                self.log(f"Thử selector: {selector}")
                element = WebDriverWait(self.driver, timeout // len(selectors)).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.log(f"✅ Tìm thấy {description}!", "SUCCESS")
                return element
            except TimeoutException:
                self.log(f"Timeout với selector: {selector}", "WARNING")
                continue
            except Exception as e:
                self.log(f"Lỗi với selector {selector}: {e}", "WARNING")
                continue
        
        self.log(f"❌ Không tìm thấy {description}", "ERROR")
        return None
    
    def smart_input_text(self, element, text, description="text"):
        """Nhập text thông minh với nhiều phương pháp"""
        self.log(f"⌨️ Nhập {description}...", "INFO")
        
        methods = [
            ("clear_and_type", lambda: self._method_clear_and_type(element, text)),
            ("js_clear_and_type", lambda: self._method_js_clear_and_type(element, text)),
            ("select_all_and_type", lambda: self._method_select_all_and_type(element, text)),
            ("action_chains", lambda: self._method_action_chains(element, text))
        ]
        
        for method_name, method_func in methods:
            try:
                self.log(f"Thử phương pháp: {method_name}")
                result = method_func()
                if result:
                    self.log(f"✅ Nhập {description} thành công với {method_name}", "SUCCESS")
                    time.sleep(1)  # Wait for input to register
                    return True
            except Exception as e:
                self.log(f"Phương pháp {method_name} thất bại: {e}", "WARNING")
                continue
        
        self.log(f"❌ Tất cả phương pháp nhập {description} đều thất bại", "ERROR")
        return False
    
    def _method_clear_and_type(self, element, text):
        """Phương pháp extract gg from pdf: Clear và type thông thường"""
        element.clear()
        time.sleep(0.5)
        element.send_keys(text)
        return True
    
    def _method_js_clear_and_type(self, element, text):
        """Phương pháp 2: Dùng JavaScript để clear và set value"""
        self.driver.execute_script("arguments[0].value = '';", element)
        time.sleep(0.5)
        element.send_keys(text)
        return True
    
    def _method_select_all_and_type(self, element, text):
        """Phương pháp 3: Select all và type"""
        element.click()
        time.sleep(0.3)
        element.send_keys(Keys.CTRL + "a")
        time.sleep(0.3)
        element.send_keys(text)
        return True
    
    def _method_action_chains(self, element, text):
        """Phương pháp 4: Dùng ActionChains"""
        actions = ActionChains(self.driver)
        actions.click(element)
        actions.key_down(Keys.CTRL).send_keys("a").key_up(Keys.CTRL)
        actions.send_keys(text)
        actions.perform()
        return True
    
    def smart_click(self, element, description="element"):
        """Click thông minh với nhiều phương pháp"""
        self.log(f"🖱️ Click {description}...", "INFO")
        
        # Highlight element
        try:
            self.driver.execute_script("arguments[0].style.border='3px solid red'", element)
            time.sleep(0.5)
        except:
            pass
        
        methods = [
            ("normal_click", lambda: element.click()),
            ("js_click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("action_chains_click", lambda: ActionChains(self.driver).click(element).perform())
        ]
        
        for method_name, method_func in methods:
            try:
                self.log(f"Thử click bằng: {method_name}")
                method_func()
                self.log(f"✅ Click {description} thành công", "SUCCESS")
                time.sleep(2)  # Wait for action to complete
                return True
            except Exception as e:
                self.log(f"Click {method_name} thất bại: {e}", "WARNING")
                continue
        
        self.log(f"❌ Tất cả phương pháp click đều thất bại", "ERROR")
        return False
    
    def test_account_smart(self, username, password):
        """Test tài khoản với phương pháp thông minh"""
        print("\n" + "="*80)
        self.log(f"🧪 BẮT ĐẦU TEST: {username}", "STEP")
        print("="*80)
        
        try:
            # Bước extract gg from pdf: Mở trang đăng nhập
            self.log("🌐 Mở trang đăng nhập Google...", "STEP")
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(3)
            
            self.take_screenshot_and_analyze("01_login_page")
            
            # Bước 2: Nhập email
            self.log("📧 Tìm và nhập email...", "STEP")
            
            email_selectors = [
                (By.ID, "identifierId"),
                (By.NAME, "identifier"),
                (By.CSS_SELECTOR, 'input[type="email"]')
            ]
            
            email_input = self.smart_wait_and_find(email_selectors, description="ô email")
            if not email_input:
                self.take_screenshot_and_analyze("02_email_not_found")
                return "email_input_not_found", "Không tìm thấy ô nhập email"
            
            if not self.smart_input_text(email_input, username, f"email {username}"):
                self.take_screenshot_and_analyze("03_email_input_failed")
                return "email_input_failed", "Không thể nhập email"
            
            self.take_screenshot_and_analyze("04_email_entered")
            
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
                self.take_screenshot_and_analyze("05_next_button_not_found")
                return "next_button_not_found", "Không tìm thấy nút Next email"
            
            if not self.smart_click(next_button, "Next email"):
                self.take_screenshot_and_analyze("06_next_click_failed")
                return "next_click_failed", "Không thể click nút Next email"
            
            # Chờ và kiểm tra trang password
            self.log("⏳ Chờ trang password...", "INFO")
            time.sleep(5)
            
            filename, analysis = self.take_screenshot_and_analyze("07_after_email_next", analyze=True)
            
            # Kiểm tra lỗi email
            if analysis.get("error_messages"):
                self.log(f"❌ Phát hiện lỗi email: {analysis['error_messages']}", "ERROR")
                return "invalid_email", f"Email không hợp lệ: {analysis['error_messages']}"
            
            # Bước 4: Tìm và nhập password
            self.log("🔐 Tìm và nhập password...", "STEP")
            
            password_selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.XPATH, "//input[@name='password']"),
                (By.XPATH, "//input[@type='password']"),
                (By.ID, "password")
            ]
            
            # Thử nhiều lần tìm password field
            password_input = None
            for attempt in range(3):
                self.log(f"Lần thử {attempt + 1}/3 tìm password field")
                password_input = self.smart_wait_and_find(password_selectors, timeout=15, description="ô password")
                if password_input:
                    break
                time.sleep(2)
            
            if not password_input:
                self.take_screenshot_and_analyze("08_password_not_found")
                return "password_input_not_found", "Không tìm thấy ô nhập mật khẩu"
            
            # Kiểm tra trạng thái password field
            try:
                is_enabled = password_input.is_enabled()
                is_displayed = password_input.is_displayed()
                self.log(f"Password field - Enabled: {is_enabled}, Displayed: {is_displayed}")
                
                if not is_enabled:
                    self.log("⚠️ Password field bị disabled, thử click để enable", "WARNING")
                    self.smart_click(password_input, "password field để enable")
                    time.sleep(1)
                    
            except Exception as e:
                self.log(f"Lỗi kiểm tra password field: {e}", "WARNING")
            
            if not self.smart_input_text(password_input, password, f"password (length: {len(password)})"):
                self.take_screenshot_and_analyze("09_password_input_failed")
                return "password_input_failed", "Không thể nhập mật khẩu"
            
            self.take_screenshot_and_analyze("10_password_entered")
            
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
                self.take_screenshot_and_analyze("11_password_next_not_found")
                return "password_next_not_found", "Không tìm thấy nút Next password"
            
            if not self.smart_click(password_next, "Next password"):
                self.take_screenshot_and_analyze("12_password_next_failed")
                return "password_next_failed", "Không thể click nút Next password"
            
            # Bước 6: Chờ và phân tích kết quả
            self.log("⏳ Chờ và phân tích kết quả...", "STEP")
            time.sleep(8)
            
            filename, analysis = self.take_screenshot_and_analyze("13_final_result", analyze=True)
            
            current_url = self.driver.current_url
            self.log(f"🔗 URL cuối: {current_url}")
            
            # Phân tích kết quả
            if analysis.get("success_indicators"):
                self.log("🎉 ĐĂNG NHẬP THÀNH CÔNG!", "SUCCESS")
                return "success"
            
            if analysis.get("error_messages"):
                error_text = " | ".join(analysis["error_messages"]).lower()
                if any(keyword in error_text for keyword in ["wrong", "incorrect", "password", "try again"]):
                    self.log("❌ SAI PASSWORD", "ERROR")
                    return "wrong_password"
                elif any(keyword in error_text for keyword in ["suspended", "disabled", "locked"]):
                    self.log("⚠️ TÀI KHOẢN BỊ KHÓA", "WARNING")
                    return "blocked"
                elif any(keyword in error_text for keyword in ["verify", "phone", "recovery"]):
                    self.log("⚠️ CẦN XÁC MINH", "WARNING")
                    return "need_verification"
            
            # Kiểm tra URL để xác định kết quả
            if any(indicator in current_url for indicator in ["myaccount", "oauth", "ManageAccount"]):
                self.log("🎉 THÀNH CÔNG qua URL!", "SUCCESS")
                return "success"
            elif "challenge" in current_url or "verify" in current_url:
                self.log("⚠️ CẦN XÁC MINH qua URL", "WARNING")
                return "need_verification"
            elif "signin" in current_url:
                # Vẫn ở trang login, có thể sai password
                page_source = self.driver.page_source.lower()
                if any(keyword in page_source for keyword in ["wrong", "incorrect", "try again"]):
                    self.log("❌ SAI PASSWORD qua page source", "ERROR")
                    return "wrong_password"
            
            self.log("❓ KẾT QUẢ KHÔNG XÁC ĐỊNH", "WARNING")
            return "unknown"
            
        except Exception as e:
            self.log(f"❌ LỖI TỔNG QUÁT: {e}", "ERROR")
            self.take_screenshot_and_analyze("14_general_error")
            return "error"
    
    def run_smart_test(self):
        """Chạy test thông minh"""
        print("🚀 SMART GOOGLE LOGIN TESTER")
        print("="*50)
        print("🧠 Phiên bản thông minh với tự đánh giá")
        print("📸 Tự động chụp ảnh và phân tích")
        print("🔄 Thử nhiều phương pháp cho mỗi bước")
        print("="*50)
        
        if not self.setup_driver():
            return
        
        accounts = self.load_accounts(2)
        if not accounts:
            return
        
        try:
            for i, (username, password) in enumerate(accounts, 1):
                print(f"\n{'='*100}")
                self.log(f"🎯 TEST TÀI KHOẢN {i}/{len(accounts)}: {username}", "STEP")
                print("="*100)
                
                result = self.test_account_smart(username, password)
                
                if result == "success":
                    self.successful_accounts.append((username, password))
                    self.log(f"🎉 TÀI KHOẢN {i} THÀNH CÔNG!", "SUCCESS")
                else:
                    self.failed_accounts.append((username, password, result))
                    self.log(f"❌ TÀI KHOẢN {i} THẤT BẠI: {result}", "ERROR")
                
                # Nghỉ giữa các tài khoản
                if i < len(accounts):
                    self.log(f"⏸️ Nghỉ 15s trước tài khoản {i+1}...", "INFO")
                    time.sleep(15)
            
            self.print_final_report()
            input("\n⏸️ Nhấn Enter để đóng...")
            
        except KeyboardInterrupt:
            self.log("⚠️ Dừng test bởi người dùng", "WARNING")
        finally:
            if self.driver:
                self.driver.quit()
                self.log("🔒 Đã đóng browser", "INFO")
    
    def print_detailed_report(self, account_results):
        """Báo cáo chi tiết 3 tài khoản"""
        print("\n" + "="*100)
        self.log("📊 BÁO CÁO CHI TIẾT 3 TÀI KHOẢN", "STEP")
        print("="*100)
        
        # Tổng quan
        self.log(f"✅ Đăng nhập thành công: {len(self.successful_accounts)}", "SUCCESS")
        self.log(f"🆕 Tài khoản mới chưa kích hoạt: {len(self.new_accounts)}", "WARNING")
        self.log(f"❌ Thất bại: {len(self.failed_accounts)}", "ERROR")
        
        # Chi tiết từng tài khoản
        print("\n📋 CHI TIẾT TỪNG TÀI KHOẢN:")
        print("-" * 80)
        
        for account in account_results:
            i = account["index"]
            username = account["username"]
            result = account["result"]
            situation = account["situation"]
            
            status_icon = {
                "success": "✅",
                "new_account": "🆕",
                "wrong_password": "❌",
                "error": "⚠️",
                "unknown": "❓"
            }.get(result, "❓")
            
            print(f"\n{status_icon} TÀI KHOẢN {i}: {username}")
            print(f"   📊 Kết quả: {result}")
            print(f"   📝 Tình huống: {situation}")
        
        print("-" * 80)
        
        # Kết luận
        print(f"\n🎯 KẾT LUẬN:")
        if self.successful_accounts:
            print(f"   ✅ {len(self.successful_accounts)} tài khoản đăng nhập thành công (đã kích hoạt)")
        
        if self.new_accounts:
            print(f"   🆕 {len(self.new_accounts)} tài khoản mới chưa kích hoạt (cần đổi mật khẩu)")
            
        if self.failed_accounts:
            print(f"   ❌ {len(self.failed_accounts)} tài khoản thất bại (sai mật khẩu hoặc lỗi khác)")
        
        # Lưu file kết quả
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.successful_accounts:
            filename = f"SUCCESSFUL_ACCOUNTS_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# TÀI KHOẢN ĐĂNG NHẬP THÀNH CÔNG\n")
                for username, password in self.successful_accounts:
                    f.write(f"{username}|{password}\n")
            self.log(f"💾 Đã lưu tài khoản thành công vào {filename}", "SUCCESS")
        
        if self.new_accounts:
            filename = f"NEW_ACCOUNTS_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# TÀI KHOẢN MỚI CHƯA KÍCH HOẠT\n")
                for username, password in self.new_accounts:
                    f.write(f"{username}|{password}\n")
            self.log(f"💾 Đã lưu tài khoản mới vào {filename}", "WARNING")
        
        # Lưu báo cáo chi tiết
        report_filename = f"DETAILED_REPORT_{timestamp}.txt"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write("# BÁO CÁO CHI TIẾT TEST 3 TÀI KHOẢN\n")
            f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for account in account_results:
                f.write(f"TÀI KHOẢN {account['index']}: {account['username']}\n")
                f.write(f"Kết quả: {account['result']}\n")
                f.write(f"Tình huống: {account['situation']}\n")
                f.write("-" * 50 + "\n")
        
        self.log(f"💾 Đã lưu báo cáo chi tiết vào {report_filename}", "INFO")
        self.log(f"📸 Đã chụp {self.screenshot_counter} ảnh màn hình", "INFO")
        print("="*100)

def main():
    tester = SmartGoogleLogin()
    tester.run_smart_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 