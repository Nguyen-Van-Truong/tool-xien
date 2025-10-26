#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎓 SANTA FE COLLEGE - DEMO TEST SELECTORS
File demo để test các selectors từng bước một
"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import sys

class SantaFeDemo:
    def __init__(self, chromedriver="driver/chromedriver.exe", headless=False):
        self.chromedriver = chromedriver
        self.headless = headless
        self.driver = None
        self.wait = None
        
        # 🎯 CÁC SELECTORS ĐƯỢC CUNG CẤP
        self.test_selectors = {
            "button_1": "#mainContent > div > form > div > div > button",
            "element_2": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-2.small-6.medium-4.columns.large-offset-3 > div > label > div", 
            "element_3": "#mainContent > div > div:nth-child(3) > fieldset > div > div.large-4.medium-6.small-12.columns.end > div > label > div.text-center.medium-button-heading"
        }

    def setup_driver(self):
        """Khởi tạo Chrome driver"""
        print("🚀 Đang khởi tạo Chrome driver...")
        
        opts = webdriver.ChromeOptions()
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument('--disable-blink-features=AutomationControlled')
        
        # Extensions nếu có
        try:
            opts.add_extension("driver/captchasolver.crx")
            print("✅ Loaded captcha solver extension")
        except:
            print("⚠️ Captcha solver extension not found")
            
        try:
            opts.add_extension("driver/extract gg from pdf.crx")
            print("✅ Loaded extension extract gg from pdf.crx")
        except:
            print("⚠️ Extension extract gg from pdf.crx not found")
        
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        
        if self.headless:
            opts.add_argument('--headless=new')
            opts.add_argument('--window-size=1920,1080')
            print("🔇 Running in headless mode")
        else:
            opts.add_argument("--start-maximized")
            print("🖥️ Running with browser window")

        self.driver = webdriver.Chrome(service=Service(str(self.chromedriver)), options=opts)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome driver initialized successfully")

    def open_website(self):
        """Mở website Santa Fe College"""
        url = "https://ss2.sfcollege.edu/sr/AdmissionApplication/#/"
        print(f"🌐 Opening website: {url}")
        
        self.driver.get(url)
        print("⏳ Waiting for page to load...")
        time.sleep(5)  # Đợi trang load
        
        # Kiểm tra title
        title = self.driver.title
        print(f"📄 Page title: {title}")
        
        # Kiểm tra URL hiện tại
        current_url = self.driver.current_url
        print(f"🔗 Current URL: {current_url}")

    def test_selector(self, selector_name, selector_value):
        """Test một selector cụ thể"""
        print(f"\n🔍 Testing selector: {selector_name}")
        print(f"📋 Selector value: {selector_value}")
        
        try:
            # Tìm element
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector_value))
            )
            print(f"✅ Element found!")
            
            # Lấy thông tin element
            tag_name = element.tag_name
            text = element.text.strip()
            is_displayed = element.is_displayed()
            is_enabled = element.is_enabled()
            
            print(f"   📌 Tag: {tag_name}")
            print(f"   📝 Text: '{text}'")
            print(f"   👁️ Displayed: {is_displayed}")
            print(f"   🔓 Enabled: {is_enabled}")
            
            # Lấy attributes
            try:
                element_id = element.get_attribute("id")
                element_class = element.get_attribute("class")
                element_type = element.get_attribute("type")
                element_name = element.get_attribute("name")
                
                if element_id:
                    print(f"   🆔 ID: {element_id}")
                if element_class:
                    print(f"   🏷️ Class: {element_class}")
                if element_type:
                    print(f"   🔧 Type: {element_type}")
                if element_name:
                    print(f"   📛 Name: {element_name}")
            except Exception as e:
                print(f"   ⚠️ Error getting attributes: {e}")
            
            # Nếu là button, thử click
            if tag_name.lower() == "button" or element.get_attribute("type") == "button":
                print(f"   🖱️ This is a button - attempting to click...")
                try:
                    # Scroll vào view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    # Thử click
                    element.click()
                    print(f"   ✅ Button clicked successfully!")
                    time.sleep(2)
                    
                except Exception as click_error:
                    print(f"   ❌ Click failed: {click_error}")
            
            return True
            
        except Exception as e:
            print(f"❌ Element not found: {e}")
            return False

    def take_screenshot(self, filename):
        """Chụp ảnh màn hình"""
        try:
            self.driver.save_screenshot(filename)
            print(f"📸 Screenshot saved: {filename}")
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")

    def run_demo(self):
        """Chạy demo test tất cả selectors"""
        print("🎯 SANTA FE COLLEGE - SELECTOR DEMO")
        print("=" * 50)
        
        try:
            # extract gg from pdf. Setup driver
            self.setup_driver()
            
            # 2. Mở website
            self.open_website()
            
            # 3. Chụp ảnh ban đầu
            self.take_screenshot("sf_college_initial.png")
            
            # 4. Test từng selector
            results = {}
            for selector_name, selector_value in self.test_selectors.items():
                success = self.test_selector(selector_name, selector_value)
                results[selector_name] = success
                
                # Chụp ảnh sau mỗi test
                self.take_screenshot(f"sf_college_after_{selector_name}.png")
                
                print(f"{'✅' if success else '❌'} {selector_name}: {'FOUND' if success else 'NOT FOUND'}")
                time.sleep(2)
            
            # 5. Tổng kết
            print("\n" + "=" * 50)
            print("📊 SUMMARY RESULTS:")
            for selector_name, success in results.items():
                status = "✅ WORKING" if success else "❌ FAILED"
                print(f"   {selector_name}: {status}")
            
            # 6. Chụp ảnh cuối
            self.take_screenshot("sf_college_final.png")
            
            print("\n🎉 Demo completed!")
            print("📸 Check screenshots for visual confirmation")
            
        except Exception as e:
            print(f"💥 Demo failed: {e}")
            self.take_screenshot("sf_college_error.png")
        
        finally:
            # Đợi một chút để xem kết quả
            if not self.headless:
                print("\n⏰ Waiting 10 seconds for you to see the browser...")
                time.sleep(10)
            
            self.cleanup()

    def cleanup(self):
        """Dọn dẹp và đóng browser"""
        if self.driver:
            try:
                self.driver.quit()
                print("🧹 Browser closed")
            except:
                pass

def main():
    """Hàm main để chạy demo"""
    print("🚀 Starting Santa Fe College Demo...")
    
    # Hỏi chế độ chạy
    mode = input("Chọn chế độ chạy (extract gg from pdf=Normal, 2=Headless): ").strip()
    headless = mode == "2"
    
    # Tạo demo instance
    demo = SantaFeDemo(headless=headless)
    
    # Chạy demo
    demo.run_demo()

if __name__ == "__main__":
    main() 