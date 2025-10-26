#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏆 FINAL IMAIL TEST
Email creation + Santa Fe registration + Verification check
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
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
        print(f"❌ Error: {e}")
        return None

def create_imail_email_final():
    """Tạo email imail final working version"""
    print("📧 FINAL IMAIL EMAIL CREATION")
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
        driver.save_screenshot("final_step1_imail_homepage.png")
        
        # Find username input (working selector)
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
        driver.save_screenshot("final_step2_username_entered.png")
        
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
        driver.save_screenshot("final_step3_domain_dropdown.png")
        
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
            print("⚠️ naka.edu.pl selection failed")
        
        time.sleep(1)
        driver.save_screenshot("final_step4_domain_selected.png")
        
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
            print("❌ Create button click failed!")
            return None
        
        time.sleep(5)
        driver.save_screenshot("final_step5_after_create.png")
        
        # Check result
        current_url = driver.current_url
        expected_email = f"{username}@naka.edu.pl"
        
        if "mailbox" in current_url.lower():
            print(f"🎯 EMAIL CREATED SUCCESSFULLY: {expected_email}")
            return {
                "email": expected_email,
                "username": username,
                "driver": driver
            }
        else:
            print(f"❌ Email creation verification failed!")
            return None
            
    except Exception as e:
        print(f"❌ Email creation error: {e}")
        if driver:
            driver.save_screenshot("final_email_error.png")
            driver.quit()
        return None

def santa_fe_with_working_selectors(email_info):
    """Santa Fe với working selectors từ test trước"""
    print(f"\n🎓 SANTA FE REGISTRATION (WORKING VERSION)")
    print("=" * 50)
    
    person = load_person_data()
    if not person:
        return None
    
    sf_driver = None
    try:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        
        # Load extensions if available
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
        
        sf_driver.save_screenshot("final_sf_step1_homepage.png")
        
        # Navigation (working selectors)
        print(f"🎯 Navigation flow...")
        
        # Button extract gg from pdf
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
        button1.click()
        time.sleep(3)
        print(f"✅ Step extract gg from pdf: Start button clicked")
        
        # Option extract gg from pdf
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
        option1.click()
        time.sleep(2)
        print(f"✅ Step 2: Option extract gg from pdf selected")
        
        # Next extract gg from pdf
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
        next1.click()
        time.sleep(3)
        print(f"✅ Step 3: Next extract gg from pdf clicked")
        
        # Option 2
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
        option2.click()
        time.sleep(2)
        print(f"✅ Step 4: Option 2 selected")
        
        # Next 2
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
        next2.click()
        time.sleep(5)
        print(f"✅ Step 5: Next 2 clicked")
        
        print(f"✅ Reached registration form!")
        sf_driver.save_screenshot("final_sf_step2_form.png")
        
        # Use working form field IDs from previous tests
        working_fields = [
            ("fstNameSTR", person['first_name']),
            ("lstNameSTR", person['last_name']),
            ("emailAddrsSTR", email_info['email']),
            ("cemailAddrsSTR", email_info['email'])
        ]
        
        print(f"📝 Filling form with imail email: {email_info['email']}")
        
        for field_id, value in working_fields:
            try:
                # Try multiple selectors
                field = None
                selectors = [f"#{field_id}", f"input[id='{field_id}']", f"input[name='{field_id}']"]
                
                for selector in selectors:
                    try:
                        field = sf_driver.find_element(By.CSS_SELECTOR, selector)
                        if field.is_displayed():
                            break
                    except:
                        continue
                
                if field:
                    field.clear()
                    field.send_keys(value)
                    print(f"✅ {field_id}: {value}")
                    time.sleep(0.5)
                else:
                    print(f"⚠️ {field_id}: field not found")
                    
            except Exception as e:
                print(f"⚠️ {field_id}: {e}")
        
        sf_driver.save_screenshot("final_sf_step3_form_filled.png")
        
        # Try to submit (flexible approach)
        print(f"\n🚀 Attempting to submit...")
        
        submit_selectors = [
            "input[type='submit'][value='Submit']",
            "input[type='submit']",
            "button[type='submit']",
            ".submit",
            "[value='Submit']"
        ]
        
        submit_clicked = False
        for selector in submit_selectors:
            try:
                submit_btn = sf_driver.find_element(By.CSS_SELECTOR, selector)
                if submit_btn.is_displayed():
                    sf_driver.execute_script("arguments[0].click();", submit_btn)
                    print(f"✅ Submit clicked with selector: {selector}")
                    submit_clicked = True
                    break
            except:
                continue
        
        if submit_clicked:
            time.sleep(8)
            sf_driver.save_screenshot("final_sf_step4_after_submit.png")
            
            # Check for verification page
            current_url = sf_driver.current_url
            page_source = sf_driver.page_source.lower()
            
            verification_keywords = ["verification", "6-digit", "code", "verify", "email"]
            found_verification = any(kw in page_source for kw in verification_keywords)
            
            if found_verification:
                print(f"✅ VERIFICATION PAGE REACHED!")
                print(f"📧 Email sent to: {email_info['email']}")
                
                return {
                    "success": True,
                    "email": email_info['email'],
                    "sf_driver": sf_driver,
                    "verification_page": True
                }
            else:
                print(f"⚠️ Verification page not clearly detected")
                return {
                    "success": True,
                    "email": email_info['email'],
                    "sf_driver": sf_driver,
                    "verification_page": False
                }
        else:
            print(f"❌ Could not submit form!")
            return None
        
    except Exception as e:
        print(f"❌ Santa Fe error: {e}")
        if sf_driver:
            sf_driver.save_screenshot("final_sf_error.png")
        return None

def check_imail_for_codes(email_info, max_checks=8):
    """Check imail for verification codes"""
    print(f"\n📬 CHECKING IMAIL FOR VERIFICATION CODES")
    print("=" * 50)
    
    email_driver = email_info['driver']
    
    for i in range(1, max_checks + 1):
        try:
            print(f"🔍 Check {i}/{max_checks}...")
            
            # Refresh mailbox
            email_driver.refresh()
            time.sleep(3)
            
            # Get page source
            page_source = email_driver.page_source
            
            # Look for 6-digit codes
            code_pattern = r'\b\d{6}\b'
            found_codes = re.findall(code_pattern, page_source)
            
            if found_codes:
                print(f"🎯 FOUND CODES: {found_codes}")
                
                # Filter for exactly 6 digits
                six_digit_codes = [code for code in found_codes if len(code) == 6]
                
                if six_digit_codes:
                    print(f"✅ 6-DIGIT VERIFICATION CODES: {six_digit_codes}")
                    return six_digit_codes[0]  # Return first valid code
            
            # Check for Santa Fe keywords
            sf_keywords = ["santa fe", "verification", "college", "admission", "code"]
            found_sf = any(kw in page_source.lower() for kw in sf_keywords)
            
            if found_sf:
                print(f"📧 Santa Fe email detected")
            
            print(f"⏰ Waiting 15 seconds...")
            time.sleep(15)
            
        except Exception as e:
            print(f"⚠️ Check {i} failed: {e}")
            time.sleep(5)
    
    print(f"❌ No verification code found after {max_checks} checks")
    return None

def final_integration_test():
    """Final complete test"""
    print("🏆 FINAL COMPLETE IMAIL + SANTA FE TEST")
    print("=" * 60)
    
    email_info = None
    sf_result = None
    
    try:
        # Step extract gg from pdf: Create email
        print(f"STEP extract gg from pdf: Creating imail email...")
        email_info = create_imail_email_final()
        
        if not email_info:
            print("❌ Email creation failed!")
            return
        
        print(f"\n✅ EMAIL CREATED: {email_info['email']}")
        
        # Step 2: Santa Fe registration
        print(f"\nSTEP 2: Santa Fe registration...")
        sf_result = santa_fe_with_working_selectors(email_info)
        
        if not sf_result:
            print("❌ Santa Fe registration failed!")
            return
        
        print(f"\n✅ SANTA FE REGISTRATION COMPLETED!")
        
        # Step 3: Check for verification
        print(f"\nSTEP 3: Checking for verification email...")
        verification_code = check_imail_for_codes(email_info)
        
        if verification_code:
            print(f"\n🎯 SUCCESS! VERIFICATION CODE: {verification_code}")
            
            # Save result
            result = {
                "email": email_info['email'],
                "verification_code": verification_code,
                "timestamp": time.time(),
                "status": "SUCCESS"
            }
            
            with open("final_test_result.json", "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"✅ Result saved to final_test_result.json")
            
        else:
            print(f"\n⚠️ No verification code found automatically")
            print(f"📧 Check manually at: {email_info['email']}")
            
            # Manual input option
            manual_code = input(f"\n🔑 Enter verification code manually (or press Enter to skip): ").strip()
            
            if manual_code and len(manual_code) == 6:
                result = {
                    "email": email_info['email'],
                    "verification_code": manual_code,
                    "timestamp": time.time(),
                    "status": "MANUAL_SUCCESS"
                }
                
                with open("final_test_result.json", "w") as f:
                    json.dump(result, f, indent=2)
                
                print(f"✅ Manual result saved!")
        
        # Final summary
        print(f"\n🏆 FINAL TEST SUMMARY:")
        print(f"📧 Email: {email_info['email']}")
        print(f"🎓 Santa Fe: {'✅ SUCCESS' if sf_result else '❌ FAILED'}")
        print(f"🔑 Verification: {'✅ FOUND' if verification_code else '⚠️ MANUAL'}")
        
        # Keep browsers open for inspection
        print(f"\n⏰ Keeping browsers open for 60 seconds...")
        time.sleep(60)
        
    except Exception as e:
        print(f"❌ Final test error: {e}")
    
    finally:
        # Cleanup
        if email_info and email_info.get('driver'):
            email_info['driver'].quit()
            print("✅ Email browser closed")
        
        if sf_result and sf_result.get('sf_driver'):
            sf_result['sf_driver'].quit()
            print("✅ Santa Fe browser closed")
        
        print(f"\n🏁 FINAL TEST COMPLETED!")

if __name__ == "__main__":
    final_integration_test() 