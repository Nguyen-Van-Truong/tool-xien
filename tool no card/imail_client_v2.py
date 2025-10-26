#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 IMAIL CLIENT V2 - Improved version
Tạo email với imail.edu.vn dựa trên kết quả khám phá
"""

import requests
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

class ImailClientV2:
    def __init__(self):
        self.base_url = "https://imail.edu.vn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def create_email_with_selenium(self, firstname):
        """Tạo email bằng Selenium với flow đã khám phá"""
        try:
            from selenium.webdriver.chrome.options import Options
            
            opts = Options()
            opts.add_argument('--start-maximized')
            opts.add_argument('--disable-blink-features=AutomationControlled')
            
            driver = webdriver.Chrome(options=opts)
            wait = WebDriverWait(driver, 10)
            
            print(f"🌐 Truy cập imail.edu.vn...")
            driver.get("https://imail.edu.vn")
            time.sleep(3)
            
            # Tạo username với format firstname + 2 số ngẫu nhiên
            random_numbers = f"{random.randint(10, 99)}"
            username = f"{firstname.lower()}{random_numbers}"
            
            print(f"📝 Username sẽ tạo: {username}")
            
            # Tìm input username (dựa trên kết quả khám phá)
            # ID: user, Name: user, Placeholder: Enter Username
            try:
                username_input = driver.find_element(By.ID, "user")
                username_input.clear()
                username_input.send_keys(username)
                print(f"✅ Đã nhập username: {username}")
                
                # Screenshot sau khi nhập
                driver.save_screenshot("imail_v2_step1_username_entered.png")
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Không tìm thấy username input: {e}")
                return None
            
            # Tìm dropdown domain (Name: domain, Placeholder: Select Domain)
            try:
                # Có thể là dropdown hoặc input có list
                domain_elements = driver.find_elements(By.NAME, "domain")
                
                if domain_elements:
                    domain_elem = domain_elements[0]
                    
                    # Click vào domain field
                    domain_elem.click()
                    time.sleep(1)
                    
                    # Tìm các options domain
                    # Từ kết quả khám phá, ta biết có naka.edu.pl
                    # Có thể là dropdown hoặc list hiện ra
                    
                    # Thử tìm naka.edu.pl trong page sau khi click
                    time.sleep(2)
                    naka_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'naka.edu.pl')]")
                    
                    if naka_elements:
                        naka_elem = naka_elements[0]
                        naka_elem.click()
                        print(f"✅ Đã chọn domain: naka.edu.pl")
                        
                        # Screenshot sau khi chọn domain
                        driver.save_screenshot("imail_v2_step2_domain_selected.png")
                        time.sleep(1)
                        
                    else:
                        print(f"⚠️ Không tìm thấy naka.edu.pl option")
                        
                else:
                    print(f"❌ Không tìm thấy domain dropdown")
                    
            except Exception as e:
                print(f"⚠️ Lỗi chọn domain: {e}")
            
            # Tìm submit button để tạo email
            # Từ kết quả khám phá: input[type='submit'] với bg-teal-500
            try:
                submit_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
                
                # Tìm button tạo email (thường là button đầu tiên hoặc có màu teal)
                create_button = None
                for btn in submit_buttons:
                    btn_class = btn.get_attribute("class")
                    if "bg-teal-500" in btn_class:
                        create_button = btn
                        break
                
                if create_button:
                    create_button.click()
                    print(f"✅ Đã click tạo email!")
                    time.sleep(3)
                    
                    # Screenshot sau khi tạo
                    driver.save_screenshot("imail_v2_step3_after_create.png")
                    
                else:
                    print(f"❌ Không tìm thấy create button")
                    
            except Exception as e:
                print(f"❌ Lỗi click create button: {e}")
            
            # Kiểm tra email đã tạo
            expected_email = f"{username}@naka.edu.pl"
            time.sleep(3)
            
            page_source = driver.page_source
            
            if expected_email in page_source:
                print(f"✅ SUCCESS! Email đã tạo: {expected_email}")
                
                email_info = {
                    "email": expected_email,
                    "username": username,
                    "domain": "naka.edu.pl",
                    "created_time": time.time(),
                    "driver": driver  # Giữ driver để check email sau
                }
                
                return email_info
                
            else:
                # Tìm email pattern khác
                email_pattern = rf"{username}@[\w\.-]+\.\w+"
                email_matches = re.findall(email_pattern, page_source)
                
                if email_matches:
                    actual_email = email_matches[0]
                    print(f"✅ Email tạo được: {actual_email}")
                    
                    email_info = {
                        "email": actual_email,
                        "username": username,
                        "domain": actual_email.split('@')[1],
                        "created_time": time.time(),
                        "driver": driver
                    }
                    
                    return email_info
                else:
                    print(f"❌ Không tìm thấy email nào được tạo")
                    return None
            
        except Exception as e:
            print(f"❌ Lỗi tạo email: {e}")
            return None
    
    def check_email_inbox(self, email_info, search_keywords=None, max_wait=300):
        """Check inbox để tìm email verification"""
        try:
            driver = email_info.get("driver")
            if not driver:
                print("❌ Không có driver để check email")
                return {"success": False, "error": "No driver"}
            
            if not search_keywords:
                search_keywords = ["santa fe", "college", "verification", "confirm", "code", "sfcollege"]
            
            start_time = time.time()
            print(f"📧 Checking inbox: {email_info['email']}")
            print(f"🔍 Tìm kiếm: {search_keywords}")
            
            # Tìm inbox area hoặc refresh button
            while (time.time() - start_time) < max_wait:
                try:
                    # Refresh trang
                    driver.refresh()
                    time.sleep(5)
                    
                    # Tìm trong page source cho email content
                    page_content = driver.page_source.lower()
                    
                    # Check nếu có keywords từ Santa Fe
                    keyword_found = False
                    for keyword in search_keywords:
                        if keyword.lower() in page_content:
                            keyword_found = True
                            break
                    
                    if keyword_found:
                        print(f"✅ Tìm thấy email từ Santa Fe College!")
                        
                        # Tìm verification code (6 digits)
                        code_matches = re.findall(r'\b\d{6}\b', driver.page_source)
                        
                        if code_matches:
                            # Lấy code có khả năng là verification code cao nhất
                            verification_code = code_matches[0]
                            print(f"✅ Mã verification: {verification_code}")
                            
                            return {
                                "success": True,
                                "verification_code": verification_code,
                                "email_content": driver.page_source
                            }
                    
                    elapsed = int(time.time() - start_time)
                    print(f"⏳ Chờ email... ({elapsed}s / {max_wait}s)")
                    time.sleep(10)  # Check mỗi 10 giây
                    
                except Exception as e:
                    print(f"⚠️ Lỗi check email: {e}")
                    time.sleep(5)
            
            print(f"⏰ Timeout waiting for email")
            return {"success": False, "error": "Timeout"}
            
        except Exception as e:
            print(f"❌ Lỗi check inbox: {e}")
            return {"success": False, "error": str(e)}
    
    def create_email_simple(self, firstname):
        """Tạo email đơn giản theo format"""
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

# Test function
def test_imail_v2():
    """Test imail client v2"""
    client = ImailClientV2()
    
    # Test tạo email thật
    print("🧪 TEST IMAIL CLIENT V2")
    print("=" * 50)
    
    firstname = "john"
    email_info = client.create_email_with_selenium(firstname)
    
    if email_info:
        print(f"✅ Test thành công: {email_info['email']}")
        
        # Test check email (giả lập)
        print(f"\n📧 Test check email...")
        # Không check thật vì chưa có email
        print(f"ℹ️ Để test check email, cần có email từ Santa Fe College")
        
        # Giữ driver mở
        print(f"\n⏰ Giữ browser mở để quan sát...")
        time.sleep(30)
        
        # Đóng driver
        if email_info.get("driver"):
            email_info["driver"].quit()
        
    else:
        print(f"❌ Test thất bại")

if __name__ == "__main__":
    test_imail_v2() 