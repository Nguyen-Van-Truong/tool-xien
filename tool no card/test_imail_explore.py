#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 IMAIL EXPLORER - Khám phá imail.edu.vn
Test tạo email với format firstname + 2 số ngẫu nhiên + @naka.edu.pl
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import json

def explore_imail():
    """Khám phá imail.edu.vn để hiểu cách tạo email"""
    print("🌐 IMAIL.EDU.VN EXPLORER")
    print("=" * 50)
    print("🎯 Khám phá cách tạo email với @naka.edu.pl")
    print("-" * 50)
    
    driver = None
    
    try:
        # SETUP BROWSER
        print("🔧 Thiết lập browser...")
        chrome_service = Service(ChromeDriverManager().install())
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 10)
        
        # TRUY CẬP IMAIL
        print("\n🌐 Truy cập imail.edu.vn...")
        driver.get("https://imail.edu.vn")
        time.sleep(5)
        
        # Screenshot trang chủ
        driver.save_screenshot("imail_step1_homepage.png")
        print("📸 Screenshot: imail_step1_homepage.png")
        
        # PHÂN TÍCH GIAO DIỆN
        print("\n🔍 Phân tích giao diện...")
        
        # Tìm tất cả input fields
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"📝 Input fields found: {len(inputs)}")
        
        for i, inp in enumerate(inputs):
            try:
                input_type = inp.get_attribute("type")
                input_id = inp.get_attribute("id")
                input_name = inp.get_attribute("name")
                input_placeholder = inp.get_attribute("placeholder")
                input_class = inp.get_attribute("class")
                
                print(f"   Input {i+1}:")
                print(f"      Type: {input_type}")
                print(f"      ID: {input_id}")
                print(f"      Name: {input_name}")
                print(f"      Placeholder: {input_placeholder}")
                print(f"      Class: {input_class}")
                print()
                
            except Exception as e:
                print(f"   Input {i+1}: Error - {e}")
        
        # Tìm tất cả buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\n🔘 Buttons found: {len(buttons)}")
        
        for i, btn in enumerate(buttons):
            try:
                btn_text = btn.text
                btn_id = btn.get_attribute("id")
                btn_class = btn.get_attribute("class")
                
                print(f"   Button {i+1}:")
                print(f"      Text: {btn_text}")
                print(f"      ID: {btn_id}")
                print(f"      Class: {btn_class}")
                print()
                
            except Exception as e:
                print(f"   Button {i+1}: Error - {e}")
        
        # Tìm dropdown/select elements
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"\n📋 Select dropdowns found: {len(selects)}")
        
        for i, sel in enumerate(selects):
            try:
                sel_id = sel.get_attribute("id")
                sel_name = sel.get_attribute("name")
                sel_class = sel.get_attribute("class")
                
                # Lấy các options
                select_obj = Select(sel)
                options = select_obj.options
                
                print(f"   Select {i+1}:")
                print(f"      ID: {sel_id}")
                print(f"      Name: {sel_name}")
                print(f"      Class: {sel_class}")
                print(f"      Options count: {len(options)}")
                
                # Hiển thị các options
                for j, opt in enumerate(options[:10]):  # Chỉ hiển thị 10 đầu
                    try:
                        opt_text = opt.text
                        opt_value = opt.get_attribute("value")
                        print(f"         Option {j+1}: {opt_text} (value: {opt_value})")
                        
                        # Check xem có naka.edu.pl không
                        if "naka.edu.pl" in opt_text:
                            print(f"         ✅ FOUND naka.edu.pl!")
                            
                    except Exception as e:
                        print(f"         Option {j+1}: Error - {e}")
                print()
                
            except Exception as e:
                print(f"   Select {i+1}: Error - {e}")
        
        # Tìm text chứa domains
        print(f"\n🔍 Tìm kiếm domain names trong page...")
        page_source = driver.page_source
        
        domains = ["naka.edu.pl", "imail.edu.vn", "gddp2018.edu.vn", "collegewh.edu.pl", "mailpro.lat", "tempmail.io.vn"]
        
        for domain in domains:
            if domain in page_source:
                print(f"   ✅ Found domain: {domain}")
            else:
                print(f"   ❌ Not found: {domain}")
        
        # TRY TẠO EMAIL
        print(f"\n🎯 Thử tạo email...")
        
        # Test với firstname + random numbers
        firstname = "john"
        random_numbers = f"{random.randint(10, 99)}"
        test_username = f"{firstname}{random_numbers}"
        
        print(f"📝 Test username: {test_username}")
        
        # Tìm input để nhập username
        username_input = None
        possible_selectors = [
            "input[type='text']",
            "input[placeholder*='email']",
            "input[placeholder*='username']",
            "input[placeholder*='name']",
            "input[id*='email']",
            "input[id*='username']",
            "input[name*='email']",
            "input[name*='username']"
        ]
        
        for selector in possible_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        username_input = elem
                        print(f"✅ Found username input: {selector}")
                        break
                if username_input:
                    break
            except:
                continue
        
        if username_input:
            try:
                # Nhập username
                username_input.clear()
                username_input.send_keys(test_username)
                print(f"✅ Đã nhập username: {test_username}")
                
                # Screenshot sau khi nhập
                driver.save_screenshot("imail_step2_username_entered.png")
                
                time.sleep(2)
                
                # Tìm dropdown domain (nếu có)
                domain_selected = False
                
                # Thử tìm và chọn naka.edu.pl
                for selector in ["select", ".dropdown", ".domain-select"]:
                    try:
                        domain_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in domain_elements:
                            elem_html = elem.get_attribute("innerHTML")
                            if elem_html and "naka.edu.pl" in elem_html:
                                print(f"✅ Found domain dropdown!")
                                
                                # Click dropdown
                                elem.click()
                                time.sleep(1)
                                
                                # Tìm option naka.edu.pl
                                try:
                                    naka_option = driver.find_element(By.XPATH, "//option[contains(text(), 'naka.edu.pl')] | //*[contains(text(), 'naka.edu.pl')]")
                                    naka_option.click()
                                    print(f"✅ Selected naka.edu.pl!")
                                    domain_selected = True
                                    
                                    # Screenshot sau khi chọn domain
                                    driver.save_screenshot("imail_step3_domain_selected.png")
                                    break
                                    
                                except Exception as e:
                                    print(f"⚠️ Không click được naka.edu.pl: {e}")
                                    
                        if domain_selected:
                            break
                    except:
                        continue
                
                # Tìm và click button tạo email
                create_clicked = False
                button_selectors = [
                    "button",
                    ".button",
                    "input[type='submit']",
                    "input[type='button']",
                    "[onclick]"
                ]
                
                for selector in button_selectors:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                btn_text = btn.get_attribute("innerHTML").lower()
                                btn_text += " " + btn.text.lower()
                                
                                # Tìm button có text tạo email
                                create_keywords = ["create", "new", "generate", "tạo", "mới", "copy", "refresh"]
                                
                                if any(keyword in btn_text for keyword in create_keywords):
                                    print(f"✅ Found create button: {btn.text or btn.get_attribute('innerHTML')[:50]}")
                                    
                                    try:
                                        btn.click()
                                        print(f"✅ Clicked create button!")
                                        create_clicked = True
                                        time.sleep(3)
                                        
                                        # Screenshot sau khi click
                                        driver.save_screenshot("imail_step4_after_create.png")
                                        break
                                        
                                    except Exception as e:
                                        print(f"⚠️ Click error: {e}")
                                        
                        if create_clicked:
                            break
                    except:
                        continue
                
                # Kiểm tra kết quả
                print(f"\n📧 Kiểm tra email đã tạo...")
                
                expected_email = f"{test_username}@naka.edu.pl"
                page_source_after = driver.page_source
                
                if expected_email in page_source_after:
                    print(f"✅ SUCCESS! Email đã tạo: {expected_email}")
                elif test_username in page_source_after:
                    print(f"✅ Username appears in page: {test_username}")
                    
                    # Tìm email hiển thị
                    import re
                    email_pattern = rf"{test_username}@[\w\.-]+\.\w+"
                    email_matches = re.findall(email_pattern, page_source_after)
                    
                    if email_matches:
                        print(f"✅ Email found: {email_matches[0]}")
                    else:
                        print(f"⚠️ Email not found in expected format")
                else:
                    print(f"❌ No sign of created email")
                
                # Screenshot cuối cùng
                driver.save_screenshot("imail_step5_final_result.png")
                
            except Exception as e:
                print(f"❌ Error testing email creation: {e}")
        else:
            print(f"❌ Không tìm thấy username input")
        
        # Giữ browser mở để quan sát
        print(f"\n⏰ Giữ browser mở để quan sát...")
        time.sleep(20)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if driver:
            driver.save_screenshot("imail_error.png")
    
    finally:
        if driver:
            print(f"\n🔄 Browser sẽ mở để bạn quan sát...")
            # driver.quit()  # Bỏ comment để đóng browser

def test_simple_email_creation():
    """Test tạo email theo format đơn giản"""
    print("\n" + "="*50)
    print("📧 TEST SIMPLE EMAIL CREATION")
    print("="*50)
    
    # Test format
    firstname = "theresa"  # Từ dữ liệu có sẵn
    random_numbers = f"{random.randint(10, 99)}"
    username = f"{firstname.lower()}{random_numbers}"
    email_address = f"{username}@naka.edu.pl"
    
    email_info = {
        "email": email_address,
        "username": username,
        "domain": "naka.edu.pl",
        "created_time": time.time()
    }
    
    print(f"✅ Email format test:")
    print(f"   Firstname: {firstname}")
    print(f"   Random numbers: {random_numbers}")
    print(f"   Username: {username}")
    print(f"   Full email: {email_address}")
    
    # Save test data
    with open("imail_test_result.json", "w", encoding="utf-8") as f:
        json.dump(email_info, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: imail_test_result.json")
    
    return email_info

if __name__ == "__main__":
    # Test format đơn giản trước
    test_simple_email_creation()
    
    # Sau đó khám phá website
    explore_imail() 