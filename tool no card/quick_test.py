#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ QUICK TEST
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import random

def load_person_data():
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def quick_test_imail():
    """Quick test tạo email imail"""
    print("⚡ QUICK TEST IMAIL")
    print("=" * 30)
    
    person = load_person_data()
    if not person:
        print("❌ No data")
        return
    
    driver = None
    try:
        print(f"👤 Person: {person['first_name']}")
        
        opts = webdriver.ChromeOptions()
        opts.add_argument('--start-maximized')
        
        driver = webdriver.Chrome(options=opts)
        
        print(f"🌐 Opening imail.edu.vn...")
        driver.get("https://imail.edu.vn")
        time.sleep(3)
        
        driver.save_screenshot("quick_imail_homepage.png")
        print(f"✅ Screenshot saved")
        
        # Tạo username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{person['first_name'].lower()}{random_numbers}"
        expected_email = f"{username}@naka.edu.pl"
        
        print(f"📧 Expected email: {expected_email}")
        
        # Nhập username
        username_input = driver.find_element(By.ID, "user")
        username_input.clear()
        username_input.send_keys(username)
        time.sleep(1)
        
        driver.save_screenshot("quick_imail_username.png")
        print(f"✅ Username entered: {username}")
        
        # Thử click tạo email
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        print(f"📍 Found {len(submit_buttons)} submit buttons")
        
        for i, btn in enumerate(submit_buttons):
            btn_class = btn.get_attribute("class") or ""
            btn_value = btn.get_attribute("value") or ""
            print(f"  Button {i+1}: class='{btn_class}', value='{btn_value}'")
            
            if "bg-teal-500" in btn_class:
                btn.click()
                print(f"✅ Clicked create button!")
                break
        
        time.sleep(3)
        driver.save_screenshot("quick_imail_after_create.png")
        
        # Check page source for confirmation
        page_source = driver.page_source.lower()
        
        if expected_email.lower() in page_source:
            print(f"✅ Email confirmed in page: {expected_email}")
        else:
            print(f"⚠️ Email not found in page source")
        
        print(f"📄 Current URL: {driver.current_url}")
        print(f"📋 Title: {driver.title}")
        
        print(f"\n⏰ Keeping browser open for 10s...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if driver:
            driver.save_screenshot("quick_imail_error.png")
    
    finally:
        if driver:
            driver.quit()
            print(f"✅ Browser closed")

if __name__ == "__main__":
    quick_test_imail() 