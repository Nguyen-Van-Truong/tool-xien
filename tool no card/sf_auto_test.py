#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - AUTO TEST (NO INPUT REQUIRED)
Test tự động không cần nhập input
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# 🎯 CÁC SELECTORS CẦN TEST
SELECTORS_TO_TEST = {
    "Button": "#mainContent > div > form > div > div > button",
    "Element_2": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div",
    "Element_3": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading"
}

def auto_test():
    """Test tự động không cần input"""
    print("🎯 SANTA FE COLLEGE - AUTO TEST")
    print("=" * 60)
    print("⚡ Chạy tự động không cần nhập input")
    print("📸 Sẽ chụp ảnh và lưu kết quả")
    print("-" * 60)
    
    driver = None
    
    try:
        # BƯỚC extract gg from pdf: Setup ChromeDriver tự động
        print("\n🔧 BƯỚC extract gg from pdf: Thiết lập ChromeDriver...")
        print("📥 Đang tự động tải ChromeDriver phiên bản mới nhất...")
        
        chrome_service = Service(ChromeDriverManager().install())
        print("✅ ChromeDriver đã được cập nhật thành công!")
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        
        # Thêm extensions nếu có
        try:
            opts.add_extension("driver/captchasolver.crx")
            print("✅ Loaded captcha solver extension")
        except:
            print("⚠️ Captcha solver extension not found (OK)")
            
        try:
            opts.add_extension("driver/extract gg from pdf.crx")
            print("✅ Loaded extension extract gg from pdf.crx")
        except:
            print("⚠️ Extension extract gg from pdf.crx not found (OK)")
        
        # BƯỚC 2: Khởi tạo browser
        print("\n🌐 BƯỚC 2: Khởi tạo trình duyệt...")
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 30)
        print("✅ Trình duyệt đã mở thành công!")
        
        # BƯỚC 3: Mở website
        print("\n🏫 BƯỚC 3: Truy cập website Santa Fe College...")
        url = "https://ss2.sfcollege.edu/sr/AdmissionApplication/#/"
        print(f"🔗 URL: {url}")
        
        driver.get(url)
        print("⏳ Đang đợi trang web tải...")
        
        # Đợi trang load và hiển thị thông tin
        print("   ⏰ Đợi 15 giây cho trang load hoàn toàn...")
        time.sleep(15)
        
        print(f"📄 Tiêu đề trang: {driver.title}")
        print(f"🔗 URL hiện tại: {driver.current_url}")
        
        # Chụp ảnh ban đầu
        driver.save_screenshot("sf_auto_test_initial.png")
        print("📸 Đã chụp ảnh ban đầu: sf_auto_test_initial.png")
        
        # BƯỚC 4: Test từng selector
        print("\n🔍 BƯỚC 4: Test từng selector...")
        results = {}
        
        for i, (name, selector) in enumerate(SELECTORS_TO_TEST.items(), 1):
            print(f"\n🧪 Test {i}/3: {name}")
            print(f"📋 Selector: {selector}")
            print("-" * 40)
            
            try:
                # Tìm element
                print("🔍 Đang tìm element...")
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                # Lấy thông tin chi tiết
                tag = element.tag_name
                text = element.text.strip()
                displayed = element.is_displayed()
                enabled = element.is_enabled()
                element_class = element.get_attribute("class") or ""
                element_id = element.get_attribute("id") or ""
                element_type = element.get_attribute("type") or ""
                element_name = element.get_attribute("name") or ""
                
                print(f"✅ ELEMENT TÌM THẤY!")
                print(f"   📌 Tag: {tag}")
                print(f"   🆔 ID: {element_id}")
                print(f"   📛 Name: {element_name}")
                print(f"   🔧 Type: {element_type}")
                print(f"   🏷️ Class: {element_class}")
                print(f"   📝 Text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
                print(f"   👁️ Hiển thị: {displayed}")
                print(f"   🔓 Kích hoạt: {enabled}")
                
                # Highlight element
                print("🎯 Đang highlight element...")
                driver.execute_script("arguments[0].style.border='5px solid red'", element)
                driver.execute_script("arguments[0].style.backgroundColor='yellow'", element)
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(2)
                
                # Lưu kết quả
                results[name] = {
                    "found": True,
                    "tag": tag,
                    "id": element_id,
                    "name": element_name,
                    "type": element_type,
                    "class": element_class,
                    "text": text,
                    "displayed": displayed,
                    "enabled": enabled
                }
                
                # Thử click nếu là button
                if (tag == "button" or 
                    "button" in element_class.lower() or 
                    "btn" in element_class.lower() or
                    element_type == "submit" or
                    element.get_attribute("onclick")):
                    
                    print("🖱️ Đây có vẻ là element có thể click! Thử click...")
                    try:
                        element.click()
                        print("   ✅ Click thành công!")
                        time.sleep(3)
                        results[name]["clicked"] = True
                    except Exception as e:
                        print(f"   ❌ Click thất bại: {e}")
                        results[name]["clicked"] = False
                
                # Chụp ảnh
                screenshot_name = f"sf_auto_test_step_{i}_{name}.png"
                driver.save_screenshot(screenshot_name)
                print(f"📸 Đã chụp ảnh: {screenshot_name}")
                
                print(f"✅ Test {name}: THÀNH CÔNG")
                
            except Exception as e:
                print(f"❌ KHÔNG TÌM THẤY ELEMENT: {e}")
                results[name] = {"found": False, "error": str(e)}
                driver.save_screenshot(f"sf_auto_test_step_{i}_{name}_ERROR.png")
                print(f"📸 Đã chụp ảnh lỗi: sf_auto_test_step_{i}_{name}_ERROR.png")
                print(f"❌ Test {name}: THẤT BẠI")
            
            # Đợi giữa các test
            time.sleep(2)
        
        # BƯỚC 5: Tổng kết
        print("\n📊 BƯỚC 5: Tổng kết...")
        print("=" * 60)
        
        print("🎯 KẾT QUẢ CHI TIẾT:")
        for name, result in results.items():
            if result.get("found"):
                print(f"\n✅ {name}:")
                print(f"   📌 Tag: {result['tag']}")
                print(f"   🆔 ID: {result['id']}")
                print(f"   📛 Name: {result['name']}")
                print(f"   🔧 Type: {result['type']}")
                print(f"   🏷️ Class: {result['class']}")
                print(f"   📝 Text: {result['text'][:50]}...")
                print(f"   👁️ Hiển thị: {result['displayed']}")
                print(f"   🔓 Kích hoạt: {result['enabled']}")
                if "clicked" in result:
                    print(f"   🖱️ Click: {'Thành công' if result['clicked'] else 'Thất bại'}")
            else:
                print(f"\n❌ {name}: KHÔNG TÌM THẤY")
                print(f"   💥 Lỗi: {result['error']}")
        
        print(f"\n📊 THỐNG KÊ:")
        found_count = sum(1 for r in results.values() if r.get("found"))
        total_count = len(results)
        print(f"   ✅ Tìm thấy: {found_count}/{total_count}")
        print(f"   ❌ Không tìm thấy: {total_count - found_count}/{total_count}")
        
        # Chụp ảnh tổng kết
        driver.save_screenshot("sf_auto_test_final_summary.png")
        print("📸 Ảnh tổng kết: sf_auto_test_final_summary.png")
        
        print("\n🎉 ĐÃ HOÀN THÀNH TẤT CẢ CÁC TEST!")
        print("📁 Kiểm tra các file ảnh đã chụp để xem chi tiết")
        
        # Giữ browser mở 10 giây để xem
        print("⏰ Giữ browser mở 10 giây để bạn xem...")
        for i in range(10, 0, -1):
            print(f"   🔒 Đóng sau {i} giây...")
            time.sleep(1)
        
    except Exception as e:
        print(f"💥 LỖI TRONG QUÁ TRÌNH TEST: {e}")
        if driver:
            try:
                driver.save_screenshot("sf_auto_test_major_error.png")
                print("📸 Đã chụp ảnh lỗi: sf_auto_test_major_error.png")
            except:
                pass
        
    finally:
        # Đóng browser
        if driver:
            try:
                driver.quit()
                print("🧹 Đã đóng trình duyệt")
            except:
                pass

if __name__ == "__main__":
    print("🚀 STARTING SANTA FE COLLEGE AUTO TEST...")
    print("⚡ Không cần nhập input - chạy tự động")
    print("-" * 60)
    auto_test()
    print("\n✨ TEST HOÀN THÀNH!") 