#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 FIX BIRTH DATE AUTOMATION
Fix lỗi birth date với đúng values để enable submit button
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
    """Tạo email imail.edu.vn"""
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
        
        # Find username input
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
        
        # Find domain input
        domain_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='domain']")
        domain_input = None
        
        for inp in domain_inputs:
            if inp.is_displayed():
                domain_input = inp
                break
        
        if not domain_input:
            print("❌ Domain input not found!")
            return None
        
        # Click domain to open dropdown
        domain_input.click()
        time.sleep(2)
        print(f"✅ Domain dropdown opened")
        
        # Select naka.edu.pl
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
        
        # Click create button
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
        
        # Check result
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

def discover_birth_date_options(sf_driver):
    """Khám phá birth date options available"""
    print(f"\n🔍 DISCOVERING BIRTH DATE OPTIONS...")
    
    try:
        # Month options
        month_select = sf_driver.find_element(By.ID, "month")
        month_options = month_select.find_elements(By.TAG_NAME, "option")
        
        print(f"📅 MONTH OPTIONS:")
        for opt in month_options:
            value = opt.get_attribute("value")
            text = opt.text.strip()
            if value:  # Skip empty option
                print(f"  Value: '{value}' - Text: '{text}'")
        
        # Day options  
        day_select = sf_driver.find_element(By.ID, "day")
        day_options = day_select.find_elements(By.TAG_NAME, "option")
        
        print(f"\n📅 DAY OPTIONS (first 10):")
        for i, opt in enumerate(day_options[:10]):
            value = opt.get_attribute("value")
            text = opt.text.strip()
            if value:  # Skip empty option
                print(f"  Value: '{value}' - Text: '{text}'")
        
        # Year options
        year_select = sf_driver.find_element(By.ID, "year")
        year_options = year_select.find_elements(By.TAG_NAME, "option")
        
        print(f"\n📅 YEAR OPTIONS (first 10):")
        for i, opt in enumerate(year_options[:10]):
            value = opt.get_attribute("value")
            text = opt.text.strip()
            if value:  # Skip empty option
                print(f"  Value: '{value}' - Text: '{text}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Birth date discovery error: {e}")
        return False

def complete_santa_fe_registration_fixed(email_info):
    """Hoàn thành registration Santa Fe với birth date fix"""
    print(f"\n🎓 SANTA FE REGISTRATION WITH BIRTH DATE FIX")
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
        sf_driver.save_screenshot("fix_step1_form.png")
        
        # First discover birth date options
        discover_birth_date_options(sf_driver)
        
        # Fill form using correct selectors
        print(f"\n📝 Filling form with REAL email: {email_info['email']}")
        
        # Required fields with CORRECT IDs
        form_fields = [
            ("fstNameSTR", person['first_name'], "First Name"),
            ("lstNameSTR", person['last_name'], "Last Name"),
            ("email", email_info['email'], "Email"),
            ("emailC", email_info['email'], "Confirm Email"),
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
        
        # Fill birth date with CORRECT VALUES
        print(f"\n📅 Filling birth date with correct values...")
        
        try:
            # Try different birth date values based on discovered options
            birth_date_attempts = [
                {"month": "01", "day": "15", "year": "1995"},  # Try 01 for January
                {"month": "extract gg from pdf", "day": "15", "year": "1995"},   # Try extract gg from pdf for January
                {"month": "June", "day": "15", "year": "1995"}, # Try text
                {"month": "6", "day": "15", "year": "1995"},   # Try 6
            ]
            
            birth_date_success = False
            
            for attempt_num, birth_date in enumerate(birth_date_attempts, 1):
                try:
                    print(f"🎯 Birth date attempt {attempt_num}: {birth_date}")
                    
                    month_select = sf_driver.find_element(By.ID, "month")
                    day_select = sf_driver.find_element(By.ID, "day") 
                    year_select = sf_driver.find_element(By.ID, "year")
                    
                    # Try to select month
                    Select(month_select).select_by_value(birth_date["month"])
                    time.sleep(0.5)
                    
                    # Try to select day
                    Select(day_select).select_by_value(birth_date["day"])
                    time.sleep(0.5)
                    
                    # Try to select year
                    Select(year_select).select_by_value(birth_date["year"])
                    time.sleep(0.5)
                    
                    print(f"✅ Birth date attempt {attempt_num} SUCCESS!")
                    birth_date_success = True
                    break
                    
                except Exception as e:
                    print(f"⚠️ Birth date attempt {attempt_num} failed: {e}")
                    continue
            
            if not birth_date_success:
                print(f"❌ All birth date attempts failed!")
                
        except Exception as e:
            print(f"❌ Birth date section error: {e}")
        
        # Fill birth country
        try:
            country_select = sf_driver.find_element(By.CSS_SELECTOR, "select[name='birthctrySTR']")
            Select(country_select).select_by_value("US")
            print(f"✅ Birth country: US")
        except Exception as e:
            print(f"⚠️ Birth country error: {e}")
        
        # Check SSN notice
        try:
            ssn_checkbox = sf_driver.find_element(By.ID, "ssnNoticeCB")
            if not ssn_checkbox.is_selected():
                sf_driver.execute_script("arguments[0].click();", ssn_checkbox)
                print(f"✅ SSN notice checked")
        except Exception as e:
            print(f"⚠️ SSN checkbox error: {e}")
        
        # Wait for form validation
        time.sleep(5)
        sf_driver.save_screenshot("fix_step2_form_complete.png")
        
        # Check submit button status
        print(f"\n🔍 CHECKING SUBMIT BUTTON STATUS...")
        
        try:
            submit_button = sf_driver.find_element(By.CSS_SELECTOR, "button[type='submit'].button.float-right")
            
            is_enabled = submit_button.is_enabled()
            button_classes = submit_button.get_attribute("class")
            button_text = submit_button.text.strip()
            
            print(f"Submit Button Status:")
            print(f"  Text: '{button_text}'")
            print(f"  Enabled: {is_enabled}")
            print(f"  Classes: '{button_classes}'")
            
            if is_enabled:
                print(f"🎯 SUBMIT BUTTON IS NOW ENABLED!")
                
                # Scroll to button
                sf_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                time.sleep(1)
                
                # Highlight button
                sf_driver.execute_script("arguments[0].style.border='3px solid green';", submit_button)
                time.sleep(2)
                
                # Click submit
                sf_driver.execute_script("arguments[0].click();", submit_button)
                print(f"✅ SUBMIT BUTTON CLICKED!")
                
                # Wait for response
                time.sleep(8)
                sf_driver.save_screenshot("fix_step3_after_submit.png")
                
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
                    print(f"🎉 SUCCESS! Registration submitted!")
                    if found_verification:
                        print(f"  Verification indicators: {found_verification}")
                    if found_success:
                        print(f"  Success indicators: {found_success}")
                    
                    # Save result
                    result = {
                        "email": email_info['email'],
                        "status": "REGISTRATION_SUBMITTED",
                        "url": current_url,
                        "verification_indicators": found_verification,
                        "success_indicators": found_success,
                        "timestamp": time.time()
                    }
                    
                    with open("fix_success_result.json", "w") as f:
                        json.dump(result, f, indent=2)
                    
                    print(f"💾 Result saved to fix_success_result.json")
                    
                    return result
                    
                else:
                    print(f"⚠️ No clear verification indicators found")
                    
            else:
                print(f"❌ Submit button is still disabled")
                print(f"💡 Form validation may still be incomplete")
        
        except Exception as e:
            print(f"❌ Submit button check error: {e}")
        
        # Manual inspection time
        print(f"\n⏰ Manual inspection time (60s)...")
        time.sleep(60)
        
        return {
            "email": email_info['email'],
            "status": "FORM_FILLED_NEEDS_MANUAL_CHECK",
            "timestamp": time.time()
        }
        
    except Exception as e:
        print(f"❌ Santa Fe registration error: {e}")
        if sf_driver:
            sf_driver.save_screenshot("fix_error.png")
        return None
    
    finally:
        if sf_driver:
            sf_driver.quit()
            print("✅ Santa Fe browser closed")

def fixed_automation():
    """Fixed automation with birth date correction"""
    print("🔧 FIXED AUTOMATION - Birth Date Correction")
    print("=" * 70)
    
    # Step extract gg from pdf: Create imail email
    print(f"\n🎯 STEP extract gg from pdf: Creating working imail email...")
    email_info = create_imail_email()
    
    if not email_info:
        print("❌ Email creation failed! Cannot proceed.")
        return
    
    print(f"\n✅ EMAIL READY: {email_info['email']}")
    
    # Step 2: Complete Santa Fe registration with birth date fix
    print(f"\n🎯 STEP 2: Completing Santa Fe registration with birth date fix...")
    sf_result = complete_santa_fe_registration_fixed(email_info)
    
    # Final result
    if sf_result:
        print(f"\n🎉 FINAL RESULT:")
        print(f"📧 Email: {sf_result['email']}")
        print(f"✅ Status: {sf_result['status']}")
        
        if sf_result['status'] == 'REGISTRATION_SUBMITTED':
            print(f"\n🏆 SUCCESS! Registration submitted successfully!")
        else:
            print(f"\n🎯 Form filled - manual verification may be needed")
    
    else:
        print(f"\n⚠️ Registration encountered issues")
    
    # Cleanup
    if email_info and email_info.get('driver'):
        email_info['driver'].quit()
        print("✅ Email browser closed")
    
    print(f"\n🏁 FIXED AUTOMATION COMPLETE!")

if __name__ == "__main__":
    fixed_automation() 