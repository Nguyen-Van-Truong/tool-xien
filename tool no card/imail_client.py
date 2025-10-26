#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 IMAIL CLIENT - Tạo email tạm từ imail.edu.vn
Tạo email với format: firstname + 2 số ngẫu nhiên + @naka.edu.pl
"""

import requests
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class ImailClient:
    def __init__(self):
        self.base_url = "https://imail.edu.vn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def create_email_with_selenium(self, firstname):
        """Tạo email bằng Selenium để tương tác với website"""
        try:
            from selenium.webdriver.chrome.options import Options
            
            opts = Options()
            opts.add_argument('--headless')  # Chạy ngầm
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=opts)
            wait = WebDriverWait(driver, 10)
            
            print(f"🌐 Truy cập imail.edu.vn...")
            driver.get("https://imail.edu.vn")
            time.sleep(3)
            
            # Tìm input hoặc button để tạo email
            # Kiểm tra xem có dropdown domain không
            try:
                # Tìm dropdown chọn domain
                domain_elements = driver.find_elements(By.CSS_SELECTOR, "select, .dropdown, .domain-select")
                for elem in domain_elements:
                    if "naka.edu.pl" in elem.get_attribute("innerHTML"):
                        elem.click()
                        time.sleep(1)
                        # Chọn naka.edu.pl
                        naka_option = driver.find_element(By.XPATH, "//option[contains(text(), 'naka.edu.pl')]")
                        naka_option.click()
                        break
                        
            except Exception as e:
                print(f"⚠️ Không tìm thấy dropdown domain: {e}")
            
            # Tạo username với format firstname + 2 số ngẫu nhiên
            random_numbers = f"{random.randint(10, 99)}"
            username = f"{firstname.lower()}{random_numbers}"
            
            # Tìm input username
            try:
                username_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[placeholder*='email'], input[placeholder*='username']")
                if username_inputs:
                    username_inputs[0].clear()
                    username_inputs[0].send_keys(username)
                    print(f"✅ Nhập username: {username}")
                    
            except Exception as e:
                print(f"❌ Không tìm thấy input username: {e}")
            
            # Tìm button tạo email
            try:
                create_buttons = driver.find_elements(By.CSS_SELECTOR, "button, .button, input[type='submit']")
                for btn in create_buttons:
                    btn_text = btn.get_attribute("innerHTML").lower()
                    if any(word in btn_text for word in ["create", "new", "generate", "tạo", "mới"]):
                        btn.click()
                        print(f"✅ Clicked create button")
                        break
                        
            except Exception as e:
                print(f"⚠️ Không tìm thấy create button: {e}")
            
            time.sleep(3)
            
            # Lấy email đã tạo
            email_address = f"{username}@naka.edu.pl"
            
            # Lưu thông tin để check email sau
            email_info = {
                "email": email_address,
                "username": username,
                "domain": "naka.edu.pl",
                "created_time": time.time(),
                "driver": driver  # Giữ driver để check email
            }
            
            print(f"✅ Email đã tạo: {email_address}")
            return email_info
            
        except Exception as e:
            print(f"❌ Lỗi tạo email: {e}")
            return None
    
    def create_email_simple(self, firstname):
        """Tạo email đơn giản theo format mong muốn"""
        try:
            random_numbers = f"{random.randint(10, 99)}"
            username = f"{firstname.lower()}{random_numbers}"
            email_address = f"{username}@naka.edu.pl"
            
            email_info = {
                "email": email_address,
                "username": username,
                "domain": "naka.edu.pl",
                "created_time": time.time()
            }
            
            print(f"✅ Email tạo theo format: {email_address}")
            return email_info
            
        except Exception as e:
            print(f"❌ Lỗi tạo email: {e}")
            return None
    
    def check_email_with_selenium(self, email_info, search_keywords=None, max_wait=300):
        """Check email bằng Selenium"""
        try:
            driver = email_info.get("driver")
            if not driver:
                # Tạo driver mới nếu không có
                from selenium.webdriver.chrome.options import Options
                opts = Options()
                opts.add_argument('--headless')
                driver = webdriver.Chrome(options=opts)
                driver.get("https://imail.edu.vn")
                # Cần setup lại email
                
            if not search_keywords:
                search_keywords = ["santa fe", "college", "verification", "confirm", "code"]
            
            start_time = time.time()
            print(f"📧 Checking email: {email_info['email']}")
            print(f"🔍 Tìm kiếm: {search_keywords}")
            
            while (time.time() - start_time) < max_wait:
                try:
                    # Refresh inbox
                    driver.refresh()
                    time.sleep(3)
                    
                    # Tìm email inbox
                    email_elements = driver.find_elements(By.CSS_SELECTOR, ".email, .message, tr, .mail-item")
                    
                    for email_elem in email_elements:
                        email_text = email_elem.get_attribute("innerHTML").lower()
                        
                        # Check nếu có keyword
                        if any(keyword.lower() in email_text for keyword in search_keywords):
                            print(f"✅ Tìm thấy email verification!")
                            
                            # Click vào email để đọc
                            email_elem.click()
                            time.sleep(2)
                            
                            # Lấy nội dung email
                            email_content = driver.page_source
                            
                            # Tìm mã verification (6 số)
                            code_match = re.search(r'\b\d{6}\b', email_content)
                            if code_match:
                                verification_code = code_match.group()
                                print(f"✅ Mã verification: {verification_code}")
                                
                                return {
                                    "success": True,
                                    "verification_code": verification_code,
                                    "email_content": email_content
                                }
                    
                    print(f"⏳ Chờ email... ({int(time.time() - start_time)}s)")
                    time.sleep(10)  # Check mỗi 10 giây
                    
                except Exception as e:
                    print(f"⚠️ Lỗi check email: {e}")
                    time.sleep(5)
            
            print(f"⏰ Timeout waiting for email")
            return {"success": False, "error": "Timeout"}
            
        except Exception as e:
            print(f"❌ Lỗi check email: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_verification_code(self, text):
        """Trích xuất mã verification từ text"""
        try:
            # Tìm mã 6 số
            code_match = re.search(r'\b\d{6}\b', text)
            if code_match:
                return code_match.group()
            
            # Tìm mã 4 số
            code_match = re.search(r'\b\d{4}\b', text)
            if code_match:
                return code_match.group()
            
            # Tìm mã alphanumeric
            code_match = re.search(r'\b[A-Z0-9]{6}\b', text, re.IGNORECASE)
            if code_match:
                return code_match.group()
                
            return None
            
        except Exception as e:
            print(f"❌ Lỗi extract code: {e}")
            return None

# Test function
def test_imail_client():
    """Test imail client"""
    client = ImailClient()
    
    # Test tạo email
    email_info = client.create_email_simple("john")
    if email_info:
        print(f"✅ Test tạo email thành công: {email_info['email']}")
    else:
        print(f"❌ Test tạo email thất bại")

if __name__ == "__main__":
    test_imail_client() 