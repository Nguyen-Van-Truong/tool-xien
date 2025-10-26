#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 FIND REAL SUBMIT BUTTON
Tìm submit button thật sự trên Santa Fe form
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

def find_real_submit():
    """Tìm submit button thật sự"""
    print("🎯 FIND REAL SUBMIT BUTTON")
    print("=" * 50)
    
    person = load_person_data()
    if not person:
        return
    
    driver = None
    try:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        
        # Load extensions
        try:
            opts.add_extension("driver/captchasolver.crx")
            opts.add_extension("driver/extract gg from pdf.crx")
        except:
            pass
        
        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, 20)
        
        print(f"🌐 Opening Santa Fe College...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(8)
        
        # Navigate to form
        print(f"🎯 Navigating to form...")
        
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
        driver.save_screenshot("find_submit_step1_form.png")
        
        # Fill COMPLETE form to enable submit button
        print(f"📝 Filling COMPLETE form...")
        
        # Generate email with imail pattern
        random_num = random.randint(10, 99)
        test_email = f"{person['first_name'].lower()}{random_num}@naka.edu.pl"
        
        # Required fields
        form_fields = {
            "fstNameSTR": person['first_name'],
            "lstNameSTR": person['last_name'], 
            "emailAddrsSTR": test_email,
            "cemailAddrsSTR": test_email,
            "ssnumSTR": person['ssn'].replace('-', ''),
            "cssnumSTR": person['ssn'].replace('-', '')
        }
        
        print(f"🎯 Using email: {test_email}")
        
        # Fill text fields
        for field_id, value in form_fields.items():
            try:
                # Try multiple selector approaches
                field = None
                selectors = [
                    f"#{field_id}",
                    f"input[id='{field_id}']",
                    f"input[name='{field_id}']",
                    f"[ng-model*='{field_id}']"
                ]
                
                for selector in selectors:
                    try:
                        field = driver.find_element(By.CSS_SELECTOR, selector)
                        if field.is_displayed():
                            break
                    except:
                        continue
                
                if field:
                    # Scroll to field
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
                    time.sleep(0.5)
                    
                    # Clear and fill
                    field.clear()
                    field.send_keys(value)
                    print(f"✅ {field_id}: {value}")
                    time.sleep(0.5)
                else:
                    print(f"⚠️ Field not found: {field_id}")
                    
            except Exception as e:
                print(f"❌ {field_id}: {e}")
        
        # Fill birth date
        try:
            print(f"📅 Filling birth date...")
            
            month_select = driver.find_element(By.ID, "month")
            day_select = driver.find_element(By.ID, "day") 
            year_select = driver.find_element(By.ID, "year")
            
            Select(month_select).select_by_value("6")  # June
            Select(day_select).select_by_value("15")   # 15th
            Select(year_select).select_by_value("1995") # 1995
            
            print(f"✅ Birth date: 6/15/1995")
            
        except Exception as e:
            print(f"⚠️ Birth date error: {e}")
        
        # Fill birth country
        try:
            country_select = driver.find_element(By.ID, "birthctrySTR")
            Select(country_select).select_by_value("US")
            print(f"✅ Birth country: US")
        except Exception as e:
            print(f"⚠️ Birth country error: {e}")
        
        # Check SSN notice
        try:
            ssn_checkbox = driver.find_element(By.ID, "ssnNoticeCB")
            if not ssn_checkbox.is_selected():
                driver.execute_script("arguments[0].click();", ssn_checkbox)
                print(f"✅ SSN notice checked")
        except Exception as e:
            print(f"⚠️ SSN checkbox error: {e}")
        
        # Wait a bit for form validation
        time.sleep(3)
        driver.save_screenshot("find_submit_step2_form_complete.png")
        
        # Now look for submit buttons that are ENABLED
        print(f"\n🔍 Looking for ENABLED submit buttons...")
        
        # Look for all buttons again
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        
        enabled_buttons = []
        for i, btn in enumerate(all_buttons):
            if btn.is_displayed() and btn.is_enabled():
                btn_text = btn.text.strip()
                btn_type = btn.get_attribute("type") or ""
                btn_class = btn.get_attribute("class") or ""
                btn_id = btn.get_attribute("id") or ""
                
                enabled_buttons.append(btn)
                print(f"  Enabled Button {i+1}:")
                print(f"    Text: '{btn_text}'")
                print(f"    Type: '{btn_type}'")
                print(f"    Class: '{btn_class}'")
                print(f"    ID: '{btn_id}'")
                print()
        
        # Look for submit-type buttons specifically
        submit_candidates = []
        for btn in enabled_buttons:
            btn_text = btn.text.strip().lower()
            btn_type = btn.get_attribute("type") or ""
            btn_class = btn.get_attribute("class") or ""
            
            submit_keywords = ["submit", "create", "register", "apply", "send", "continue"]
            
            if (btn_type == "submit" or 
                any(kw in btn_text for kw in submit_keywords) or
                "submit" in btn_class.lower()):
                
                submit_candidates.append(btn)
                print(f"🎯 SUBMIT CANDIDATE: '{btn.text.strip()}' (type: {btn_type})")
        
        # Try each submit candidate
        print(f"\n🚀 TRYING SUBMIT CANDIDATES...")
        
        for i, btn in enumerate(submit_candidates):
            try:
                btn_text = btn.text.strip()
                btn_type = btn.get_attribute("type") or ""
                
                print(f"\nTrying candidate {i+1}: '{btn_text}' (type: {btn_type})")
                
                # Scroll and highlight
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                driver.execute_script("arguments[0].style.border='3px solid red';", btn)
                time.sleep(2)
                
                # Screenshot before click
                driver.save_screenshot(f"find_submit_candidate_{i+1}.png")
                
                # Click
                driver.execute_script("arguments[0].click();", btn)
                print(f"✅ Clicked candidate {i+1}!")
                
                time.sleep(8)
                
                # Check result
                current_url = driver.current_url
                page_source = driver.page_source.lower()
                
                print(f"  Current URL: {current_url}")
                
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
                
                if found_verification:
                    print(f"  🎯 VERIFICATION INDICATORS: {found_verification}")
                    
                    # Save success result
                    result = {
                        "button": {
                            "text": btn_text,
                            "type": btn_type,
                            "class": btn.get_attribute("class") or ""
                        },
                        "email": test_email,
                        "verification_keywords": found_verification,
                        "success_keywords": found_success,
                        "final_url": current_url,
                        "timestamp": time.time(),
                        "status": "VERIFICATION_PAGE_REACHED"
                    }
                    
                    with open("real_submit_success.json", "w") as f:
                        json.dump(result, f, indent=2)
                    
                    driver.save_screenshot(f"find_submit_verification_page.png")
                    
                    print(f"🎉 SUCCESS! VERIFICATION PAGE REACHED!")
                    print(f"📧 Email sent to: {test_email}")
                    print(f"💾 Result saved to real_submit_success.json")
                    
                    # Keep browser open for manual verification
                    print(f"\n⏰ Keeping browser open for manual verification (120s)...")
                    time.sleep(120)
                    
                    return result
                    
                elif found_success:
                    print(f"  ✅ SUCCESS INDICATORS: {found_success}")
                    
                else:
                    print(f"  ⚠️ No clear success/verification indicators")
                    driver.save_screenshot(f"find_submit_result_{i+1}.png")
                
            except Exception as e:
                print(f"  ❌ Candidate {i+1} failed: {e}")
                continue
        
        print(f"⚠️ No working submit button found")
        
        # Manual inspection
        print(f"\n⏰ Manual inspection time (60s)...")
        time.sleep(60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if driver:
            driver.save_screenshot("find_submit_error.png")
    
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    find_real_submit() 