#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - COMPLETE AUTO REGISTRATION BOT
Đăng ký hoàn chỉnh với imail.edu.vn email verification
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
from imail_client import ImailClient
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

# 🔍 VERIFICATION SELECTORS
VERIFICATION_SELECTORS = {
    "verification_code_input": "input[placeholder*='verification'], input[placeholder*='code'], input[id*='verification'], input[id*='code'], input[name*='verification'], input[name*='code']",
    "verify_button": "button:contains('Verify'), button:contains('Submit'), button:contains('Continue'), button:contains('Next')",
    "resend_button": "button:contains('Resend'), a:contains('Resend')"
}

def load_person_data():
    """Load dữ liệu người để đăng ký"""
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["people"][0] if data["people"] else None
    except:
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

def save_registration_info(person, email_info, registration_data):
    """Lưu thông tin đăng ký hoàn chỉnh"""
    info = {
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "person_info": person,
        "email_info": email_info,
        "registration_data": registration_data,
        "verification_status": "pending"
    }
    
    with open("sf_complete_registrations.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    # File txt dễ đọc
    with open("sf_complete_registrations.txt", "w", encoding="utf-8") as f:
        f.write("🎓 SANTA FE COLLEGE - COMPLETE REGISTRATION INFO\n")
        f.write("=" * 60 + "\n")
        f.write(f"Registration Date: {info['registration_date']}\n")
        f.write("-" * 60 + "\n\n")
        
        f.write("👤 PERSON REGISTERED:\n")
        f.write(f"   Name: {person['full_name']}\n")
        f.write(f"   Original Email: {person['email']}\n")
        f.write(f"   Registration Email: {email_info['email']}\n")
        f.write(f"   SSN: {person['ssn']}\n")
        f.write(f"   Birth Date: {person['birth_date']}\n")
        f.write(f"   Phone: {person['phone']}\n\n")
        
        f.write("📧 EMAIL VERIFICATION INFO:\n")
        f.write(f"   Email Used: {email_info['email']}\n")
        f.write(f"   Domain: {email_info['domain']}\n")
        f.write(f"   Username: {email_info['username']}\n")
        f.write("   Status: Verification in progress\n\n")

def complete_auto_register():
    """Đăng ký hoàn chỉnh với email verification"""
    print("🎯 SANTA FE COLLEGE - COMPLETE AUTO REGISTRATION")
    print("=" * 60)
    print("🚀 Đăng ký hoàn chỉnh với imail.edu.vn email")
    print("📧 Format: firstname + 2 số ngẫu nhiên + @naka.edu.pl")
    print("🔐 Xử lý email verification tự động")
    print("-" * 60)
    
    # Load dữ liệu
    person = load_person_data()
    if not person:
        print("❌ Không có dữ liệu!")
        return
    
    print(f"👤 Đăng ký: {person['full_name']}")
    print(f"📧 Email gốc: {person['email']}")
    
    # Tạo email với imail.edu.vn
    print(f"\n📧 BƯỚC extract gg from pdf: Tạo email tạm...")
    imail_client = ImailClient()
    email_info = imail_client.create_email_simple(person['first_name'])
    
    if not email_info:
        print("❌ Không thể tạo email!")
        return
    
    print(f"✅ Email tạm: {email_info['email']}")
    
    driver = None
    
    try:
        # SETUP BROWSER
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
        
        # BƯỚC 3: Mở website và navigate
        print(f"\n🌐 BƯỚC 3: Truy cập Santa Fe...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        
        time.sleep(5)
        close_overlays(driver)
        driver.save_screenshot("complete_reg_step1_homepage.png")
        
        # Navigation qua các bước
        print(f"\n🎯 BƯỚC 4: Navigate qua các options...")
        
        # Click Start button
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step1_button"])))
        smart_click(driver, button1)
        time.sleep(3)
        close_overlays(driver)
        driver.save_screenshot("complete_reg_step2_after_start.png")
        
        # Click Option extract gg from pdf
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_option1"])))
        smart_click(driver, option1)
        time.sleep(1)
        
        # Click Next
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_next"])))
        smart_click(driver, next1)
        time.sleep(3)
        close_overlays(driver)
        driver.save_screenshot("complete_reg_step3_after_option1.png")
        
        # Click Option 2
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_option2"])))
        smart_click(driver, option2)
        time.sleep(1)
        
        # Click Next
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_next"])))
        smart_click(driver, next2)
        time.sleep(5)
        close_overlays(driver)
        driver.save_screenshot("complete_reg_step4_registration_form.png")
        
        # BƯỚC 5: Điền form với email imail
        print(f"\n📝 BƯỚC 5: Điền registration form...")
        
        form_data = {}
        
        for field_id, person_key in REQUIRED_FIELDS.items():
            try:
                element = driver.find_element(By.ID, field_id)
                
                if field_id == "emailAddrsSTR" or field_id == "cemailAddrsSTR":
                    # Dùng email imail thay vì email gốc
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
        
        driver.save_screenshot("complete_reg_step5_form_filled.png")
        
        # BƯỚC 6: Submit form
        print(f"\n🚀 BƯỚC 6: Submit registration...")
        
        try:
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
            
            if submit_buttons:
                btn = submit_buttons[0]
                driver.execute_script("arguments[0].style.border='5px solid red'", btn)
                time.sleep(2)
                
                smart_click(driver, btn)
                time.sleep(8)
                
                driver.save_screenshot("complete_reg_step6_after_submit.png")
                print(f"✅ Form đã submit!")
                print(f"📄 URL: {driver.current_url}")
                
        except Exception as e:
            print(f"❌ Submit error: {e}")
        
        # BƯỚC 7: Xử lý Email Verification
        print(f"\n📧 BƯỚC 7: Xử lý Email Verification...")
        
        # Kiểm tra xem có trang verification không
        verification_indicators = [
            "verification", "verify", "confirm", "code", 
            "To create your account", "enter the 6-digit", "verification code"
        ]
        
        page_source = driver.page_source.lower()
        is_verification_page = any(indicator in page_source for indicator in verification_indicators)
        
        if is_verification_page:
            print(f"✅ Đã đến trang verification!")
            driver.save_screenshot("complete_reg_step7_verification_page.png")
            
            # Tìm input verification code
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
                # Bắt đầu check email
                print(f"\n📧 Checking email cho verification code...")
                
                # Tạo selenium driver thứ 2 để check email
                email_driver = None
                try:
                    from selenium.webdriver.chrome.options import Options
                    email_opts = Options()
                    # email_opts.add_argument('--headless')  # Có thể bỏ comment để chạy ngầm
                    email_driver = webdriver.Chrome(options=email_opts)
                    
                    print(f"🌐 Truy cập imail.edu.vn để check email...")
                    email_driver.get("https://imail.edu.vn")
                    time.sleep(3)
                    
                    # Check email và nhập mã
                    max_wait_time = 300  # 5 phút
                    start_time = time.time()
                    verification_code = None
                    
                    while (time.time() - start_time) < max_wait_time and not verification_code:
                        try:
                            print(f"⏳ Tìm kiếm email verification... ({int(time.time() - start_time)}s)")
                            
                            # Refresh trang email
                            email_driver.refresh()
                            time.sleep(5)
                            
                            # Tìm trong page source
                            page_content = email_driver.page_source.lower()
                            
                            # Tìm keywords Santa Fe
                            if any(keyword in page_content for keyword in ["santa fe", "college", "verification", "sfcollege"]):
                                print(f"✅ Tìm thấy email từ Santa Fe College!")
                                
                                # Tìm mã 6 số
                                code_matches = re.findall(r'\b\d{6}\b', email_driver.page_source)
                                if code_matches:
                                    # Lấy mã đầu tiên tìm thấy
                                    verification_code = code_matches[0]
                                    print(f"✅ Mã verification: {verification_code}")
                                    break
                            
                            time.sleep(10)  # Check mỗi 10 giây
                            
                        except Exception as e:
                            print(f"⚠️ Lỗi check email: {e}")
                            time.sleep(5)
                    
                    # Đóng email driver
                    if email_driver:
                        email_driver.quit()
                    
                    # Nhập mã verification
                    if verification_code:
                        print(f"\n🔐 Nhập mã verification: {verification_code}")
                        
                        verification_input.clear()
                        verification_input.send_keys(verification_code)
                        time.sleep(2)
                        
                        # Tìm và click verify button
                        verify_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue') or contains(text(), 'Next')]")
                        
                        if verify_buttons:
                            verify_btn = verify_buttons[0]
                            smart_click(driver, verify_btn)
                            time.sleep(5)
                            
                            driver.save_screenshot("complete_reg_step8_after_verification.png")
                            print(f"✅ Đã nhập mã verification!")
                            
                            # BƯỚC 8: Tiếp tục sau verification
                            print(f"\n🎉 BƯỚC 8: Kiểm tra kết quả...")
                            print(f"📄 URL hiện tại: {driver.current_url}")
                            
                            # Lưu thông tin hoàn chỉnh
                            save_registration_info(person, email_info, form_data)
                            
                            # Khám phá tiếp
                            print(f"\n🔍 KHÁM PHÁ TIẾP...")
                            explore_next_steps(driver)
                            
                        else:
                            print(f"❌ Không tìm thấy verify button!")
                    else:
                        print(f"❌ Không nhận được mã verification!")
                        
                except Exception as e:
                    print(f"❌ Lỗi email verification: {e}")
                    if email_driver:
                        email_driver.quit()
            else:
                print(f"❌ Không tìm thấy verification input!")
        else:
            print(f"❌ Không phải trang verification")
        
        # Giữ browser mở để xem kết quả
        print(f"\n⏰ Giữ browser mở để quan sát...")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ Lỗi chung: {e}")
        if driver:
            driver.save_screenshot("complete_reg_error.png")
    
    finally:
        if driver:
            print(f"\n🔄 Browser sẽ mở để bạn xem kết quả...")
            # driver.quit()  # Bỏ comment để đóng browser

def explore_next_steps(driver):
    """Khám phá các bước tiếp theo sau verification"""
    try:
        print(f"\n🔍 EXPLORING NEXT STEPS...")
        current_url = driver.current_url
        page_title = driver.title
        
        print(f"📄 Current URL: {current_url}")
        print(f"📋 Page Title: {page_title}")
        
        # Tìm các nút có thể click
        clickable_elements = driver.find_elements(By.XPATH, "//button | //a[@href] | //input[@type='submit']")
        
        print(f"\n🎯 Clickable Elements Found:")
        for i, elem in enumerate(clickable_elements[:10]):  # Chỉ hiển thị 10 đầu
            try:
                text = elem.get_attribute("innerHTML")[:100] if elem.get_attribute("innerHTML") else elem.text[:100]
                print(f"   {i+1}. {text}")
            except:
                pass
        
        # Tìm form hoặc input fields
        forms = driver.find_elements(By.TAG_NAME, "form")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        
        print(f"\n📝 Forms: {len(forms)} | Inputs: {len(inputs)}")
        
        # Check xem có thông báo success không
        success_indicators = [
            "success", "complete", "congratulations", "welcome",
            "application submitted", "registration complete",
            "thank you", "next steps"
        ]
        
        page_source = driver.page_source.lower()
        found_success = [indicator for indicator in success_indicators if indicator in page_source]
        
        if found_success:
            print(f"✅ Success indicators found: {found_success}")
        
        # Screenshot để xem
        driver.save_screenshot("complete_reg_explore_next.png")
        
    except Exception as e:
        print(f"❌ Error exploring: {e}")

if __name__ == "__main__":
    complete_auto_register() 