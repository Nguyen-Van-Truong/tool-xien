#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 EXPLORE IMAIL DOMAINS
Khám phá chi tiết domain selection trên imail.edu.vn
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

def load_person_data():
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[0] if data else None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def explore_imail_domains():
    """Khám phá chi tiết về domain selection"""
    print("🔍 EXPLORE IMAIL DOMAINS")
    print("=" * 50)
    
    person = load_person_data()
    if not person:
        print("❌ No data")
        return
    
    driver = None
    try:
        print(f"👤 Person: {person['first_name']}")
        
        opts = webdriver.ChromeOptions()
        opts.add_argument('--start-maximized')
        
        driver = webdriver.Chrome(options=opts)
        
        print(f"🌐 Opening imail.edu.vn...")
        driver.get("https://imail.edu.vn")
        time.sleep(5)
        
        driver.save_screenshot("explore_step1_homepage.png")
        
        # Generate username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{person['first_name'].lower()}{random_numbers}"
        
        print(f"👤 Username: {username}")
        
        # Explore ALL elements on page
        print(f"\n🔍 EXPLORING ALL PAGE ELEMENTS...")
        
        # Find all inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"\n📝 FOUND {len(inputs)} INPUT ELEMENTS:")
        
        username_input = None
        domain_input = None
        submit_buttons = []
        
        for i, inp in enumerate(inputs):
            inp_id = inp.get_attribute("id") or ""
            inp_name = inp.get_attribute("name") or ""
            inp_type = inp.get_attribute("type") or ""
            inp_placeholder = inp.get_attribute("placeholder") or ""
            inp_value = inp.get_attribute("value") or ""
            inp_class = inp.get_attribute("class") or ""
            is_displayed = inp.is_displayed()
            is_enabled = inp.is_enabled()
            
            print(f"  Input {i+1}:")
            print(f"    ID: '{inp_id}'")
            print(f"    Name: '{inp_name}'")
            print(f"    Type: '{inp_type}'")
            print(f"    Placeholder: '{inp_placeholder}'")
            print(f"    Value: '{inp_value}'")
            print(f"    Class: '{inp_class}'")
            print(f"    Displayed: {is_displayed}, Enabled: {is_enabled}")
            print()
            
            # Identify elements
            if inp_name == "user" and inp_type == "text" and is_displayed:
                username_input = inp
                print(f"    🎯 IDENTIFIED AS USERNAME INPUT")
            
            if inp_name == "domain" and is_displayed:
                domain_input = inp
                print(f"    🎯 IDENTIFIED AS DOMAIN INPUT")
                
            if inp_type == "submit" and is_displayed:
                submit_buttons.append(inp)
                print(f"    🎯 IDENTIFIED AS SUBMIT BUTTON")
        
        # Find all selects
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"\n📋 FOUND {len(selects)} SELECT ELEMENTS:")
        
        domain_select = None
        
        for i, sel in enumerate(selects):
            sel_id = sel.get_attribute("id") or ""
            sel_name = sel.get_attribute("name") or ""
            sel_class = sel.get_attribute("class") or ""
            is_displayed = sel.is_displayed()
            is_enabled = sel.is_enabled()
            
            print(f"  Select {i+1}:")
            print(f"    ID: '{sel_id}'")
            print(f"    Name: '{sel_name}'")
            print(f"    Class: '{sel_class}'")
            print(f"    Displayed: {is_displayed}, Enabled: {is_enabled}")
            
            if is_displayed and is_enabled:
                try:
                    select_obj = Select(sel)
                    options = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]
                    print(f"    Options ({len(options)}): {options}")
                    
                    if sel_name == "domain" or "domain" in sel_id.lower():
                        domain_select = sel
                        print(f"    🎯 IDENTIFIED AS DOMAIN SELECT")
                        
                        # Check for naka.edu.pl
                        naka_option = None
                        for opt in select_obj.options:
                            if "naka.edu.pl" in opt.text:
                                naka_option = opt
                                print(f"    ✅ FOUND naka.edu.pl: '{opt.text}'")
                                break
                        
                        if not naka_option:
                            print(f"    ⚠️ naka.edu.pl NOT FOUND in options")
                    
                except Exception as e:
                    print(f"    ❌ Error reading options: {e}")
            print()
        
        # Enter username
        if username_input:
            print(f"\n📝 ENTERING USERNAME...")
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", username_input)
                time.sleep(1)
                username_input.clear()
                username_input.send_keys(username)
                print(f"✅ Username entered: {username}")
                driver.save_screenshot("explore_step2_username_entered.png")
            except Exception as e:
                print(f"❌ Username input failed: {e}")
        else:
            print(f"❌ No username input found!")
        
        # Handle domain
        if domain_select:
            print(f"\n📋 HANDLING DOMAIN SELECT...")
            try:
                select_obj = Select(domain_select)
                
                # Try to select naka.edu.pl
                naka_selected = False
                for opt in select_obj.options:
                    if "naka.edu.pl" in opt.text:
                        select_obj.select_by_visible_text(opt.text)
                        print(f"✅ Selected domain: {opt.text}")
                        naka_selected = True
                        break
                
                if not naka_selected:
                    # Select first available option
                    if len(select_obj.options) > 1:
                        select_obj.select_by_index(1)  # Skip first empty option
                        selected_text = select_obj.first_selected_option.text
                        print(f"⚠️ Selected fallback domain: {selected_text}")
                
                driver.save_screenshot("explore_step3_domain_selected.png")
                
            except Exception as e:
                print(f"❌ Domain selection failed: {e}")
                
        elif domain_input:
            print(f"\n📝 HANDLING DOMAIN INPUT...")
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", domain_input)
                time.sleep(1)
                domain_input.clear()
                domain_input.send_keys("naka.edu.pl")
                print(f"✅ Domain entered: naka.edu.pl")
                driver.save_screenshot("explore_step3_domain_entered.png")
            except Exception as e:
                print(f"❌ Domain input failed: {e}")
        else:
            print(f"⚠️ No domain input/select found!")
        
        # Click submit
        print(f"\n🚀 CLICKING SUBMIT BUTTON...")
        
        create_clicked = False
        for i, btn in enumerate(submit_buttons):
            btn_class = btn.get_attribute("class") or ""
            btn_value = btn.get_attribute("value") or ""
            
            print(f"  Button {i+1}: class='{btn_class}', value='{btn_value}'")
            
            if "bg-teal-500" in btn_class or "teal" in btn_class:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"✅ Clicked button {i+1}!")
                    create_clicked = True
                    break
                except Exception as e:
                    print(f"❌ Button {i+1} click failed: {e}")
        
        if not create_clicked and submit_buttons:
            # Try first available button
            try:
                btn = submit_buttons[0]
                driver.execute_script("arguments[0].click();", btn)
                print(f"✅ Clicked fallback button!")
                create_clicked = True
            except Exception as e:
                print(f"❌ Fallback click failed: {e}")
        
        time.sleep(5)
        driver.save_screenshot("explore_step4_after_submit.png")
        
        # Analyze result
        print(f"\n🔍 ANALYZING RESULT...")
        current_url = driver.current_url
        page_title = driver.title
        page_source = driver.page_source.lower()
        
        print(f"📄 URL: {current_url}")
        print(f"📋 Title: {page_title}")
        
        # Check for email creation success
        email_indicators = [
            username.lower(),
            "naka.edu.pl",
            "email created",
            "success", 
            "successful",
            "inbox",
            "mailbox"
        ]
        
        found_indicators = [ind for ind in email_indicators if ind in page_source]
        
        if found_indicators:
            print(f"✅ Success indicators: {found_indicators}")
            
            # Try to find the actual email
            possible_emails = [
                f"{username}@naka.edu.pl",
                f"{username}@edu.pl",
                f"{username}@mail.pl"
            ]
            
            found_email = None
            for email in possible_emails:
                if email.lower() in page_source:
                    found_email = email
                    print(f"🎯 CONFIRMED EMAIL: {email}")
                    break
            
            if not found_email:
                print(f"⚠️ Email not found in page source")
        else:
            print(f"❌ No success indicators found")
        
        # Check for error messages
        error_keywords = ["error", "failed", "invalid", "wrong", "lỗi", "không"]
        found_errors = [kw for kw in error_keywords if kw in page_source]
        
        if found_errors:
            print(f"⚠️ Possible errors: {found_errors}")
        
        print(f"\n⏰ Keeping browser open for manual inspection (30s)...")
        time.sleep(30)
        
        # Final summary
        print(f"\n📊 EXPLORATION SUMMARY:")
        print(f"👤 Username: {username}")
        print(f"🌐 Final URL: {current_url}")
        print(f"🔄 Button Clicked: {create_clicked}")
        print(f"✅ Success Indicators: {found_indicators}")
        print(f"📧 Possible Email: {username}@naka.edu.pl")
        
    except Exception as e:
        print(f"❌ Exploration error: {e}")
        if driver:
            driver.save_screenshot("explore_error.png")
    
    finally:
        if driver:
            driver.quit()
            print(f"✅ Browser closed")

if __name__ == "__main__":
    explore_imail_domains() 