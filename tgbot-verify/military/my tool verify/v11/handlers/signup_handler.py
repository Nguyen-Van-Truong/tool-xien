# -*- coding: utf-8 -*-
"""
Signup Handler
Xử lý signup flow: Email, Password, OTP, About You
"""

import time
from typing import Callable, Dict, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.element_finder import wait_for_element, find_button_by_text, is_visible
from utils.click_helper import click_element
from utils.human_behavior import random_delay, human_type
from email_otp_handler import get_otp_from_email


class SignupHandler:
    """Xử lý signup flow"""
    
    def __init__(self, driver: WebDriver, account: Dict, logger: Callable = None):
        self.driver = driver
        self.account = account
        self.log = logger or print
    
    def fill_email(self) -> bool:
        """
        Điền email và click Continue
        
        Returns:
            True nếu thành công
        """
        try:
            email_selectors = [
                'input[type="email"]',
                'input[name*="email" i]',
                'input[placeholder*="email" i]',
                'input[id*="email" i]',
            ]
            
            email_input = None
            for sel in email_selectors:
                email_input = wait_for_element(self.driver, sel, timeout=10)
                if email_input:
                    break
            
            if not email_input:
                self.log("❌ Email input not found")
                return False
            
            self.log(f"📝 Typing email: {self.account['email']}")
            
            # Clear và type
            email_input.clear()
            human_type(email_input, self.account['email'])
            
            # Trigger events
            self.driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """, email_input)
            
            random_delay(0.5, 1)
            
            # Click Continue button
            continue_texts = ["Continue", "Next", "Tiếp tục"]
            continue_btn = find_button_by_text(self.driver, continue_texts)
            
            if continue_btn:
                success, _ = click_element(self.driver, continue_btn)
                if success:
                    self.log("✅ Email submitted")
                    return True
            
            # Try Enter key
            email_input.send_keys(Keys.ENTER)
            self.log("✅ Email submitted (Enter key)")
            return True
            
        except Exception as e:
            self.log(f"❌ Email error: {e}")
            return False
    
    def fill_password(self) -> bool:
        """
        Điền password và click Continue
        
        Returns:
            True nếu thành công
        """
        try:
            random_delay(2, 3)
            
            password_input = wait_for_element(
                self.driver, 
                'input[type="password"]',
                timeout=15
            )
            
            if not password_input:
                self.log("❌ Password input not found")
                return False
            
            self.log("📝 Typing password...")
            
            password_input.clear()
            human_type(password_input, self.account['password'])
            
            random_delay(0.5, 1)
            
            # Click Continue
            continue_texts = ["Continue", "Next", "Log in", "Sign up"]
            continue_btn = find_button_by_text(self.driver, continue_texts)
            
            if continue_btn:
                success, _ = click_element(self.driver, continue_btn)
                if success:
                    self.log("✅ Password submitted")
                    return True
            
            password_input.send_keys(Keys.ENTER)
            self.log("✅ Password submitted (Enter key)")
            return True
            
        except Exception as e:
            self.log(f"❌ Password error: {e}")
            return False
    
    def handle_otp(self) -> bool:
        """
        Xử lý OTP verification
        
        Returns:
            True nếu thành công
        """
        try:
            self.log("📧 Waiting for OTP email...")
            random_delay(5, 8)  # Wait for email
            
            # Get OTP from email API
            otp = get_otp_from_email(
                email_login=self.account.get('emailLogin', self.account['email']),
                email_password=self.account.get('passEmail', self.account['password']),
                refresh_token=self.account.get('refreshToken', ''),
                client_id=self.account.get('clientId', '')
            )
            
            if not otp:
                self.log("❌ Failed to get OTP")
                return False
            
            self.log(f"✅ Got OTP: {otp}")
            
            # Find OTP input(s)
            otp_selectors = [
                'input[name*="code"]',
                'input[type="text"][maxlength="1"]',
                'input[type="text"][autocomplete="one-time-code"]',
                'input[id*="otp"]',
            ]
            
            # Try individual input boxes (6 boxes)
            try:
                otp_boxes = self.driver.find_elements(
                    By.CSS_SELECTOR, 'input[type="text"][maxlength="1"]'
                )
                if len(otp_boxes) >= 6:
                    for i, digit in enumerate(otp[:6]):
                        if i < len(otp_boxes):
                            otp_boxes[i].send_keys(digit)
                            random_delay(0.1, 0.2)
                    self.log("✅ OTP entered in individual boxes")
                    return True
            except:
                pass
            
            # Try single input
            for sel in otp_selectors:
                try:
                    otp_input = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if otp_input and is_visible(otp_input):
                        human_type(otp_input, otp)
                        
                        # Click verify button
                        verify_texts = ["Verify", "Submit", "Continue"]
                        verify_btn = find_button_by_text(self.driver, verify_texts)
                        if verify_btn:
                            click_element(self.driver, verify_btn)
                        else:
                            otp_input.send_keys(Keys.ENTER)
                        
                        self.log("✅ OTP submitted")
                        return True
                except:
                    continue
            
            self.log("❌ Could not enter OTP")
            return False
            
        except Exception as e:
            self.log(f"❌ OTP error: {e}")
            return False
    
    def fill_about_you(self) -> bool:
        """
        Điền trang "About You" (tên, ngày sinh, etc.)
        
        Returns:
            True nếu thành công
        """
        try:
            random_delay(2, 3)
            
            # Check if on About You page
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text or ""
            
            if not any(x in body_text for x in ['Tell us about you', 'About you', 'Về bạn']):
                self.log("ℹ️ Not on About You page")
                return True  # Skip - not required
            
            self.log("📝 Filling About You page...")
            
            # Fill name inputs
            name_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, 'input[type="text"]:not([type="email"])'
            )
            
            if name_inputs:
                for inp in name_inputs:
                    if is_visible(inp) and not inp.get_attribute('value'):
                        placeholder = (inp.get_attribute('placeholder') or '').lower()
                        
                        if 'first' in placeholder or 'name' in placeholder:
                            human_type(inp, self.account.get('first', 'User'))
                        elif 'last' in placeholder:
                            human_type(inp, self.account.get('last', 'Test'))
                        
                        random_delay(0.3, 0.5)
            
            # Click Continue
            random_delay(1, 2)
            continue_btn = find_button_by_text(self.driver, ["Continue", "Next", "Submit"])
            if continue_btn:
                click_element(self.driver, continue_btn)
                self.log("✅ About You completed")
            
            return True
            
        except Exception as e:
            self.log(f"⚠️ About You error: {e}")
            return True  # Non-critical
