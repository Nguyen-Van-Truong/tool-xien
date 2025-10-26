#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 EXPLORE SUBMIT BUTTON
Khám phá submit button trên Santa Fe registration form
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

def load_person_data():
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def explore_submit_button():
    """Khám phá submit button trên Santa Fe form"""
    print("🔍 EXPLORE SUBMIT BUTTON ON SANTA FE FORM")
    print("=" * 60)
    
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
            print(f"✅ Extensions loaded")
        except:
            print(f"⚠️ Extensions not available")
        
        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, 20)
        
        print(f"🌐 Opening Santa Fe College...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(8)
        
        # Quick navigation to form
        print(f"🎯 Quick navigation to form...")
        
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
        driver.save_screenshot("explore_submit_step1_form.png")
        
        # Fill minimum required fields
        print(f"📝 Filling minimum fields...")
        
        try:
            # First name
            fname = driver.find_element(By.ID, "fstNameSTR")
            fname.clear()
            fname.send_keys(person['first_name'])
            print(f"✅ First name: {person['first_name']}")
            
            # Last name  
            lname = driver.find_element(By.ID, "lstNameSTR")
            lname.clear()
            lname.send_keys(person['last_name'])
            print(f"✅ Last name: {person['last_name']}")
            
            # Email
            email1 = driver.find_element(By.ID, "emailAddrsSTR")
            email1.clear()
            email1.send_keys("test@naka.edu.pl")
            
            email2 = driver.find_element(By.ID, "cemailAddrsSTR")
            email2.clear()
            email2.send_keys("test@naka.edu.pl")
            print(f"✅ Email fields filled")
            
        except Exception as e:
            print(f"⚠️ Form filling error: {e}")
        
        driver.save_screenshot("explore_submit_step2_form_filled.png")
        
        # EXPLORE ALL POSSIBLE SUBMIT BUTTONS
        print(f"\n🔍 EXPLORING ALL POSSIBLE SUBMIT BUTTONS...")
        
        # Method extract gg from pdf: Find all buttons
        print(f"\n🔘 ALL BUTTONS ON PAGE...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        for i, btn in enumerate(buttons):
            btn_text = btn.text.strip()
            btn_value = btn.get_attribute("value") or ""
            btn_class = btn.get_attribute("class") or ""
            btn_id = btn.get_attribute("id") or ""
            btn_type = btn.get_attribute("type") or ""
            is_displayed = btn.is_displayed()
            is_enabled = btn.is_enabled()
            
            if is_displayed:
                print(f"  Button {i+1}:")
                print(f"    Text: '{btn_text}'")
                print(f"    Type: '{btn_type}'")
                print(f"    Value: '{btn_value}'")
                print(f"    Class: '{btn_class}'")
                print(f"    ID: '{btn_id}'")
                print(f"    Displayed: {is_displayed}, Enabled: {is_enabled}")
                print()
        
        # Method 2: Find all inputs
        print(f"\n📝 ALL INPUTS ON PAGE...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        
        for i, inp in enumerate(inputs):
            inp_type = inp.get_attribute("type") or ""
            inp_value = inp.get_attribute("value") or ""
            inp_class = inp.get_attribute("class") or ""
            inp_id = inp.get_attribute("id") or ""
            is_displayed = inp.is_displayed()
            is_enabled = inp.is_enabled()
            
            if is_displayed and inp_type in ["submit", "button"]:
                print(f"  Input {i+1}:")
                print(f"    Type: '{inp_type}'")
                print(f"    Value: '{inp_value}'")
                print(f"    Class: '{inp_class}'")
                print(f"    ID: '{inp_id}'")
                print(f"    Displayed: {is_displayed}, Enabled: {is_enabled}")
                print()
        
        # Method 3: Scroll down and look for more elements
        print(f"\n📜 SCROLLING TO FIND MORE ELEMENTS...")
        
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.save_screenshot("explore_submit_step3_scrolled_down.png")
        
        # Look again after scroll
        buttons_after_scroll = driver.find_elements(By.TAG_NAME, "button")
        inputs_after_scroll = driver.find_elements(By.TAG_NAME, "input")
        
        print(f"After scroll - Buttons: {len(buttons_after_scroll)}, Inputs: {len(inputs_after_scroll)}")
        
        # Check for new visible elements
        new_buttons = []
        for btn in buttons_after_scroll:
            if btn.is_displayed():
                btn_text = btn.text.strip()
                btn_type = btn.get_attribute("type") or ""
                if btn_text or btn_type == "submit":
                    new_buttons.append(btn)
                    print(f"  New button found: '{btn_text}' (type: {btn_type})")
        
        new_inputs = []
        for inp in inputs_after_scroll:
            if inp.is_displayed():
                inp_type = inp.get_attribute("type") or ""
                inp_value = inp.get_attribute("value") or ""
                if inp_type in ["submit", "button"]:
                    new_inputs.append(inp)
                    print(f"  New input found: type='{inp_type}' value='{inp_value}'")
        
        # Try clicking promising elements
        print(f"\n🚀 TRYING TO CLICK PROMISING ELEMENTS...")
        
        all_clickable = new_buttons + new_inputs
        
        for i, elem in enumerate(all_clickable):
            try:
                elem_text = elem.text.strip()
                elem_value = elem.get_attribute("value") or ""
                elem_type = elem.get_attribute("type") or ""
                elem_tag = elem.tag_name
                
                print(f"\nTrying element {i+1}: {elem_tag}")
                print(f"  Text: '{elem_text}'")
                print(f"  Value: '{elem_value}'")
                print(f"  Type: '{elem_type}'")
                
                # Scroll to element and highlight
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                driver.execute_script("arguments[0].style.border='3px solid red';", elem)
                time.sleep(2)
                
                # Take screenshot
                driver.save_screenshot(f"explore_submit_element_{i+1}.png")
                
                # Try to click
                driver.execute_script("arguments[0].click();", elem)
                print(f"✅ Clicked element {i+1}!")
                
                time.sleep(5)
                driver.save_screenshot(f"explore_submit_after_click_{i+1}.png")
                
                # Check result
                current_url = driver.current_url
                page_source = driver.page_source.lower()
                
                print(f"  Current URL: {current_url}")
                
                # Look for success indicators
                success_keywords = ["verification", "success", "submitted", "thank you", "created", "account", "email sent"]
                found_indicators = [kw for kw in success_keywords if kw in page_source]
                
                if found_indicators:
                    print(f"  🎯 SUCCESS INDICATORS FOUND: {found_indicators}")
                    
                    # Save success
                    result = {
                        "element": {
                            "tag": elem_tag,
                            "text": elem_text,
                            "value": elem_value,
                            "type": elem_type
                        },
                        "success_indicators": found_indicators,
                        "final_url": current_url,
                        "timestamp": time.time()
                    }
                    
                    with open("submit_success.json", "w") as f:
                        json.dump(result, f, indent=2)
                    
                    print(f"✅ SUCCESS! Saved to submit_success.json")
                    break
                else:
                    print(f"  ⚠️ No success indicators found")
                
            except Exception as e:
                print(f"  ❌ Element {i+1} click failed: {e}")
                continue
        
        # Manual inspection time
        print(f"\n⏰ Manual inspection time (45s)...")
        time.sleep(45)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if driver:
            driver.save_screenshot("explore_submit_error.png")
    
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    explore_submit_button() 