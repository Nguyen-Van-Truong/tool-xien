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

def setup_driver():
    """Thiết lập Chrome driver đơn giản"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')
        
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
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        else:
            # Nếu không tìm thấy chromedriver, thử không dùng service
            driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Chrome driver đã được khởi tạo")
        return driver
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo driver: {e}")
        print("💡 Hãy đảm bảo Chrome và ChromeDriver đã được cài đặt")
        return None

def test_google_login(driver, username, password):
    """Test đăng nhập Google"""
    try:
        print(f"\n🔍 Testing: {username}")
        
        # Mở trang đăng nhập Google
        driver.get("https://accounts.google.com/signin")
        time.sleep(3)
        
        # Nhập email
        try:
            email_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_input.clear()
            email_input.send_keys(username)
            time.sleep(1)
            
            # Nhấn Next
            next_button = driver.find_element(By.ID, "identifierNext")
            next_button.click()
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Lỗi nhập email: {e}")
            return "error"
        
        # Kiểm tra lỗi email
        try:
            error_elements = driver.find_elements(By.CSS_SELECTOR, '[role="alert"]')
            for error_element in error_elements:
                if error_element.text and 'find' in error_element.text.lower():
                    print(f"❌ Email không tồn tại: {username}")
                    return "invalid_email"
        except:
            pass
        
        # Nhập password
        try:
            password_input = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.NAME, "password"))
            )
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(1)
            
            # Nhấn Next
            password_next = driver.find_element(By.ID, "passwordNext")
            password_next.click()
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Lỗi nhập password: {e}")
            return "error"
        
        # Kiểm tra kết quả
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        if "myaccount.google.com" in current_url:
            print(f"✅ THÀNH CÔNG: {username}")
            return "success"
        elif "wrong password" in page_source or "incorrect" in page_source:
            print(f"❌ Sai mật khẩu: {username}")
            return "wrong_password"
        elif "suspended" in page_source or "disabled" in page_source:
            print(f"⚠️ Tài khoản bị khóa: {username}")
            return "blocked"
        elif "verify" in page_source or "phone" in page_source:
            print(f"⚠️ Cần xác minh: {username}")
            return "need_verification"
        else:
            print(f"❓ Không rõ kết quả: {username}")
            return "unknown"
            
    except Exception as e:
        print(f"❌ Lỗi test {username}: {e}")
        return "error"

def load_test_accounts(count=5):
    """Tải một vài tài khoản để test"""
    try:
        with open("students_accounts.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        accounts = []
        for line in lines[:count]:
            line = line.strip()
            if '|' in line:
                username, password = line.split('|', 1)
                accounts.append((username.strip(), password.strip()))
        
        print(f"📚 Đã tải {len(accounts)} tài khoản để test")
        return accounts
        
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return []

def main():
    print("🧪 QUICK TEST GOOGLE LOGIN")
    print("=" * 50)
    
    # Nhập số lượng tài khoản muốn test
    try:
        count = int(input("➤ Số lượng tài khoản muốn test (mặc định 5): ") or "5")
    except ValueError:
        count = 5
    
    # Tải tài khoản
    accounts = load_test_accounts(count)
    if not accounts:
        print("❌ Không có tài khoản để test")
        return
    
    # Thiết lập driver
    driver = setup_driver()
    if not driver:
        print("❌ Không thể khởi tạo driver")
        return
    
    successful_accounts = []
    
    try:
        for i, (username, password) in enumerate(accounts, 1):
            print(f"\n[{i}/{len(accounts)}] Testing account...")
            
            result = test_google_login(driver, username, password)
            
            if result == "success":
                successful_accounts.append((username, password))
                print(f"🎉 Tìm thấy tài khoản hợp lệ: {username}")
            
            # Nghỉ giữa các lần test
            if i < len(accounts):
                delay = random.uniform(3, 8)
                print(f"⏳ Nghỉ {delay:.1f}s...")
                time.sleep(delay)
    
    except KeyboardInterrupt:
        print("\n⚠️ Đã dừng test")
    
    finally:
        # Lưu kết quả
        if successful_accounts:
            with open("test_successful_accounts.txt", 'w', encoding='utf-8') as f:
                for username, password in successful_accounts:
                    f.write(f"{username}|{password}\n")
            print(f"\n✅ Đã lưu {len(successful_accounts)} tài khoản thành công vào test_successful_accounts.txt")
        else:
            print("\n❌ Không tìm thấy tài khoản nào hợp lệ")
        
        # Đóng driver
        driver.quit()
        print("🔒 Đã đóng trình duyệt")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng chương trình!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 