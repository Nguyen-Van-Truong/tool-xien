#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - FAST AUTO REGISTRATION BOT
Đăng ký tự động NHANH với xử lý email verification
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
import os
from datetime import datetime

# 🎯 FLOW SELECTORS
FLOW_SELECTORS = {
    "step1_button": "#mainContent > div > form > div > div > button",
    "step2_option1": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div",
    "step2_next": "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right",
    "step3_option2": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading",
    "step3_next": "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right"
}

def load_person_data():
    """Load dữ liệu người từ file JSON"""
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            people = json.load(f)
        return people[0] if people else None
    except:
        print("❌ Không thể đọc file dữ liệu!")
        return None

def save_registration_info(person, registration_data):
    """Lưu thông tin đăng ký để dùng sau"""
    info = {
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "person_info": person,
        "registration_data": registration_data,
        "email_info": {
            "email": person['email'],
            "gmail_login_url": "https://mail.google.com",
            "search_keywords": [
                "Santa Fe College",
                "Application",
                "Verification",
                "Confirm",
                person['email']
            ],
            "note": "Kiểm tra Inbox và Spam folder cho email verification"
        }
    }
    
    with open("sf_registered_accounts.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    # Tạo file txt dễ đọc
    with open("sf_registered_accounts.txt", "w", encoding="utf-8") as f:
        f.write("🎓 SANTA FE COLLEGE - REGISTERED ACCOUNT INFO\n")
        f.write("=" * 60 + "\n")
        f.write(f"Registration Date: {info['registration_date']}\n")
        f.write("-" * 60 + "\n\n")
        
        f.write("👤 PERSON REGISTERED:\n")
        f.write(f"   Name: {person['full_name']}\n")
        f.write(f"   Email: {person['email']}\n")
        f.write(f"   SSN: {person['ssn']}\n")
        f.write(f"   Birth Date: {person['birth_date']}\n")
        f.write(f"   Phone: {person['phone']}\n\n")
        
        f.write("📧 EMAIL VERIFICATION INFO:\n")
        f.write(f"   Email Account: {person['email']}\n")
        f.write("   Gmail Login: https://mail.google.com\n")
        f.write("   Search For: 'Santa Fe College' OR 'Application' OR 'Verification'\n")
        f.write("   Check: Inbox AND Spam folder\n")
        f.write("   Usually arrives: Within 5-15 minutes\n\n")
        
        f.write("🔍 HOW TO FIND VERIFICATION EMAIL:\n")
        f.write("   extract gg from pdf. Go to https://mail.google.com\n")
        f.write(f"   2. Login with: {person['email']}\n")
        f.write("   3. Search: 'Santa Fe College verification'\n")
        f.write("   4. Check Spam if not in Inbox\n")
        f.write("   5. Click verification link in email\n\n")
        
        f.write("💡 NEXT STEPS:\n")
        f.write("   - Check email within 15 minutes\n")
        f.write("   - Click verification link\n")
        f.write("   - Complete any additional steps\n")
        f.write("   - Save this file for future reference\n")

def close_overlays(driver):
    """Đóng overlay nhanh"""
    try:
        overlays = [".Fab-zoomContainer"]
        for selector in overlays:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    driver.execute_script("arguments[0].style.display = 'none';", elem)
    except:
        pass

def smart_click(driver, element):
    """Click nhanh bằng JS"""
    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except:
        return False

def fast_wait(message, seconds=1):
    """Chờ ngắn với thông báo"""
    print(f"⚡ {message}")
    if seconds > 0:
        time.sleep(seconds)

def fast_auto_register():
    """Đăng ký tự động NHANH"""
    print("⚡ SANTA FE COLLEGE - FAST AUTO REGISTRATION")
    print("=" * 60)
    print("🚀 Chế độ NHANH - ít thời gian chờ")
    print("📧 Có hỗ trợ email verification")
    print("-" * 60)
    
    # Load dữ liệu
    person = load_person_data()
    if not person:
        print("❌ Không có dữ liệu!")
        return
    
    print(f"👤 Đăng ký: {person['full_name']}")
    print(f"📧 Email: {person['email']}")
    
    driver = None
    
    try:
        # SETUP NHANH
        print(f"\n🔧 Thiết lập ChromeDriver...")
        chrome_service = Service(ChromeDriverManager().install())
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        # Load extensions
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
        wait = WebDriverWait(driver, 20)  # Giảm từ 30 xuống 20
        
        fast_wait("Browser khởi tạo", 1)
        
        # BƯỚC extract gg from pdf: Mở website
        print(f"\n🌐 Truy cập Santa Fe...")
        driver.get("https://ss2.sfcollege.edu/sr/AdmissionApplication/#/")
        
        time.sleep(5)  # Giảm từ 8 xuống 5
        close_overlays(driver)
        fast_wait("Trang đã load", 0)
        
        # BƯỚC 2: Click Start
        print(f"\n🎯 Click 'Start New Application'...")
        button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step1_button"])))
        driver.execute_script("arguments[0].style.border='3px solid red'", button1)
        fast_wait(f"Found: {button1.text}", 1)
        
        smart_click(driver, button1)
        time.sleep(3)  # Giảm từ 5 xuống 3
        fast_wait("✅ Clicked Start", 0)
        
        # BƯỚC 3: Option extract gg from pdf
        print(f"\n🎯 Chọn First Time Student...")
        option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_option1"])))
        driver.execute_script("arguments[0].style.border='3px solid red'", option1)
        fast_wait("Option extract gg from pdf highlighted", 1)
        
        smart_click(driver, option1)
        time.sleep(2)  # Giảm từ 3 xuống 2
        close_overlays(driver)
        
        # Next extract gg from pdf
        next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_next"])))
        driver.execute_script("arguments[0].style.border='3px solid blue'", next1)
        fast_wait("Next extract gg from pdf ready", 1)
        
        smart_click(driver, next1)
        time.sleep(3)  # Giảm từ 5 xuống 3
        fast_wait("✅ Next extract gg from pdf clicked", 0)
        
        # BƯỚC 4: Option 2
        print(f"\n🎯 Chọn Academic Goal...")
        option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_option2"])))
        driver.execute_script("arguments[0].style.border='3px solid red'", option2)
        fast_wait("Option 2 highlighted", 1)
        
        smart_click(driver, option2)
        time.sleep(2)
        close_overlays(driver)
        
        # Next 2
        next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_next"])))
        driver.execute_script("arguments[0].style.border='3px solid blue'", next2)
        fast_wait("Next 2 ready", 1)
        
        smart_click(driver, next2)
        time.sleep(5)  # Giảm từ 8 xuống 5
        close_overlays(driver)
        fast_wait("✅ Đến form đăng ký!", 0)
        
        # BƯỚC 5: Điền form NHANH
        print(f"\n📝 Điền form nhanh...")
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Parse birth date
        birth_parts = person['birth_date'].split('/')
        birth_month_num = int(birth_parts[0])
        birth_day_num = int(birth_parts[1])
        birth_year = birth_parts[2]
        
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        birth_month_name = months[birth_month_num]
        birth_day_str = f"{birth_day_num:02d}"
        
        # Data mapping
        form_data = {
            "fstNameSTR": person['first_name'],
            "lstNameSTR": person['last_name'], 
            "emailAddrsSTR": person['email'],
            "cemailAddrsSTR": person['email'],
            "ssnumSTR": person['ssn'].replace('-', ''),
            "cssnumSTR": person['ssn'].replace('-', ''),
            "month": birth_month_name,
            "day": birth_day_str,
            "year": birth_year,
            "birthctrySTR": "United States Of America"
        }
        
        print(f"📋 Điền {len(form_data)} fields...")
        
        # Fill fields rapidly
        fields_filled = 0
        
        # extract gg from pdf. First Name
        try:
            elem = driver.find_element(By.ID, "fstNameSTR")
            elem.clear()
            elem.send_keys(form_data['fstNameSTR'])
            fields_filled += 1
            fast_wait(f"✅ First Name: {form_data['fstNameSTR']}", 0.5)
        except Exception as e:
            print(f"❌ First Name: {e}")
        
        # 2. Last Name
        try:
            elem = driver.find_element(By.ID, "lstNameSTR")
            elem.clear()
            elem.send_keys(form_data['lstNameSTR'])
            fields_filled += 1
            fast_wait(f"✅ Last Name: {form_data['lstNameSTR']}", 0.5)
        except Exception as e:
            print(f"❌ Last Name: {e}")
        
        # 3. Email
        try:
            elem = driver.find_element(By.ID, "email")
            elem.clear()
            elem.send_keys(form_data['emailAddrsSTR'])
            fields_filled += 1
            fast_wait(f"✅ Email: {form_data['emailAddrsSTR']}", 0.5)
        except Exception as e:
            print(f"❌ Email: {e}")
        
        # 4. Confirm Email
        try:
            elem = driver.find_element(By.ID, "emailC")
            elem.clear()
            elem.send_keys(form_data['cemailAddrsSTR'])
            fields_filled += 1
            fast_wait(f"✅ Confirm Email", 0.5)
        except Exception as e:
            print(f"❌ Confirm Email: {e}")
        
        # 5. SSN
        try:
            elem = driver.find_element(By.ID, "ssn")
            elem.clear()
            elem.send_keys(form_data['ssnumSTR'])
            fields_filled += 1
            fast_wait(f"✅ SSN", 0.5)
        except Exception as e:
            print(f"❌ SSN: {e}")
        
        # 6. Confirm SSN
        try:
            elem = driver.find_element(By.ID, "ssnC")
            elem.clear()
            elem.send_keys(form_data['cssnumSTR'])
            fields_filled += 1
            fast_wait(f"✅ Confirm SSN", 0.5)
        except Exception as e:
            print(f"❌ Confirm SSN: {e}")
        
        # 7. Birth Month
        try:
            select = Select(driver.find_element(By.ID, "month"))
            select.select_by_visible_text(form_data['month'])
            fields_filled += 1
            fast_wait(f"✅ Month: {form_data['month']}", 0.5)
        except Exception as e:
            print(f"❌ Month: {e}")
        
        # 8. Birth Day
        try:
            select = Select(driver.find_element(By.ID, "day"))
            select.select_by_visible_text(form_data['day'])
            fields_filled += 1
            fast_wait(f"✅ Day: {form_data['day']}", 0.5)
        except Exception as e:
            print(f"❌ Day: {e}")
        
        # 9. Birth Year
        try:
            select = Select(driver.find_element(By.ID, "year"))
            select.select_by_visible_text(form_data['year'])
            fields_filled += 1
            fast_wait(f"✅ Year: {form_data['year']}", 0.5)
        except Exception as e:
            print(f"❌ Year: {e}")
        
        # 10. Birth Country
        try:
            selects = driver.find_elements(By.TAG_NAME, "select")
            for select_elem in selects:
                options = select_elem.find_elements(By.TAG_NAME, "option")
                option_texts = [opt.text for opt in options]
                if "United States Of America" in option_texts:
                    select = Select(select_elem)
                    select.select_by_visible_text(form_data['birthctrySTR'])
                    fields_filled += 1
                    fast_wait(f"✅ Country: USA", 0.5)
                    break
        except Exception as e:
            print(f"❌ Country: {e}")
        
        # 11. SSN Checkbox
        try:
            checkbox = driver.find_element(By.ID, "ssnNoticeCB")
            if not checkbox.is_selected():
                smart_click(driver, checkbox)
                fields_filled += 1
                fast_wait(f"✅ SSN Notice checked", 0.5)
        except Exception as e:
            print(f"❌ SSN Checkbox: {e}")
        
        print(f"\n✅ Đã điền {fields_filled}/11 fields")
        
        # Screenshot
        driver.save_screenshot("fast_reg_form_filled.png")
        fast_wait("📸 Form screenshot saved", 1)
        
        # BƯỚC 6: Submit
        print(f"\n🚀 Submit đăng ký...")
        try:
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
            
            if submit_buttons:
                btn = submit_buttons[0]
                driver.execute_script("arguments[0].style.border='5px solid red'", btn)
                fast_wait(f"Submit button: {btn.text}", 2)
                
                smart_click(driver, btn)
                time.sleep(8)  # Chờ submit xử lý
                
                driver.save_screenshot("fast_reg_after_submit.png")
                print(f"✅ Đã submit thành công!")
                print(f"📄 URL: {driver.current_url}")
                
        except Exception as e:
            print(f"❌ Submit error: {e}")
        
        # Lưu thông tin registration
        save_registration_info(person, form_data)
        
        # HƯỚNG DẪN EMAIL
        print(f"\n📧 EMAIL VERIFICATION GUIDE:")
        print(f"=" * 50)
        print(f"🎯 Bây giờ cần check email để verify!")
        print(f"📧 Email: {person['email']}")
        print(f"🔗 Gmail: https://mail.google.com")
        print(f"🔍 Search: 'Santa Fe College' hoặc 'verification'")
        print(f"⏰ Email thường đến trong 5-15 phút")
        print(f"📁 Kiểm tra cả Inbox VÀ Spam folder")
        print(f"💾 Thông tin đã lưu: sf_registered_accounts.txt")
        
        print(f"\n🔍 CÁCH TÌM EMAIL:")
        print(f"extract gg from pdf. Mở https://mail.google.com")
        print(f"2. Login: {person['email']}")
        print(f"3. Search: 'Santa Fe College verification'")
        print(f"4. Check Spam nếu không có trong Inbox")
        print(f"5. Click link verification trong email")
        
        # Giữ browser mở
        print(f"\n⏰ Giữ browser mở để check email...")
        time.sleep(10)
        
        print(f"\n🎉 REGISTRATION COMPLETED!")
        print(f"👤 Name: {person['full_name']}")
        print(f"📧 Email: {person['email']}")
        print(f"📸 Screenshots saved")
        print(f"💾 Account info: sf_registered_accounts.txt")
        
    except Exception as e:
        print(f"💥 ERROR: {e}")
        if driver:
            driver.save_screenshot("fast_reg_error.png")
    
    finally:
        if driver:
            try:
                input(f"\n⏸️ Press Enter to close browser...")
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    fast_auto_register() 