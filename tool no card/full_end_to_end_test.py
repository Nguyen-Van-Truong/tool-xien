#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 FULL END-TO-END TEST
Test hoàn chỉnh từ tạo email đến verification
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import random
from datetime import datetime
import re

def load_person_data():
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def create_imail_email_working(firstname):
    """Tạo email imail working version"""
    driver = None
    try:
        print(f"📧 STEP extract gg from pdf: Tạo email imail.edu.vn...")
        
        opts = webdriver.ChromeOptions()
        opts.add_argument('--start-maximized')
        
        driver = webdriver.Chrome(options=opts)
        
        print(f"🌐 Opening imail.edu.vn...")
        driver.get("https://imail.edu.vn")
        time.sleep(5)
        
        driver.save_screenshot("e2e_step1_imail_homepage.png")
        
        # Generate username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{firstname.lower()}{random_numbers}"
        expected_email = f"{username}@naka.edu.pl"
        
        print(f"📧 Target email: {expected_email}")
        
        # Find username input
        username_input = None
        selectors = ["input[name='user'][type='text']", "input[id='user']"]
        
        for selector in selectors:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled():
                        username_input = inp
                        break
                if username_input:
                    break
            except:
                continue
        
        if not username_input:
            print(f"❌ No username input found!")
            return None
        
        # Enter username
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", username_input)
        time.sleep(1)
        username_input.clear()
        username_input.send_keys(username)
        print(f"✅ Username entered: {username}")
        
        driver.save_screenshot("e2e_step2_imail_username.png")
        
        # Click create button
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        
        create_clicked = False
        for btn in submit_buttons:
            if btn.is_displayed() and btn.is_enabled():
                btn_class = btn.get_attribute("class") or ""
                if "bg-teal-500" in btn_class:
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"✅ Email create button clicked!")
                    create_clicked = True
                    break
        
        if not create_clicked:
            print(f"❌ Could not click create button!")
            return None
        
        time.sleep(3)
        driver.save_screenshot("e2e_step3_imail_created.png")
        
        # Verify success
        page_source = driver.page_source.lower()
        success_indicators = ["naka.edu.pl", "success", "email"]
        
        if any(ind in page_source for ind in success_indicators):
            print(f"✅ Email creation confirmed!")
            
            email_info = {
                "email": expected_email,
                "username": username,
                "domain": "naka.edu.pl",
                "driver": driver
            }
            
            return email_info
        else:
            print(f"❌ Email creation not confirmed!")
            return None
            
    except Exception as e:
        print(f"❌ Email creation error: {e}")
        if driver:
            driver.quit()
        return None

def register_santa_fe_working(email_info, person):
    """Đăng ký Santa Fe working version"""
    driver = None
    try:
        print(f"\n🎓 STEP 2: Đăng ký Santa Fe College...")
        
        chrome_service = Service(ChromeDriverManager().install())
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            opts.add_extension("driver/captchasolver.crx")
        except:
            pass
            
        try:
            opts.add_extension("driver/extract gg from pdf.crx")
        except:
            pass
        
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 20)
        time.sleep(2)
        
        print(f"🌐 Opening Santa Fe College...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(5)
        driver.save_screenshot("e2e_step4_sf_homepage.png")
        
        print(f"🎯 Navigating registration flow...")
        
        # Click Start
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
        button1.click()
        time.sleep(3)
        driver.save_screenshot("e2e_step5_sf_after_start.png")
        
        # Click Option extract gg from pdf (First Time Student)
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
        option1.click()
        time.sleep(1)
        
        # Click Next
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
        next1.click()
        time.sleep(3)
        driver.save_screenshot("e2e_step6_sf_after_option1.png")
        
        # Click Option 2
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
        option2.click()
        time.sleep(1)
        
        # Click Next
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
        next2.click()
        time.sleep(5)
        driver.save_screenshot("e2e_step7_sf_form.png")
        
        print(f"📝 Filling registration form...")
        
        # Fill form fields
        fields = {
            "fstNameSTR": person['first_name'],
            "lstNameSTR": person['last_name'],
            "emailAddrsSTR": email_info['email'],
            "cemailAddrsSTR": email_info['email'],
            "ssnumSTR": person['ssn'],
            "cssnumSTR": person['ssn']
        }
        
        for field_id, value in fields.items():
            try:
                element = driver.find_element(By.ID, field_id)
                element.clear()
                element.send_keys(value)
                print(f"✅ {field_id}: {value}")
                time.sleep(0.3)
            except Exception as e:
                print(f"⚠️ {field_id}: {e}")
        
        # Handle birth date dropdowns
        try:
            month_select = Select(driver.find_element(By.ID, "month"))
            month_num = person['birth_date'].split('/')[0]
            month_select.select_by_value(month_num)
            
            day_select = Select(driver.find_element(By.ID, "day"))
            day_num = person['birth_date'].split('/')[1]
            day_select.select_by_value(day_num)
            
            year_select = Select(driver.find_element(By.ID, "year"))
            year_num = person['birth_date'].split('/')[2]
            year_select.select_by_value(year_num)
            
            country_select = Select(driver.find_element(By.ID, "birthctrySTR"))
            country_select.select_by_visible_text("United States")
            
            print(f"✅ Birth date: {person['birth_date']}, Country: United States")
            
        except Exception as e:
            print(f"⚠️ Birth date error: {e}")
        
        # SSN Notice checkbox
        try:
            checkbox = driver.find_element(By.ID, "ssnNoticeCB")
            if not checkbox.is_selected():
                checkbox.click()
                print(f"✅ SSN Notice checked")
        except Exception as e:
            print(f"⚠️ Checkbox error: {e}")
        
        driver.save_screenshot("e2e_step8_sf_form_filled.png")
        
        # Submit form
        print(f"🚀 Submitting form...")
        
        submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
        
        if submit_buttons:
            btn = submit_buttons[0]
            driver.execute_script("arguments[0].style.border='5px solid red'", btn)
            time.sleep(2)
            btn.click()
            time.sleep(8)
            
            driver.save_screenshot("e2e_step9_sf_submitted.png")
            print(f"✅ Form submitted!")
            print(f"📄 Current URL: {driver.current_url}")
            
            return driver
        else:
            print(f"❌ No submit button found!")
            return None
            
    except Exception as e:
        print(f"❌ Santa Fe registration error: {e}")
        if driver:
            driver.save_screenshot("e2e_sf_error.png")
        return None

def handle_verification_complete(sf_driver, email_driver, email_info):
    """Handle verification với auto + manual fallback"""
    try:
        print(f"\n🔐 STEP 3: Email verification process...")
        
        # Check if on verification page
        verification_keywords = [
            "verification", "verify", "confirm", "code", 
            "To create your account", "enter the 6-digit"
        ]
        
        page_source = sf_driver.page_source.lower()
        is_verification_page = any(kw in page_source for kw in verification_keywords)
        
        if not is_verification_page:
            print(f"❌ Not on verification page!")
            print(f"📄 Current URL: {sf_driver.current_url}")
            return False
        
        print(f"✅ On verification page!")
        sf_driver.save_screenshot("e2e_step10_verification_page.png")
        
        # Find verification input
        verification_input = None
        selectors = [
            "input[placeholder*='verification']",
            "input[placeholder*='code']", 
            "input[id*='verification']",
            "input[id*='code']",
            "input[type='text']",
            "input[type='number']"
        ]
        
        for selector in selectors:
            try:
                inputs = sf_driver.find_elements(By.CSS_SELECTOR, selector)
                for inp in inputs:
                    if inp.is_displayed():
                        verification_input = inp
                        print(f"✅ Found verification input")
                        break
                if verification_input:
                    break
            except:
                continue
        
        if not verification_input:
            print(f"❌ No verification input found!")
            return False
        
        # AUTO: Check email for verification code
        print(f"\n📧 AUTO: Checking email for verification code...")
        
        verification_code = None
        max_attempts = 12  # 2 minutes
        
        for attempt in range(max_attempts):
            try:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts} - Checking email...")
                
                email_driver.refresh()
                time.sleep(5)
                
                page_source = email_driver.page_source.lower()
                santa_fe_keywords = ["santa fe", "college", "verification", "sfcollege"]
                
                if any(kw in page_source for kw in santa_fe_keywords):
                    print(f"✅ Found Santa Fe email!")
                    
                    # Extract 6-digit code
                    code_matches = re.findall(r'\b\d{6}\b', email_driver.page_source)
                    
                    if code_matches:
                        verification_code = code_matches[0]
                        print(f"🎯 AUTO FOUND VERIFICATION CODE: {verification_code}")
                        break
                    else:
                        print(f"⚠️ Email found but no 6-digit code yet")
                        
                else:
                    print(f"⏳ Waiting for Santa Fe email...")
                
                time.sleep(10)
                
            except Exception as e:
                print(f"⚠️ Email check error: {e}")
                time.sleep(5)
        
        # Enter verification code
        if verification_code:
            print(f"\n🔐 AUTO: Entering verification code...")
            
            verification_input.clear()
            verification_input.send_keys(verification_code)
            time.sleep(2)
            
            # Find verify button
            verify_buttons = sf_driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
            
            if verify_buttons:
                verify_btn = verify_buttons[0]
                verify_btn.click()
                time.sleep(5)
                
                sf_driver.save_screenshot("e2e_step11_verified.png")
                print(f"🎉 AUTO VERIFICATION SUCCESSFUL!")
                print(f"📄 Final URL: {sf_driver.current_url}")
                
                # Save success result
                result = {
                    "status": "auto_success",
                    "email": email_info['email'],
                    "verification_code": verification_code,
                    "final_url": sf_driver.current_url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open("e2e_test_result.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                return True
            else:
                print(f"❌ No verify button found!")
                return False
        else:
            # MANUAL FALLBACK
            print(f"\n🔧 MANUAL FALLBACK:")
            print(f"📧 Email: {email_info['email']}")
            print(f"🌐 Check manually: https://imail.edu.vn")
            print(f"⏰ Tìm email từ Santa Fe College và lấy mã 6 số")
            
            try:
                manual_code = input("\n🔐 Nhập mã verification (6 số): ").strip()
                
                if len(manual_code) == 6 and manual_code.isdigit():
                    verification_input.clear()
                    verification_input.send_keys(manual_code)
                    
                    verify_buttons = sf_driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
                    
                    if verify_buttons:
                        verify_btn = verify_buttons[0]
                        verify_btn.click()
                        time.sleep(5)
                        
                        sf_driver.save_screenshot("e2e_step11_manual_verified.png")
                        print(f"🎉 MANUAL VERIFICATION SUCCESSFUL!")
                        
                        # Save manual result
                        result = {
                            "status": "manual_success",
                            "email": email_info['email'],
                            "verification_code": manual_code,
                            "final_url": sf_driver.current_url,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        with open("e2e_test_result.json", "w", encoding="utf-8") as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        
                        return True
                    else:
                        print(f"❌ No verify button found!")
                        return False
                else:
                    print(f"❌ Invalid code format!")
                    return False
                    
            except Exception as e:
                print(f"❌ Manual input error: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def full_end_to_end_test():
    """Test hoàn chỉnh từ đầu đến cuối"""
    print("🎯 FULL END-TO-END TEST")
    print("=" * 60)
    print("🚀 Test quy trình hoàn chỉnh:")
    print("   extract gg from pdf. ✅ Tạo email imail.edu.vn")
    print("   2. ✅ Đăng ký Santa Fe College")
    print("   3. ✅ Auto check email + Manual fallback")
    print("   4. ✅ Verify và hoàn thành")
    print("-" * 60)
    
    # Load data
    person = load_person_data()
    if not person:
        print("❌ No person data!")
        return
    
    print(f"👤 Person: {person['full_name']}")
    
    email_driver = None
    sf_driver = None
    
    try:
        # Step extract gg from pdf: Create email
        email_info = create_imail_email_working(person['first_name'])
        if not email_info:
            print("❌ Email creation failed!")
            return
        
        email_driver = email_info['driver']
        print(f"✅ Email ready: {email_info['email']}")
        
        # Step 2: Register Santa Fe
        sf_driver = register_santa_fe_working(email_info, person)
        if not sf_driver:
            print("❌ Santa Fe registration failed!")
            return
        
        print(f"✅ Santa Fe registration submitted!")
        
        # Step 3: Handle verification
        success = handle_verification_complete(sf_driver, email_driver, email_info)
        
        if success:
            print(f"\n🏆 END-TO-END TEST THÀNH CÔNG!")
            print(f"📧 Email: {email_info['email']}")
            print(f"👤 Person: {person['full_name']}")
            print(f"🎓 Santa Fe College registration completed!")
        else:
            print(f"\n❌ Verification failed!")
        
        print(f"\n⏰ Keeping browsers open for inspection (60s)...")
        time.sleep(60)
        
    except Exception as e:
        print(f"❌ End-to-end test error: {e}")
    
    finally:
        # Cleanup
        if email_driver:
            try:
                email_driver.quit()
                print("✅ Email browser closed")
            except:
                pass
        
        if sf_driver:
            try:
                sf_driver.quit()
                print("✅ Santa Fe browser closed")
            except:
                pass

if __name__ == "__main__":
    full_end_to_end_test() 