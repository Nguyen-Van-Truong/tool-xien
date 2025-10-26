#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏆 COMPLETE TEST WITH REAL EMAIL
Sử dụng email đã tạo thành công để test Santa Fe registration
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

def load_person_data():
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def create_working_imail():
    """Tạo email imail working"""
    print("📧 CREATING WORKING IMAIL EMAIL")
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
            print("⚠️ naka.edu.pl selection failed")
        
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

def test_santa_fe_with_real_email(email_info):
    """Test Santa Fe với email thật"""
    print(f"\n🎓 TESTING SANTA FE WITH REAL EMAIL")
    print("=" * 50)
    
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
        
        # Navigation working flow
        print(f"🎯 Navigation...")
        
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
        button1.click()
        time.sleep(3)
        
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
        option1.click()
        time.sleep(2)
        
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
        next1.click()
        time.sleep(3)
        
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
        option2.click()
        time.sleep(2)
        
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
        next2.click()
        time.sleep(5)
        
        print(f"✅ Reached registration form!")
        sf_driver.save_screenshot("real_email_step1_form.png")
        
        # Fill form with real email
        print(f"📝 Filling form with REAL email: {email_info['email']}")
        
        # Basic required fields that we know work
        working_fields = [
            ("fstNameSTR", person['first_name']),
            ("lstNameSTR", person['last_name']),
            ("emailAddrsSTR", email_info['email']),
            ("cemailAddrsSTR", email_info['email'])
        ]
        
        for field_id, value in working_fields:
            try:
                field = sf_driver.find_element(By.ID, field_id)
                field.clear()
                field.send_keys(value)
                print(f"✅ {field_id}: {value}")
                time.sleep(0.8)
            except Exception as e:
                print(f"⚠️ {field_id}: {e}")
        
        sf_driver.save_screenshot("real_email_step2_form_filled.png")
        
        # Look for ANY submit mechanism
        print(f"\n🔍 LOOKING FOR SUBMIT MECHANISMS...")
        
        # Try JavaScript form submission
        try:
            print(f"🚀 Trying JavaScript form submit...")
            sf_driver.execute_script("document.forms[0].submit();")
            time.sleep(5)
            print(f"✅ JavaScript submit attempted")
        except Exception as e:
            print(f"⚠️ JavaScript submit failed: {e}")
        
        # Try pressing Enter on last field
        try:
            print(f"⌨️ Trying Enter key on last field...")
            from selenium.webdriver.common.keys import Keys
            last_field = sf_driver.find_element(By.ID, "cemailAddrsSTR")
            last_field.send_keys(Keys.ENTER)
            time.sleep(5)
            print(f"✅ Enter key attempted")
        except Exception as e:
            print(f"⚠️ Enter key failed: {e}")
        
        # Check if anything happened
        current_url = sf_driver.current_url
        page_source = sf_driver.page_source.lower()
        
        print(f"📄 Current URL: {current_url}")
        
        # Look for verification indicators
        verification_keywords = [
            "verification", "verify", "6-digit", "email sent", 
            "check your email", "code", "activate", "confirm"
        ]
        
        found_verification = [kw for kw in verification_keywords if kw in page_source]
        
        if found_verification:
            print(f"🎯 VERIFICATION INDICATORS: {found_verification}")
            
            sf_driver.save_screenshot("real_email_step3_verification.png")
            
            # Success! Now check email
            print(f"\n📬 CHECKING EMAIL FOR VERIFICATION CODE...")
            
            email_driver = email_info['driver']
            
            for attempt in range(1, 13):  # 12 attempts = 2 minutes
                try:
                    print(f"🔍 Email check {attempt}/12...")
                    
                    # Refresh email
                    email_driver.refresh()
                    time.sleep(3)
                    
                    # Look for verification code
                    email_source = email_driver.page_source
                    
                    # Pattern for 6-digit codes
                    import re
                    codes = re.findall(r'\b\d{6}\b', email_source)
                    
                    if codes:
                        print(f"🎯 FOUND CODES: {codes}")
                        
                        # Use first 6-digit code
                        verification_code = codes[0]
                        print(f"✅ VERIFICATION CODE: {verification_code}")
                        
                        # Try to enter verification code
                        try:
                            # Look for verification input
                            verification_inputs = sf_driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                            
                            for inp in verification_inputs:
                                placeholder = inp.get_attribute("placeholder") or ""
                                if "code" in placeholder.lower() or "verification" in placeholder.lower():
                                    inp.clear()
                                    inp.send_keys(verification_code)
                                    print(f"✅ Verification code entered!")
                                    
                                    # Look for submit
                                    submit_buttons = sf_driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button")
                                    for btn in submit_buttons:
                                        if btn.is_displayed() and btn.is_enabled():
                                            btn_text = btn.text.strip().lower()
                                            btn_value = btn.get_attribute("value") or ""
                                            if any(word in btn_text for word in ["verify", "submit", "continue"]) or any(word in btn_value.lower() for word in ["verify", "submit", "continue"]):
                                                btn.click()
                                                print(f"✅ Verification submitted!")
                                                break
                                    break
                            
                            time.sleep(5)
                            sf_driver.save_screenshot("real_email_step4_verification_complete.png")
                            
                            # Final success check
                            final_url = sf_driver.current_url
                            final_source = sf_driver.page_source.lower()
                            
                            success_keywords = ["success", "complete", "thank you", "account created"]
                            final_success = [kw for kw in success_keywords if kw in final_source]
                            
                            if final_success:
                                print(f"🎉 FINAL SUCCESS: {final_success}")
                                
                                # Save complete result
                                result = {
                                    "email": email_info['email'],
                                    "verification_code": verification_code,
                                    "final_url": final_url,
                                    "success_indicators": final_success,
                                    "timestamp": time.time(),
                                    "status": "COMPLETE_SUCCESS"
                                }
                                
                                with open("complete_test_success.json", "w") as f:
                                    json.dump(result, f, indent=2)
                                
                                print(f"💾 Complete success saved!")
                                
                                return result
                        
                        except Exception as e:
                            print(f"⚠️ Verification entry error: {e}")
                        
                        break
                    
                    else:
                        print(f"⏰ No codes yet, waiting 10s...")
                        time.sleep(10)
                
                except Exception as e:
                    print(f"⚠️ Email check {attempt} failed: {e}")
                    time.sleep(5)
            
            print(f"⚠️ No verification code found in email")
            
        else:
            print(f"⚠️ No verification page detected")
        
        # Manual inspection
        print(f"\n⏰ Manual inspection time (60s)...")
        time.sleep(60)
        
        return {
            "email": email_info['email'],
            "status": "PARTIAL_SUCCESS",
            "url": current_url
        }
        
    except Exception as e:
        print(f"❌ Santa Fe test error: {e}")
        if sf_driver:
            sf_driver.save_screenshot("real_email_error.png")
        return None
    
    finally:
        if sf_driver:
            sf_driver.quit()
            print("✅ Santa Fe browser closed")

def complete_test():
    """Test hoàn chỉnh"""
    print("🏆 COMPLETE TEST: REAL EMAIL + SANTA FE + VERIFICATION")
    print("=" * 70)
    
    # Step extract gg from pdf: Create real email
    email_info = create_working_imail()
    
    if not email_info:
        print("❌ Email creation failed!")
        return
    
    print(f"\n✅ EMAIL READY: {email_info['email']}")
    
    # Step 2: Test Santa Fe
    sf_result = test_santa_fe_with_real_email(email_info)
    
    if sf_result:
        print(f"\n🎯 TEST RESULT:")
        print(f"📧 Email: {sf_result['email']}")
        print(f"✅ Status: {sf_result['status']}")
        
        if sf_result.get('verification_code'):
            print(f"🔑 Verification Code: {sf_result['verification_code']}")
    
    # Cleanup
    if email_info and email_info.get('driver'):
        email_info['driver'].quit()
        print("✅ Email browser closed")
    
    print(f"\n🏁 COMPLETE TEST FINISHED!")

if __name__ == "__main__":
    complete_test() 