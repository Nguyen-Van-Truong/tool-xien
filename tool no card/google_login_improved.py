#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GoogleLoginImproved:
    def __init__(self):
        self.driver = None
        self.step_delay = 1.5  # Tăng delay lên extract gg from pdf.5s
        self.successful_accounts = []
        self.failed_accounts = []
        
    def log_step(self, step_number, message):
        """Log từng bước với timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] BƯỚC {step_number}: {message}")
        time.sleep(self.step_delay)
    
    def setup_driver(self):
        """Thiết lập Chrome driver với options cải tiến"""
        self.log_step(1, "🔧 Bắt đầu thiết lập Chrome driver...")
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent để tránh detection
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
            
            self.log_step(2, "⚙️ Đã thiết lập Chrome options nâng cao")
            
            # Load extensions nếu có
            if os.path.exists('driver/1.crx'):
                chrome_options.add_extension('driver/extract gg from pdf.crx')
                self.log_step(3, "🔌 Đã load extension extract gg from pdf.crx")
            
            if os.path.exists('driver/captchasolver.crx'):
                chrome_options.add_extension('driver/captchasolver.crx')
                self.log_step(4, "🔌 Đã load extension captchasolver.crx")
            
            # Chrome driver path
            driver_path = 'driver/chromedriver.exe'
            self.log_step(5, f"📁 Đường dẫn ChromeDriver: {driver_path}")
            
            # Khởi tạo driver
            chrome_service = Service(driver_path)
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            
            # Ẩn automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.log_step(6, "✅ Chrome driver đã được khởi tạo thành công")
            self.log_step(7, "🌐 Chrome browser đã mở thành công!")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo driver: {e}")
            return False
    
    def load_accounts(self, count=2):
        """Tải tài khoản để test"""
        self.log_step(8, f"📚 Đang tải {count} tài khoản từ file...")
        
        try:
            with open("students_accounts.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            accounts = []
            for line in lines[:count]:
                line = line.strip()
                if '|' in line:
                    username, password = line.split('|', 1)
                    accounts.append((username.strip(), password.strip()))
            
            self.log_step(9, f"✅ Đã tải thành công {len(accounts)} tài khoản")
            for i, (username, password) in enumerate(accounts, 1):
                self.log_step(f"9.{i}", f"📋 Tài khoản {i}: {username} | Password: {password}")
            
            return accounts
            
        except Exception as e:
            print(f"❌ Lỗi đọc file: {e}")
            return []
    
    def safe_find_element(self, by, value, timeout=20, description="element"):
        """Tìm element với xử lý lỗi an toàn"""
        try:
            self.log_step("FIND", f"🔍 Đang tìm {description}...")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            self.log_step("FIND", f"✅ Đã tìm thấy {description}!")
            return element
        except TimeoutException:
            self.log_step("ERROR", f"⏰ Timeout khi tìm {description} (đã chờ {timeout}s)")
            return None
        except Exception as e:
            self.log_step("ERROR", f"❌ Lỗi tìm {description}: {e}")
            return None
    
    def safe_click_element(self, element, description="element"):
        """Click element với xử lý lỗi an toàn"""
        try:
            # Scroll đến element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Highlight element
            self.driver.execute_script("arguments[0].style.border='3px solid red'", element)
            self.log_step("CLICK", f"🔴 Đã highlight {description}")
            
            # Click
            element.click()
            self.log_step("CLICK", f"✅ Đã click {description}")
            return True
        except Exception as e:
            self.log_step("ERROR", f"❌ Lỗi click {description}: {e}")
            return False
    
    def safe_input_text(self, element, text, description="input"):
        """Nhập text với xử lý lỗi an toàn"""
        try:
            # Clear field
            element.clear()
            time.sleep(0.5)
            
            # Type slowly
            self.log_step("INPUT", f"⌨️ Đang nhập {description}...")
            for char in text:
                element.send_keys(char)
                time.sleep(0.05)  # Gõ chậm hơn
            
            self.log_step("INPUT", f"✅ Đã nhập xong {description}")
            return True
        except Exception as e:
            self.log_step("ERROR", f"❌ Lỗi nhập {description}: {e}")
            return False
    
    def take_screenshot(self, name):
        """Chụp screenshot với xử lý lỗi"""
        try:
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f"screenshot_{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            self.log_step("SCREEN", f"📸 Screenshot: {filename}")
            return filename
        except Exception as e:
            self.log_step("ERROR", f"❌ Lỗi chụp screenshot: {e}")
            return None
    
    def test_google_login_detailed(self, username, password):
        """Test đăng nhập Google với xử lý lỗi cải tiến"""
        print("\n" + "="*80)
        print(f"🧪 BẮT ĐẦU TEST ĐĂNG NHẬP: {username}")
        print("="*80)
        
        try:
            # Bước extract gg from pdf: Mở trang Google
            self.log_step(10, "🌐 Điều hướng đến trang đăng nhập Google...")
            self.driver.get("https://accounts.google.com/signin")
            
            self.log_step(11, "⏳ Chờ trang tải hoàn toàn...")
            time.sleep(5)  # Tăng thời gian chờ
            
            # Screenshot trang đăng nhập
            self.take_screenshot("login_page")
            
            # Bước 2: Tìm và nhập email
            email_input = self.safe_find_element(By.ID, "identifierId", 20, "ô nhập email")
            if not email_input:
                return "email_input_not_found"
            
            # Highlight và nhập email
            self.driver.execute_script("arguments[0].style.border='3px solid blue'", email_input)
            self.log_step(12, "🔵 Đã highlight ô email")
            
            if not self.safe_input_text(email_input, username, f"email: {username}"):
                return "email_input_failed"
            
            self.take_screenshot("email_entered")
            
            # Bước 3: Click Next email
            next_button = self.safe_find_element(By.ID, "identifierNext", 15, "nút Next email")
            if not next_button:
                return "next_button_not_found"
            
            if not self.safe_click_element(next_button, "nút Next email"):
                return "next_button_click_failed"
            
            self.log_step(13, "⏳ Chờ chuyển đến trang password...")
            time.sleep(6)  # Tăng thời gian chờ
            
            # Kiểm tra lỗi email
            self.log_step(14, "🔍 Kiểm tra lỗi email...")
            try:
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, '[role="alert"]')
                for error_element in error_elements:
                    if error_element.text:
                        error_text = error_element.text.lower()
                        self.log_step(15, f"⚠️ Thông báo: {error_element.text}")
                        if any(keyword in error_text for keyword in ['email', 'account', 'find', 'exist', "couldn't find"]):
                            self.log_step(16, "❌ Email không hợp lệ!")
                            return "invalid_email"
            except:
                pass
            
            self.log_step(17, "✅ Email OK, tiếp tục tìm password field...")
            
            # Bước 4: Tìm password field với nhiều cách
            password_input = None
            
            # Thử nhiều selector khác nhau
            password_selectors = [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.XPATH, "//input[@name='password']"),
                (By.XPATH, "//input[@type='password']")
            ]
            
            for i, (by, selector) in enumerate(password_selectors, 1):
                self.log_step(f"18.{i}", f"🔍 Thử tìm password với selector {i}: {selector}")
                password_input = self.safe_find_element(by, selector, 10, f"password input (cách {i})")
                if password_input:
                    break
                time.sleep(2)
            
            if not password_input:
                self.log_step("ERROR", "❌ Không tìm thấy ô password bằng bất kỳ cách nào!")
                self.take_screenshot("password_not_found")
                return "password_input_not_found"
            
            # Highlight và nhập password
            self.driver.execute_script("arguments[0].style.border='3px solid green'", password_input)
            self.log_step(19, "🟢 Đã highlight ô password")
            
            if not self.safe_input_text(password_input, password, f"password (length: {len(password)})"):
                return "password_input_failed"
            
            self.take_screenshot("password_entered")
            
            # Bước 5: Click Next password
            password_next = self.safe_find_element(By.ID, "passwordNext", 15, "nút Next password")
            if not password_next:
                return "password_next_not_found"
            
            if not self.safe_click_element(password_next, "nút Next password"):
                return "password_next_click_failed"
            
            self.log_step(20, "⏳ Chờ kết quả đăng nhập...")
            time.sleep(8)  # Tăng thời gian chờ kết quả
            
            # Bước 6: Phân tích kết quả
            self.log_step(21, "🔍 Phân tích kết quả đăng nhập...")
            
            current_url = self.driver.current_url
            self.log_step(22, f"🔗 URL hiện tại: {current_url}")
            
            self.take_screenshot("final_result")
            
            # Kiểm tra thành công
            success_indicators = [
                "myaccount.google.com",
                "accounts.google.com/signin/oauth",
                "accounts.google.com/b/0/ManageAccount"
            ]
            
            for indicator in success_indicators:
                if indicator in current_url:
                    self.log_step(23, f"✅ THÀNH CÔNG! Phát hiện: {indicator}")
                    return "success"
            
            # Kiểm tra page source cho các lỗi
            page_source = self.driver.page_source.lower()
            
            # Sai password
            password_errors = ['wrong password', 'incorrect password', 'enter the right password', 'try again']
            for error in password_errors:
                if error in page_source:
                    self.log_step(24, f"❌ SAI PASSWORD - Phát hiện: {error}")
                    return "wrong_password"
            
            # Tài khoản bị khóa
            blocked_indicators = ['suspended', 'disabled', 'locked', 'blocked', 'deactivated']
            for indicator in blocked_indicators:
                if indicator in page_source:
                    self.log_step(25, f"⚠️ TÀI KHOẢN BỊ KHÓA - Phát hiện: {indicator}")
                    return "blocked"
            
            # Cần xác minh
            verification_indicators = ['verify', 'verification', 'phone', 'recovery', '2-step', 'confirm']
            for indicator in verification_indicators:
                if indicator in page_source:
                    self.log_step(26, f"⚠️ CẦN XÁC MINH - Phát hiện: {indicator}")
                    return "need_verification"
            
            self.log_step(27, "❓ KẾT QUẢ KHÔNG XÁC ĐỊNH")
            return "unknown"
            
        except Exception as e:
            self.log_step("ERROR", f"❌ Lỗi tổng quát: {e}")
            return "error"
    
    def run_test(self):
        """Chạy test với 2 tài khoản"""
        print("🚀 GOOGLE LOGIN IMPROVED TESTER")
        print("="*50)
        print("🔧 Version: Cải tiến với xử lý lỗi tốt hơn")
        print("📊 Sẽ test 2 tài khoản đầu tiên")
        print("="*50)
        
        # Thiết lập driver
        if not self.setup_driver():
            print("❌ Không thể khởi tạo driver!")
            return
        
        # Tải tài khoản
        accounts = self.load_accounts(2)  # Test 2 tài khoản
        if not accounts:
            print("❌ Không có tài khoản để test!")
            return
        
        try:
            # Test từng tài khoản
            for i, (username, password) in enumerate(accounts, 1):
                print(f"\n{'='*100}")
                print(f"🎯 TEST TÀI KHOẢN {i}/{len(accounts)}")
                print(f"{'='*100}")
                
                result = self.test_google_login_detailed(username, password)
                
                # Lưu kết quả
                if result == "success":
                    self.successful_accounts.append((username, password))
                    print(f"🎉 TÀI KHOẢN {i} THÀNH CÔNG!")
                else:
                    self.failed_accounts.append((username, password, result))
                    print(f"❌ TÀI KHOẢN {i} THẤT BẠI: {result}")
                
                # Nghỉ giữa các tài khoản
                if i < len(accounts):
                    self.log_step("BREAK", f"⏸️ Nghỉ 10s trước khi test tài khoản {i+1}...")
                    time.sleep(10)
            
            # Báo cáo tổng kết
            self.print_final_report()
            
            # Giữ browser mở
            input("\n⏸️ Nhấn Enter để đóng browser và kết thúc...")
            
        except KeyboardInterrupt:
            print("\n⚠️ Đã dừng test bởi người dùng")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Đã đóng browser")
    
    def print_final_report(self):
        """In báo cáo tổng kết"""
        print("\n" + "="*100)
        print("📊 BÁO CÁO TỔNG KẾT")
        print("="*100)
        print(f"✅ Tài khoản thành công: {len(self.successful_accounts)}")
        print(f"❌ Tài khoản thất bại: {len(self.failed_accounts)}")
        
        if self.successful_accounts:
            print("\n🎯 CÁC TÀI KHOẢN THÀNH CÔNG:")
            for i, (username, password) in enumerate(self.successful_accounts, 1):
                print(f"  {i}. {username}")
                # Lưu vào file
                with open("successful_google_accounts.txt", "a", encoding="utf-8") as f:
                    f.write(f"{username}|{password}\n")
            print("💾 Đã lưu vào file successful_google_accounts.txt")
        
        if self.failed_accounts:
            print("\n❌ CÁC TÀI KHOẢN THẤT BẠI:")
            for i, (username, password, reason) in enumerate(self.failed_accounts, 1):
                print(f"  {i}. {username} - Lý do: {reason}")
        
        print("="*100)

def main():
    tester = GoogleLoginImproved()
    tester.run_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng chương trình!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 