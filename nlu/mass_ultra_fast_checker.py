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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class MassUltraFastChecker:
    def __init__(self):
        self.driver = None
        self.results = []
        self.success_accounts = []
        self.wrong_password_accounts = []
        self.error_accounts = []
        self.processed_count = 0
        self.start_time = datetime.now()
        
    def log(self, message, level="INFO"):
        """Log nhanh với timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "🔵", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "STEP": "🎯"}
        icon = icons.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")
    
    def setup_fresh_incognito_driver(self):
        """Thiết lập Chrome ẩn danh MỚI cho mỗi tài khoản"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-save-password-bubble')
            chrome_options.add_argument('--disable-password-generation')
            chrome_options.add_argument('--disable-autofill')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            
            # Vô hiệu hóa logging để nhanh hơn
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')
            
            # Đảm bảo mỗi instance hoàn toàn độc lập
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            
            chrome_service = Service('driver/chromedriver.exe')
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi tạo Chrome: {e}", "ERROR")
            return False
    
    def close_driver_completely(self):
        """Đóng Chrome hoàn toàn"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                time.sleep(1)  # Đảm bảo Chrome đóng hoàn toàn
        except:
            pass
    
    def smart_wait_and_find_fast(self, selectors, timeout=10, description="element"):
        """Tìm element nhanh - giảm timeout"""
        for by, selector in selectors:
            try:
                wait = WebDriverWait(self.driver, timeout // len(selectors))
                element = wait.until(EC.presence_of_element_located((by, selector)))
                if element and element.is_displayed():
                    return element
            except:
                continue
        return None
    
    def smart_input_fast(self, element, text):
        """Nhập text nhanh"""
        try:
            element.clear()
            element.send_keys(text)
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].value = '';", element)
                element.send_keys(text)
                return True
            except:
                return False
    
    def smart_click_fast(self, element):
        """Click nhanh"""
        try:
            element.click()
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False
    
    def check_wrong_password_fast(self):
        """Kiểm tra sai password siêu nhanh"""
        try:
            page_source = self.driver.page_source
            
            # Kiểm tra các từ khóa lỗi
            wrong_indicators = [
                "Wrong password. Try again or click Forgot password to reset it.",
                "Wrong password",
                "wrong password", 
                "incorrect password",
                "try again",
                "forgot password",
                "couldn't sign you in"
            ]
            
            page_lower = page_source.lower()
            for indicator in wrong_indicators:
                if indicator.lower() in page_lower:
                    return True
            
            return False
            
        except:
            return False
    
    def load_all_accounts(self):
        """Tải TẤT CẢ tài khoản"""
        self.log("📚 Tải TẤT CẢ tài khoản...", "STEP")
        
        try:
            with open("students_accounts.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            accounts = []
            for i, line in enumerate(lines):
                line = line.strip()
                if '|' in line:
                    username, password = line.split('|', 1)
                    accounts.append((username.strip(), password.strip(), i+1))
            
            self.log(f"✅ Đã tải {len(accounts)} tài khoản", "SUCCESS")
            return accounts
            
        except Exception as e:
            self.log(f"❌ Lỗi tải tài khoản: {e}", "ERROR")
            return []
    
    def test_single_account_with_fresh_browser(self, username, password, index):
        """Test một tài khoản với trình duyệt ẩn danh MỚI"""
        result = {
            "index": index,
            "username": username,
            "password": password,
            "status": "unknown",
            "description": ""
        }
        
        # Bước 0: Tạo Chrome ẩn danh mới
        if not self.setup_fresh_incognito_driver():
            result["status"] = "error"
            result["description"] = "Không thể tạo Chrome ẩn danh mới"
            return result
        
        try:
            # Bước 1: Mở Google login
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(2)
            
            # Bước 2: Nhập email
            email_selectors = [
                (By.ID, "identifierId"),
                (By.NAME, "identifier"),
                (By.CSS_SELECTOR, 'input[type="email"]')
            ]
            
            email_input = self.smart_wait_and_find_fast(email_selectors, timeout=8, description="ô email")
            if not email_input:
                result["status"] = "error"
                result["description"] = "Không tìm thấy ô email"
                return result
            
            if not self.smart_input_fast(email_input, username):
                result["status"] = "error"
                result["description"] = "Không thể nhập email"
                return result
            
            # Bước 3: Click Next email
            next_selectors = [
                (By.ID, "identifierNext"),
                (By.CSS_SELECTOR, '[data-id="identifierNext"]'),
                (By.XPATH, "//span[text()='Next']//parent::button")
            ]
            
            next_button = self.smart_wait_and_find_fast(next_selectors, timeout=5, description="nút Next email")
            if not next_button:
                result["status"] = "error"
                result["description"] = "Không tìm thấy nút Next"
                return result
            
            if not self.smart_click_fast(next_button):
                result["status"] = "error"
                result["description"] = "Không thể click nút Next"
                return result
            
            time.sleep(3)
            
            # Bước 4: Nhập password
            password_selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.XPATH, "//input[@name='password']")
            ]
            
            password_input = self.smart_wait_and_find_fast(password_selectors, timeout=10, description="ô password")
            if not password_input:
                result["status"] = "error"
                result["description"] = "Không tìm thấy ô password"
                return result
            
            if not self.smart_input_fast(password_input, password):
                result["status"] = "error"
                result["description"] = "Không thể nhập password"
                return result
            
            # Bước 5: Click Next password
            password_next_selectors = [
                (By.ID, "passwordNext"),
                (By.CSS_SELECTOR, '[data-id="passwordNext"]'),
                (By.XPATH, "//span[text()='Next']//parent::button")
            ]
            
            password_next = self.smart_wait_and_find_fast(password_next_selectors, timeout=5, description="nút Next password")
            if not password_next:
                result["status"] = "error"
                result["description"] = "Không tìm thấy nút Next password"
                return result
            
            if not self.smart_click_fast(password_next):
                result["status"] = "error"
                result["description"] = "Không thể click nút Next password"
                return result
            
            # Bước 6: Kiểm tra kết quả
            time.sleep(5)
            
            if self.check_wrong_password_fast():
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
            # QUAN TRỌNG: Luôn đóng Chrome sau mỗi tài khoản
            self.close_driver_completely()
    
    def save_progress_every_50(self):
        """Lưu tiến trình mỗi 50 tài khoản"""
        try:
            if self.processed_count % 50 == 0:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"mass_progress_{self.processed_count}_{timestamp}.txt"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# TIẾN TRÌNH - ĐÃ XỬ LÝ {self.processed_count} TÀI KHOẢN\n")
                    f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("## TÀI KHOẢN ĐĂNG NHẬP THÀNH CÔNG:\n")
                    for acc in self.success_accounts:
                        f.write(f"{acc['username']}|{acc['password']}\n")
                    
                    f.write(f"\n## TÀI KHOẢN SAI MẬT KHẨU:\n")
                    for acc in self.wrong_password_accounts:
                        f.write(f"{acc['username']}|{acc['password']}\n")
                    
                    f.write(f"\n## THỐNG KÊ:\n")
                    f.write(f"- Thành công: {len(self.success_accounts)}\n")
                    f.write(f"- Sai mật khẩu: {len(self.wrong_password_accounts)}\n")
                    f.write(f"- Lỗi kỹ thuật: {len(self.error_accounts)}\n")
                    f.write(f"- Tổng đã xử lý: {self.processed_count}\n")
                
                self.log(f"💾 Đã lưu tiến trình: {filename}", "SUCCESS")
                
        except Exception as e:
            self.log(f"Lỗi lưu tiến trình: {e}", "ERROR")
    
    def create_final_mass_report(self):
        """Tạo báo cáo cuối cùng cho tất cả tài khoản"""
        try:
            with open("accstatus.txt", "w", encoding="utf-8") as f:
                f.write("# TÌNH TRẠNG TẤT CẢ TÀI KHOẢN - MỖI TK MỘT CHROME ẨN DANH MỚI\n")
                f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Tổng thời gian: {datetime.now() - self.start_time}\n")
                f.write("# Logic: Có 'Wrong password' = Sai | Không có = Thành công\n\n")
                
                f.write(f"## TỔNG KẾT CUỐI CÙNG:\n")
                f.write(f"- Đăng nhập thành công: {len(self.success_accounts)}\n")
                f.write(f"- Sai mật khẩu: {len(self.wrong_password_accounts)}\n")
                f.write(f"- Lỗi kỹ thuật: {len(self.error_accounts)}\n")
                f.write(f"- Tổng đã xử lý: {self.processed_count}\n\n")
                
                f.write(f"## DANH SÁCH {len(self.success_accounts)} TÀI KHOẢN HOẠT ĐỘNG:\n")
                for acc in self.success_accounts:
                    f.write(f"{acc['username']}|{acc['password']}\n")
                
                if self.wrong_password_accounts:
                    f.write(f"\n## DANH SÁCH {len(self.wrong_password_accounts)} TÀI KHOẢN SAI MẬT KHẨU:\n")
                    for acc in self.wrong_password_accounts:
                        f.write(f"{acc['username']}|{acc['password']}\n")
            
            self.log("✅ Đã tạo accstatus.txt cuối cùng", "SUCCESS")
            
        except Exception as e:
            self.log(f"Lỗi tạo báo cáo: {e}", "ERROR")
    
    def run_mass_fresh_browser_test(self):
        """Chạy test với Chrome ẩn danh MỚI cho MỖI tài khoản"""
        print("🚀 MASS ULTRA FAST - MỖI TÀI KHOẢN MỘT CHROME ẨN DANH MỚI")
        print("="*80)
        print("🔄 Mỗi tài khoản = Mở Chrome ẩn danh mới → Test → Đóng")
        print("⚡ SIÊU NHANH - Không chụp ảnh")
        print("💾 Lưu tiến trình mỗi 50 tài khoản")
        print("❌ Có 'Wrong password' = SAI MẬT KHẨU")
        print("✅ Không có = ĐĂNG NHẬP THÀNH CÔNG")
        print("="*80)
        
        accounts = self.load_all_accounts()
        if not accounts:
            return
        
        total_accounts = len(accounts)
        
        try:
            for username, password, index in accounts:
                self.processed_count += 1
                
                # Hiển thị tiến trình mỗi 5 tài khoản
                if self.processed_count % 5 == 0:
                    elapsed = datetime.now() - self.start_time
                    if elapsed.total_seconds() > 0:
                        speed = self.processed_count / elapsed.total_seconds() * 60  # tài khoản/phút
                        eta_minutes = (total_accounts - self.processed_count) / (speed / 60) if speed > 0 else 0
                        print(f"⚡ {self.processed_count}/{total_accounts} | ✅{len(self.success_accounts)} ❌{len(self.wrong_password_accounts)} | {speed:.1f} tk/phút | ETA: {eta_minutes:.0f}p")
                
                try:
                    # Test tài khoản với Chrome ẩn danh mới
                    result = self.test_single_account_with_fresh_browser(username, password, index)
                    
                    # Phân loại kết quả
                    if result["status"] == "success":
                        self.success_accounts.append(result)
                        self.log(f"✅ TK{index}: {username[:20]}... → THÀNH CÔNG", "SUCCESS")
                    elif result["status"] == "wrong_password":
                        self.wrong_password_accounts.append(result)
                        self.log(f"❌ TK{index}: {username[:20]}... → SAI PASSWORD", "ERROR")
                    else:
                        self.error_accounts.append(result)
                        self.log(f"💥 TK{index}: {username[:20]}... → LỖI: {result['description'][:30]}", "WARNING")
                    
                    # Lưu tiến trình mỗi 50 tài khoản
                    self.save_progress_every_50()
                    
                    # Nghỉ ngắn giữa các tài khoản để Chrome có thời gian đóng hoàn toàn
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    self.log("⚠️ Dừng test bởi người dùng", "WARNING")
                    raise
                except Exception as e:
                    self.log(f"❌ Lỗi TK {index}: {e}", "ERROR")
                    self.error_accounts.append({
                        "index": index, "username": username, "password": password,
                        "status": "error", "description": f"Exception: {str(e)[:50]}"
                    })
                    continue
            
            # Tạo báo cáo cuối cùng
            self.create_final_mass_report()
            
            # Tổng kết cuối cùng
            elapsed = datetime.now() - self.start_time
            speed = total_accounts / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
            
            print(f"\n{'='*100}")
            self.log("🎉 HOÀN THÀNH TẤT CẢ!", "SUCCESS")
            print("="*100)
            print(f"📊 TỔNG KẾT CUỐI CÙNG:")
            print(f"   ✅ Đăng nhập thành công: {len(self.success_accounts)}/{total_accounts} ({len(self.success_accounts)/total_accounts*100:.1f}%)")
            print(f"   ❌ Sai mật khẩu: {len(self.wrong_password_accounts)}/{total_accounts} ({len(self.wrong_password_accounts)/total_accounts*100:.1f}%)")
            print(f"   💥 Lỗi kỹ thuật: {len(self.error_accounts)}/{total_accounts} ({len(self.error_accounts)/total_accounts*100:.1f}%)")
            print(f"   ⏱️ Thời gian: {elapsed}")
            print(f"   ⚡ Tốc độ trung bình: {speed:.1f} tài khoản/phút")
            print("="*100)
            print(f"📄 Kết quả cuối cùng: accstatus.txt")
            print(f"💾 Các file backup: mass_progress_*.txt")
            
        except KeyboardInterrupt:
            self.log("⚠️ Dừng test bởi người dùng", "WARNING")
            self.close_driver_completely()
            self.create_final_mass_report()
        except Exception as e:
            self.log(f"❌ Lỗi tổng quát: {e}", "ERROR")
            self.close_driver_completely()

def main():
    checker = MassUltraFastChecker()
    checker.run_mass_fresh_browser_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 