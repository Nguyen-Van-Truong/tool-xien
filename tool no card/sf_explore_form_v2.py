#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - FORM EXPLORER V2
Khám phá form đăng ký - Version 2 với bypass overlay
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

def close_overlays(driver):
    """Đóng tất cả overlay có thể che button"""
    try:
        # Tìm và đóng các overlay phổ biến
        overlays = [
            ".Fab-zoomContainer",
            ".overlay",
            ".modal", 
            ".popup",
            ".dialog",
            "[role='dialog']",
            ".ui-dialog",
            ".fancybox-container"
        ]
        
        for overlay_selector in overlays:
            try:
                overlays_found = driver.find_elements(By.CSS_SELECTOR, overlay_selector)
                for overlay in overlays_found:
                    if overlay.is_displayed():
                        print(f"🚫 Tìm thấy overlay: {overlay_selector}")
                        driver.execute_script("arguments[0].style.display = 'none';", overlay)
                        print(f"✅ Đã ẩn overlay: {overlay_selector}")
            except:
                continue
                
        # Tìm và click close buttons
        close_buttons = [
            ".close", ".btn-close", "[aria-label='close']", 
            "[aria-label='Close']", ".modal-close", ".ui-dialog-titlebar-close"
        ]
        
        for close_selector in close_buttons:
            try:
                close_btns = driver.find_elements(By.CSS_SELECTOR, close_selector)
                for btn in close_btns:
                    if btn.is_displayed():
                        btn.click()
                        print(f"✅ Đã click close button: {close_selector}")
                        time.sleep(1)
            except:
                continue
                
    except Exception as e:
        print(f"⚠️ Lỗi khi đóng overlay: {e}")

def smart_click(driver, element, method="js"):
    """Click thông minh với nhiều phương pháp"""
    try:
        if method == "normal":
            element.click()
            return True
        elif method == "js":
            driver.execute_script("arguments[0].click();", element)
            return True
        elif method == "action":
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            return True
        elif method == "force":
            # Force click bằng JS
            driver.execute_script("""
                arguments[0].dispatchEvent(new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                }));
            """, element)
            return True
    except Exception as e:
        print(f"❌ {method} click failed: {e}")
        return False

def explore_form_v2():
    """Khám phá form v2 với bypass overlay"""
    print("🎯 SANTA FE COLLEGE - FORM EXPLORER V2")
    print("=" * 60)
    print("🚀 Khám phá form với bypass overlay")
    print("-" * 60)
    
    driver = None
    
    try:
        # SETUP
        print("\n🔧 Thiết lập ChromeDriver...")
        chrome_service = Service(ChromeDriverManager().install())
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--disable-extensions-file-access-check')
        opts.add_argument('--disable-extensions-https-only')
        opts.add_argument('--disable-web-security')
        opts.add_argument('--allow-running-insecure-content')
        
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
        close_overlays(driver)
        driver.save_screenshot("sf_form_v2_step0_initial.png")
        print("📸 Chụp ảnh ban đầu: sf_form_v2_step0_initial.png")
        
        # BƯỚC 2: Click button đầu tiên
        print("\n🎯 BƯỚC 2: Click button đầu tiên...")
        try:
            button1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step1_button"])))
            print(f"✅ Tìm thấy button: {button1.text}")
            
            driver.execute_script("arguments[0].style.border='3px solid red'", button1)
            time.sleep(2)
            
            if smart_click(driver, button1, "js"):
                print("✅ Đã click button đầu tiên")
            else:
                print("❌ Không thể click button extract gg from pdf")
                return
            
            time.sleep(5)
            close_overlays(driver)
            driver.save_screenshot("sf_form_v2_step1_after_first_button.png")
            
        except Exception as e:
            print(f"❌ Lỗi button extract gg from pdf: {e}")
            return
        
        # BƯỚC 3: Chọn option extract gg from pdf và click Next
        print("\n🎯 BƯỚC 3: Chọn option extract gg from pdf và Next...")
        try:
            # Chọn option extract gg from pdf
            option1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step2_option1"])))
            print(f"✅ Tìm thấy option extract gg from pdf")
            
            driver.execute_script("arguments[0].style.border='3px solid red'", option1)
            time.sleep(2)
            
            if smart_click(driver, option1, "js"):
                print("✅ Đã chọn option extract gg from pdf")
            else:
                print("❌ Không thể chọn option extract gg from pdf")
                return
            
            time.sleep(3)
            close_overlays(driver)
            
            # Click Next với multiple attempts
            next1 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, FLOW_SELECTORS["step2_next"])))
            print(f"✅ Tìm thấy Next button: {next1.text}")
            
            driver.execute_script("arguments[0].style.border='3px solid blue'", next1)
            time.sleep(2)
            
            # Thử nhiều phương pháp click
            clicked = False
            for method in ["js", "force", "action", "normal"]:
                print(f"🔄 Thử click Next bằng {method}...")
                if smart_click(driver, next1, method):
                    print(f"✅ Click Next thành công bằng {method}")
                    clicked = True
                    break
                time.sleep(1)
                close_overlays(driver)
            
            if not clicked:
                print("❌ Tất cả phương pháp click Next đều thất bại")
                # Thử scroll và click
                driver.execute_script("arguments[0].scrollIntoView(true);", next1)
                time.sleep(2)
                close_overlays(driver)
                if smart_click(driver, next1, "force"):
                    print("✅ Click Next thành công sau scroll")
                    clicked = True
            
            if not clicked:
                print("❌ Không thể click Next - dừng tại đây")
                driver.save_screenshot("sf_form_v2_step2_ERROR.png")
                return
            
            time.sleep(5)
            close_overlays(driver)
            driver.save_screenshot("sf_form_v2_step2_after_option1_next.png")
            
        except Exception as e:
            print(f"❌ Lỗi option extract gg from pdf: {e}")
            driver.save_screenshot("sf_form_v2_step2_ERROR.png")
            return
        
        # BƯỚC 4: Chọn option 2 và click Next
        print("\n🎯 BƯỚC 4: Chọn option 2 và Next...")
        try:
            # Chọn option 2
            option2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, FLOW_SELECTORS["step3_option2"])))
            print(f"✅ Tìm thấy option 2")
            
            driver.execute_script("arguments[0].style.border='3px solid red'", option2)
            time.sleep(2)
            
            if smart_click(driver, option2, "js"):
                print("✅ Đã chọn option 2")
            else:
                print("❌ Không thể chọn option 2")
                return
            
            time.sleep(3)
            close_overlays(driver)
            
            # Click Next 2
            next2 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, FLOW_SELECTORS["step3_next"])))
            print(f"✅ Tìm thấy Next button 2: {next2.text}")
            
            driver.execute_script("arguments[0].style.border='3px solid blue'", next2)
            time.sleep(2)
            
            # Thử click Next 2
            clicked = False
            for method in ["js", "force", "action", "normal"]:
                print(f"🔄 Thử click Next 2 bằng {method}...")
                if smart_click(driver, next2, method):
                    print(f"✅ Click Next 2 thành công bằng {method}")
                    clicked = True
                    break
                time.sleep(1)
                close_overlays(driver)
            
            if not clicked:
                print("❌ Không thể click Next 2")
                driver.save_screenshot("sf_form_v2_step3_ERROR.png")
                return
            
            time.sleep(8)
            close_overlays(driver)
            driver.save_screenshot("sf_form_v2_step3_final_form.png")
            
        except Exception as e:
            print(f"❌ Lỗi option 2: {e}")
            driver.save_screenshot("sf_form_v2_step3_ERROR.png")
            return
        
        # BƯỚC 5: Khám phá form đăng ký
        print("\n🔍 BƯỚC 5: Khám phá form đăng ký...")
        print(f"📄 URL hiện tại: {driver.current_url}")
        print(f"📄 Tiêu đề: {driver.title}")
        
        # Scroll to top để đảm bảo thấy hết form
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Tìm tất cả elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        selects = driver.find_elements(By.TAG_NAME, "select")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        form_fields = {}
        
        print(f"\n📝 Tìm thấy {len(inputs)} input fields:")
        for i, inp in enumerate(inputs, 1):
            try:
                field_type = inp.get_attribute("type") or "text"
                field_name = inp.get_attribute("name") or f"input_{i}"
                field_id = inp.get_attribute("id") or ""
                field_placeholder = inp.get_attribute("placeholder") or ""
                field_required = inp.get_attribute("required") or False
                field_class = inp.get_attribute("class") or ""
                field_visible = inp.is_displayed()
                
                if field_visible and field_type not in ["hidden", "submit", "button"]:
                    print(f"   {i:2d}. Name: {field_name:<25} Type: {field_type:<15} ID: {field_id}")
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
                    "visible": field_visible,
                    "element_type": "input"
                }
            except Exception as e:
                print(f"   ❌ Lỗi input {i}: {e}")
        
        print(f"\n📋 Tìm thấy {len(selects)} select fields:")
        for i, sel in enumerate(selects, 1):
            try:
                field_name = sel.get_attribute("name") or f"select_{i}"
                field_id = sel.get_attribute("id") or ""
                field_required = sel.get_attribute("required") or False
                field_visible = sel.is_displayed()
                
                if field_visible:
                    # Lấy options
                    options = sel.find_elements(By.TAG_NAME, "option")
                    option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
                    
                    print(f"   {i:2d}. Name: {field_name:<25} ID: {field_id}")
                    print(f"       Options ({len(option_texts)}): {option_texts[:3]}{'...' if len(option_texts) > 3 else ''}")
                    if field_required:
                        print(f"       ⚠️ Required: {field_required}")
                
                form_fields[field_name] = {
                    "type": "select",
                    "id": field_id,
                    "required": bool(field_required),
                    "options": option_texts if field_visible else [],
                    "visible": field_visible,
                    "element_type": "select"
                }
            except Exception as e:
                print(f"   ❌ Lỗi select {i}: {e}")
        
        print(f"\n📝 Tìm thấy {len(textareas)} textarea fields:")
        for i, txt in enumerate(textareas, 1):
            try:
                field_name = txt.get_attribute("name") or f"textarea_{i}"
                field_id = txt.get_attribute("id") or ""
                field_placeholder = txt.get_attribute("placeholder") or ""
                field_required = txt.get_attribute("required") or False
                field_visible = txt.is_displayed()
                
                if field_visible:
                    print(f"   {i:2d}. Name: {field_name:<25} ID: {field_id}")
                    if field_placeholder:
                        print(f"       Placeholder: {field_placeholder}")
                    if field_required:
                        print(f"       ⚠️ Required: {field_required}")
                
                form_fields[field_name] = {
                    "type": "textarea",
                    "id": field_id,
                    "placeholder": field_placeholder,
                    "required": bool(field_required),
                    "visible": field_visible,
                    "element_type": "textarea"
                }
            except Exception as e:
                print(f"   ❌ Lỗi textarea {i}: {e}")
        
        print(f"\n🔘 Tìm thấy {len(buttons)} buttons:")
        visible_buttons = []
        for i, btn in enumerate(buttons, 1):
            try:
                btn_text = btn.text.strip()
                btn_type = btn.get_attribute("type") or ""
                btn_class = btn.get_attribute("class") or ""
                btn_visible = btn.is_displayed()
                
                if btn_visible and btn_text:
                    print(f"   {i:2d}. Text: {btn_text:<25} Type: {btn_type}")
                    visible_buttons.append(btn_text)
            except Exception as e:
                continue
        
        # Lưu thông tin form
        form_info = {
            "url": driver.current_url,
            "title": driver.title,
            "total_inputs": len([f for f in form_fields.values() if f["element_type"] == "input" and f.get("visible", True)]),
            "total_selects": len([f for f in form_fields.values() if f["element_type"] == "select" and f.get("visible", True)]),
            "total_textareas": len([f for f in form_fields.values() if f["element_type"] == "textarea" and f.get("visible", True)]),
            "visible_buttons": visible_buttons,
            "fields": form_fields
        }
        
        with open("sf_form_fields_v2.json", "w", encoding="utf-8") as f:
            json.dump(form_info, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Đã lưu thông tin form: sf_form_fields_v2.json")
        
        # Scroll và chụp ảnh multiple sections
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        driver.save_screenshot("sf_form_v2_final_top.png")
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.save_screenshot("sf_form_v2_final_middle.png")
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.save_screenshot("sf_form_v2_final_bottom.png")
        
        print("📸 Đã chụp ảnh: top, middle, bottom")
        
        print(f"\n🎉 HOÀN THÀNH KHÁM PHÁ V2!")
        visible_fields = len([f for f in form_fields.values() if f.get("visible", True)])
        print(f"📊 Tổng cộng {visible_fields} fields có thể nhìn thấy")
        print(f"🔘 {len(visible_buttons)} buttons có thể tương tác")
        
        # Giữ browser mở để xem
        print("\n⏰ Giữ browser mở 20 giây để kiểm tra...")
        for i in range(20, 0, -1):
            print(f"   🔒 Đóng sau {i} giây...")
            time.sleep(1)
        
    except Exception as e:
        print(f"💥 LỖI: {e}")
        if driver:
            driver.save_screenshot("sf_form_v2_major_error.png")
            print("📸 Ảnh lỗi: sf_form_v2_major_error.png")
        
    finally:
        if driver:
            try:
                driver.quit()
                print("🧹 Đã đóng browser")
            except:
                pass

if __name__ == "__main__":
    explore_form_v2() 