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

class GoogleLoginStepByStep:
    def __init__(self):
        self.driver = None
        self.step_delay = 1.0  # Delay extract gg from pdf giây mỗi bước
        
    def log_step(self, step_number, message):
        """Log từng bước với timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] BƯỚC {step_number}: {message}")
        time.sleep(self.step_delay)
    
    def setup_driver(self):
        """Thiết lập Chrome driver với hiển thị từng bước"""
        self.log_step(1, "🔧 Bắt đầu thiết lập Chrome driver...")
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.log_step(2, "⚙️ Đã thiết lập Chrome options")
            
            # Load extensions nếu có
            if os.path.exists('driver/1.crx'):
                chrome_options.add_extension('driver/extract gg from pdf.crx')
                self.log_step(3, "🔌 Đã load extension extract gg from pdf.crx")
            
            if os.path.exists('driver/captchasolver.crx'):
                chrome_options.add_extension('driver/captchasolver.crx')
                self.log_step(4, "🔌 Đã load extension captchasolver.crx")
            
            # Chrome driver path
            driver_path = 'driver/chromedriver.exe'
            if not os.path.exists(driver_path):
                driver_path = 'chromedriver.exe'
            
            self.log_step(5, f"📁 Đường dẫn ChromeDriver: {driver_path}")
            
            # Khởi tạo driver
            if os.path.exists(driver_path):
                chrome_service = Service(driver_path)
                self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
                self.log_step(6, "✅ Chrome driver đã được khởi tạo với Service")
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.log_step(6, "✅ Chrome driver đã được khởi tạo từ system PATH")
            
            self.log_step(7, "🌐 Chrome browser đã mở thành công!")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo driver: {e}")
            return False
    
    def load_accounts(self, count=1):
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
    
    def test_google_login_detailed(self, username, password):
        """Test đăng nhập Google với hiển thị chi tiết từng bước"""
        print("\n" + "="*80)
        print(f"🧪 BẮT ĐẦU TEST ĐĂNG NHẬP: {username}")
        print("="*80)
        
        try:
            # Bước extract gg from pdf: Mở trang Google
            self.log_step(10, "🌐 Điều hướng đến trang đăng nhập Google...")
            self.driver.get("https://accounts.google.com/signin")
            
            self.log_step(11, "⏳ Chờ trang tải hoàn toàn...")
            time.sleep(3)
            
            # Chụp screenshot trang đăng nhập
            try:
                screenshot_name = f"screenshot_login_page_{datetime.now().strftime('%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_name)
                self.log_step(12, f"📸 Đã chụp screenshot: {screenshot_name}")
            except:
                pass
            
            # Bước 2: Tìm và nhập email
            self.log_step(13, "🔍 Tìm ô nhập email...")
            
            try:
                email_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "identifierId"))
                )
                self.log_step(14, "✅ Đã tìm thấy ô nhập email!")
                
                # Highlight element
                self.driver.execute_script("arguments[0].style.border='3px solid red'", email_input)
                self.log_step(15, "🔴 Đã highlight ô email với viền đỏ")
                
                # Clear và nhập email
                self.log_step(16, "🧹 Xóa nội dung cũ trong ô email...")
                email_input.clear()
                
                self.log_step(17, f"⌨️ Nhập email: {username}")
                for char in username:
                    email_input.send_keys(char)
                    time.sleep(0.1)  # Gõ chậm từng ký tự
                
                self.log_step(18, "✅ Đã nhập xong email!")
                
                # Chụp screenshot sau khi nhập email
                try:
                    screenshot_name = f"screenshot_email_entered_{datetime.now().strftime('%H%M%S')}.png"
                    self.driver.save_screenshot(screenshot_name)
                    self.log_step(19, f"📸 Đã chụp screenshot sau khi nhập email: {screenshot_name}")
                except:
                    pass
                
                # Tìm và click nút Next
                self.log_step(20, "🔍 Tìm nút 'Next' để tiếp tục...")
                next_button = self.driver.find_element(By.ID, "identifierNext")
                
                # Highlight nút Next
                self.driver.execute_script("arguments[0].style.border='3px solid blue'", next_button)
                self.log_step(21, "🔵 Đã highlight nút Next với viền xanh")
                
                self.log_step(22, "👆 Click nút Next...")
                next_button.click()
                
                self.log_step(23, "⏳ Chờ trang chuyển đến bước nhập password...")
                time.sleep(4)
                
            except Exception as e:
                self.log_step("ERROR", f"❌ Lỗi ở bước nhập email: {e}")
                return "email_error"
            
            # Kiểm tra lỗi email
            self.log_step(24, "🔍 Kiểm tra có lỗi email không...")
            try:
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, '[role="alert"]')
                for error_element in error_elements:
                    if error_element.text:
                        error_text = error_element.text.lower()
                        self.log_step(25, f"⚠️ Phát hiện thông báo lỗi: {error_element.text}")
                        if any(keyword in error_text for keyword in ['email', 'account', 'find', 'exist', "couldn't find"]):
                            self.log_step(26, "❌ Email không tồn tại hoặc không hợp lệ!")
                            return "invalid_email"
            except:
                pass
            
            self.log_step(27, "✅ Không có lỗi email, tiếp tục...")
            
            # Bước 3: Nhập password
            self.log_step(28, "🔍 Tìm ô nhập password...")
            
            try:
                password_input = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.NAME, "password"))
                )
                self.log_step(29, "✅ Đã tìm thấy ô nhập password!")
                
                # Highlight password field
                self.driver.execute_script("arguments[0].style.border='3px solid green'", password_input)
                self.log_step(30, "🟢 Đã highlight ô password với viền xanh lá")
                
                # Clear và nhập password
                self.log_step(31, "🧹 Xóa nội dung cũ trong ô password...")
                password_input.clear()
                
                self.log_step(32, f"⌨️ Nhập password: {'*' * len(password)}")
                for char in password:
                    password_input.send_keys(char)
                    time.sleep(0.1)  # Gõ chậm từng ký tự
                
                self.log_step(33, "✅ Đã nhập xong password!")
                
                # Chụp screenshot sau khi nhập password
                try:
                    screenshot_name = f"screenshot_password_entered_{datetime.now().strftime('%H%M%S')}.png"
                    self.driver.save_screenshot(screenshot_name)
                    self.log_step(34, f"📸 Đã chụp screenshot sau khi nhập password: {screenshot_name}")
                except:
                    pass
                
                # Tìm và click nút Next password
                self.log_step(35, "🔍 Tìm nút 'Next' cho password...")
                password_next = self.driver.find_element(By.ID, "passwordNext")
                
                # Highlight nút
                self.driver.execute_script("arguments[0].style.border='3px solid purple'", password_next)
                self.log_step(36, "🟣 Đã highlight nút Next password với viền tím")
                
                self.log_step(37, "👆 Click nút Next password...")
                password_next.click()
                
                self.log_step(38, "⏳ Chờ kết quả đăng nhập...")
                time.sleep(5)
                
            except Exception as e:
                self.log_step("ERROR", f"❌ Lỗi ở bước nhập password: {e}")
                return "password_error"
            
            # Bước 4: Kiểm tra kết quả
            self.log_step(39, "🔍 Phân tích kết quả đăng nhập...")
            
            current_url = self.driver.current_url
            self.log_step(40, f"🔗 URL hiện tại: {current_url}")
            
            # Chụp screenshot kết quả cuối
            try:
                screenshot_name = f"screenshot_final_result_{datetime.now().strftime('%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_name)
                self.log_step(41, f"📸 Đã chụp screenshot kết quả cuối: {screenshot_name}")
            except:
                pass
            
            # Kiểm tra các dấu hiệu thành công
            success_indicators = [
                "myaccount.google.com",
                "accounts.google.com/signin/oauth",
                "accounts.google.com/b/0/ManageAccount"
            ]
            
            for indicator in success_indicators:
                if indicator in current_url:
                    self.log_step(42, f"✅ THÀNH CÔNG! Phát hiện: {indicator}")
                    return "success"
            
            # Kiểm tra page source
            page_source = self.driver.page_source.lower()
            
            # Kiểm tra lỗi sai password
            password_errors = ['wrong password', 'incorrect password', 'sai mật khẩu', 'enter the right password']
            for error in password_errors:
                if error in page_source:
                    self.log_step(43, f"❌ THẤT BẠI: Sai mật khẩu - Phát hiện: {error}")
                    return "wrong_password"
            
            # Kiểm tra tài khoản bị khóa
            blocked_indicators = ['suspended', 'disabled', 'locked', 'blocked', 'deactivated']
            for indicator in blocked_indicators:
                if indicator in page_source:
                    self.log_step(44, f"⚠️ TÀI KHOẢN BỊ KHÓA - Phát hiện: {indicator}")
                    return "blocked"
            
            # Kiểm tra cần xác minh
            verification_indicators = ['verify', 'verification', 'phone', 'recovery', '2-step']
            for indicator in verification_indicators:
                if indicator in page_source:
                    self.log_step(45, f"⚠️ CẦN XÁC MINH - Phát hiện: {indicator}")
                    return "need_verification"
            
            # Kiểm tra captcha
            captcha_indicators = ['captcha', 'robot', 'unusual traffic']
            for indicator in captcha_indicators:
                if indicator in page_source:
                    self.log_step(46, f"🤖 CAPTCHA - Phát hiện: {indicator}")
                    return "captcha"
            
            self.log_step(47, "❓ KẾT QUẢ KHÔNG XÁC ĐỊNH")
            return "unknown"
            
        except Exception as e:
            self.log_step("ERROR", f"❌ Lỗi tổng quát: {e}")
            return "error"
    
    def run_test(self):
        """Chạy test với extract gg from pdf tài khoản"""
        print("🚀 GOOGLE LOGIN STEP-BY-STEP TESTER")
        print("="*50)
        
        # Thiết lập driver
        if not self.setup_driver():
            print("❌ Không thể khởi tạo driver!")
            return
        
        # Tải tài khoản
        accounts = self.load_accounts(1)  # Chỉ test extract gg from pdf tài khoản
        if not accounts:
            print("❌ Không có tài khoản để test!")
            return
        
        username, password = accounts[0]
        
        try:
            # Test đăng nhập
            result = self.test_google_login_detailed(username, password)
            
            # Báo cáo kết quả
            print("\n" + "="*80)
            print("📊 KẾT QUẢ CUỐI CÙNG")
            print("="*80)
            print(f"👤 Tài khoản: {username}")
            print(f"🔑 Password: {'*' * len(password)}")
            print(f"📈 Kết quả: {result}")
            
            if result == "success":
                print("🎉 ĐĂNG NHẬP THÀNH CÔNG!")
                with open("successful_accounts.txt", "a", encoding="utf-8") as f:
                    f.write(f"{username}|{password}\n")
                print("💾 Đã lưu tài khoản thành công vào file successful_accounts.txt")
            else:
                print(f"❌ ĐĂNG NHẬP THẤT BẠI: {result}")
            
            print("="*80)
            
            # Giữ browser mở để quan sát
            input("\n⏸️ Nhấn Enter để đóng browser và kết thúc...")
            
        except KeyboardInterrupt:
            print("\n⚠️ Đã dừng test bởi người dùng")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Đã đóng browser")

def main():
    tester = GoogleLoginStepByStep()
    tester.run_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng chương trình!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 