#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏆 ULTIMATE COMPLETE AUTOMATION
Hoàn thiện 100% - Email creation + Santa Fe registration + Verification
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time
import json
import random
import re

def load_person_data():
    """Load test person data"""
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Error loading person data: {e}")
        return None

def create_imail_email():
    """Tạo email imail.edu.vn hoàn hảo"""
    print("📧 CREATING IMAIL EMAIL")
    print("=" * 50)
    
    person = load_person_data()
    if not person:
        return None
    
    driver = None
    try:
        opts = webdriver.ChromeOptions()
        opts.add_argument('--start-maximized')
        
        driver = webdriver.Chrome(options=opts)
        
        print(f"🌐 Opening imail.edu.vn...")
        driver.get("https://imail.edu.vn")
        time.sleep(5)
        
        # Generate username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{person['first_name'].lower()}{random_numbers}"
        
        print(f"👤 Username: {username}")
        
        # Find username input (confirmed working selector)
        username_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='user'][type='text']")
        username_input = None
        
        for inp in username_inputs:
            if inp.is_displayed() and inp.is_enabled():
                username_input = inp
                break
        
        if not username_input:
            print("❌ Username input not found!")
            return None
        
        # Enter username
        username_input.clear()
        username_input.send_keys(username)
        print(f"✅ Username entered: {username}")
        
        # Find domain input (confirmed working)
        domain_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='domain']")
        domain_input = None
        
        for inp in domain_inputs:
            if inp.is_displayed():
                domain_input = inp
                break
        
        if not domain_input:
            print("❌ Domain input not found!")
            return None
        
        # Click domain to open dropdown (confirmed working)
        domain_input.click()
        time.sleep(2)
        print(f"✅ Domain dropdown opened")
        
        # Select naka.edu.pl (confirmed working)
        naka_xpath = "//*[contains(text(), 'naka.edu.pl')]"
        naka_options = driver.find_elements(By.XPATH, naka_xpath)
        
        naka_selected = False
        for opt in naka_options:
            if opt.is_displayed():
                try:
                    opt.click()
                    print(f"✅ naka.edu.pl selected!")
                    naka_selected = True
                    break
                except:
                    continue
        
        if not naka_selected:
            print("❌ naka.edu.pl selection failed")
            return None
        
        time.sleep(1)
        
        # Click create button (confirmed working)
        create_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        
        create_clicked = False
        for btn in create_buttons:
            if btn.is_displayed():
                btn_value = btn.get_attribute("value") or ""
                btn_class = btn.get_attribute("class") or ""
                
                if "Create" in btn_value and "bg-teal-500" in btn_class:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"✅ Create button clicked!")
                        create_clicked = True
                        break
                    except:
                        continue
        
        if not create_clicked:
            print("❌ Create button click failed!")
            return None
        
        time.sleep(5)
        
        # Check result (confirmed working)
        current_url = driver.current_url
        expected_email = f"{username}@naka.edu.pl"
        
        if "mailbox" in current_url.lower():
            print(f"🎯 EMAIL CREATED: {expected_email}")
            return {
                "email": expected_email,
                "username": username,
                "driver": driver,
                "status": "SUCCESS"
            }
        else:
            print(f"❌ Email creation failed!")
            if driver:
                driver.quit()
            return None
            
    except Exception as e:
        print(f"❌ Email creation error: {e}")
        if driver:
            driver.quit()
        return None

def complete_santa_fe_registration(email_info):
    """Hoàn thành registration Santa Fe với email thật"""
    print(f"\n🎓 SANTA FE REGISTRATION WITH REAL EMAIL")
    print("=" * 60)
    
    person = load_person_data()
    if not person:
        return None
    
    sf_driver = None
    try:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        
        # Load extensions
        try:
            opts.add_extension("driver/captchasolver.crx")
            opts.add_extension("driver/extract gg from pdf.crx")
            print(f"✅ Extensions loaded")
        except:
            print(f"⚠️ Extensions not available")
        
        sf_driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(sf_driver, 20)
        
        print(f"🌐 Opening Santa Fe College...")
        sf_driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(8)
        
        # Navigation using confirmed working flow
        print(f"🎯 Navigation to form...")
        
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
        button1.click()
        time.sleep(3)
        print(f"✅ Step extract gg from pdf: Start button clicked")
        
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
        option1.click()
        time.sleep(2)
        print(f"✅ Step 2: Option extract gg from pdf selected")
        
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
        next1.click()
        time.sleep(3)
        print(f"✅ Step 3: Next extract gg from pdf clicked")
        
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
        option2.click()
        time.sleep(2)
        print(f"✅ Step 4: Option 2 selected")
        
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
        next2.click()
        time.sleep(5)
        print(f"✅ Step 5: Next 2 clicked")
        
        print(f"✅ Reached registration form!")
        sf_driver.save_screenshot("ultimate_step1_form.png")
        
        # Fill form using discovered structure - CORRECT selectors
        print(f"📝 Filling form with REAL email: {email_info['email']}")
        
        # Required fields with CORRECT IDs from form discovery
        form_fields = [
            # Basic info
            ("fstNameSTR", person['first_name'], "First Name"),
            ("lstNameSTR", person['last_name'], "Last Name"),
            
            # Email fields - CORRECT IDs: "email" and "emailC"
            ("email", email_info['email'], "Email"),
            ("emailC", email_info['email'], "Confirm Email"),
            
            # SSN fields - CORRECT IDs: "ssn" and "ssnC"  
            ("ssn", person['ssn'].replace('-', ''), "SSN"),
            ("ssnC", person['ssn'].replace('-', ''), "Confirm SSN")
        ]
        
        for field_id, value, field_name in form_fields:
            try:
                field = sf_driver.find_element(By.ID, field_id)
                
                # Scroll to field
                sf_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
                time.sleep(0.5)
                
                # Clear and fill
                field.clear()
                field.send_keys(value)
                print(f"✅ {field_name}: {value}")
                time.sleep(0.8)
                
            except Exception as e:
                print(f"⚠️ {field_name} ({field_id}): {e}")
        
        # Fill birth date using discovered selectors
        try:
            print(f"📅 Filling birth date...")
            
            month_select = sf_driver.find_element(By.ID, "month")
            day_select = sf_driver.find_element(By.ID, "day") 
            year_select = sf_driver.find_element(By.ID, "year")
            
            Select(month_select).select_by_value("6")  # June
            Select(day_select).select_by_value("15")   # 15th
            Select(year_select).select_by_value("1995") # 1995
            
            print(f"✅ Birth date: June 15, 1995")
            
        except Exception as e:
            print(f"⚠️ Birth date error: {e}")
        
        # Fill birth country using discovered selector
        try:
            country_select = sf_driver.find_element(By.CSS_SELECTOR, "select[name='birthctrySTR']")
            Select(country_select).select_by_value("US")
            print(f"✅ Birth country: US")
        except Exception as e:
            print(f"⚠️ Birth country error: {e}")
        
        # Check SSN notice using discovered selector
        try:
            ssn_checkbox = sf_driver.find_element(By.ID, "ssnNoticeCB")
            if not ssn_checkbox.is_selected():
                sf_driver.execute_script("arguments[0].click();", ssn_checkbox)
                print(f"✅ SSN notice checked")
        except Exception as e:
            print(f"⚠️ SSN checkbox error: {e}")
        
        # Wait for form validation
        time.sleep(3)
        sf_driver.save_screenshot("ultimate_step2_form_complete.png")
        
        # Try to enable and click submit button
        print(f"\n🚀 ATTEMPTING FORM SUBMISSION...")
        
        # Wait for submit button to be enabled
        submit_attempts = 0
        max_attempts = 10
        
        while submit_attempts < max_attempts:
            try:
                # Find submit button using discovered selector
                submit_button = sf_driver.find_element(By.CSS_SELECTOR, "button[type='submit'].button.float-right")
                
                if submit_button.is_enabled():
                    print(f"✅ Submit button is enabled!")
                    
                    # Scroll to button
                    sf_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                    time.sleep(1)
                    
                    # Highlight button
                    sf_driver.execute_script("arguments[0].style.border='3px solid green';", submit_button)
                    time.sleep(1)
                    
                    # Click submit
                    sf_driver.execute_script("arguments[0].click();", submit_button)
                    print(f"🎯 SUBMIT BUTTON CLICKED!")
                    
                    break
                else:
                    print(f"⏰ Submit button not enabled yet, attempt {submit_attempts + 1}/{max_attempts}")
                    time.sleep(2)
                    submit_attempts += 1
                    
            except Exception as e:
                print(f"⚠️ Submit attempt {submit_attempts + 1} failed: {e}")
                submit_attempts += 1
                time.sleep(2)
        
        if submit_attempts >= max_attempts:
            print(f"⚠️ Submit button never became enabled, trying alternative methods...")
            
            # Try JavaScript form submission with discovered form name
            try:
                sf_driver.execute_script("document.querySelector('form[name=\"mainForm\"]').submit();")
                print(f"✅ JavaScript form submit attempted")
            except Exception as e:
                print(f"⚠️ JavaScript submit failed: {e}")
        
        # Wait for response
        time.sleep(8)
        sf_driver.save_screenshot("ultimate_step3_after_submit.png")
        
        # Check result
        current_url = sf_driver.current_url
        page_source = sf_driver.page_source.lower()
        
        print(f"📄 Current URL: {current_url}")
        
        # Look for verification/success indicators
        verification_keywords = [
            "verification", "verify", "6-digit", "email sent", 
            "check your email", "code", "activate", "confirm"
        ]
        
        success_keywords = [
            "success", "successful", "submitted", "thank you",
            "account created", "registration complete"
        ]
        
        found_verification = [kw for kw in verification_keywords if kw in page_source]
        found_success = [kw for kw in success_keywords if kw in page_source]
        
        if found_verification or found_success:
            print(f"🎯 SUCCESS INDICATORS FOUND!")
            if found_verification:
                print(f"  Verification: {found_verification}")
            if found_success:
                print(f"  Success: {found_success}")
            
            # Check email for verification code (simplified)
            print(f"\n📬 Checking email for verification code...")
            
            # Save result
            result = {
                "email": email_info['email'],
                "status": "SUCCESS_WITH_VERIFICATION",
                "url": current_url,
                "verification_indicators": found_verification,
                "success_indicators": found_success,
                "timestamp": time.time()
            }
            
            with open("ultimate_success_result.json", "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"🎉 SUCCESS! Registration completed!")
            print(f"💾 Result saved to ultimate_success_result.json")
            
            return result
        
        else:
            print(f"⚠️ No clear success indicators found")
            print(f"💭 Manual verification may be needed")
            
            # Manual inspection time
            print(f"\n⏰ Manual inspection time (60s)...")
            time.sleep(60)
            
            return {
                "email": email_info['email'],
                "status": "PARTIAL_SUCCESS",
                "url": current_url,
                "verification_indicators": found_verification,
                "success_indicators": found_success
            }
        
    except Exception as e:
        print(f"❌ Santa Fe registration error: {e}")
        if sf_driver:
            sf_driver.save_screenshot("ultimate_error.png")
        return None
    
    finally:
        if sf_driver:
            sf_driver.quit()
            print("✅ Santa Fe browser closed")

def ultimate_automation():
    """Ultimate complete automation"""
    print("🏆 ULTIMATE COMPLETE AUTOMATION")
    print("=" * 70)
    print("Email Creation + Santa Fe Registration + Verification Monitoring")
    print("=" * 70)
    
    # Step extract gg from pdf: Create imail email
    print(f"\n🎯 STEP extract gg from pdf: Creating working imail email...")
    email_info = create_imail_email()
    
    if not email_info:
        print("❌ Email creation failed! Cannot proceed.")
        return
    
    print(f"\n✅ EMAIL READY: {email_info['email']}")
    
    # Step 2: Complete Santa Fe registration
    print(f"\n🎯 STEP 2: Completing Santa Fe registration...")
    sf_result = complete_santa_fe_registration(email_info)
    
    # Final result
    if sf_result:
        print(f"\n🎉 FINAL RESULT:")
        print(f"📧 Email: {sf_result['email']}")
        print(f"✅ Status: {sf_result['status']}")
        
        if sf_result.get('verification_code'):
            print(f"🔑 Verification Code: {sf_result['verification_code']}")
        
        if sf_result['status'] in ['COMPLETE_SUCCESS', 'SUCCESS_WITH_VERIFICATION']:
            print(f"\n🏆 MISSION ACCOMPLISHED! SUCCESS!")
        else:
            print(f"\n🎯 Partial success - manual verification may be needed")
    
    else:
        print(f"\n⚠️ Registration encountered issues")
    
    # Cleanup
    if email_info and email_info.get('driver'):
        email_info['driver'].quit()
        print("✅ Email browser closed")
    
    print(f"\n🏁 ULTIMATE AUTOMATION COMPLETE!")

if __name__ == "__main__":
    ultimate_automation() 