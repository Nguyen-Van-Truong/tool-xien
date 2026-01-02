# -*- coding: utf-8 -*-
"""
Verify Handler
Xử lý military verification qua SheerID (từ v9)
"""

import time
import random
import string
from typing import Callable, Dict, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from utils.element_finder import (
    wait_for_element, find_button_by_text, is_visible, 
    wait_for_any_element
)
from utils.click_helper import click_element
from utils.human_behavior import random_delay, human_type


class VerifyHandler:
    """Xử lý SheerID military verification"""
    
    VETERANS_URL = "https://chatgpt.com/veterans-claim"
    SHEERID_DOMAIN = "services.sheerid.com"
    
    # Branch options (như trong SheerID form)
    BRANCHES = [
        "Air Force", "Army", "Coast Guard", 
        "Marine Corps", "National Guard", "Navy", "Space Force"
    ]
    
    def __init__(self, driver: WebDriver, veteran_data: Dict, logger: Callable = None):
        """
        Args:
            driver: Selenium WebDriver
            veteran_data: Dict với keys: first, last, branch, month, day, year
            logger: Log function
        """
        self.driver = driver
        self.data = veteran_data
        self.log = logger or print
        self.temp_email = None
    
    def is_on_sheerid(self) -> bool:
        """Check xem đang ở trang SheerID không"""
        return self.SHEERID_DOMAIN in self.driver.current_url
    
    def is_on_veterans_page(self) -> bool:
        """Check xem đang ở trang veterans-claim không"""
        return "veterans-claim" in self.driver.current_url
    
    def navigate_to_veterans_page(self) -> bool:
        """
        Navigate tới trang veterans-claim
        
        Returns:
            True nếu thành công
        """
        self.log("🌐 Navigating to veterans-claim page...")
        self.driver.get(self.VETERANS_URL)
        random_delay(3, 5)
        
        return self.is_on_veterans_page() or self.is_on_sheerid()
    
    def click_verify_button(self) -> bool:
        """
        Click nút "Verify" trên trang veterans-claim
        
        Returns:
            True nếu thành công
        """
        self.log("🔍 Looking for verify button...")
        random_delay(2, 3)
        
        # Tìm nút verify với nhiều text patterns
        verify_texts = [
            "Xác minh tư cách đủ điều kiện",
            "Xác minh",
            "Verify eligibility",
            "Verify",
            "Claim offer",
        ]
        
        # Try primary button
        try:
            primary_btns = self.driver.find_elements(
                By.CSS_SELECTOR, 'button.btn-primary, button[class*="btn-primary"]'
            )
            for btn in primary_btns:
                if is_visible(btn):
                    btn_text = btn.text or btn.get_attribute("textContent") or ""
                    if any(t.lower() in btn_text.lower() for t in verify_texts):
                        success, method = click_element(self.driver, btn)
                        if success:
                            self.log(f"✅ Clicked verify button ({method})")
                            return self._wait_for_sheerid_redirect()
        except:
            pass
        
        # Fallback: find by text
        verify_btn = find_button_by_text(self.driver, verify_texts)
        
        if verify_btn:
            success, method = click_element(self.driver, verify_btn)
            if success:
                self.log(f"✅ Clicked verify button ({method})")
                return self._wait_for_sheerid_redirect()
        
        self.log("❌ Verify button not found")
        return False
    
    def _wait_for_sheerid_redirect(self, timeout: int = 30) -> bool:
        """
        Đợi redirect tới SheerID
        
        Returns:
            True nếu đã redirect
        """
        self.log("⏳ Waiting for SheerID redirect...")
        
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.is_on_sheerid():
                self.log("✅ Redirected to SheerID")
                random_delay(2, 3)
                return True
            time.sleep(1)
        
        self.log("⚠️ SheerID redirect timeout")
        return False
    
    def generate_temp_email(self) -> Optional[str]:
        """
        Generate temporary email cho verification
        
        Returns:
            Email address hoặc None
        """
        try:
            # Fetch random domains from API
            import requests
            resp = requests.get(
                "https://tinyhost.shop/api/random-domains/?limit=10",
                timeout=10
            )
            if resp.ok:
                domains = resp.json().get("domains", [])
                if domains:
                    domain = random.choice(domains)
                    username = ''.join(
                        random.choices(string.ascii_lowercase + string.digits, k=16)
                    )
                    self.temp_email = f"{username}@{domain}"
                    self.log(f"📧 Generated email: {self.temp_email}")
                    return self.temp_email
        except Exception as e:
            self.log(f"⚠️ Email generation error: {e}")
        
        # Fallback: use random gmail-like
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        self.temp_email = f"{username}@temp-mail.org"
        return self.temp_email
    
    def fill_sheerid_form(self) -> bool:
        """
        Điền form SheerID với veteran data
        
        Returns:
            True nếu thành công
        """
        if not self.is_on_sheerid():
            self.log("❌ Not on SheerID page")
            return False
        
        self.log("📝 Filling SheerID form...")
        random_delay(2, 3)
        
        try:
            # 1. Select Status (Veteran)
            self._select_status("Veteran")
            
            # 2. Fill First Name
            self._fill_input_by_label("First Name", self.data.get("first", ""))
            
            # 3. Fill Last Name  
            self._fill_input_by_label("Last Name", self.data.get("last", ""))
            
            # 4. Select Branch
            self._select_branch(self.data.get("branch", "Army"))
            
            # 5. Fill Date of Birth
            self._fill_dob(
                self.data.get("month", "01"),
                self.data.get("day", "15"),
                self.data.get("year", "1970")
            )
            
            # 6. Generate and fill email
            if not self.temp_email:
                self.generate_temp_email()
            self._fill_input_by_label("Email", self.temp_email)
            
            self.log("✅ Form filled")
            return True
            
        except Exception as e:
            self.log(f"❌ Form fill error: {e}")
            return False
    
    def _select_status(self, status: str) -> bool:
        """Select status dropdown"""
        try:
            # Find status dropdown
            selectors = [
                'select[name*="status" i]',
                'select[id*="status" i]',
                '#status',
            ]
            
            for sel in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if is_visible(elem):
                        Select(elem).select_by_visible_text(status)
                        self.log(f"✅ Selected status: {status}")
                        random_delay(0.5, 0.8)
                        return True
                except:
                    continue
            
            # Try clicking dropdown wrapper
            status_texts = ["Veteran", "Current Service Member", "Select Status"]
            btn = find_button_by_text(self.driver, status_texts, tags=["button", "div", "span"])
            if btn:
                click_element(self.driver, btn)
                random_delay(0.5, 1)
                
                # Click Veteran option
                option = find_button_by_text(self.driver, [status], tags=["div", "li", "span", "button"])
                if option:
                    click_element(self.driver, option)
                    self.log(f"✅ Selected status: {status}")
                    return True
            
            return False
        except Exception as e:
            self.log(f"⚠️ Status select error: {e}")
            return False
    
    def _fill_input_by_label(self, label: str, value: str) -> bool:
        """Điền input theo label"""
        if not value:
            return False
        
        try:
            # Find by placeholder
            placeholder_sels = [
                f'input[placeholder*="{label}" i]',
                f'input[aria-label*="{label}" i]',
            ]
            
            for sel in placeholder_sels:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if is_visible(elem):
                        elem.clear()
                        human_type(elem, value)
                        self.log(f"✅ Filled {label}: {value[:10]}...")
                        random_delay(0.3, 0.5)
                        return True
                except:
                    continue
            
            # Find by label element
            try:
                labels = self.driver.find_elements(By.TAG_NAME, "label")
                for lbl in labels:
                    if label.lower() in (lbl.text or "").lower():
                        for_id = lbl.get_attribute("for")
                        if for_id:
                            input_elem = self.driver.find_element(By.ID, for_id)
                            if is_visible(input_elem):
                                input_elem.clear()
                                human_type(input_elem, value)
                                self.log(f"✅ Filled {label}")
                                return True
            except:
                pass
            
            return False
        except Exception as e:
            self.log(f"⚠️ Fill {label} error: {e}")
            return False
    
    def _select_branch(self, branch: str) -> bool:
        """Select military branch"""
        try:
            # Normalize branch name
            branch_lower = branch.lower()
            for b in self.BRANCHES:
                if branch_lower in b.lower() or b.lower() in branch_lower:
                    branch = b
                    break
            
            # Find dropdown
            selectors = [
                'select[name*="branch" i]',
                'select[id*="branch" i]',
                'select[name*="service" i]',
            ]
            
            for sel in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if is_visible(elem):
                        Select(elem).select_by_visible_text(branch)
                        self.log(f"✅ Selected branch: {branch}")
                        random_delay(0.3, 0.5)
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            self.log(f"⚠️ Branch select error: {e}")
            return False
    
    def _fill_dob(self, month: str, day: str, year: str) -> bool:
        """Fill date of birth (3 dropdowns or 3 inputs)"""
        try:
            # Try dropdowns first
            month_sels = ['select[name*="month" i]', 'select[id*="month" i]']
            day_sels = ['select[name*="day" i]', 'select[id*="day" i]']
            year_sels = ['select[name*="year" i]', 'select[id*="year" i]']
            
            filled = 0
            
            for sel in month_sels:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if is_visible(elem):
                        Select(elem).select_by_value(month)
                        filled += 1
                        break
                except:
                    continue
            
            for sel in day_sels:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if is_visible(elem):
                        Select(elem).select_by_value(day)
                        filled += 1
                        break
                except:
                    continue
            
            for sel in year_sels:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if is_visible(elem):
                        Select(elem).select_by_value(year)
                        filled += 1
                        break
                except:
                    continue
            
            if filled == 3:
                self.log(f"✅ Filled DOB: {month}/{day}/{year}")
                return True
            
            # Try input fields
            dob_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'input[type="text"][maxlength="2"], input[type="text"][maxlength="4"]'
            )
            
            if len(dob_inputs) >= 3:
                dob_inputs[0].clear()
                dob_inputs[0].send_keys(month)
                dob_inputs[1].clear()
                dob_inputs[1].send_keys(day)
                dob_inputs[2].clear()
                dob_inputs[2].send_keys(year)
                self.log(f"✅ Filled DOB inputs")
                return True
            
            return False
        except Exception as e:
            self.log(f"⚠️ DOB fill error: {e}")
            return False
    
    def submit_form(self) -> bool:
        """
        Submit SheerID form và đợi kết quả
        
        Returns:
            True nếu submit thành công
        """
        try:
            submit_texts = [
                "Verify My Military Status",
                "Verify",
                "Submit",
                "Xác minh",
            ]
            
            submit_btn = find_button_by_text(self.driver, submit_texts)
            
            if submit_btn:
                success, method = click_element(self.driver, submit_btn)
                if success:
                    self.log(f"✅ Form submitted ({method})")
                    return True
            
            self.log("❌ Submit button not found")
            return False
            
        except Exception as e:
            self.log(f"❌ Submit error: {e}")
            return False
    
    def check_verification_result(self) -> str:
        """
        Check kết quả verification
        
        Returns:
            'success', 'not_approved', 'vpn_error', 'pending', hoặc 'error'
        """
        try:
            random_delay(3, 5)
            
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text or ""
            current_url = self.driver.current_url
            
            # Check for VPN/proxy errors
            vpn_errors = [
                "sourcesUnavailable",
                "unable to verify you at this time",
                "sources unavailable",
            ]
            if any(e in body_text.lower() or e in current_url.lower() for e in vpn_errors):
                return "vpn_error"
            
            # Check for success
            success_indicators = [
                "verified",
                "success",
                "congratulations",
                "thành công",
            ]
            if any(s in body_text.lower() for s in success_indicators):
                return "success"
            
            # Check for not approved
            fail_indicators = [
                "not approved",
                "không được chấp nhận",
                "verification limit exceeded",
            ]
            if any(f in body_text.lower() for f in fail_indicators):
                return "not_approved"
            
            # Still on form - might need more info
            if self.is_on_sheerid():
                return "pending"
            
            return "error"
            
        except Exception as e:
            self.log(f"⚠️ Result check error: {e}")
            return "error"
    
    def run_verification_flow(self) -> Dict:
        """
        Chạy toàn bộ verification flow
        
        Returns:
            Dict với keys: success, status, message
        """
        try:
            # Step 1: Navigate to veterans page if needed
            if not self.is_on_sheerid():
                if not self.is_on_veterans_page():
                    if not self.navigate_to_veterans_page():
                        return {
                            "success": False,
                            "status": "failed",
                            "message": "Failed to navigate to veterans page"
                        }
                
                # Step 2: Click verify button
                if not self.is_on_sheerid():
                    if not self.click_verify_button():
                        return {
                            "success": False,
                            "status": "failed",
                            "message": "Failed to click verify button"
                        }
            
            # Step 3: Fill SheerID form
            if not self.fill_sheerid_form():
                return {
                    "success": False,
                    "status": "failed", 
                    "message": "Failed to fill SheerID form"
                }
            
            # Step 4: Submit
            if not self.submit_form():
                return {
                    "success": False,
                    "status": "failed",
                    "message": "Failed to submit form"
                }
            
            # Step 5: Check result
            result = self.check_verification_result()
            
            if result == "success":
                return {
                    "success": True,
                    "status": "success",
                    "message": "Verification successful!"
                }
            elif result == "not_approved":
                return {
                    "success": False,
                    "status": "not_approved",
                    "message": "Not approved - try next data"
                }
            elif result == "vpn_error":
                return {
                    "success": False,
                    "status": "vpn_error",
                    "message": "VPN/Proxy error - please change VPN"
                }
            else:
                return {
                    "success": False,
                    "status": "pending",
                    "message": "Verification pending or unknown state"
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": str(e)
            }
