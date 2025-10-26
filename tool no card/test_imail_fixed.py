#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 FIXED IMAIL TEST
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

def test_imail_fixed():
    """Test imail with fixed element finding"""
    print("🔧 FIXED IMAIL TEST")
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
        time.sleep(5)
        
        driver.save_screenshot("fixed_step1_homepage.png")
        
        # Find username input - look for displayed inputs with name="user"
        print(f"\n🔍 Finding username input...")
        username_input = None
        
        # Try multiple selectors
        selectors_to_try = [
            "input[name='user'][type='text']",
            "input[id='user']",
            "input[placeholder*='Username']",
            "input[placeholder*='username']"
        ]
        
        for selector in selectors_to_try:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled():
                        username_input = inp
                        print(f"✅ Found username input with selector: {selector}")
                        break
                if username_input:
                    break
            except:
                continue
        
        if not username_input:
            print(f"❌ No username input found!")
            return
        
        # Generate username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{person['first_name'].lower()}{random_numbers}"
        expected_email = f"{username}@naka.edu.pl"
        
        print(f"📧 Expected email: {expected_email}")
        
        # Enter username
        print(f"\n📝 Entering username...")
        
        try:
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", username_input)
            time.sleep(1)
            
            # Clear and enter username
            username_input.clear()
            username_input.send_keys(username)
            
            print(f"✅ Username entered: {username}")
            driver.save_screenshot("fixed_step2_username_entered.png")
            
        except Exception as e:
            print(f"❌ Username input failed: {e}")
            return
        
        # Find domain selector (if needed)
        print(f"\n🔍 Finding domain selector...")
        try:
            domain_selectors = [
                "input[name='domain']",
                "select[name='domain']",
                "input[placeholder*='Domain']"
            ]
            
            domain_input = None
            for selector in domain_selectors:
                try:
                    inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        if inp.is_displayed():
                            domain_input = inp
                            print(f"✅ Found domain input: {selector}")
                            break
                    if domain_input:
                        break
                except:
                    continue
            
            if domain_input:
                # Check if naka.edu.pl is available
                domain_tag = domain_input.tag_name.lower()
                if domain_tag == "select":
                    # It's a dropdown
                    from selenium.webdriver.support.ui import Select
                    select = Select(domain_input)
                    
                    options = [opt.text for opt in select.options]
                    print(f"Domain options: {options}")
                    
                    # Try to select naka.edu.pl
                    for option in select.options:
                        if "naka.edu.pl" in option.text:
                            select.select_by_visible_text(option.text)
                            print(f"✅ Selected domain: {option.text}")
                            break
                else:
                    # It's an input field
                    domain_input.clear()
                    domain_input.send_keys("naka.edu.pl")
                    print(f"✅ Entered domain: naka.edu.pl")
        
        except Exception as e:
            print(f"⚠️ Domain selection failed: {e}")
        
        # Find and click create button
        print(f"\n🚀 Finding create button...")
        
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        print(f"Found {len(submit_buttons)} submit buttons")
        
        create_clicked = False
        for i, btn in enumerate(submit_buttons):
            if btn.is_displayed() and btn.is_enabled():
                btn_class = btn.get_attribute("class") or ""
                btn_value = btn.get_attribute("value") or ""
                
                print(f"  Button {i+1}: class='{btn_class}', value='{btn_value}'")
                
                # Try to click - prefer buttons with teal class
                if "bg-teal-500" in btn_class or "teal" in btn_class:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        btn.click()
                        print(f"✅ Clicked teal button!")
                        create_clicked = True
                        break
                    except Exception as e:
                        print(f"⚠️ Teal button failed: {e}")
        
        # If no teal button worked, try any submit button
        if not create_clicked:
            for btn in submit_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"✅ Clicked fallback button!")
                        create_clicked = True
                        break
                    except:
                        continue
        
        if not create_clicked:
            print(f"❌ No button could be clicked!")
        
        time.sleep(5)
        driver.save_screenshot("fixed_step3_after_create.png")
        
        # Check result
        print(f"\n🔍 Checking result...")
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        print(f"📄 URL: {current_url}")
        
        # Success indicators
        success_indicators = [
            expected_email.lower(),
            username.lower(),
            "naka.edu.pl",
            "email created",
            "success",
            "successful"
        ]
        
        found_indicators = [ind for ind in success_indicators if ind in page_source]
        
        if found_indicators:
            print(f"✅ Success indicators found: {found_indicators}")
        else:
            print(f"⚠️ No clear success indicators")
        
        # Check for inbox/email interface
        email_interface_indicators = [
            "inbox", "mailbox", "compose", "emails",
            "received", "sent", "messages"
        ]
        
        found_interface = [ind for ind in email_interface_indicators if ind in page_source]
        if found_interface:
            print(f"✅ Email interface detected: {found_interface}")
        
        print(f"\n⏰ Keeping browser open for 20s for manual inspection...")
        time.sleep(20)
        
        # Final summary
        print(f"\n📊 FINAL SUMMARY:")
        print(f"✉️ Target Email: {expected_email}")
        print(f"👤 Username: {username}")
        print(f"🌐 Final URL: {current_url}")
        print(f"🔄 Button Clicked: {create_clicked}")
        print(f"✅ Success Indicators: {found_indicators}")
        
    except Exception as e:
        print(f"❌ General error: {e}")
        if driver:
            driver.save_screenshot("fixed_error.png")
    
    finally:
        if driver:
            driver.quit()
            print(f"✅ Browser closed")

if __name__ == "__main__":
    test_imail_fixed() 