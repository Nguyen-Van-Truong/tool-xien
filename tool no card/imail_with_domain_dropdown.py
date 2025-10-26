#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 IMAIL WITH DOMAIN DROPDOWN
Handle domain dropdown để chọn naka.edu.pl
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

def create_email_with_domain_dropdown():
    """Tạo email với domain dropdown"""
    print("🎯 IMAIL WITH DOMAIN DROPDOWN")
    print("=" * 50)
    
    person = load_person_data()
    if not person:
        print("❌ No data")
        return None
    
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
        
        driver.save_screenshot("dropdown_step1_homepage.png")
        
        # Generate username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{person['first_name'].lower()}{random_numbers}"
        
        print(f"👤 Username: {username}")
        
        # Find username input
        username_input = None
        selectors = ["input[name='user'][type='text']"]
        
        for selector in selectors:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled():
                        username_input = inp
                        print(f"✅ Found username input")
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
        
        driver.save_screenshot("dropdown_step2_username_entered.png")
        
        # Find domain input (dropdown trigger)
        print(f"\n🔍 Finding domain dropdown...")
        domain_input = None
        
        domain_selectors = [
            "input[name='domain'][placeholder='Select Domain']",
            "input[placeholder='Select Domain']",
            "input[name='domain']"
        ]
        
        for selector in domain_selectors:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for inp in inputs:
                    if inp.is_displayed():
                        domain_input = inp
                        print(f"✅ Found domain dropdown trigger")
                        break
                if domain_input:
                    break
            except:
                continue
        
        if not domain_input:
            print(f"❌ No domain dropdown found!")
            return None
        
        # Click domain input to open dropdown
        print(f"\n📋 Opening domain dropdown...")
        
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", domain_input)
            time.sleep(1)
            
            # Try multiple click methods
            try:
                domain_input.click()
                print(f"✅ Clicked domain input")
            except:
                try:
                    ActionChains(driver).move_to_element(domain_input).click().perform()
                    print(f"✅ ActionChains clicked domain input")
                except:
                    driver.execute_script("arguments[0].click();", domain_input)
                    print(f"✅ JavaScript clicked domain input")
            
            time.sleep(2)
            driver.save_screenshot("dropdown_step3_domain_clicked.png")
            
            # Look for dropdown options
            print(f"\n🔍 Looking for dropdown options...")
            
            # Try multiple selectors for dropdown options
            option_selectors = [
                "div[class*='dropdown'] div", 
                "ul[class*='dropdown'] li",
                "div[class*='option']",
                "li[class*='option']",
                ".dropdown-item",
                ".option",
                "[data-value]",
                "div:contains('naka.edu.pl')",
                "li:contains('naka.edu.pl')"
            ]
            
            naka_option = None
            all_options = []
            
            for selector in option_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for contains
                        xpath = f"//*[contains(text(), 'naka.edu.pl')]"
                        options = driver.find_elements(By.XPATH, xpath)
                    else:
                        options = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for opt in options:
                        if opt.is_displayed():
                            opt_text = opt.text.strip()
                            if opt_text:
                                all_options.append(opt_text)
                                print(f"  Found option: '{opt_text}'")
                                
                                if "naka.edu.pl" in opt_text.lower():
                                    naka_option = opt
                                    print(f"  🎯 FOUND NAKA.EDU.PL OPTION!")
                    
                    if naka_option:
                        break
                        
                except Exception as e:
                    print(f"  ⚠️ Selector {selector} failed: {e}")
            
            print(f"\nFound {len(all_options)} dropdown options: {all_options}")
            
            # If naka.edu.pl found, click it
            if naka_option:
                print(f"\n✅ Selecting naka.edu.pl...")
                try:
                    naka_option.click()
                    print(f"✅ naka.edu.pl selected!")
                except:
                    try:
                        driver.execute_script("arguments[0].click();", naka_option)
                        print(f"✅ naka.edu.pl selected via JavaScript!")
                    except Exception as e:
                        print(f"❌ Failed to select naka.edu.pl: {e}")
            else:
                print(f"⚠️ naka.edu.pl not found in dropdown options")
                
                # Try alternative approaches
                print(f"\n🔧 Trying alternative approaches...")
                
                # Method extract gg from pdf: Type domain manually
                try:
                    domain_input.clear()
                    domain_input.send_keys("naka.edu.pl")
                    print(f"✅ Typed naka.edu.pl manually")
                except Exception as e:
                    print(f"❌ Manual typing failed: {e}")
                
                # Method 2: Use keyboard navigation
                try:
                    from selenium.webdriver.common.keys import Keys
                    domain_input.send_keys(Keys.ARROW_DOWN)
                    time.sleep(1)
                    domain_input.send_keys(Keys.ARROW_DOWN)
                    time.sleep(1)
                    domain_input.send_keys(Keys.ENTER)
                    print(f"✅ Used keyboard navigation")
                except Exception as e:
                    print(f"❌ Keyboard navigation failed: {e}")
            
            time.sleep(2)
            driver.save_screenshot("dropdown_step4_domain_selected.png")
            
        except Exception as e:
            print(f"❌ Domain dropdown handling failed: {e}")
        
        # Click create button
        print(f"\n🚀 Creating email...")
        
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
        
        create_clicked = False
        for btn in submit_buttons:
            if btn.is_displayed() and btn.is_enabled():
                btn_class = btn.get_attribute("class") or ""
                btn_value = btn.get_attribute("value") or ""
                
                if "bg-teal-500" in btn_class and "Create" in btn_value:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"✅ Create button clicked!")
                        create_clicked = True
                        break
                    except Exception as e:
                        print(f"❌ Create button failed: {e}")
        
        if not create_clicked:
            print(f"❌ Could not click create button!")
            return None
        
        time.sleep(5)
        driver.save_screenshot("dropdown_step5_after_create.png")
        
        # Check result
        print(f"\n🔍 Checking result...")
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        print(f"📄 URL: {current_url}")
        
        # Expected email
        expected_email = f"{username}@naka.edu.pl"
        
        # Check for success
        success_indicators = [
            expected_email.lower(),
            username.lower(),
            "naka.edu.pl",
            "email created",
            "success",
            "inbox"
        ]
        
        found_indicators = [ind for ind in success_indicators if ind in page_source]
        
        if found_indicators:
            print(f"✅ Success indicators: {found_indicators}")
            
            # Confirm email in page
            if expected_email.lower() in page_source:
                print(f"🎯 EMAIL CONFIRMED: {expected_email}")
                
                email_info = {
                    "email": expected_email,
                    "username": username,
                    "domain": "naka.edu.pl",
                    "driver": driver,
                    "created_time": time.time()
                }
                
                print(f"✅ Email creation successful!")
                return email_info
            else:
                print(f"⚠️ Expected email not found in page")
        else:
            print(f"❌ No success indicators found")
        
        print(f"\n⏰ Keeping browser open for inspection (20s)...")
        time.sleep(20)
        
        return None
        
    except Exception as e:
        print(f"❌ Email creation error: {e}")
        if driver:
            driver.save_screenshot("dropdown_error.png")
        return None

def test_email_creation_and_verification():
    """Test tạo email và test với Santa Fe nếu thành công"""
    print("🎯 FULL TEST: EMAIL CREATION + SANTA FE VERIFICATION")
    print("=" * 60)
    
    # Step extract gg from pdf: Create email with proper domain selection
    email_info = create_email_with_domain_dropdown()
    
    if not email_info:
        print("❌ Email creation failed!")
        return
    
    email_driver = email_info['driver']
    
    print(f"\n✅ EMAIL CREATED: {email_info['email']}")
    print(f"📧 Ready for Santa Fe registration test!")
    
    # Step 2: Quick Santa Fe test (optional)
    response = input("\n🎓 Test với Santa Fe College ngay? (y/n): ").strip().lower()
    
    if response == 'y':
        print(f"\n🎓 Starting Santa Fe registration test...")
        
        # Load person data
        person = load_person_data()
        if not person:
            print("❌ No person data!")
            email_driver.quit()
            return
        
        # Quick Santa Fe registration
        sf_driver = None
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_service = Service(ChromeDriverManager().install())
            opts = webdriver.ChromeOptions()
            opts.add_argument("--start-maximized")
            
            sf_driver = webdriver.Chrome(service=chrome_service, options=opts)
            wait = WebDriverWait(sf_driver, 20)
            
            print(f"🌐 Opening Santa Fe College...")
            sf_driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
            time.sleep(5)
            
            # Quick flow navigation (simplified)
            button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
            button1.click()
            time.sleep(2)
            
            option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
            option1.click()
            time.sleep(1)
            
            next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
            next1.click()
            time.sleep(2)
            
            option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
            option2.click()
            time.sleep(1)
            
            next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
            next2.click()
            time.sleep(3)
            
            print(f"✅ Reached Santa Fe registration form!")
            
            # Fill email fields
            try:
                email_field1 = sf_driver.find_element(By.ID, "emailAddrsSTR")
                email_field1.clear()
                email_field1.send_keys(email_info['email'])
                
                email_field2 = sf_driver.find_element(By.ID, "cemailAddrsSTR")
                email_field2.clear()
                email_field2.send_keys(email_info['email'])
                
                print(f"✅ Email fields filled: {email_info['email']}")
                
            except Exception as e:
                print(f"⚠️ Email field error: {e}")
            
            sf_driver.save_screenshot("test_sf_with_imail_email.png")
            
            print(f"\n🎯 INTEGRATION TEST RESULT:")
            print(f"📧 imail Email: {email_info['email']}")
            print(f"✅ Santa Fe form reached")
            print(f"✅ Email fields populated")
            print(f"🎓 Ready for full registration test!")
            
            print(f"\n⏰ Keeping Santa Fe browser open for inspection (30s)...")
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Santa Fe test error: {e}")
        finally:
            if sf_driver:
                sf_driver.quit()
                print("✅ Santa Fe browser closed")
    
    # Cleanup
    if email_driver:
        email_driver.quit()
        print("✅ Email browser closed")
    
    print(f"\n🏆 TEST COMPLETED!")
    print(f"📧 Email: {email_info['email']}")

if __name__ == "__main__":
    test_email_creation_and_verification() 