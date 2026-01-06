#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GammaPromoTester:
    def __init__(self):
        self.driver = None
        self.valid_codes = []
        self.invalid_codes = []
        self.error_codes = []
        self.processed_count = 0
        self.start_time = datetime.now()

        # Gamma billing URL
        self.gamma_url = "https://billing.gamma.app/c/pay/cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i#fidnandhYHdWcXxpYCc%2FJ3dqcGthJykndnBndmZ3bHVxbGprUGtsdHBga2B2dkBrZGdpYGEnP2NkaXZgKSdkdWxOYHwnPyd1blppbHNgWjA0SFYzdkRANk1HRzB8d01xM2JHYTcyM1ZJMUZCVjduQkJVRDFiblxiY0phTkc2YjxANE1IZFB8akBsNV8xMnY1bTRDU0E0SHBcZF82RHw2N1A0Nn10YE0xNTVLVVZubWlcZicpJ2N3amhWYHdzYHcnP3F3cGApJ2dkZm5id2pwa2FGamlqdyc%2FJyZgY2MyY2MnKSdpZHxqcHFRfHVgJz8naHBpcWxabHFgaCcpJ2BrZGdpYFVpZGZgbWppYWB3dic%2FcXdwYHgl"

    def log(self, message, level="INFO"):
        """Log nhanh với timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "🔵", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "STEP": "🎯"}
        icon = icons.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")

    def setup_driver(self):
        """Thiết lập Chrome driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')

            # Tắt logging để nhanh hơn
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')

            # Đường dẫn Chrome driver
            driver_paths = [
                'driver/chromedriver.exe',
                '../nlu/driver/chromedriver.exe',
                'chromedriver.exe'
            ]

            for driver_path in driver_paths:
                if os.path.exists(driver_path):
                    chrome_service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
                    self.log(f"✅ Đã tạo Chrome driver: {driver_path}", "SUCCESS")
                    return True

            self.log("❌ Không tìm thấy chromedriver.exe", "ERROR")
            return False

        except Exception as e:
            self.log(f"❌ Lỗi tạo Chrome driver: {e}", "ERROR")
            return False

    def close_driver(self):
        """Đóng Chrome driver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except:
            pass

    def smart_wait_and_find(self, selectors, timeout=10, description="element"):
        """Tìm element thông minh"""
        for by, selector in selectors:
            try:
                wait = WebDriverWait(self.driver, timeout // len(selectors))
                element = wait.until(EC.presence_of_element_located((by, selector)))
                if element and element.is_displayed():
                    return element
            except:
                continue
        return None

    def smart_input(self, element, text):
        """Nhập text thông minh"""
        try:
            element.clear()
            element.send_keys(text)
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].value = '';", element)
                element.send_keys(text)
                return True
            except:
                return False

    def smart_click(self, element):
        """Click thông minh"""
        try:
            element.click()
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False

    def wait_for_promo_result(self, timeout=5):
        """Đợi kết quả promo code"""
        time.sleep(2)  # Đợi API response

        # Kiểm tra có alert "This code is invalid" không
        try:
            alert_selectors = [
                (By.XPATH, "//div[contains(text(), 'This code is invalid')]"),
                (By.XPATH, "//div[contains(text(), 'invalid')]"),
                (By.CLASS_NAME, "alert"),
                (By.CSS_SELECTOR, "[role='alert']")
            ]

            alert_element = self.smart_wait_and_find(alert_selectors, timeout=3, description="alert message")
            if alert_element and alert_element.is_displayed():
                alert_text = alert_element.text.lower()
                if 'invalid' in alert_text or 'code is invalid' in alert_text:
                    return False, "Invalid promo code"
        except:
            pass

        # Kiểm tra giá có thay đổi không (nếu có discount)
        try:
            # Tìm element giá
            price_selectors = [
                (By.XPATH, "//span[contains(text(), '₫')]"),
                (By.CSS_SELECTOR, "[data-testid*='price']"),
                (By.CLASS_NAME, "price")
            ]

            price_element = self.smart_wait_and_find(price_selectors, timeout=2, description="price")
            if price_element:
                current_price = price_element.text
                # Nếu giá thay đổi so với ban đầu thì có thể valid
                # (cần implement logic so sánh)
                pass
        except:
            pass

        return True, "Code applied (need manual check)"

    def test_single_promo_code(self, code):
        """Test một promo code"""
        result = {
            "code": code,
            "status": "unknown",
            "description": "",
            "timestamp": datetime.now()
        }

        try:
            # Mở trang Gamma billing
            self.log(f"🌐 Mở trang Gamma billing cho code: {code}", "STEP")
            self.driver.get(self.gamma_url)
            time.sleep(3)

            # Tìm nút "Add code"
            add_code_selectors = [
                (By.XPATH, "//button[contains(text(), 'Add code')]"),
                (By.CSS_SELECTOR, "button[data-testid*='add-code']"),
                (By.ID, "add-code-button")
            ]

            add_code_button = self.smart_wait_and_find(add_code_selectors, timeout=10, description="Add code button")
            if not add_code_button:
                result["status"] = "error"
                result["description"] = "Không tìm thấy nút Add code"
                return result

            self.log("📝 Click nút Add code", "STEP")
            if not self.smart_click(add_code_button):
                result["status"] = "error"
                result["description"] = "Không thể click nút Add code"
                return result

            time.sleep(2)

            # Tìm ô input promo code
            promo_input_selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='promotion code']"),
                (By.CSS_SELECTOR, "input[placeholder*='Add promotion code']"),
                (By.ID, "promotion-code"),
                (By.NAME, "promotion_code")
            ]

            promo_input = self.smart_wait_and_find(promo_input_selectors, timeout=10, description="promo code input")
            if not promo_input:
                result["status"] = "error"
                result["description"] = "Không tìm thấy ô nhập promo code"
                return result

            self.log(f"⌨️ Nhập promo code: {code}", "STEP")
            if not self.smart_input(promo_input, code):
                result["status"] = "error"
                result["description"] = "Không thể nhập promo code"
                return result

            # Tìm nút Apply
            apply_selectors = [
                (By.XPATH, "//button[contains(text(), 'Apply')]"),
                (By.CSS_SELECTOR, "button[data-testid*='apply']"),
                (By.ID, "apply-button")
            ]

            apply_button = self.smart_wait_and_find(apply_selectors, timeout=5, description="Apply button")
            if not apply_button:
                result["status"] = "error"
                result["description"] = "Không tìm thấy nút Apply"
                return result

            self.log("✅ Click nút Apply", "STEP")
            if not self.smart_click(apply_button):
                result["status"] = "error"
                result["description"] = "Không thể click nút Apply"
                return result

            # Đợi và kiểm tra kết quả
            is_valid, description = self.wait_for_promo_result()

            if is_valid:
                result["status"] = "valid"
                result["description"] = description
                self.valid_codes.append(result)
            else:
                result["status"] = "invalid"
                result["description"] = description
                self.invalid_codes.append(result)

            return result

        except Exception as e:
            result["status"] = "error"
            result["description"] = f"Lỗi: {str(e)[:100]}"
            self.error_codes.append(result)
            return result

    def load_promo_codes(self):
        """Tải promo codes từ file"""
        self.log("📚 Tải promo codes từ file...", "STEP")

        try:
            with open("promocode.txt", 'r', encoding='utf-8') as f:
                codes = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            self.log(f"✅ Đã tải {len(codes)} promo codes", "SUCCESS")
            return codes

        except Exception as e:
            self.log(f"❌ Lỗi tải promo codes: {e}", "ERROR")
            return []

    def save_results(self):
        """Lưu kết quả"""
        try:
            # Lưu valid codes
            with open("gamma_valid_codes.txt", "w", encoding="utf-8") as f:
                f.write("# Gamma Promo Codes - VALID\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for code in self.valid_codes:
                    f.write(f"{code['code']}\n")

            # Lưu tất cả kết quả
            with open("gamma_test_results.json", "w", encoding="utf-8") as f:
                results = {
                    "timestamp": datetime.now().isoformat(),
                    "total_tested": self.processed_count,
                    "valid_count": len(self.valid_codes),
                    "invalid_count": len(self.invalid_codes),
                    "error_count": len(self.error_codes),
                    "valid_codes": self.valid_codes,
                    "invalid_codes": self.invalid_codes,
                    "error_codes": self.error_codes
                }
                import json
                json.dump(results, f, indent=2, default=str)

            self.log("💾 Đã lưu kết quả", "SUCCESS")

        except Exception as e:
            self.log(f"Lỗi lưu kết quả: {e}", "ERROR")

    def run_test(self):
        """Chạy test promo codes"""
        print("🚀 GAMMA PROMO CODE TESTER")
        print("="*60)
        print("🌐 Sử dụng Chrome driver để test promo codes")
        print("💡 Mỗi code = Mở trang → Nhập code → Kiểm tra kết quả")
        print("="*60)

        # Khởi tạo driver
        if not self.setup_driver():
            return

        # Tải promo codes
        codes = self.load_promo_codes()
        if not codes:
            self.close_driver()
            return

        total_codes = len(codes)

        try:
            for i, code in enumerate(codes, 1):
                self.processed_count += 1

                # Hiển thị tiến trình
                if i % 5 == 0 or i == 1:
                    elapsed = datetime.now() - self.start_time
                    if elapsed.total_seconds() > 0:
                        speed = self.processed_count / elapsed.total_seconds() * 60
                        eta_minutes = (total_codes - self.processed_count) / (speed / 60) if speed > 0 else 0
                        print(f"⚡ {i}/{total_codes} | ✅{len(self.valid_codes)} ❌{len(self.invalid_codes)} 💥{len(self.error_codes)} | {speed:.1f} codes/phút | ETA: {eta_minutes:.0f}p")

                # Test promo code
                result = self.test_single_promo_code(code)

                if result["status"] == "valid":
                    self.log(f"✅ CODE: {code[:10]}... → VALID", "SUCCESS")
                elif result["status"] == "invalid":
                    self.log(f"❌ CODE: {code[:10]}... → INVALID", "ERROR")
                else:
                    self.log(f"💥 CODE: {code[:10]}... → ERROR: {result['description'][:30]}", "WARNING")

                # Nghỉ giữa các lần test
                time.sleep(2)

            # Lưu kết quả
            self.save_results()

            # Tổng kết
            elapsed = datetime.now() - self.start_time
            speed = total_codes / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0

            print(f"\n{'='*80}")
            self.log("🎉 HOÀN THÀNH KIỂM TRA!", "SUCCESS")
            print("="*80)
            print("📊 TỔNG KẾT CUỐI CÙNG:")
            print(f"   ✅ Valid codes: {len(self.valid_codes)}/{total_codes} ({len(self.valid_codes)/total_codes*100:.1f}%)")
            print(f"   ❌ Invalid codes: {len(self.invalid_codes)}/{total_codes} ({len(self.invalid_codes)/total_codes*100:.1f}%)")
            print(f"   💥 Error codes: {len(self.error_codes)}/{total_codes} ({len(self.error_codes)/total_codes*100:.1f}%)")
            print(f"   ⏱️ Thời gian: {elapsed}")
            print(f"   ⚡ Tốc độ: {speed:.1f} codes/phút")
            print("="*80)
            print("📄 Kết quả: gamma_valid_codes.txt")
            print("📄 Chi tiết: gamma_test_results.json")

        except KeyboardInterrupt:
            self.log("⚠️ Dừng test bởi người dùng", "WARNING")
            self.save_results()
        except Exception as e:
            self.log(f"❌ Lỗi tổng quát: {e}", "ERROR")
        finally:
            self.close_driver()

def main():
    tester = GammaPromoTester()
    tester.run_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")



