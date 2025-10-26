#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SANTA FE COLLEGE - STEP BY STEP TEST
Test từng bước với pause để xem kỹ
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

def pause_and_continue(message):
    """Pause và đợi user nhấn Enter"""
    print(f"\n⏸️ {message}")
    input("👆 Nhấn Enter để tiếp tục...")

def step_by_step_test():
    """Test từng bước với pause"""
    print("🎯 SANTA FE COLLEGE - STEP BY STEP TEST")
    print("=" * 60)
    
    # BƯỚC extract gg from pdf: Setup ChromeDriver tự động
    print("🔧 BƯỚC extract gg from pdf: Thiết lập ChromeDriver...")
    print("📥 Đang tự động tải ChromeDriver phiên bản mới nhất...")
    
    try:
        # Sử dụng webdriver-manager để tự động tải ChromeDriver đúng version
        chrome_service = Service(ChromeDriverManager().install())
        print("✅ ChromeDriver đã được cập nhật thành công!")
        
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        
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
        
        pause_and_continue("ChromeDriver đã sẵn sàng. Sẽ mở trình duyệt...")
        
        # BƯỚC 2: Khởi tạo browser
        print("\n🌐 BƯỚC 2: Khởi tạo trình duyệt...")
        driver = webdriver.Chrome(service=chrome_service, options=opts)
        wait = WebDriverWait(driver, 30)
        print("✅ Trình duyệt đã mở thành công!")
        
        pause_and_continue("Trình duyệt đã mở. Sẽ truy cập website Santa Fe College...")
        
        # BƯỚC 3: Mở website
        print("\n🏫 BƯỚC 3: Truy cập website Santa Fe College...")
        url = "https://ss2.sfcollege.edu/sr/AdmissionApplication/#/"
        print(f"🔗 URL: {url}")
        
        driver.get(url)
        print("⏳ Đang đợi trang web tải...")
        
        # Đợi trang load và hiển thị thông tin
        for i in range(10, 0, -1):
            print(f"   ⏰ Đợi {i} giây...")
            time.sleep(1)
        
        print(f"📄 Tiêu đề trang: {driver.title}")
        print(f"🔗 URL hiện tại: {driver.current_url}")
        
        pause_and_continue("Website đã tải xong. Bây giờ sẽ test từng selector...")
        
        # BƯỚC 4: Test từng selector
        print("\n🔍 BƯỚC 4: Test từng selector...")
        
        for i, (name, selector) in enumerate(SELECTORS_TO_TEST.items(), 1):
            print(f"\n🧪 Test {i}/3: {name}")
            print(f"📋 Selector: {selector}")
            print("-" * 40)
            
            try:
                # Tìm element với timeout ngắn hơn
                print("🔍 Đang tìm element...")
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                # Lấy thông tin chi tiết
                tag = element.tag_name
                text = element.text.strip()
                displayed = element.is_displayed()
                enabled = element.is_enabled()
                element_class = element.get_attribute("class") or ""
                element_id = element.get_attribute("id") or ""
                
                print(f"✅ ELEMENT TÌM THẤY!")
                print(f"   📌 Tag: {tag}")
                print(f"   🆔 ID: {element_id}")
                print(f"   🏷️ Class: {element_class}")
                print(f"   📝 Text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
                print(f"   👁️ Hiển thị: {displayed}")
                print(f"   🔓 Kích hoạt: {enabled}")
                
                # Highlight element
                print("🎯 Đang highlight element...")
                driver.execute_script("arguments[0].style.border='3px solid red'", element)
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                
                # Nếu là button hoặc clickable element
                if (tag == "button" or 
                    "button" in element_class.lower() or 
                    "btn" in element_class.lower() or
                    element.get_attribute("onclick")):
                    
                    print("🖱️ Đây có vẻ là element có thể click!")
                    click_test = input("   🤔 Bạn có muốn thử click element này? (y/n): ").strip().lower()
                    
                    if click_test == 'y':
                        try:
                            element.click()
                            print("   ✅ Click thành công!")
                            time.sleep(3)
                        except Exception as e:
                            print(f"   ❌ Click thất bại: {e}")
                
                # Chụp ảnh
                screenshot_name = f"sf_test_step_{i}_{name}.png"
                driver.save_screenshot(screenshot_name)
                print(f"📸 Đã chụp ảnh: {screenshot_name}")
                
            except Exception as e:
                print(f"❌ KHÔNG TÌM THẤY ELEMENT: {e}")
                driver.save_screenshot(f"sf_test_step_{i}_{name}_ERROR.png")
                print(f"📸 Đã chụp ảnh lỗi: sf_test_step_{i}_{name}_ERROR.png")
            
            # Pause giữa các test
            if i < len(SELECTORS_TO_TEST):
                pause_and_continue(f"Hoàn thành test {i}/3. Tiếp tục test selector tiếp theo...")
        
        # BƯỚC 5: Tổng kết
        print("\n📊 BƯỚC 5: Tổng kết...")
        print("=" * 60)
        print("🎉 ĐÃ HOÀN THÀNH TẤT CẢ CÁC TEST!")
        print("📸 Kiểm tra các file ảnh đã chụp để xem chi tiết")
        print("📋 Kết quả test sẽ giúp xác định selectors nào hoạt động")
        
        # Chụp ảnh tổng kết
        driver.save_screenshot("sf_test_final_summary.png")
        print("📸 Ảnh tổng kết: sf_test_final_summary.png")
        
        pause_and_continue("Test hoàn thành! Sẽ đóng trình duyệt sau 10 giây...")
        
        # Đếm ngược đóng browser
        for i in range(10, 0, -1):
            print(f"🔒 Đóng trình duyệt sau {i} giây...")
            time.sleep(1)
        
    except Exception as e:
        print(f"💥 LỖI TRONG QUÁ TRÌNH TEST: {e}")
        try:
            driver.save_screenshot("sf_test_major_error.png")
            print("📸 Đã chụp ảnh lỗi: sf_test_major_error.png")
        except:
            pass
        
    finally:
        # Đóng browser
        try:
            driver.quit()
            print("🧹 Đã đóng trình duyệt")
        except:
            pass

def main():
    """Hàm main"""
    print("🚀 SANTA FE COLLEGE - STEP BY STEP SELECTOR TEST")
    print("💡 Test này sẽ dừng lại từng bước để bạn xem kỹ")
    print("📸 Mỗi bước sẽ chụp ảnh để lưu lại")
    print("🔧 Tự động cập nhật ChromeDriver")
    print("-" * 60)
    
    confirm = input("🤔 Bạn có muốn bắt đầu test? (y/n): ").strip().lower()
    
    if confirm == 'y':
        step_by_step_test()
    else:
        print("👋 Tạm biệt!")

if __name__ == "__main__":
    main() 