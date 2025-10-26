#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - AUTO REGISTRATION BOT
Đăng ký tự động từ đầu đến cuối với chỉ thông tin bắt buộc
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

# 🎯 FLOW SELECTORS
FLOW_SELECTORS = {
    "step1_button": "#mainContent > div > form > div > div > button",
    "step2_option1": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div",
    "step2_next": "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right",
    "step3_option2": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading",
    "step3_next": "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right"
}

# 📋 REQUIRED FIELDS (chỉ những trường bắt buộc)
REQUIRED_FIELDS = {
    "fstNameSTR": "first_name",      # First Name
    "lstNameSTR": "last_name",       # Last Name  
    "emailAddrsSTR": "email",        # Email
    "cemailAddrsSTR": "email",       # Confirm Email (same)
    "ssnumSTR": "ssn",              # SSN
    "cssnumSTR": "ssn",             # Confirm SSN (same)
    "ssnNoticeCB": "checkbox",       # SSN Notice Checkbox
    "month": "birth_month",          # Birth Month
    "day": "birth_day",             # Birth Day
    "year": "birth_year",           # Birth Year
    "birthctrySTR": "birth_country" # Birth Country
}

def load_person_data():
    """Load dữ liệu người từ file JSON"""
    try:
        with open("sf_registration_data.json", "r", encoding="utf-8") as f:
            people = json.load(f)
        return people[0] if people else None  # Lấy người đầu tiên
    except:
        print("❌ Không thể đọc file dữ liệu!")
        return None

def close_overlays(driver):
    """Đóng tất cả overlay"""
    try:
        overlays = [".Fab-zoomContainer", ".overlay", ".modal", ".popup", ".dialog"]
        for overlay_selector in overlays:
            try:
                overlays_found = driver.find_elements(By.CSS_SELECTOR, overlay_selector)
                for overlay in overlays_found:
                    if overlay.is_displayed():
                        driver.execute_script("arguments[0].style.display = 'none';", overlay)
            except:
                continue
    except:
        pass

def smart_click(driver, element, method="js"):
    """Click thông minh"""
    try:
        if method == "js":
            driver.execute_script("arguments[0].click();", element)
            return True
        elif method == "force":
            driver.execute_script("""
                arguments[0].dispatchEvent(new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                }));
            """, element)
            return True
        else:
            element.click()
            return True
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

def wait_and_see(message, seconds=3):
    """Dừng và hiển thị thông báo để user xem"""
    print(f"\n⏰ {message}")
    for i in range(seconds, 0, -1):
        print(f"   ⏳ Đợi {i} giây để xem...")
        time.sleep(1)

def auto_register():
    """Đăng ký tự động từ đầu đến cuối"""
    print("🎯 SANTA FE COLLEGE - AUTO REGISTRATION")
    print("=" * 60)
    print("🚀 Đăng ký tự động từ đầu đến cuối")
    print("📋 Chỉ điền những thông tin BẮT BUỘC")
    print("-" * 60)
    
    # Load dữ liệu
    person = load_person_data()
    if not person:
        print("❌ Không có dữ liệu người để đăng ký!")
        return
    
    print(f"👤 Đăng ký cho: {person['full_name']}")
    print(f"📧 Email: {person['email']}")
    print(f"🆔 SSN: {person['ssn']}")
    print(f"🎂 Sinh ngày: {person['birth_date']}")
    
    driver = None
    
    try:
        # SETUP
        print(f"\n🔧 BƯỚC extract gg from pdf: Thiết lập ChromeDriver...")
        chrome_service = Service(ChromeDriverManager().install())
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            opts.add_extension("driver/captchasolver.crx")
            print("✅ Loaded captcha solver")
        except:
            print("⚠️ No captcha solver")
            
        try:
            opts.add_extension("driver/extract gg from pdf.crx")
            print("✅ Loaded extension extract gg from pdf")
        except:
            print("⚠️ No extension extract gg from pdf")
        
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 30)
        print("✅ Browser đã khởi tạo")
        
        wait_and_see("Browser đã mở, bạn có thể thấy cửa sổ Chrome", 3)
        
        # BƯỚC 2: Mở website
        print(f"\n🌐 BƯỚC 2: Truy cập Santa Fe College...")
        url = "https://ss2.sfcollege.edu/sr/AdmissionApplication/#/"
        driver.get(url)
        print(f"🔗 URL: {url}")
        
        time.sleep(8)
        close_overlays(driver)
        driver.save_screenshot("auto_reg_step1_homepage.png")
        print("📸 Chụp ảnh: auto_reg_step1_homepage.png")
        
        wait_and_see("Đã load trang chính Santa Fe College", 4)
        
        # BƯỚC 3: Click "Start New Application"
        print(f"\n🎯 BƯỚC 3: Click 'Start New Application'...")
        try:
            button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step1_button"])))
            print(f"✅ Tìm thấy button: '{button1.text}'")
            
            # Highlight button
            driver.execute_script("arguments[0].style.border='5px solid red'", button1)
            driver.execute_script("arguments[0].style.backgroundColor='yellow'", button1)
            
            wait_and_see("Button 'Start New Application' đã được highlight màu đỏ", 3)
            
            if smart_click(driver, button1, "js"):
                print("✅ Đã click 'Start New Application'")
            else:
                print("❌ Không thể click button")
                return
            
            time.sleep(5)
            driver.save_screenshot("auto_reg_step2_after_start.png")
            print("📸 Chụp ảnh: auto_reg_step2_after_start.png")
            
            wait_and_see("Đã chuyển đến trang chọn loại học sinh", 3)
            
        except Exception as e:
            print(f"❌ Lỗi button Start: {e}")
            return
        
        # BƯỚC 4: Chọn Option extract gg from pdf (First Time Student)
        print(f"\n🎯 BƯỚC 4: Chọn Option extract gg from pdf (First Time Student)...")
        try:
            option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_option1"])))
            print("✅ Tìm thấy Option extract gg from pdf")
            
            # Highlight option
            driver.execute_script("arguments[0].style.border='5px solid red'", option1)
            driver.execute_script("arguments[0].style.backgroundColor='yellow'", option1)
            
            wait_and_see("Option extract gg from pdf đã được highlight - đây là First Time Student", 3)
            
            if smart_click(driver, option1, "js"):
                print("✅ Đã chọn Option extract gg from pdf")
            else:
                print("❌ Không thể chọn Option extract gg from pdf")
                return
            
            time.sleep(3)
            close_overlays(driver)
            
            # Click Next extract gg from pdf
            next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_next"])))
            print(f"✅ Tìm thấy Next button: '{next1.text}'")
            
            driver.execute_script("arguments[0].style.border='5px solid blue'", next1)
            wait_and_see("Next button màu xanh - sẽ click để chuyển bước", 2)
            
            if smart_click(driver, next1, "js"):
                print("✅ Đã click Next extract gg from pdf")
            else:
                print("❌ Không thể click Next extract gg from pdf")
                return
            
            time.sleep(5)
            driver.save_screenshot("auto_reg_step3_after_option1.png")
            print("📸 Chụp ảnh: auto_reg_step3_after_option1.png")
            
            wait_and_see("Đã chuyển đến trang chọn mục tiêu học tập", 3)
            
        except Exception as e:
            print(f"❌ Lỗi Option extract gg from pdf: {e}")
            return
        
        # BƯỚC 5: Chọn Option 2 (Academic Goal)
        print(f"\n🎯 BƯỚC 5: Chọn Option 2 (Academic Goal)...")
        try:
            option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_option2"])))
            print("✅ Tìm thấy Option 2")
            
            # Highlight option
            driver.execute_script("arguments[0].style.border='5px solid red'", option2)
            driver.execute_script("arguments[0].style.backgroundColor='yellow'", option2)
            
            wait_and_see("Option 2 đã được highlight - đây là mục tiêu học tập", 3)
            
            if smart_click(driver, option2, "js"):
                print("✅ Đã chọn Option 2")
            else:
                print("❌ Không thể chọn Option 2")
                return
            
            time.sleep(3)
            close_overlays(driver)
            
            # Click Next 2
            next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_next"])))
            print(f"✅ Tìm thấy Next button 2: '{next2.text}'")
            
            driver.execute_script("arguments[0].style.border='5px solid blue'", next2)
            wait_and_see("Next button 2 màu xanh - sẽ click để đến form đăng ký", 2)
            
            if smart_click(driver, next2, "js"):
                print("✅ Đã click Next 2")
            else:
                print("❌ Không thể click Next 2")
                return
            
            time.sleep(8)
            close_overlays(driver)
            driver.save_screenshot("auto_reg_step4_registration_form.png")
            print("📸 Chụp ảnh: auto_reg_step4_registration_form.png")
            
            wait_and_see("🎉 ĐÃ ĐẾN FORM ĐĂNG KÝ! Bây giờ sẽ điền thông tin", 4)
            
        except Exception as e:
            print(f"❌ Lỗi Option 2: {e}")
            return
        
        # BƯỚC 6: Điền form đăng ký
        print(f"\n📝 BƯỚC 6: Điền thông tin đăng ký...")
        print(f"📄 URL hiện tại: {driver.current_url}")
        
        # Scroll to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Parse birth date
        birth_parts = person['birth_date'].split('/')  # MM/DD/YYYY
        birth_month_num = int(birth_parts[0])
        birth_day_num = int(birth_parts[1])
        birth_year = birth_parts[2]
        
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        birth_month_name = months[birth_month_num]
        birth_day_str = f"{birth_day_num:02d}"
        
        # Mapping dữ liệu
        form_data = {
            "fstNameSTR": person['first_name'],
            "lstNameSTR": person['last_name'],
            "emailAddrsSTR": person['email'],
            "cemailAddrsSTR": person['email'],  # Confirm email same
            "ssnumSTR": person['ssn'].replace('-', ''),  # Remove dashes
            "cssnumSTR": person['ssn'].replace('-', ''),  # Confirm SSN same
            "month": birth_month_name,
            "day": birth_day_str,
            "year": birth_year,
            "birthctrySTR": "United States Of America"
        }
        
        print(f"\n📋 Dữ liệu sẽ điền:")
        for field, value in form_data.items():
            print(f"   {field}: {value}")
        
        wait_and_see("Bây giờ sẽ điền từng trường một cách từ từ", 3)
        
        # Điền từng trường
        field_count = 0
        
        # extract gg from pdf. First Name
        field_count += 1
        print(f"\n📝 {field_count}. Điền First Name: {form_data['fstNameSTR']}")
        try:
            first_name_field = wait.until(EC.element_to_be_clickable((By.ID, "fstNameSTR")))
            driver.execute_script("arguments[0].style.border='3px solid green'", first_name_field)
            first_name_field.clear()
            first_name_field.send_keys(form_data['fstNameSTR'])
            print(f"✅ Đã điền First Name")
            wait_and_see(f"First Name '{form_data['fstNameSTR']}' đã được điền", 2)
        except Exception as e:
            print(f"❌ Lỗi First Name: {e}")
        
        # 2. Last Name
        field_count += 1
        print(f"\n📝 {field_count}. Điền Last Name: {form_data['lstNameSTR']}")
        try:
            last_name_field = driver.find_element(By.ID, "lstNameSTR")
            driver.execute_script("arguments[0].style.border='3px solid green'", last_name_field)
            last_name_field.clear()
            last_name_field.send_keys(form_data['lstNameSTR'])
            print(f"✅ Đã điền Last Name")
            wait_and_see(f"Last Name '{form_data['lstNameSTR']}' đã được điền", 2)
        except Exception as e:
            print(f"❌ Lỗi Last Name: {e}")
        
        # 3. Email
        field_count += 1
        print(f"\n📝 {field_count}. Điền Email: {form_data['emailAddrsSTR']}")
        try:
            email_field = driver.find_element(By.ID, "email")
            driver.execute_script("arguments[0].style.border='3px solid green'", email_field)
            email_field.clear()
            email_field.send_keys(form_data['emailAddrsSTR'])
            print(f"✅ Đã điền Email")
            wait_and_see(f"Email '{form_data['emailAddrsSTR']}' đã được điền", 2)
        except Exception as e:
            print(f"❌ Lỗi Email: {e}")
        
        # 4. Confirm Email
        field_count += 1
        print(f"\n📝 {field_count}. Điền Confirm Email: {form_data['cemailAddrsSTR']}")
        try:
            confirm_email_field = driver.find_element(By.ID, "emailC")
            driver.execute_script("arguments[0].style.border='3px solid green'", confirm_email_field)
            confirm_email_field.clear()
            confirm_email_field.send_keys(form_data['cemailAddrsSTR'])
            print(f"✅ Đã điền Confirm Email")
            wait_and_see(f"Confirm Email đã được điền", 2)
        except Exception as e:
            print(f"❌ Lỗi Confirm Email: {e}")
        
        # 5. SSN
        field_count += 1
        print(f"\n📝 {field_count}. Điền SSN: {form_data['ssnumSTR']}")
        try:
            ssn_field = driver.find_element(By.ID, "ssn")
            driver.execute_script("arguments[0].style.border='3px solid green'", ssn_field)
            ssn_field.clear()
            ssn_field.send_keys(form_data['ssnumSTR'])
            print(f"✅ Đã điền SSN")
            wait_and_see(f"SSN đã được điền", 2)
        except Exception as e:
            print(f"❌ Lỗi SSN: {e}")
        
        # 6. Confirm SSN
        field_count += 1
        print(f"\n📝 {field_count}. Điền Confirm SSN: {form_data['cssnumSTR']}")
        try:
            confirm_ssn_field = driver.find_element(By.ID, "ssnC")
            driver.execute_script("arguments[0].style.border='3px solid green'", confirm_ssn_field)
            confirm_ssn_field.clear()
            confirm_ssn_field.send_keys(form_data['cssnumSTR'])
            print(f"✅ Đã điền Confirm SSN")
            wait_and_see(f"Confirm SSN đã được điền", 2)
        except Exception as e:
            print(f"❌ Lỗi Confirm SSN: {e}")
        
        # 7. Birth Month
        field_count += 1
        print(f"\n📋 {field_count}. Chọn Birth Month: {form_data['month']}")
        try:
            month_select = Select(driver.find_element(By.ID, "month"))
            driver.execute_script("arguments[0].style.border='3px solid green'", month_select._el)
            month_select.select_by_visible_text(form_data['month'])
            print(f"✅ Đã chọn Month")
            wait_and_see(f"Tháng sinh '{form_data['month']}' đã được chọn", 2)
        except Exception as e:
            print(f"❌ Lỗi Month: {e}")
        
        # 8. Birth Day
        field_count += 1
        print(f"\n📋 {field_count}. Chọn Birth Day: {form_data['day']}")
        try:
            day_select = Select(driver.find_element(By.ID, "day"))
            driver.execute_script("arguments[0].style.border='3px solid green'", day_select._el)
            day_select.select_by_visible_text(form_data['day'])
            print(f"✅ Đã chọn Day")
            wait_and_see(f"Ngày sinh '{form_data['day']}' đã được chọn", 2)
        except Exception as e:
            print(f"❌ Lỗi Day: {e}")
        
        # 9. Birth Year
        field_count += 1
        print(f"\n📋 {field_count}. Chọn Birth Year: {form_data['year']}")
        try:
            year_select = Select(driver.find_element(By.ID, "year"))
            driver.execute_script("arguments[0].style.border='3px solid green'", year_select._el)
            year_select.select_by_visible_text(form_data['year'])
            print(f"✅ Đã chọn Year")
            wait_and_see(f"Năm sinh '{form_data['year']}' đã được chọn", 2)
        except Exception as e:
            print(f"❌ Lỗi Year: {e}")
        
        # 10. Birth Country
        field_count += 1
        print(f"\n📋 {field_count}. Chọn Birth Country: {form_data['birthctrySTR']}")
        try:
            # Tìm select birth country (có thể không có name/id rõ ràng)
            country_selects = driver.find_elements(By.TAG_NAME, "select")
            for select_elem in country_selects:
                options = select_elem.find_elements(By.TAG_NAME, "option")
                option_texts = [opt.text for opt in options]
                if "United States Of America" in option_texts:
                    country_select = Select(select_elem)
                    driver.execute_script("arguments[0].style.border='3px solid green'", select_elem)
                    country_select.select_by_visible_text(form_data['birthctrySTR'])
                    print(f"✅ Đã chọn Birth Country")
                    wait_and_see(f"Quốc gia sinh '{form_data['birthctrySTR']}' đã được chọn", 2)
                    break
        except Exception as e:
            print(f"❌ Lỗi Birth Country: {e}")
        
        # 11. SSN Notice Checkbox
        field_count += 1
        print(f"\n☑️ {field_count}. Check SSN Notice Checkbox")
        try:
            ssn_checkbox = driver.find_element(By.ID, "ssnNoticeCB")
            driver.execute_script("arguments[0].style.border='3px solid green'", ssn_checkbox)
            if not ssn_checkbox.is_selected():
                smart_click(driver, ssn_checkbox, "js")
                print(f"✅ Đã check SSN Notice")
                wait_and_see("SSN Notice checkbox đã được check", 2)
            else:
                print(f"✅ SSN Notice đã được check từ trước")
        except Exception as e:
            print(f"❌ Lỗi SSN Checkbox: {e}")
        
        # Chụp ảnh form đã điền
        driver.save_screenshot("auto_reg_step5_form_filled.png")
        print(f"\n📸 Chụp ảnh form đã điền: auto_reg_step5_form_filled.png")
        
        wait_and_see("🎉 ĐÃ ĐIỀN XONG TẤT CẢ THÔNG TIN BẮT BUỘC!", 5)
        
        # BƯỚC 7: Submit form
        print(f"\n🚀 BƯỚC 7: Submit form đăng ký...")
        try:
            # Tìm Next/Submit button
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
            
            if submit_buttons:
                submit_btn = submit_buttons[0]
                print(f"✅ Tìm thấy Submit button: '{submit_btn.text}'")
                
                driver.execute_script("arguments[0].style.border='5px solid red'", submit_btn)
                driver.execute_script("arguments[0].style.backgroundColor='yellow'", submit_btn)
                
                wait_and_see("Submit button đã được highlight - sẽ click để gửi đăng ký", 4)
                
                if smart_click(driver, submit_btn, "js"):
                    print("✅ Đã click Submit!")
                    
                    time.sleep(10)
                    driver.save_screenshot("auto_reg_step6_after_submit.png")
                    print("📸 Chụp ảnh sau submit: auto_reg_step6_after_submit.png")
                    
                    print(f"\n🎉 ĐĂNG KÝ HOÀN TẤT!")
                    print(f"📄 URL sau submit: {driver.current_url}")
                    print(f"👤 Đã đăng ký thành công cho: {person['full_name']}")
                    print(f"📧 Email: {person['email']}")
                    
                else:
                    print("❌ Không thể click Submit")
            else:
                print("❌ Không tìm thấy Submit button")
                
        except Exception as e:
            print(f"❌ Lỗi Submit: {e}")
        
        # Giữ browser mở để xem kết quả
        wait_and_see("🎊 HOÀN THÀNH! Giữ browser mở để bạn xem kết quả", 15)
        
        print(f"\n✨ TỔNG KẾT:")
        print(f"👤 Người đăng ký: {person['full_name']}")
        print(f"📧 Email: {person['email']}")
        print(f"🆔 SSN: {person['ssn']}")
        print(f"🎂 Ngày sinh: {person['birth_date']}")
        print(f"📸 Đã chụp {field_count + 2} ảnh để lưu lại quá trình")
        print(f"🏁 Status: ĐĂNG KÝ THÀNH CÔNG!")
        
    except Exception as e:
        print(f"💥 LỖI TỔNG QUÁT: {e}")
        if driver:
            driver.save_screenshot("auto_reg_major_error.png")
            print("📸 Ảnh lỗi: auto_reg_major_error.png")
        
    finally:
        if driver:
            try:
                input("\n⏸️ Nhấn Enter để đóng browser...")
                driver.quit()
                print("🧹 Đã đóng browser")
            except:
                pass

if __name__ == "__main__":
    auto_register() 