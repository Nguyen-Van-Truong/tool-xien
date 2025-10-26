#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 DISCOVER FORM STRUCTURE
Khám phá chi tiết form structure để tìm đúng selectors
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

def discover_form_structure():
    """Khám phá form structure chi tiết"""
    print("🔍 DISCOVERING SANTA FE FORM STRUCTURE")
    print("=" * 60)
    
    driver = None
    try:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        
        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, 20)
        
        print(f"🌐 Opening Santa Fe College...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(8)
        
        # Navigate to form using working flow
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
        driver.save_screenshot("discover_step1_form.png")
        
        # DISCOVER ALL FORM ELEMENTS
        print(f"\n🔍 DISCOVERING ALL FORM ELEMENTS...")
        
        # extract gg from pdf. Find all input elements
        print(f"\n📝 ALL INPUT ELEMENTS:")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        
        input_data = []
        for i, inp in enumerate(inputs):
            if inp.is_displayed():
                inp_data = {
                    "index": i+1,
                    "id": inp.get_attribute("id") or "",
                    "name": inp.get_attribute("name") or "",
                    "type": inp.get_attribute("type") or "",
                    "placeholder": inp.get_attribute("placeholder") or "",
                    "class": inp.get_attribute("class") or "",
                    "value": inp.get_attribute("value") or "",
                    "required": inp.get_attribute("required") or "",
                    "ng_model": inp.get_attribute("ng-model") or "",
                    "displayed": inp.is_displayed(),
                    "enabled": inp.is_enabled()
                }
                
                input_data.append(inp_data)
                
                print(f"  Input {i+1}:")
                print(f"    ID: '{inp_data['id']}'")
                print(f"    Name: '{inp_data['name']}'")
                print(f"    Type: '{inp_data['type']}'")
                print(f"    Placeholder: '{inp_data['placeholder']}'")
                print(f"    Class: '{inp_data['class']}'")
                print(f"    Value: '{inp_data['value']}'")
                print(f"    Required: '{inp_data['required']}'")
                print(f"    NG-Model: '{inp_data['ng_model']}'")
                print(f"    Displayed: {inp_data['displayed']}, Enabled: {inp_data['enabled']}")
                print()
        
        # 2. Find all select elements
        print(f"\n📋 ALL SELECT ELEMENTS:")
        selects = driver.find_elements(By.TAG_NAME, "select")
        
        select_data = []
        for i, sel in enumerate(selects):
            if sel.is_displayed():
                sel_data = {
                    "index": i+1,
                    "id": sel.get_attribute("id") or "",
                    "name": sel.get_attribute("name") or "",
                    "class": sel.get_attribute("class") or "",
                    "ng_model": sel.get_attribute("ng-model") or "",
                    "displayed": sel.is_displayed(),
                    "enabled": sel.is_enabled()
                }
                
                select_data.append(sel_data)
                
                print(f"  Select {i+1}:")
                print(f"    ID: '{sel_data['id']}'")
                print(f"    Name: '{sel_data['name']}'")
                print(f"    Class: '{sel_data['class']}'")
                print(f"    NG-Model: '{sel_data['ng_model']}'")
                print(f"    Displayed: {sel_data['displayed']}, Enabled: {sel_data['enabled']}")
                print()
        
        # 3. Find all button elements
        print(f"\n🔘 ALL BUTTON ELEMENTS:")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        button_data = []
        for i, btn in enumerate(buttons):
            if btn.is_displayed():
                btn_data = {
                    "index": i+1,
                    "id": btn.get_attribute("id") or "",
                    "type": btn.get_attribute("type") or "",
                    "class": btn.get_attribute("class") or "",
                    "text": btn.text.strip(),
                    "value": btn.get_attribute("value") or "",
                    "onclick": btn.get_attribute("onclick") or "",
                    "ng_click": btn.get_attribute("ng-click") or "",
                    "displayed": btn.is_displayed(),
                    "enabled": btn.is_enabled()
                }
                
                button_data.append(btn_data)
                
                print(f"  Button {i+1}:")
                print(f"    ID: '{btn_data['id']}'")
                print(f"    Type: '{btn_data['type']}'")
                print(f"    Class: '{btn_data['class']}'")
                print(f"    Text: '{btn_data['text']}'")
                print(f"    Value: '{btn_data['value']}'")
                print(f"    OnClick: '{btn_data['onclick']}'")
                print(f"    NG-Click: '{btn_data['ng_click']}'")
                print(f"    Displayed: {btn_data['displayed']}, Enabled: {btn_data['enabled']}")
                print()
        
        # 4. Find all forms
        print(f"\n📋 ALL FORM ELEMENTS:")
        forms = driver.find_elements(By.TAG_NAME, "form")
        
        form_data = []
        for i, form in enumerate(forms):
            if form.is_displayed():
                form_info = {
                    "index": i+1,
                    "id": form.get_attribute("id") or "",
                    "name": form.get_attribute("name") or "",
                    "action": form.get_attribute("action") or "",
                    "method": form.get_attribute("method") or "",
                    "class": form.get_attribute("class") or "",
                    "ng_submit": form.get_attribute("ng-submit") or "",
                    "displayed": form.is_displayed()
                }
                
                form_data.append(form_info)
                
                print(f"  Form {i+1}:")
                print(f"    ID: '{form_info['id']}'")
                print(f"    Name: '{form_info['name']}'")
                print(f"    Action: '{form_info['action']}'")
                print(f"    Method: '{form_info['method']}'")
                print(f"    Class: '{form_info['class']}'")
                print(f"    NG-Submit: '{form_info['ng_submit']}'")
                print(f"    Displayed: {form_info['displayed']}")
                print()
        
        # 5. Look for email-related fields specifically
        print(f"\n📧 EMAIL-RELATED FIELD SEARCH:")
        
        email_keywords = ["email", "mail", "@", "address"]
        email_fields = []
        
        for inp in inputs:
            if inp.is_displayed():
                inp_id = inp.get_attribute("id") or ""
                inp_name = inp.get_attribute("name") or ""
                inp_placeholder = inp.get_attribute("placeholder") or ""
                inp_class = inp.get_attribute("class") or ""
                inp_ng_model = inp.get_attribute("ng-model") or ""
                
                all_attributes = f"{inp_id} {inp_name} {inp_placeholder} {inp_class} {inp_ng_model}".lower()
                
                if any(keyword in all_attributes for keyword in email_keywords):
                    email_field = {
                        "id": inp_id,
                        "name": inp_name,
                        "type": inp.get_attribute("type") or "",
                        "placeholder": inp_placeholder,
                        "class": inp_class,
                        "ng_model": inp_ng_model,
                        "all_text": all_attributes
                    }
                    
                    email_fields.append(email_field)
                    
                    print(f"  EMAIL FIELD FOUND:")
                    print(f"    ID: '{email_field['id']}'")
                    print(f"    Name: '{email_field['name']}'")
                    print(f"    Type: '{email_field['type']}'")
                    print(f"    Placeholder: '{email_field['placeholder']}'")
                    print(f"    Class: '{email_field['class']}'")
                    print(f"    NG-Model: '{email_field['ng_model']}'")
                    print()
        
        # 6. Look for submit-related elements
        print(f"\n🚀 SUBMIT-RELATED ELEMENT SEARCH:")
        
        submit_keywords = ["submit", "send", "create", "register", "apply", "continue", "next"]
        submit_elements = []
        
        # Check buttons
        for btn in buttons:
            if btn.is_displayed():
                btn_text = btn.text.strip().lower()
                btn_class = btn.get_attribute("class") or ""
                btn_onclick = btn.get_attribute("onclick") or ""
                btn_ng_click = btn.get_attribute("ng-click") or ""
                btn_type = btn.get_attribute("type") or ""
                
                all_btn_text = f"{btn_text} {btn_class} {btn_onclick} {btn_ng_click} {btn_type}".lower()
                
                if any(keyword in all_btn_text for keyword in submit_keywords):
                    submit_element = {
                        "type": "button",
                        "id": btn.get_attribute("id") or "",
                        "text": btn.text.strip(),
                        "class": btn_class,
                        "type_attr": btn_type,
                        "onclick": btn_onclick,
                        "ng_click": btn_ng_click,
                        "enabled": btn.is_enabled(),
                        "all_text": all_btn_text
                    }
                    
                    submit_elements.append(submit_element)
                    
                    print(f"  SUBMIT BUTTON FOUND:")
                    print(f"    Text: '{submit_element['text']}'")
                    print(f"    ID: '{submit_element['id']}'")
                    print(f"    Class: '{submit_element['class']}'")
                    print(f"    Type: '{submit_element['type_attr']}'")
                    print(f"    OnClick: '{submit_element['onclick']}'")
                    print(f"    NG-Click: '{submit_element['ng_click']}'")
                    print(f"    Enabled: {submit_element['enabled']}")
                    print()
        
        # Check inputs
        for inp in inputs:
            if inp.is_displayed():
                inp_type = inp.get_attribute("type") or ""
                inp_value = inp.get_attribute("value") or ""
                inp_class = inp.get_attribute("class") or ""
                inp_onclick = inp.get_attribute("onclick") or ""
                
                all_inp_text = f"{inp_type} {inp_value} {inp_class} {inp_onclick}".lower()
                
                if any(keyword in all_inp_text for keyword in submit_keywords) or inp_type == "submit":
                    submit_element = {
                        "type": "input",
                        "id": inp.get_attribute("id") or "",
                        "type_attr": inp_type,
                        "value": inp_value,
                        "class": inp_class,
                        "onclick": inp_onclick,
                        "enabled": inp.is_enabled(),
                        "all_text": all_inp_text
                    }
                    
                    submit_elements.append(submit_element)
                    
                    print(f"  SUBMIT INPUT FOUND:")
                    print(f"    Type: '{submit_element['type_attr']}'")
                    print(f"    ID: '{submit_element['id']}'")
                    print(f"    Value: '{submit_element['value']}'")
                    print(f"    Class: '{submit_element['class']}'")
                    print(f"    OnClick: '{submit_element['onclick']}'")
                    print(f"    Enabled: {submit_element['enabled']}")
                    print()
        
        # Save all data
        complete_structure = {
            "inputs": input_data,
            "selects": select_data,
            "buttons": button_data,
            "forms": form_data,
            "email_fields": email_fields,
            "submit_elements": submit_elements,
            "timestamp": time.time(),
            "url": driver.current_url
        }
        
        with open("form_structure_complete.json", "w", encoding="utf-8") as f:
            json.dump(complete_structure, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Complete structure saved to form_structure_complete.json")
        
        # Take final screenshot
        driver.save_screenshot("discover_step2_complete.png")
        
        # Manual inspection time
        print(f"\n⏰ Manual inspection time (45s) for final verification...")
        time.sleep(45)
        
    except Exception as e:
        print(f"❌ Discovery error: {e}")
        if driver:
            driver.save_screenshot("discover_error.png")
    
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    discover_form_structure() 