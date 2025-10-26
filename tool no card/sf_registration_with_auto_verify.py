#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - AUTO REGISTRATION WITH AUTO VERIFY
Phiên bản cải tiến với auto check email và nhập mã verification
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
from datetime import datetime
import re

# 🎯 FLOW SELECTORS
FLOW_SELECTORS = {
    "step1_button": "#mainContent > div > form > div > div > button",
    "step2_option1": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div",
    "step2_next": "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right",
    "step3_option2": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading",
    "step3_next": "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right"
}

# 📋 REQUIRED FIELDS
REQUIRED_FIELDS = {
    "fstNameSTR": "first_name",
    "lstNameSTR": "last_name",
    "emailAddrsSTR": "email",
    "cemailAddrsSTR": "email",
    "ssnumSTR": "ssn",
    "cssnumSTR": "ssn",
    "ssnNoticeCB": "checkbox",
    "month": "birth_month",
    "day": "birth_day",
    "year": "birth_year",
    "birthctrySTR": "birth_country"
}

def load_person_data():
    """Load dữ liệu người để đăng ký"""
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # File format là array của người
            return data[0] if data else None
    except:
        return None

def create_imail_email_with_auto_check(firstname):
    """Tạo email imail và return driver để auto check"""
    try:
        # Setup browser cho imail
        opts = webdriver.ChromeOptions()
        opts.add_argument('--start-maximized')
        
        email_driver = webdriver.Chrome(options=opts)
        
        print(f"🌐 Tạo email imail.edu.vn...")
        email_driver.get("https://imail.edu.vn")
        time.sleep(3)
        
        # Tạo username
        random_numbers = f"{random.randint(10, 99)}"
        username = f"{firstname.lower()}{random_numbers}"
        
        print(f"📝 Username: {username}")
        
        # Nhập username
        try:
            username_input = email_driver.find_element(By.ID, "user")
            username_input.clear()
            username_input.send_keys(username)
            print(f"✅ Đã nhập username: {username}")
            
            time.sleep(2)
            
            # Click tạo email (tìm button submit)
            submit_buttons = email_driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
            
            for btn in submit_buttons:
                btn_class = btn.get_attribute("class") or ""
                if "bg-teal-500" in btn_class:
                    btn.click()
                    print(f"✅ Đã click tạo email!")
                    break
            
            time.sleep(3)
            
            # Check email đã tạo
            expected_email = f"{username}@naka.edu.pl"
            
            email_info = {
                "email": expected_email,
                "username": username,
                "domain": "naka.edu.pl",
                "created_time": time.time(),
                "driver": email_driver  # Giữ driver để check email
            }
            
            print(f"✅ Email created: {expected_email}")
            return email_info
            
        except Exception as e:
            print(f"❌ Lỗi tạo email: {e}")
            email_driver.quit()
            return None
            
    except Exception as e:
        print(f"❌ Lỗi setup email driver: {e}")
        return None

def check_email_for_verification_code(email_driver, max_wait=180):
    """Check email để tìm mã verification trong 3 phút"""
    start_time = time.time()
    print(f"📧 Bắt đầu check email để tìm verification code...")
    
    while (time.time() - start_time) < max_wait:
        try:
            # Refresh trang email
            email_driver.refresh()
            time.sleep(5)
            
            # Tìm trong page source
            page_source = email_driver.page_source.lower()
            
            # Tìm keywords Santa Fe
            santa_fe_keywords = ["santa fe", "college", "verification", "sfcollege", "application"]
            
            if any(keyword in page_source for keyword in santa_fe_keywords):
                print(f"✅ Tìm thấy email từ Santa Fe College!")
                
                # Tìm mã 6 số
                code_matches = re.findall(r'\b\d{6}\b', email_driver.page_source)
                
                if code_matches:
                    verification_code = code_matches[0]
                    print(f"✅ Tìm thấy mã verification: {verification_code}")
                    return verification_code
                else:
                    print(f"⚠️ Tìm thấy email nhưng chưa có mã 6 số")
            
            elapsed = int(time.time() - start_time)
            print(f"⏳ Chờ email... ({elapsed}s / {max_wait}s)")
            time.sleep(10)  # Check mỗi 10 giây
            
        except Exception as e:
            print(f"⚠️ Lỗi check email: {e}")
            time.sleep(5)
    
    print(f"⏰ Timeout - không tìm thấy mã verification trong {max_wait}s")
    return None

def smart_click(driver, element):
    """Click thông minh với nhiều cách"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        
        try:
            element.click()
        except:
            try:
                ActionChains(driver).move_to_element(element).click().perform()
            except:
                driver.execute_script("arguments[0].click();", element)
        
        return True
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

def close_overlays(driver):
    """Đóng các overlay/popup có thể che form"""
    overlays = [
        "div.modal", "div.popup", "div.overlay", 
        ".close", ".modal-close", "[aria-label='close']"
    ]
    
    for selector in overlays:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    driver.execute_script("arguments[0].style.display='none'", elem)
        except:
            pass

def auto_registration_with_verify():
    """Đăng ký hoàn chỉnh với auto verify"""
    print("🎯 SANTA FE COLLEGE - AUTO REGISTRATION WITH AUTO VERIFY")
    print("=" * 60)
    print("🚀 Test quy trình hoàn chỉnh với auto check email")
    print("📧 Tạo email imail → Đăng ký Santa Fe → Auto verify")
    print("-" * 60)
    
    # Load dữ liệu
    person = load_person_data()
    if not person:
        print("❌ Không có dữ liệu!")
        return
    
    print(f"👤 Đăng ký: {person['full_name']}")
    print(f"📧 Email gốc: {person['email']}")
    
    # BƯỚC extract gg from pdf: Tạo email imail với driver
    print(f"\n📧 BƯỚC extract gg from pdf: Tạo email imail.edu.vn...")
    email_info = create_imail_email_with_auto_check(person['first_name'])
    
    if not email_info:
        print("❌ Không thể tạo email!")
        return
    
    print(f"✅ Email: {email_info['email']}")
    email_driver = email_info['driver']
    
    santa_fe_driver = None
    
    try:
        # BƯỚC 2: Setup Santa Fe Browser
        print(f"\n🔧 BƯỚC 2: Thiết lập Santa Fe Browser...")
        chrome_service = Service(ChromeDriverManager().install())
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            opts.add_extension("driver/captchasolver.crx")
            print("✅ Captcha solver loaded")
        except:
            pass
            
        try:
            opts.add_extension("driver/extract gg from pdf.crx")
            print("✅ Extension loaded")
        except:
            pass
        
        santa_fe_driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(santa_fe_driver, 20)
        
        time.sleep(2)
        
        # BƯỚC 3: Truy cập Santa Fe
        print(f"\n🌐 BƯỚC 3: Truy cập Santa Fe College...")
        santa_fe_driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        
        time.sleep(5)
        close_overlays(santa_fe_driver)
        santa_fe_driver.save_screenshot("auto_verify_step1_homepage.png")
        
        # BƯỚC 4: Navigate flow
        print(f"\n🎯 BƯỚC 4: Navigate qua flow...")
        
        # Click Start
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step1_button"])))
        smart_click(santa_fe_driver, button1)
        time.sleep(3)
        close_overlays(santa_fe_driver)
        santa_fe_driver.save_screenshot("auto_verify_step2_after_start.png")
        
        # Click Option extract gg from pdf
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_option1"])))
        smart_click(santa_fe_driver, option1)
        time.sleep(1)
        
        # Click Next
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_next"])))
        smart_click(santa_fe_driver, next1)
        time.sleep(3)
        close_overlays(santa_fe_driver)
        santa_fe_driver.save_screenshot("auto_verify_step3_after_option1.png")
        
        # Click Option 2
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_option2"])))
        smart_click(santa_fe_driver, option2)
        time.sleep(1)
        
        # Click Next
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_next"])))
        smart_click(santa_fe_driver, next2)
        time.sleep(5)
        close_overlays(santa_fe_driver)
        santa_fe_driver.save_screenshot("auto_verify_step4_registration_form.png")
        
        # BƯỚC 5: Điền form
        print(f"\n📝 BƯỚC 5: Điền registration form...")
        
        form_data = {}
        
        for field_id, person_key in REQUIRED_FIELDS.items():
            try:
                element = santa_fe_driver.find_element(By.ID, field_id)
                
                if field_id == "emailAddrsSTR" or field_id == "cemailAddrsSTR":
                    # Dùng email imail
                    value = email_info['email']
                    element.clear()
                    element.send_keys(value)
                    form_data[field_id] = value
                    print(f"✅ {field_id}: {value}")
                    
                elif field_id == "ssnNoticeCB":
                    if not element.is_selected():
                        smart_click(santa_fe_driver, element)
                        form_data[field_id] = True
                        print(f"✅ {field_id}: Checked")
                        
                elif field_id in ["month", "day", "year", "birthctrySTR"]:
                    select = Select(element)
                    
                    if field_id == "month":
                        month_num = person['birth_date'].split('/')[0]
                        select.select_by_value(month_num)
                        form_data[field_id] = month_num
                        
                    elif field_id == "day":
                        day_num = person['birth_date'].split('/')[1]
                        select.select_by_value(day_num)
                        form_data[field_id] = day_num
                        
                    elif field_id == "year":
                        year_num = person['birth_date'].split('/')[2]
                        select.select_by_value(year_num)
                        form_data[field_id] = year_num
                        
                    elif field_id == "birthctrySTR":
                        select.select_by_visible_text("United States")
                        form_data[field_id] = "United States"
                        
                    print(f"✅ {field_id}: {form_data[field_id]}")
                    
                else:
                    value = person.get(person_key, "")
                    element.clear()
                    element.send_keys(value)
                    form_data[field_id] = value
                    print(f"✅ {field_id}: {value}")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"⚠️ Lỗi {field_id}: {e}")
        
        santa_fe_driver.save_screenshot("auto_verify_step5_form_filled.png")
        
        # BƯỚC 6: Submit
        print(f"\n🚀 BƯỚC 6: Submit form...")
        
        try:
            submit_buttons = santa_fe_driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
            
            if submit_buttons:
                btn = submit_buttons[0]
                santa_fe_driver.execute_script("arguments[0].style.border='5px solid red'", btn)
                time.sleep(2)
                
                smart_click(santa_fe_driver, btn)
                time.sleep(8)
                
                santa_fe_driver.save_screenshot("auto_verify_step6_after_submit.png")
                print(f"✅ Form đã submit!")
                print(f"📄 URL: {santa_fe_driver.current_url}")
                
        except Exception as e:
            print(f"❌ Submit error: {e}")
        
        # BƯỚC 7: Email Verification AUTO
        print(f"\n📧 BƯỚC 7: AUTO Email Verification...")
        
        # Check verification page
        verification_indicators = [
            "verification", "verify", "confirm", "code", 
            "To create your account", "enter the 6-digit", "verification code"
        ]
        
        page_source = santa_fe_driver.page_source.lower()
        is_verification_page = any(indicator in page_source for indicator in verification_indicators)
        
        if is_verification_page:
            print(f"✅ Đã đến trang verification!")
            santa_fe_driver.save_screenshot("auto_verify_step7_verification_page.png")
            
            # Tìm verification input
            verification_input = None
            selectors_to_try = [
                "input[placeholder*='verification']",
                "input[placeholder*='code']", 
                "input[id*='verification']",
                "input[id*='code']",
                "input[name*='verification']",
                "input[name*='code']",
                "input[type='text']",
                "input[type='number']"
            ]
            
            for selector in selectors_to_try:
                try:
                    inputs = santa_fe_driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        if inp.is_displayed():
                            verification_input = inp
                            print(f"✅ Tìm thấy verification input: {selector}")
                            break
                    if verification_input:
                        break
                except:
                    continue
            
            if verification_input:
                print(f"\n📧 AUTO CHECK EMAIL cho verification code...")
                
                # Auto check email trong background
                verification_code = check_email_for_verification_code(email_driver, max_wait=180)
                
                if verification_code:
                    print(f"\n🔐 AUTO nhập mã verification: {verification_code}")
                    
                    verification_input.clear()
                    verification_input.send_keys(verification_code)
                    time.sleep(2)
                    
                    # Click verify
                    verify_buttons = santa_fe_driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
                    
                    if verify_buttons:
                        verify_btn = verify_buttons[0]
                        smart_click(santa_fe_driver, verify_btn)
                        time.sleep(5)
                        
                        santa_fe_driver.save_screenshot("auto_verify_step8_after_verification.png")
                        print(f"✅ AUTO VERIFICATION COMPLETED!")
                        print(f"📄 URL: {santa_fe_driver.current_url}")
                        
                        # Khám phá kết quả
                        explore_result(santa_fe_driver)
                        
                        print(f"\n🏆 AUTO ĐĂNG KÝ HOÀN THÀNH!")
                        print(f"📧 Email: {email_info['email']}")
                        print(f"🔐 Code: {verification_code}")
                        print(f"👤 Name: {person['full_name']}")
                        
                        # Save result
                        save_auto_result(person, email_info, verification_code, "success")
                        
                    else:
                        print(f"❌ Không tìm thấy verify button!")
                        save_auto_result(person, email_info, verification_code, "no_verify_button")
                else:
                    # Fallback manual
                    print(f"\n🔧 FALLBACK MANUAL verification:")
                    print(f"📧 Email: {email_info['email']}")
                    print(f"🌐 Check: https://imail.edu.vn")
                    
                    try:
                        manual_code = input("🔐 Nhập mã verification (6 số): ").strip()
                        if len(manual_code) == 6 and manual_code.isdigit():
                            verification_input.clear()
                            verification_input.send_keys(manual_code)
                            
                            verify_buttons = santa_fe_driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
                            
                            if verify_buttons:
                                verify_btn = verify_buttons[0]
                                smart_click(santa_fe_driver, verify_btn)
                                time.sleep(5)
                                
                                print(f"✅ MANUAL verification completed!")
                                save_auto_result(person, email_info, manual_code, "manual_success")
                            else:
                                print(f"❌ No verify button!")
                                save_auto_result(person, email_info, manual_code, "manual_no_button")
                        else:
                            print(f"❌ Invalid code!")
                            save_auto_result(person, email_info, "", "invalid_code")
                    except:
                        print(f"❌ Manual input failed!")
                        save_auto_result(person, email_info, "", "manual_failed")
            else:
                print(f"❌ Không tìm thấy verification input!")
                save_auto_result(person, email_info, "", "no_input")
        else:
            print(f"❌ Không phải trang verification")
            save_auto_result(person, email_info, "", "no_verification_page")
        
        # Giữ browser
        print(f"\n⏰ Giữ browser mở để xem kết quả...")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ Lỗi chung: {e}")
        if santa_fe_driver:
            santa_fe_driver.save_screenshot("auto_verify_error.png")
        save_auto_result(person, email_info, "", "error_general")
    
    finally:
        # Cleanup
        if email_driver:
            try:
                email_driver.quit()
                print("✅ Đóng email browser")
            except:
                pass
        
        if santa_fe_driver:
            print(f"\n🔄 Santa Fe browser vẫn mở...")
            # santa_fe_driver.quit()

def explore_result(driver):
    """Khám phá kết quả"""
    try:
        print(f"\n🔍 EXPLORING RESULT...")
        current_url = driver.current_url
        page_title = driver.title
        
        print(f"📄 URL: {current_url}")
        print(f"📋 Title: {page_title}")
        
        # Success indicators
        success_indicators = [
            "success", "complete", "congratulations", "welcome",
            "application submitted", "registration complete",
            "thank you", "next steps", "student id", "account created"
        ]
        
        page_source = driver.page_source.lower()
        found_success = [indicator for indicator in success_indicators if indicator in page_source]
        
        if found_success:
            print(f"✅ Success indicators: {found_success}")
        
        # Tìm student ID
        student_id_matches = re.findall(r'student id[:\s]+(\w+)', page_source, re.IGNORECASE)
        if student_id_matches:
            print(f"🆔 Student ID: {student_id_matches[0]}")
        
        driver.save_screenshot("auto_verify_final_result.png")
        
    except Exception as e:
        print(f"❌ Error exploring: {e}")

def save_auto_result(person, email_info, verification_code, status):
    """Save auto test result"""
    result = {
        "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "person": person,
        "email_info": email_info,
        "verification_code": verification_code,
        "status": status
    }
    
    with open("auto_verify_test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    with open("auto_verify_test_result.txt", "w", encoding="utf-8") as f:
        f.write("🎯 AUTO VERIFICATION TEST RESULT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {result['test_date']}\n")
        f.write(f"Status: {status}\n")
        f.write(f"Person: {person['full_name']}\n")
        f.write(f"Email: {email_info['email']}\n")
        f.write(f"Verification Code: {verification_code}\n")

if __name__ == "__main__":
    auto_registration_with_verify() 