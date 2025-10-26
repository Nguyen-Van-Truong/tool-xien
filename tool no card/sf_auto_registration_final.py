#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - FINAL AUTO REGISTRATION BOT
Phiên bản hoàn chỉnh với imail.edu.vn integration
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

# Import imail client (sẽ fallback nếu không có)
try:
    from imail_client_v2 import ImailClientV2
    IMAIL_AVAILABLE = True
except:
    IMAIL_AVAILABLE = False
    print("⚠️ imail_client_v2 không có sẵn, sẽ dùng email format")

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
            return data["people"][0] if data["people"] else None
    except:
        return None

def create_imail_email(firstname):
    """Tạo email imail với fallback"""
    try:
        if IMAIL_AVAILABLE:
            imail_client = ImailClientV2()
            # Thử tạo email thật
            email_info = imail_client.create_email_with_selenium(firstname)
            if not email_info:
                # Fallback to simple format
                email_info = imail_client.create_email_simple(firstname)
            return email_info
        else:
            # Simple format fallback
            random_numbers = f"{random.randint(10, 99)}"
            username = f"{firstname.lower()}{random_numbers}"
            email_address = f"{username}@naka.edu.pl"
            
            return {
                "email": email_address,
                "username": username,
                "domain": "naka.edu.pl",
                "created_time": time.time()
            }
    except Exception as e:
        print(f"❌ Lỗi tạo email: {e}")
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
        ".close", ".modal-close", "[aria-label='close']",
        "button:contains('×')", "button:contains('Close')"
    ]
    
    for selector in overlays:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    driver.execute_script("arguments[0].style.display='none'", elem)
        except:
            pass

def wait_and_see(message, seconds):
    """Hiển thị thông báo và đợi"""
    print(f"⏰ {message} - Đợi {seconds}s...")
    time.sleep(seconds)

def save_final_registration_info(person, email_info, registration_data, verification_status="pending"):
    """Lưu thông tin đăng ký hoàn chỉnh"""
    info = {
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "person_info": person,
        "email_info": email_info,
        "registration_data": registration_data,
        "verification_status": verification_status,
        "santa_fe_status": "pending"
    }
    
    with open("sf_final_registrations.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    # File txt dễ đọc
    with open("sf_final_registrations.txt", "w", encoding="utf-8") as f:
        f.write("🎓 SANTA FE COLLEGE - FINAL REGISTRATION INFO\n")
        f.write("=" * 60 + "\n")
        f.write(f"Registration Date: {info['registration_date']}\n")
        f.write("-" * 60 + "\n\n")
        
        f.write("👤 PERSON REGISTERED:\n")
        f.write(f"   Name: {person['full_name']}\n")
        f.write(f"   Original Email: {person['email']}\n")
        f.write(f"   iMail Email: {email_info['email']}\n")
        f.write(f"   SSN: {person['ssn']}\n")
        f.write(f"   Birth Date: {person['birth_date']}\n")
        f.write(f"   Phone: {person['phone']}\n\n")
        
        f.write("📧 EMAIL INFO:\n")
        f.write(f"   Registration Email: {email_info['email']}\n")
        f.write(f"   Domain: {email_info['domain']}\n")
        f.write(f"   Username: {email_info['username']}\n")
        f.write(f"   Verification Status: {verification_status}\n\n")
        
        f.write("🎯 REGISTRATION STATUS:\n")
        f.write(f"   Form Submitted: ✅\n")
        f.write(f"   Email Verification: {verification_status}\n")
        f.write(f"   Santa Fe Status: {info['santa_fe_status']}\n\n")
        
        if verification_status == "manual_required":
            f.write("📝 MANUAL VERIFICATION NEEDED:\n")
            f.write(f"   extract gg from pdf. Truy cập: https://imail.edu.vn\n")
            f.write(f"   2. Tìm email từ Santa Fe College\n")
            f.write(f"   3. Lấy mã verification 6 số\n")
            f.write(f"   4. Nhập vào trang Santa Fe\n\n")

def final_auto_register():
    """Đăng ký hoàn chỉnh cuối cùng"""
    print("🎯 SANTA FE COLLEGE - FINAL AUTO REGISTRATION")
    print("=" * 60)
    print("🚀 Phiên bản FINAL với imail.edu.vn")
    print("📧 Tạo email: firstname + 2 số ngẫu nhiên + @naka.edu.pl")
    print("🔐 Xử lý email verification (auto + manual fallback)")
    print("🎉 Hoàn thành toàn bộ quy trình đăng ký")
    print("-" * 60)
    
    # Load dữ liệu
    person = load_person_data()
    if not person:
        print("❌ Không có dữ liệu!")
        return
    
    print(f"👤 Đăng ký: {person['full_name']}")
    print(f"📧 Email gốc: {person['email']}")
    
    # BƯỚC extract gg from pdf: Tạo email
    print(f"\n📧 BƯỚC extract gg from pdf: Tạo email với imail.edu.vn...")
    email_info = create_imail_email(person['first_name'])
    
    if not email_info:
        print("❌ Không thể tạo email!")
        return
    
    print(f"✅ Email: {email_info['email']}")
    
    driver = None
    
    try:
        # BƯỚC 2: Setup Browser
        print(f"\n🔧 BƯỚC 2: Thiết lập Browser...")
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
        
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 20)
        
        wait_and_see("Browser khởi tạo", 2)
        
        # BƯỚC 3: Truy cập Santa Fe
        print(f"\n🌐 BƯỚC 3: Truy cập Santa Fe College...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        
        time.sleep(5)
        close_overlays(driver)
        driver.save_screenshot("final_reg_step1_homepage.png")
        
        # BƯỚC 4: Navigate flow
        print(f"\n🎯 BƯỚC 4: Navigate qua flow...")
        
        # Click Start
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step1_button"])))
        smart_click(driver, button1)
        time.sleep(3)
        close_overlays(driver)
        driver.save_screenshot("final_reg_step2_after_start.png")
        
        # Click Option extract gg from pdf
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_option1"])))
        smart_click(driver, option1)
        time.sleep(1)
        
        # Click Next
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_next"])))
        smart_click(driver, next1)
        time.sleep(3)
        close_overlays(driver)
        driver.save_screenshot("final_reg_step3_after_option1.png")
        
        # Click Option 2
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_option2"])))
        smart_click(driver, option2)
        time.sleep(1)
        
        # Click Next
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_next"])))
        smart_click(driver, next2)
        time.sleep(5)
        close_overlays(driver)
        driver.save_screenshot("final_reg_step4_registration_form.png")
        
        # BƯỚC 5: Điền form
        print(f"\n📝 BƯỚC 5: Điền registration form...")
        
        form_data = {}
        
        for field_id, person_key in REQUIRED_FIELDS.items():
            try:
                element = driver.find_element(By.ID, field_id)
                
                if field_id == "emailAddrsSTR" or field_id == "cemailAddrsSTR":
                    # Dùng email imail
                    value = email_info['email']
                    element.clear()
                    element.send_keys(value)
                    form_data[field_id] = value
                    print(f"✅ {field_id}: {value}")
                    
                elif field_id == "ssnNoticeCB":
                    if not element.is_selected():
                        smart_click(driver, element)
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
        
        driver.save_screenshot("final_reg_step5_form_filled.png")
        
        # BƯỚC 6: Submit
        print(f"\n🚀 BƯỚC 6: Submit form...")
        
        try:
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
            
            if submit_buttons:
                btn = submit_buttons[0]
                driver.execute_script("arguments[0].style.border='5px solid red'", btn)
                time.sleep(2)
                
                smart_click(driver, btn)
                time.sleep(8)
                
                driver.save_screenshot("final_reg_step6_after_submit.png")
                print(f"✅ Form đã submit!")
                print(f"📄 URL: {driver.current_url}")
                
        except Exception as e:
            print(f"❌ Submit error: {e}")
        
        # BƯỚC 7: Email Verification
        print(f"\n📧 BƯỚC 7: Xử lý Email Verification...")
        
        # Check verification page
        verification_indicators = [
            "verification", "verify", "confirm", "code", 
            "To create your account", "enter the 6-digit", "verification code"
        ]
        
        page_source = driver.page_source.lower()
        is_verification_page = any(indicator in page_source for indicator in verification_indicators)
        
        if is_verification_page:
            print(f"✅ Đã đến trang verification!")
            driver.save_screenshot("final_reg_step7_verification_page.png")
            
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
                    inputs = driver.find_elements(By.CSS_SELECTOR, selector)
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
                # MANUAL VERIFICATION
                print(f"\n🔧 MANUAL EMAIL VERIFICATION:")
                print(f"📧 Email đã tạo: {email_info['email']}")
                print(f"🌐 Truy cập: https://imail.edu.vn")
                print(f"🔍 Tìm email từ Santa Fe College")
                print(f"📝 Lấy mã verification 6 số")
                print(f"-" * 50)
                
                verification_code = None
                
                # Đợi user nhập mã
                try:
                    verification_code = input("🔐 Nhập mã verification (6 số): ").strip()
                    if len(verification_code) == 6 and verification_code.isdigit():
                        print(f"✅ Mã nhập: {verification_code}")
                    else:
                        print(f"❌ Mã không hợp lệ (cần 6 số)")
                        verification_code = None
                except KeyboardInterrupt:
                    print(f"\n❌ User hủy")
                    verification_code = None
                except:
                    verification_code = None
                
                # Nhập mã
                if verification_code:
                    print(f"\n🔐 Nhập mã verification: {verification_code}")
                    
                    verification_input.clear()
                    verification_input.send_keys(verification_code)
                    time.sleep(2)
                    
                    # Click verify
                    verify_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
                    
                    if verify_buttons:
                        verify_btn = verify_buttons[0]
                        smart_click(driver, verify_btn)
                        time.sleep(5)
                        
                        driver.save_screenshot("final_reg_step8_after_verification.png")
                        print(f"✅ Đã submit verification!")
                        
                        # HOÀN THÀNH
                        print(f"\n🎉 VERIFICATION COMPLETED!")
                        print(f"📄 URL: {driver.current_url}")
                        
                        save_final_registration_info(person, email_info, form_data, "success")
                        
                        # Khám phá kết quả
                        explore_final_result(driver)
                        
                        print(f"\n🏆 ĐĂNG KÝ HOÀN THÀNH!")
                        print(f"📧 Email: {email_info['email']}")
                        print(f"👤 Name: {person['full_name']}")
                        print(f"💾 Info: sf_final_registrations.txt")
                        
                    else:
                        print(f"❌ Không tìm thấy verify button!")
                        save_final_registration_info(person, email_info, form_data, "error_no_verify_button")
                else:
                    print(f"❌ Không có mã verification!")
                    save_final_registration_info(person, email_info, form_data, "manual_required")
            else:
                print(f"❌ Không tìm thấy verification input!")
                save_final_registration_info(person, email_info, form_data, "error_no_input")
        else:
            print(f"❌ Không phải trang verification")
            save_final_registration_info(person, email_info, form_data, "error_no_verification_page")
        
        # Giữ browser
        print(f"\n⏰ Giữ browser mở để xem kết quả...")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ Lỗi chung: {e}")
        if driver:
            driver.save_screenshot("final_reg_error.png")
        save_final_registration_info(person, email_info, {}, "error_general")
    
    finally:
        # Cleanup imail driver
        if email_info.get("driver"):
            try:
                email_info["driver"].quit()
                print("✅ Đóng imail browser")
            except:
                pass
        
        if driver:
            print(f"\n🔄 Santa Fe browser vẫn mở để bạn quan sát...")
            # driver.quit()  # Bỏ comment để đóng

def explore_final_result(driver):
    """Khám phá kết quả cuối cùng"""
    try:
        print(f"\n🔍 EXPLORING FINAL RESULT...")
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
        student_id_patterns = [
            r'student id[:\s]+(\w+)',
            r'id[:\s]+(\d+)',
            r'student number[:\s]+(\w+)'
        ]
        
        for pattern in student_id_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                print(f"🆔 Student ID: {matches[0]}")
                break
        
        driver.save_screenshot("final_reg_explore_result.png")
        
    except Exception as e:
        print(f"❌ Error exploring: {e}")

if __name__ == "__main__":
    final_auto_register() 