#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 IMPROVED IMAIL TEST
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

def test_imail_improved():
    """Test imail with improved element finding"""
    print("🔧 IMPROVED IMAIL TEST")
    print("=" * 40)
    
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
        wait = WebDriverWait(driver, 10)
        
        print(f"🌐 Opening imail.edu.vn...")
        driver.get("https://imail.edu.vn")
        time.sleep(5)  # Wait longer for page load
        
        driver.save_screenshot("improved_step1_homepage.png")
        
        # Explore all input elements
        print(f"\n🔍 Finding input elements...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input elements:")
        
        username_input = None
        for i, inp in enumerate(inputs):
            inp_id = inp.get_attribute("id") or ""
            inp_name = inp.get_attribute("name") or ""
            inp_type = inp.get_attribute("type") or ""
            inp_placeholder = inp.get_attribute("placeholder") or ""
            is_displayed = inp.is_displayed()
            is_enabled = inp.is_enabled()
            
            print(f"  Input {i+1}: id='{inp_id}', name='{inp_name}', type='{inp_type}', placeholder='{inp_placeholder}', displayed={is_displayed}, enabled={is_enabled}")
            
            if inp_id == "user" and is_displayed and is_enabled:
                username_input = inp
                print(f"  ✅ Found username input!")
        
        if not username_input:
            print(f"❌ No suitable username input found!")
            return
        
        # Generate username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{person['first_name'].lower()}{random_numbers}"
        expected_email = f"{username}@naka.edu.pl"
        
        print(f"\n📧 Expected email: {expected_email}")
        
        # Try multiple ways to interact with username input
        print(f"\n📝 Entering username...")
        
        try:
            # Method extract gg from pdf: Scroll into view first
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", username_input)
            time.sleep(1)
            
            # Method 2: Clear and send keys
            username_input.clear()
            username_input.send_keys(username)
            
            print(f"✅ Username entered: {username}")
            driver.save_screenshot("improved_step2_username_entered.png")
            
        except Exception as e:
            print(f"❌ Username input error: {e}")
            
            # Try ActionChains
            try:
                actions = ActionChains(driver)
                actions.move_to_element(username_input).click().send_keys(username).perform()
                print(f"✅ Username entered via ActionChains: {username}")
            except Exception as e2:
                print(f"❌ ActionChains failed: {e2}")
                return
        
        # Find submit buttons
        print(f"\n🔍 Finding submit buttons...")
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        print(f"Found {len(submit_buttons)} submit buttons:")
        
        for i, btn in enumerate(submit_buttons):
            btn_class = btn.get_attribute("class") or ""
            btn_value = btn.get_attribute("value") or ""
            btn_id = btn.get_attribute("id") or ""
            is_displayed = btn.is_displayed()
            is_enabled = btn.is_enabled()
            
            print(f"  Button {i+1}: id='{btn_id}', class='{btn_class}', value='{btn_value}', displayed={is_displayed}, enabled={is_enabled}")
        
        # Try to click create button
        print(f"\n🚀 Trying to create email...")
        
        create_clicked = False
        for btn in submit_buttons:
            btn_class = btn.get_attribute("class") or ""
            if "bg-teal-500" in btn_class and btn.is_displayed() and btn.is_enabled():
                try:
                    # Scroll to button
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(1)
                    
                    # Try click
                    btn.click()
                    print(f"✅ Clicked create button!")
                    create_clicked = True
                    break
                    
                except Exception as e:
                    print(f"⚠️ Button click failed: {e}")
                    
                    # Try JavaScript click
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"✅ JavaScript clicked create button!")
                        create_clicked = True
                        break
                    except Exception as e2:
                        print(f"❌ JavaScript click failed: {e2}")
        
        if not create_clicked:
            print(f"❌ Could not click any create button!")
            
            # Try manual approach - click any submit button
            for btn in submit_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"✅ Clicked fallback button!")
                        create_clicked = True
                        break
                    except:
                        continue
        
        time.sleep(5)
        driver.save_screenshot("improved_step3_after_create.png")
        
        # Check result
        print(f"\n🔍 Checking result...")
        current_url = driver.current_url
        page_title = driver.title
        page_source = driver.page_source.lower()
        
        print(f"📄 URL: {current_url}")
        print(f"📋 Title: {page_title}")
        
        # Look for email confirmation
        if expected_email.lower() in page_source:
            print(f"✅ Email confirmed: {expected_email}")
        elif username.lower() in page_source:
            print(f"✅ Username found in page: {username}")
        elif "naka.edu.pl" in page_source:
            print(f"✅ Domain found in page")
        else:
            print(f"⚠️ No obvious confirmation found")
        
        # Look for error messages
        error_keywords = ["error", "failed", "invalid", "không", "lỗi"]
        found_errors = [kw for kw in error_keywords if kw in page_source]
        if found_errors:
            print(f"⚠️ Possible errors: {found_errors}")
        
        print(f"\n⏰ Keeping browser open for 15s for manual inspection...")
        time.sleep(15)
        
        # Final result
        print(f"\n📊 FINAL RESULT:")
        print(f"✉️ Expected Email: {expected_email}")
        print(f"👤 Username: {username}")
        print(f"🌐 Final URL: {current_url}")
        print(f"🔄 Create Button Clicked: {create_clicked}")
        
    except Exception as e:
        print(f"❌ General error: {e}")
        if driver:
            driver.save_screenshot("improved_error.png")
    
    finally:
        if driver:
            driver.quit()
            print(f"✅ Browser closed")

if __name__ == "__main__":
    test_imail_improved() 