#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 QUICK BIRTH DATE FIX
Discover và fix birth date để enable submit button
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import json

def discover_and_fix_birth_date():
    """Discover birth date options và fix"""
    print("🔧 QUICK BIRTH DATE FIX")
    print("=" * 50)
    
    # Load person data
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            person = data[0] if data else None
    except:
        print("❌ Person data not found")
        return
    
    if not person:
        print("❌ No person data available")
        return
    
    driver = None
    try:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        
        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, 20)
        
        print(f"🌐 Opening Santa Fe College...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        time.sleep(8)
        
        # Quick navigation to form
        print(f"🎯 Navigating to form...")
        
        # Step extract gg from pdf
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > form > div > div > button")))
        button1.click()
        time.sleep(3)
        
        # Step 2 
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div")))
        option1.click()
        time.sleep(2)
        
        # Step 3
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right")))
        next1.click()
        time.sleep(3)
        
        # Step 4
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading")))
        option2.click()
        time.sleep(2)
        
        # Step 5
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right")))
        next2.click()
        time.sleep(5)
        
        print(f"✅ Reached form!")
        
        # Discover birth date options
        print(f"\n🔍 DISCOVERING BIRTH DATE OPTIONS...")
        
        try:
            # Month options
            month_select = driver.find_element(By.ID, "month")
            month_options = month_select.find_elements(By.TAG_NAME, "option")
            
            print(f"\n📅 MONTH OPTIONS:")
            valid_months = []
            for opt in month_options:
                value = opt.get_attribute("value")
                text = opt.text.strip()
                if value and value != "":
                    valid_months.append(value)
                    print(f"  '{value}' = '{text}'")
            
            # Day options
            day_select = driver.find_element(By.ID, "day")
            day_options = day_select.find_elements(By.TAG_NAME, "option")
            
            print(f"\n📅 DAY OPTIONS (sample):")
            valid_days = []
            for opt in day_options[:5]:  # First 5
                value = opt.get_attribute("value")
                text = opt.text.strip()
                if value and value != "":
                    valid_days.append(value)
                    print(f"  '{value}' = '{text}'")
            
            # Year options  
            year_select = driver.find_element(By.ID, "year")
            year_options = year_select.find_elements(By.TAG_NAME, "option")
            
            print(f"\n📅 YEAR OPTIONS (sample):")
            valid_years = []
            for opt in year_options[:5]:  # First 5
                value = opt.get_attribute("value")
                text = opt.text.strip()
                if value and value != "":
                    valid_years.append(value)
                    print(f"  '{value}' = '{text}'")
            
            # Try to set birth date with first valid values
            if valid_months and valid_days and valid_years:
                print(f"\n🎯 ATTEMPTING BIRTH DATE FIX...")
                
                test_month = valid_months[1] if len(valid_months) > 1 else valid_months[0]  # Skip first (usually empty)
                test_day = "15"  # Common day
                test_year = "1995"  # Common year
                
                # Try to find 15 in days
                for day_val in valid_days:
                    if day_val == "15":
                        test_day = day_val
                        break
                
                # Try to find 1995 in years
                for year_val in valid_years:
                    if year_val == "1995":
                        test_year = year_val
                        break
                
                print(f"🎯 Testing: Month={test_month}, Day={test_day}, Year={test_year}")
                
                # Select month
                Select(month_select).select_by_value(test_month)
                time.sleep(1)
                print(f"✅ Month selected: {test_month}")
                
                # Select day
                Select(day_select).select_by_value(test_day)
                time.sleep(1)
                print(f"✅ Day selected: {test_day}")
                
                # Select year
                Select(year_select).select_by_value(test_year)
                time.sleep(1)
                print(f"✅ Year selected: {test_year}")
                
                # Quick fill other required fields
                print(f"\n📝 Quick filling required fields...")
                
                form_fields = [
                    ("fstNameSTR", person['first_name']),
                    ("lstNameSTR", person['last_name']),
                    ("email", "test@example.com"),
                    ("emailC", "test@example.com"),
                    ("ssn", person['ssn'].replace('-', '')),
                    ("ssnC", person['ssn'].replace('-', ''))
                ]
                
                for field_id, value in form_fields:
                    try:
                        field = driver.find_element(By.ID, field_id)
                        field.clear()
                        field.send_keys(value)
                        time.sleep(0.5)
                    except:
                        pass
                
                # Birth country
                try:
                    country_select = driver.find_element(By.CSS_SELECTOR, "select[name='birthctrySTR']")
                    Select(country_select).select_by_value("US")
                    print(f"✅ Birth country: US")
                except:
                    pass
                
                # SSN checkbox
                try:
                    ssn_checkbox = driver.find_element(By.ID, "ssnNoticeCB")
                    if not ssn_checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", ssn_checkbox)
                        print(f"✅ SSN notice checked")
                except:
                    pass
                
                # Wait for validation
                time.sleep(3)
                
                # Check submit button
                print(f"\n🔍 CHECKING SUBMIT BUTTON...")
                
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'].button.float-right")
                    
                    is_enabled = submit_button.is_enabled()
                    button_text = submit_button.text.strip()
                    
                    print(f"Submit Button:")
                    print(f"  Text: '{button_text}'")
                    print(f"  Enabled: {is_enabled}")
                    
                    if is_enabled:
                        print(f"🎉 SUCCESS! Submit button is now ENABLED!")
                        driver.execute_script("arguments[0].style.border='5px solid green';", submit_button)
                        
                        # Save the working birth date values
                        birth_date_fix = {
                            "month": test_month,
                            "day": test_day, 
                            "year": test_year,
                            "status": "WORKING"
                        }
                        
                        with open("birth_date_fix.json", "w") as f:
                            json.dump(birth_date_fix, f, indent=2)
                        
                        print(f"💾 Working birth date saved to birth_date_fix.json")
                        
                    else:
                        print(f"❌ Submit button still disabled")
                        
                except Exception as e:
                    print(f"❌ Submit button check error: {e}")
                
                # Screenshot
                driver.save_screenshot("birth_date_fix_result.png")
                print(f"📸 Screenshot saved: birth_date_fix_result.png")
                
                # Wait for manual inspection
                print(f"\n⏰ Manual inspection time (30s)...")
                time.sleep(30)
                
            else:
                print(f"❌ No valid birth date options found")
                
        except Exception as e:
            print(f"❌ Birth date discovery error: {e}")
        
    except Exception as e:
        print(f"❌ Script error: {e}")
    
    finally:
        if driver:
            driver.quit()
            print(f"✅ Browser closed")

if __name__ == "__main__":
    discover_and_fix_birth_date() 