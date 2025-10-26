#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 SIMPLE TEST - DEBUG STEP BY STEP
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

def load_person_data():
    """Load dữ liệu người để đăng ký"""
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Lỗi đọc data: {e}")
        return None

def test_simple_flow():
    """Test đơn giản từng bước"""
    print("🔧 SIMPLE TEST - DEBUG STEP BY STEP")
    print("=" * 50)
    
    # Load data
    person = load_person_data()
    if not person:
        print("❌ Không có dữ liệu!")
        return
    
    print(f"✅ Data loaded: {person['full_name']}")
    
    driver = None
    
    try:
        # Setup browser
        print(f"\n🔧 Setup browser...")
        chrome_service = Service(ChromeDriverManager().install())
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 20)
        
        print(f"✅ Browser started")
        
        # Test extract gg from pdf: Open Santa Fe
        print(f"\n🌐 Test 1: Open Santa Fe...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(5)
        
        driver.save_screenshot("debug_step1_homepage.png")
        print(f"✅ Opened: {driver.title}")
        print(f"📄 URL: {driver.current_url}")
        
        # Test 2: Find start button
        print(f"\n🔍 Test 2: Find start button...")
        button_selector = "#mainContent > div > form > div > div > button"
        
        try:
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))
            print(f"✅ Found button: {button.text}")
            
            # Highlight button
            driver.execute_script("arguments[0].style.border='5px solid red'", button)
            time.sleep(2)
            
            driver.save_screenshot("debug_step2_button_found.png")
            
            # Click button
            button.click()
            time.sleep(3)
            
            driver.save_screenshot("debug_step3_after_click.png")
            print(f"✅ Clicked button")
            print(f"📄 New URL: {driver.current_url}")
            
        except Exception as e:
            print(f"❌ Button error: {e}")
            driver.save_screenshot("debug_step2_button_error.png")
        
        # Test 3: Find option extract gg from pdf
        print(f"\n🔍 Test 3: Find option 1...")
        option1_selector = "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div"
        
        try:
            option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, option1_selector)))
            print(f"✅ Found option 1")
            
            # Highlight
            driver.execute_script("arguments[0].style.border='5px solid blue'", option1)
            time.sleep(2)
            
            driver.save_screenshot("debug_step4_option1_found.png")
            
            # Click
            option1.click()
            time.sleep(2)
            print(f"✅ Clicked option 1")
            
        except Exception as e:
            print(f"❌ Option 1 error: {e}")
            driver.save_screenshot("debug_step4_option1_error.png")
        
        # Test 4: Find Next button
        print(f"\n🔍 Test 4: Find Next button...")
        next_selector = "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right"
        
        try:
            next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_selector)))
            print(f"✅ Found next button: {next_btn.text}")
            
            # Highlight
            driver.execute_script("arguments[0].style.border='5px solid green'", next_btn)
            time.sleep(2)
            
            driver.save_screenshot("debug_step5_next_found.png")
            
            # Click
            next_btn.click()
            time.sleep(3)
            print(f"✅ Clicked next")
            print(f"📄 New URL: {driver.current_url}")
            
            driver.save_screenshot("debug_step6_after_next.png")
            
        except Exception as e:
            print(f"❌ Next button error: {e}")
            driver.save_screenshot("debug_step5_next_error.png")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"📄 Final URL: {driver.current_url}")
        print(f"📋 Title: {driver.title}")
        print(f"🖼️ Screenshots saved with 'debug_' prefix")
        
        # Keep browser open
        print(f"\n⏰ Keeping browser open for 30s...")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ General error: {e}")
        if driver:
            driver.save_screenshot("debug_error.png")
    
    finally:
        if driver:
            print(f"🔄 Closing browser...")
            driver.quit()

if __name__ == "__main__":
    test_simple_flow() 