#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 COMPLETE IMAIL + SANTA FE INTEGRATION
Test hoàn thiện từ tạo email đến nhận verification code
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
import re

def load_person_data():
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def create_imail_email():
    """Tạo email trên imail.edu.vn với domain naka.edu.pl"""
    print("📧 CREATING IMAIL EMAIL")
    print("=" * 40)
    
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
        
        # Find and fill username
        username_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='user'][type='text']")
        username_input = None
        
        for inp in username_inputs:
            if inp.is_displayed() and inp.is_enabled():
                username_input = inp
                break
        
        if not username_input:
            print("❌ Username input not found!")
            return None
        
        username_input.clear()
        username_input.send_keys(username)
        print(f"✅ Username entered: {username}")
        
        # Find and click domain dropdown
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
        
        # Find and click naka.edu.pl option
        naka_xpath = "//*[contains(text(), 'naka.edu.pl')]"
        naka_options = driver.find_elements(By.XPATH, naka_xpath)
        
        naka_clicked = False
        for opt in naka_options:
            if opt.is_displayed():
                try:
                    opt.click()
                    print(f"✅ naka.edu.pl selected!")
                    naka_clicked = True
                    break
                except:
                    continue
        
        if not naka_clicked:
            print("⚠️ Could not select naka.edu.pl")
        
        time.sleep(1)
        
        # Click create button
        create_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        
        create_clicked = False
        for btn in create_buttons:
            if btn.is_displayed() and "Create" in btn.get_attribute("value"):
                btn_class = btn.get_attribute("class") or ""
                if "bg-teal-500" in btn_class:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"✅ Create button clicked!")
                        create_clicked = True
                        break
                    except:
                        continue
        
        if not create_clicked:
            print("❌ Could not click create button!")
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
                "driver": driver
            }
        else:
            print(f"❌ Email creation failed!")
            return None
            
    except Exception as e:
        print(f"❌ Email creation error: {e}")
        if driver:
            driver.quit()
        return None

def santa_fe_registration_with_email(email_info):
    """Đăng ký Santa Fe với email đã tạo"""
    print(f"\n🎓 SANTA FE REGISTRATION")
    print("=" * 40)
    
    person = load_person_data()
    if not person:
        return None
    
    sf_driver = None
    try:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        
        # Load extensions
        extensions = [
            "driver/captchasolver.crx",
            "driver/extract gg from pdf.crx"
        ]
        
        for ext in extensions:
            try:
                opts.add_extension(ext)
                print(f"✅ Loaded extension: {ext}")
            except:
                print(f"⚠️ Could not load extension: {ext}")
        
        sf_driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(sf_driver, 20)
        
        print(f"🌐 Opening Santa Fe College...")
        sf_driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(8)
        
        sf_driver.save_screenshot("integration_step1_sf_homepage.png")
        
        # Navigation flow
        print(f"🎯 Step extract gg from pdf: Click Start button...")
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
        button1.click()
        time.sleep(3)
        
        print(f"🎯 Step 2: Select Option extract gg from pdf...")
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
        option1.click()
        time.sleep(2)
        
        print(f"🎯 Step 3: Click Next extract gg from pdf...")
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
        next1.click()
        time.sleep(3)
        
        print(f"🎯 Step 4: Select Option 2...")
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
        option2.click()
        time.sleep(2)
        
        print(f"🎯 Step 5: Click Next 2...")
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
        next2.click()
        time.sleep(5)
        
        print(f"✅ Reached registration form!")
        sf_driver.save_screenshot("integration_step2_sf_form.png")
        
        # Fill form with person data and imail email
        form_data = {
            "fstNameSTR": person['first_name'],
            "lstNameSTR": person['last_name'],
            "emailAddrsSTR": email_info['email'],
            "cemailAddrsSTR": email_info['email'],
            "ssnumSTR": person['ssn'],
            "cssnumSTR": person['ssn']
        }
        
        print(f"📝 Filling form with imail email: {email_info['email']}")
        
        for field_id, value in form_data.items():
            try:
                field = sf_driver.find_element(By.ID, field_id)
                field.clear()
                field.send_keys(value)
                print(f"✅ {field_id}: {value}")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ {field_id}: {e}")
        
        # Fill birth date
        try:
            month_select = sf_driver.find_element(By.ID, "month")
            day_select = sf_driver.find_element(By.ID, "day")
            year_select = sf_driver.find_element(By.ID, "year")
            
            from selenium.webdriver.support.ui import Select
            
            Select(month_select).select_by_value(str(person['birth_month']))
            Select(day_select).select_by_value(str(person['birth_day']))
            Select(year_select).select_by_value(str(person['birth_year']))
            
            print(f"✅ Birth date: {person['birth_month']}/{person['birth_day']}/{person['birth_year']}")
            
        except Exception as e:
            print(f"⚠️ Birth date error: {e}")
        
        # Fill birth country
        try:
            country_select = sf_driver.find_element(By.ID, "birthctrySTR")
            Select(country_select).select_by_value("US")
            print(f"✅ Birth country: US")
        except Exception as e:
            print(f"⚠️ Birth country error: {e}")
        
        # Check SSN notice checkbox
        try:
            ssn_checkbox = sf_driver.find_element(By.ID, "ssnNoticeCB")
            if not ssn_checkbox.is_selected():
                ssn_checkbox.click()
                print(f"✅ SSN notice checked")
        except Exception as e:
            print(f"⚠️ SSN checkbox error: {e}")
        
        sf_driver.save_screenshot("integration_step3_form_filled.png")
        
        # Submit form
        print(f"\n🚀 Submitting form...")
        
        submit_button = sf_driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Submit']")
        sf_driver.execute_script("arguments[0].click();", submit_button)
        
        time.sleep(8)
        sf_driver.save_screenshot("integration_step4_after_submit.png")
        
        # Check for verification page
        current_url = sf_driver.current_url
        page_source = sf_driver.page_source.lower()
        
        print(f"📄 Current URL: {current_url}")
        
        verification_keywords = [
            "verification",
            "6-digit",
            "email",
            "code",
            "verify"
        ]
        
        found_verification = any(kw in page_source for kw in verification_keywords)
        
        if found_verification:
            print(f"✅ VERIFICATION PAGE REACHED!")
            print(f"📧 Verification email sent to: {email_info['email']}")
            
            return {
                "success": True,
                "email": email_info['email'],
                "sf_driver": sf_driver,
                "verification_needed": True
            }
        else:
            print(f"⚠️ Verification page not detected")
            return {
                "success": False,
                "sf_driver": sf_driver
            }
        
    except Exception as e:
        print(f"❌ Santa Fe registration error: {e}")
        if sf_driver:
            sf_driver.save_screenshot("integration_error.png")
        return None

def check_verification_email(email_info, max_attempts=10):
    """Check for verification code in imail"""
    print(f"\n📬 CHECKING VERIFICATION EMAIL")
    print("=" * 40)
    
    email_driver = email_info['driver']
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"🔍 Attempt {attempt}/{max_attempts}...")
            
            # Refresh mailbox
            email_driver.refresh()
            time.sleep(3)
            
            # Look for emails
            page_source = email_driver.page_source
            
            # Check for verification code pattern
            code_pattern = r'\b\d{6}\b'
            codes = re.findall(code_pattern, page_source)
            
            if codes:
                print(f"🎯 FOUND VERIFICATION CODES: {codes}")
                
                # Return the most likely code (6 digits)
                for code in codes:
                    if len(code) == 6:
                        print(f"✅ VERIFICATION CODE: {code}")
                        return code
            
            # Check for Santa Fe email keywords
            sf_keywords = ["santa fe", "verification", "college", "admission"]
            found_sf_email = any(kw in page_source.lower() for kw in sf_keywords)
            
            if found_sf_email:
                print(f"📧 Santa Fe email detected, but no clear verification code")
            
            print(f"⏰ Waiting 10 seconds before next check...")
            time.sleep(10)
            
        except Exception as e:
            print(f"⚠️ Check attempt {attempt} failed: {e}")
            time.sleep(5)
    
    print(f"❌ No verification code found after {max_attempts} attempts")
    return None

def complete_integration_test():
    """Test hoàn thiện từ tạo email đến verification"""
    print("🎯 COMPLETE IMAIL + SANTA FE INTEGRATION TEST")
    print("=" * 60)
    
    email_info = None
    sf_result = None
    
    try:
        # Step extract gg from pdf: Create imail email
        email_info = create_imail_email()
        
        if not email_info:
            print("❌ Email creation failed!")
            return
        
        print(f"\n✅ EMAIL CREATED: {email_info['email']}")
        
        # Step 2: Register with Santa Fe
        sf_result = santa_fe_registration_with_email(email_info)
        
        if not sf_result or not sf_result.get('success'):
            print("❌ Santa Fe registration failed!")
            return
        
        print(f"\n✅ SANTA FE REGISTRATION SUBMITTED!")
        print(f"📧 Verification email should be sent to: {email_info['email']}")
        
        # Step 3: Check for verification email
        print(f"\n📬 Checking for verification email...")
        
        verification_code = check_verification_email(email_info, max_attempts=12)
        
        if verification_code:
            print(f"\n🎯 SUCCESS! VERIFICATION CODE: {verification_code}")
            
            # Enter verification code
            sf_driver = sf_result['sf_driver']
            
            try:
                # Look for verification input field
                verification_inputs = sf_driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                
                for inp in verification_inputs:
                    placeholder = inp.get_attribute("placeholder") or ""
                    if "code" in placeholder.lower() or "verification" in placeholder.lower():
                        inp.clear()
                        inp.send_keys(verification_code)
                        print(f"✅ Verification code entered!")
                        
                        # Look for submit button
                        submit_buttons = sf_driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                        
                        for btn in submit_buttons:
                            btn_text = btn.get_attribute("value") or btn.text or ""
                            if any(word in btn_text.lower() for word in ["verify", "submit", "continue"]):
                                btn.click()
                                print(f"✅ Verification submitted!")
                                break
                        
                        break
                
                time.sleep(5)
                sf_driver.save_screenshot("integration_step5_verification_completed.png")
                
                print(f"\n🏆 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
                print(f"📧 Email: {email_info['email']}")
                print(f"🔑 Verification Code: {verification_code}")
                
            except Exception as e:
                print(f"⚠️ Verification entry error: {e}")
        else:
            print(f"\n⚠️ Manual verification needed")
            print(f"📧 Check email: {email_info['email']}")
            
            # Manual input
            manual_code = input(f"\n🔑 Enter verification code manually: ").strip()
            
            if manual_code and len(manual_code) == 6:
                print(f"✅ Manual code: {manual_code}")
                # Enter manual code logic here...
        
        # Keep browsers open for inspection
        print(f"\n⏰ Keeping browsers open for inspection (60s)...")
        time.sleep(60)
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
    
    finally:
        # Cleanup
        if email_info and email_info.get('driver'):
            email_info['driver'].quit()
            print("✅ Email browser closed")
        
        if sf_result and sf_result.get('sf_driver'):
            sf_result['sf_driver'].quit()
            print("✅ Santa Fe browser closed")
        
        print(f"\n🏁 TEST COMPLETED!")

if __name__ == "__main__":
    complete_integration_test() 