#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - FORM EXPLORER
Khám phá form đăng ký theo flow: Button → Option1 → Next → Option2 → Next → Form
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

# 🎯 FLOW SELECTORS
FLOW_SELECTORS = {
    "step1_button": "#mainContent > div > form > div > div > button",
    "step2_option1": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div",
    "step2_next": "#mainContent > div > div:nth-child(5) > div > div > button.button.float-right",
    "step3_option2": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading",
    "step3_next": "#mainContent > div > div:nth-child(4) > div > div > button.button.float-right"
}

def explore_form():
    """Khám phá form đăng ký Santa Fe College"""
    print("🎯 SANTA FE COLLEGE - FORM EXPLORER")
    print("=" * 60)
    print("🚀 Khám phá form đăng ký theo flow đã biết")
    print("-" * 60)
    
    driver = None
    
    try:
        # SETUP
        print("\n🔧 Thiết lập ChromeDriver...")
        chrome_service = Service(ChromeDriverManager().install())
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        # Load extensions
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
        
        # BƯỚC extract gg from pdf: Mở website
        print("\n🌐 BƯỚC extract gg from pdf: Mở website...")
        url = "https://ss2.sfcollege.edu/sr/AdmissionApplication/#/"
        driver.get(url)
        print(f"🔗 URL: {url}")
        
        time.sleep(10)
        driver.save_screenshot("sf_form_step0_initial.png")
        print("📸 Chụp ảnh ban đầu: sf_form_step0_initial.png")
        
        # BƯỚC 2: Click button đầu tiên
        print("\n🎯 BƯỚC 2: Click button đầu tiên...")
        try:
            button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step1_button"])))
            print(f"✅ Tìm thấy button: {button1.text}")
            
            # Highlight và click
            driver.execute_script("arguments[0].style.border='3px solid red'", button1)
            time.sleep(2)
            button1.click()
            print("✅ Đã click button đầu tiên")
            
            time.sleep(5)
            driver.save_screenshot("sf_form_step1_after_first_button.png")
            print("📸 Chụp ảnh sau button extract gg from pdf: sf_form_step1_after_first_button.png")
            
        except Exception as e:
            print(f"❌ Lỗi button extract gg from pdf: {e}")
            driver.save_screenshot("sf_form_step1_ERROR.png")
            return
        
        # BƯỚC 3: Chọn option extract gg from pdf và click Next
        print("\n🎯 BƯỚC 3: Chọn option extract gg from pdf và Next...")
        try:
            # Chọn option extract gg from pdf
            option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_option1"])))
            print(f"✅ Tìm thấy option extract gg from pdf")
            
            driver.execute_script("arguments[0].style.border='3px solid red'", option1)
            time.sleep(2)
            option1.click()
            print("✅ Đã chọn option extract gg from pdf")
            
            time.sleep(3)
            
            # Click Next
            next1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_next"])))
            print(f"✅ Tìm thấy Next button: {next1.text}")
            
            driver.execute_script("arguments[0].style.border='3px solid blue'", next1)
            time.sleep(2)
            next1.click()
            print("✅ Đã click Next extract gg from pdf")
            
            time.sleep(5)
            driver.save_screenshot("sf_form_step2_after_option1_next.png")
            print("📸 Chụp ảnh sau option extract gg from pdf: sf_form_step2_after_option1_next.png")
            
        except Exception as e:
            print(f"❌ Lỗi option extract gg from pdf: {e}")
            driver.save_screenshot("sf_form_step2_ERROR.png")
            return
        
        # BƯỚC 4: Chọn option 2 và click Next
        print("\n🎯 BƯỚC 4: Chọn option 2 và Next...")
        try:
            # Chọn option 2
            option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_option2"])))
            print(f"✅ Tìm thấy option 2")
            
            driver.execute_script("arguments[0].style.border='3px solid red'", option2)
            time.sleep(2)
            option2.click()
            print("✅ Đã chọn option 2")
            
            time.sleep(3)
            
            # Click Next
            next2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_next"])))
            print(f"✅ Tìm thấy Next button: {next2.text}")
            
            driver.execute_script("arguments[0].style.border='3px solid blue'", next2)
            time.sleep(2)
            next2.click()
            print("✅ Đã click Next 2")
            
            time.sleep(8)
            driver.save_screenshot("sf_form_step3_final_form.png")
            print("📸 Chụp ảnh form cuối: sf_form_step3_final_form.png")
            
        except Exception as e:
            print(f"❌ Lỗi option 2: {e}")
            driver.save_screenshot("sf_form_step3_ERROR.png")
            return
        
        # BƯỚC 5: Khám phá form đăng ký
        print("\n🔍 BƯỚC 5: Khám phá form đăng ký...")
        print(f"📄 URL hiện tại: {driver.current_url}")
        print(f"📄 Tiêu đề: {driver.title}")
        
        # Tìm tất cả input fields
        inputs = driver.find_elements(By.TAG_NAME, "input")
        selects = driver.find_elements(By.TAG_NAME, "select")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        
        form_fields = {}
        
        print(f"\n📝 Tìm thấy {len(inputs)} input fields:")
        for i, inp in enumerate(inputs, 1):
            field_type = inp.get_attribute("type") or "text"
            field_name = inp.get_attribute("name") or f"input_{i}"
            field_id = inp.get_attribute("id") or ""
            field_placeholder = inp.get_attribute("placeholder") or ""
            field_required = inp.get_attribute("required") or False
            field_class = inp.get_attribute("class") or ""
            
            print(f"   {i:2d}. Name: {field_name:<20} Type: {field_type:<15} ID: {field_id}")
            if field_placeholder:
                print(f"       Placeholder: {field_placeholder}")
            if field_required:
                print(f"       ⚠️ Required: {field_required}")
            
            form_fields[field_name] = {
                "type": field_type,
                "id": field_id,
                "placeholder": field_placeholder,
                "required": bool(field_required),
                "class": field_class,
                "element_type": "input"
            }
        
        print(f"\n📋 Tìm thấy {len(selects)} select fields:")
        for i, sel in enumerate(selects, 1):
            field_name = sel.get_attribute("name") or f"select_{i}"
            field_id = sel.get_attribute("id") or ""
            field_required = sel.get_attribute("required") or False
            
            # Lấy options
            options = sel.find_elements(By.TAG_NAME, "option")
            option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
            
            print(f"   {i:2d}. Name: {field_name:<20} ID: {field_id}")
            print(f"       Options: {option_texts[:5]}{'...' if len(option_texts) > 5 else ''}")
            if field_required:
                print(f"       ⚠️ Required: {field_required}")
            
            form_fields[field_name] = {
                "type": "select",
                "id": field_id,
                "required": bool(field_required),
                "options": option_texts,
                "element_type": "select"
            }
        
        print(f"\n📝 Tìm thấy {len(textareas)} textarea fields:")
        for i, txt in enumerate(textareas, 1):
            field_name = txt.get_attribute("name") or f"textarea_{i}"
            field_id = txt.get_attribute("id") or ""
            field_placeholder = txt.get_attribute("placeholder") or ""
            field_required = txt.get_attribute("required") or False
            
            print(f"   {i:2d}. Name: {field_name:<20} ID: {field_id}")
            if field_placeholder:
                print(f"       Placeholder: {field_placeholder}")
            if field_required:
                print(f"       ⚠️ Required: {field_required}")
            
            form_fields[field_name] = {
                "type": "textarea",
                "id": field_id,
                "placeholder": field_placeholder,
                "required": bool(field_required),
                "element_type": "textarea"
            }
        
        # Lưu thông tin form
        with open("sf_form_fields.json", "w", encoding="utf-8") as f:
            json.dump(form_fields, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Đã lưu thông tin form: sf_form_fields.json")
        
        # Chụp ảnh cuối cùng
        driver.save_screenshot("sf_form_final_analysis.png")
        print("📸 Ảnh phân tích cuối: sf_form_final_analysis.png")
        
        print(f"\n🎉 HOÀN THÀNH KHÁM PHÁ!")
        print(f"📊 Tổng cộng: {len(inputs)} inputs + {len(selects)} selects + {len(textareas)} textareas")
        
        # Giữ browser mở để xem
        print("\n⏰ Giữ browser mở 15 giây để kiểm tra...")
        for i in range(15, 0, -1):
            print(f"   🔒 Đóng sau {i} giây...")
            time.sleep(1)
        
    except Exception as e:
        print(f"💥 LỖI: {e}")
        if driver:
            driver.save_screenshot("sf_form_major_error.png")
            print("📸 Ảnh lỗi: sf_form_major_error.png")
        
    finally:
        if driver:
            try:
                driver.quit()
                print("🧹 Đã đóng browser")
            except:
                pass

if __name__ == "__main__":
    explore_form() 