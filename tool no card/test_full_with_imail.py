#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 FULL TEST WITH IMAIL
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
    """Load dữ liệu người để đăng ký"""
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Lỗi đọc data: {e}")
        return None

def create_imail_email(firstname):
    """Tạo email imail và return thông tin"""
    email_driver = None
    try:
        print(f"📧 STEP extract gg from pdf: Tạo email imail.edu.vn...")
        
        # Setup browser cho imail
        opts = webdriver.ChromeOptions()
        opts.add_argument('--start-maximized')
        
        email_driver = webdriver.Chrome(options=opts)
        
        # Truy cập imail
        email_driver.get("https://imail.edu.vn")
        time.sleep(3)
        email_driver.save_screenshot("imail_step1_homepage.png")
        
        # Tạo username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{firstname.lower()}{random_numbers}"
        expected_email = f"{username}@naka.edu.pl"
        
        print(f"📝 Username: {username}")
        print(f"📧 Expected email: {expected_email}")
        
        # Nhập username
        username_input = email_driver.find_element(By.ID, "user")
        username_input.clear()
        username_input.send_keys(username)
        time.sleep(2)
        email_driver.save_screenshot("imail_step2_username_entered.png")
        
        # Click tạo email
        submit_buttons = email_driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        
        for btn in submit_buttons:
            btn_class = btn.get_attribute("class") or ""
            if "bg-teal-500" in btn_class:
                btn.click()
                print(f"✅ Clicked create email button!")
                break
        
        time.sleep(5)
        email_driver.save_screenshot("imail_step3_after_create.png")
        
        email_info = {
            "email": expected_email,
            "username": username,
            "domain": "naka.edu.pl",
            "created_time": time.time(),
            "driver": email_driver
        }
        
        print(f"✅ Email created: {expected_email}")
        return email_info
        
    except Exception as e:
        print(f"❌ Lỗi tạo email: {e}")
        if email_driver:
            email_driver.save_screenshot("imail_error.png")
            email_driver.quit()
        return None

def register_santa_fe(email_info, person):
    """Đăng ký Santa Fe với email imail"""
    driver = None
    try:
        print(f"\n🎓 STEP 2: Đăng ký Santa Fe College...")
        
        # Setup browser
        chrome_service = Service(ChromeDriverManager().install())
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        # Add extensions if available
        try:
            opts.add_extension("driver/captchasolver.crx")
            print("✅ Captcha solver loaded")
        except:
            pass
            
        try:
            opts.add_extension("driver/extract gg from pdf.crx")
            print("✅ Extension loaded")
        except:
            pass
        
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 20)
        time.sleep(2)
        
        # Navigate Santa Fe flow
        print(f"\n🌐 Opening Santa Fe College...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(5)
        driver.save_screenshot("sf_step1_homepage.png")
        
        print(f"\n🎯 Navigating flow...")
        
        # Step extract gg from pdf: Click Start
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
        button1.click()
        time.sleep(3)
        driver.save_screenshot("sf_step2_after_start.png")
        
        # Step 2: Click Option extract gg from pdf (First Time Student)
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
        option1.click()
        time.sleep(1)
        
        # Click Next
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
        next1.click()
        time.sleep(3)
        driver.save_screenshot("sf_step3_after_option1.png")
        
        # Step 3: Click Option 2
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
        option2.click()
        time.sleep(1)
        
        # Click Next
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
        next2.click()
        time.sleep(5)
        driver.save_screenshot("sf_step4_registration_form.png")
        
        print(f"\n📝 Filling registration form...")
        
        # Fill form fields
        required_fields = {
            "fstNameSTR": person['first_name'],
            "lstNameSTR": person['last_name'],
            "emailAddrsSTR": email_info['email'],
            "cemailAddrsSTR": email_info['email'],
            "ssnumSTR": person['ssn'],
            "cssnumSTR": person['ssn']
        }
        
        for field_id, value in required_fields.items():
            try:
                element = driver.find_element(By.ID, field_id)
                element.clear()
                element.send_keys(value)
                print(f"✅ {field_id}: {value}")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Error {field_id}: {e}")
        
        # Handle dropdowns
        try:
            # Birth month
            month_select = Select(driver.find_element(By.ID, "month"))
            month_num = person['birth_date'].split('/')[0]
            month_select.select_by_value(month_num)
            print(f"✅ Month: {month_num}")
            
            # Birth day
            day_select = Select(driver.find_element(By.ID, "day"))
            day_num = person['birth_date'].split('/')[1]
            day_select.select_by_value(day_num)
            print(f"✅ Day: {day_num}")
            
            # Birth year
            year_select = Select(driver.find_element(By.ID, "year"))
            year_num = person['birth_date'].split('/')[2]
            year_select.select_by_value(year_num)
            print(f"✅ Year: {year_num}")
            
            # Birth country
            country_select = Select(driver.find_element(By.ID, "birthctrySTR"))
            country_select.select_by_visible_text("United States")
            print(f"✅ Country: United States")
            
        except Exception as e:
            print(f"⚠️ Dropdown error: {e}")
        
        # SSN Notice checkbox
        try:
            checkbox = driver.find_element(By.ID, "ssnNoticeCB")
            if not checkbox.is_selected():
                checkbox.click()
                print(f"✅ SSN Notice: Checked")
        except Exception as e:
            print(f"⚠️ Checkbox error: {e}")
        
        driver.save_screenshot("sf_step5_form_filled.png")
        
        # Submit form
        print(f"\n🚀 Submitting form...")
        
        submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
        
        if submit_buttons:
            btn = submit_buttons[0]
            driver.execute_script("arguments[0].style.border='5px solid red'", btn)
            time.sleep(2)
            btn.click()
            time.sleep(8)
            
            driver.save_screenshot("sf_step6_after_submit.png")
            print(f"✅ Form submitted!")
            print(f"📄 URL: {driver.current_url}")
            
            return driver
        else:
            print(f"❌ No submit button found!")
            return None
            
    except Exception as e:
        print(f"❌ Santa Fe registration error: {e}")
        if driver:
            driver.save_screenshot("sf_error.png")
        return None

def check_verification_and_handle(sf_driver, email_driver, email_info):
    """Check verification page và handle"""
    try:
        print(f"\n🔐 STEP 3: Email verification...")
        
        # Check if we're on verification page
        verification_indicators = [
            "verification", "verify", "confirm", "code", 
            "To create your account", "enter the 6-digit", "verification code"
        ]
        
        page_source = sf_driver.page_source.lower()
        is_verification_page = any(indicator in page_source for indicator in verification_indicators)
        
        if is_verification_page:
            print(f"✅ On verification page!")
            sf_driver.save_screenshot("sf_step7_verification_page.png")
            
            # Find verification input
            verification_input = None
            selectors_to_try = [
                "input[placeholder*='verification']",
                "input[placeholder*='code']", 
                "input[id*='verification']",
                "input[id*='code']",
                "input[name*='verification']",
                "input[name*='code']",
                "input[type='text']",
                "input[type='number']"
            ]
            
            for selector in selectors_to_try:
                try:
                    inputs = sf_driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        if inp.is_displayed():
                            verification_input = inp
                            print(f"✅ Found verification input: {selector}")
                            break
                    if verification_input:
                        break
                except:
                    continue
            
            if verification_input:
                print(f"\n📧 Checking email for verification code...")
                
                # Check email multiple times
                max_attempts = 18  # 3 minutes with 10s intervals
                verification_code = None
                
                for attempt in range(max_attempts):
                    try:
                        print(f"⏳ Attempt {attempt + 1}/{max_attempts}...")
                        
                        # Refresh email page
                        email_driver.refresh()
                        time.sleep(5)
                        
                        # Look for Santa Fe email
                        page_source = email_driver.page_source.lower()
                        santa_fe_keywords = ["santa fe", "college", "verification", "sfcollege", "application"]
                        
                        if any(keyword in page_source for keyword in santa_fe_keywords):
                            print(f"✅ Found Santa Fe email!")
                            
                            # Extract 6-digit code
                            code_matches = re.findall(r'\b\d{6}\b', email_driver.page_source)
                            
                            if code_matches:
                                verification_code = code_matches[0]
                                print(f"✅ Found verification code: {verification_code}")
                                break
                            else:
                                print(f"⚠️ Email found but no 6-digit code yet")
                        
                        time.sleep(10)  # Wait 10 seconds before next check
                        
                    except Exception as e:
                        print(f"⚠️ Email check error: {e}")
                        time.sleep(5)
                
                if verification_code:
                    print(f"\n🔐 Entering verification code: {verification_code}")
                    
                    verification_input.clear()
                    verification_input.send_keys(verification_code)
                    time.sleep(2)
                    
                    # Find and click verify button
                    verify_buttons = sf_driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
                    
                    if verify_buttons:
                        verify_btn = verify_buttons[0]
                        verify_btn.click()
                        time.sleep(5)
                        
                        sf_driver.save_screenshot("sf_step8_after_verification.png")
                        print(f"✅ VERIFICATION COMPLETED!")
                        print(f"📄 Final URL: {sf_driver.current_url}")
                        
                        # Save success result
                        result = {
                            "status": "success",
                            "email": email_info['email'],
                            "verification_code": verification_code,
                            "final_url": sf_driver.current_url,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        with open("full_test_result.json", "w", encoding="utf-8") as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        
                        print(f"🏆 FULL TEST COMPLETED SUCCESSFULLY!")
                        print(f"📧 Email: {email_info['email']}")
                        print(f"🔐 Code: {verification_code}")
                        
                        return True
                    else:
                        print(f"❌ No verify button found!")
                        return False
                else:
                    print(f"❌ No verification code found in email after 3 minutes")
                    
                    # Manual fallback
                    print(f"\n🔧 MANUAL FALLBACK:")
                    print(f"📧 Email: {email_info['email']}")
                    print(f"🌐 Check: https://imail.edu.vn")
                    print(f"⏰ Please check email manually and enter code...")
                    
                    try:
                        manual_code = input("🔐 Enter verification code (6 digits): ").strip()
                        if len(manual_code) == 6 and manual_code.isdigit():
                            verification_input.clear()
                            verification_input.send_keys(manual_code)
                            
                            verify_buttons = sf_driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
                            
                            if verify_buttons:
                                verify_btn = verify_buttons[0]
                                verify_btn.click()
                                time.sleep(5)
                                
                                print(f"✅ Manual verification completed!")
                                return True
                            else:
                                print(f"❌ No verify button!")
                                return False
                        else:
                            print(f"❌ Invalid code format!")
                            return False
                    except:
                        print(f"❌ Manual input failed!")
                        return False
            else:
                print(f"❌ No verification input found!")
                return False
        else:
            print(f"❌ Not on verification page")
            print(f"📄 Current URL: {sf_driver.current_url}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def full_test_with_imail():
    """Test hoàn chỉnh từ tạo email đến verification"""
    print("🎯 FULL TEST WITH IMAIL")
    print("=" * 60)
    print("🚀 Test quy trình hoàn chỉnh:")
    print("   extract gg from pdf. Tạo email imail.edu.vn")
    print("   2. Đăng ký Santa Fe College")
    print("   3. Auto check email và verify")
    print("-" * 60)
    
    # Load person data
    person = load_person_data()
    if not person:
        print("❌ No person data!")
        return
    
    print(f"👤 Person: {person['full_name']}")
    
    email_driver = None
    sf_driver = None
    
    try:
        # Step extract gg from pdf: Create imail email
        email_info = create_imail_email(person['first_name'])
        if not email_info:
            print("❌ Failed to create email!")
            return
        
        email_driver = email_info['driver']
        
        # Step 2: Register Santa Fe
        sf_driver = register_santa_fe(email_info, person)
        if not sf_driver:
            print("❌ Failed to register Santa Fe!")
            return
        
        # Step 3: Handle verification
        success = check_verification_and_handle(sf_driver, email_driver, email_info)
        
        if success:
            print(f"\n🎉 TEST THÀNH CÔNG!")
        else:
            print(f"\n❌ Test failed at verification step")
        
        # Keep browsers open for inspection
        print(f"\n⏰ Keeping browsers open for 60 seconds...")
        time.sleep(60)
        
    except Exception as e:
        print(f"❌ General error: {e}")
    
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
    full_test_with_imail() 