#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - QUICK TEST
File test nhanh các selectors
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 🎯 CÁC SELECTORS CẦN TEST
SELECTORS_TO_TEST = {
    "Button": "#mainContent > div > form > div > div > button",
    "Element_2": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div",
    "Element_3": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading"
}

def quick_test():
    """Test nhanh các selectors"""
    print("🚀 STARTING QUICK TEST...")
    print("🌐 Opening Santa Fe College website...")
    
    # Setup Chrome
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(service=Service("driver/chromedriver.exe"), options=opts)
    wait = WebDriverWait(driver, 20)
    
    try:
        # Mở website
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        print("⏳ Waiting for page load...")
        time.sleep(10)  # Đợi trang load
        
        print(f"📄 Page title: {driver.title}")
        print(f"🔗 Current URL: {driver.current_url}")
        
        # Test từng selector
        print("\n" + "="*50)
        print("🔍 TESTING SELECTORS...")
        
        for name, selector in SELECTORS_TO_TEST.items():
            print(f"\n🧪 Testing: {name}")
            print(f"📋 Selector: {selector}")
            
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                # Thông tin element
                tag = element.tag_name
                text = element.text.strip()[:100]  # Chỉ lấy 100 ký tự đầu
                displayed = element.is_displayed()
                enabled = element.is_enabled()
                
                print(f"   ✅ FOUND!")
                print(f"   📌 Tag: {tag}")
                print(f"   📝 Text: '{text}'")
                print(f"   👁️ Visible: {displayed}")
                print(f"   🔓 Enabled: {enabled}")
                
                # Nếu là button hoặc clickable, thử click
                if tag == "button" or "button" in element.get_attribute("class", "") or "btn" in element.get_attribute("class", ""):
                    print(f"   🖱️ Attempting click...")
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        element.click()
                        print(f"   ✅ Clicked successfully!")
                        time.sleep(3)
                    except Exception as e:
                        print(f"   ❌ Click failed: {e}")
                
            except Exception as e:
                print(f"   ❌ NOT FOUND: {e}")
        
        # Screenshot cuối
        driver.save_screenshot("sf_quick_test_result.png")
        print(f"\n📸 Screenshot saved: sf_quick_test_result.png")
        
        print("\n" + "="*50)
        print("🎉 QUICK TEST COMPLETED!")
        print("⏰ Keeping browser open for 15 seconds...")
        time.sleep(15)
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        driver.save_screenshot("sf_quick_test_error.png")
        
    finally:
        driver.quit()
        print("🧹 Browser closed")

if __name__ == "__main__":
    quick_test() 