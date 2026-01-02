# -*- coding: utf-8 -*-
"""
State-based Signup Handler
Xử lý signup với state machine, tự detect page state và retry khi lỗi
"""

import time
from typing import Callable, Dict, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.page_state import PageState, PageStateDetector
from utils.element_finder import wait_for_element, find_button_by_text, is_visible
from utils.click_helper import click_element
from utils.human_behavior import random_delay, human_type
from email_otp_handler import get_otp_from_email


class StateBasedSignupHandler:
    """
    Signup handler với state machine
    - Liên tục check trạng thái trang
    - Xác định đang ở bước nào
    - Retry khi lỗi (chờ 10s rồi thử lại)
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY = 10  # seconds
    MAX_STEPS = 20  # Tránh infinite loop
    
    def __init__(self, driver: WebDriver, account: Dict, logger: Callable = None):
        self.driver = driver
        self.account = account
        self.log = logger or print
        self.state_detector = PageStateDetector(driver, logger)
        self.step_count = 0
        self.retries = 0
    
    def run_signup(self) -> Dict:
        """
        Chạy signup flow với state machine
        
        Returns:
            Dict với success, status, message
        """
        self.step_count = 0
        
        while self.step_count < self.MAX_STEPS:
            self.step_count += 1
            
            # Detect current state
            state, description = self.state_detector.detect()
            self.log(f"📍 Step {self.step_count}: {state.value} - {description}")
            
            # Handle based on state
            try:
                result = self._handle_state(state)
                
                if result.get('done'):
                    return result
                
                if result.get('error'):
                    # Retry logic
                    self.retries += 1
                    if self.retries >= self.MAX_RETRIES:
                        return {
                            'success': False,
                            'status': 'failed',
                            'message': f"Max retries exceeded at state: {state.value}"
                        }
                    
                    self.log(f"⚠️ Error, waiting {self.RETRY_DELAY}s before retry ({self.retries}/{self.MAX_RETRIES})...")
                    time.sleep(self.RETRY_DELAY)
                    continue
                
                # Success - reset retries
                self.retries = 0
                
                # Small delay between steps
                random_delay(1, 2)
                
            except Exception as e:
                self.log(f"❌ Exception at step {self.step_count}: {e}")
                self.retries += 1
                if self.retries >= self.MAX_RETRIES:
                    return {
                        'success': False,
                        'status': 'failed',
                        'message': str(e)
                    }
                self.log(f"⏳ Waiting {self.RETRY_DELAY}s before retry...")
                time.sleep(self.RETRY_DELAY)
        
        return {
            'success': False,
            'status': 'failed',
            'message': 'Max steps exceeded'
        }
    
    def _handle_state(self, state: PageState) -> Dict:
        """
        Xử lý theo state hiện tại
        
        Returns:
            Dict với done=True nếu hoàn thành, error=True nếu lỗi
        """
        
        if state == PageState.CHATGPT_LOGGED_IN:
            self.log("✅ Already logged in!")
            return {'done': True, 'success': True, 'status': 'exists', 'message': 'Already logged in'}
        
        elif state == PageState.CHATGPT_HOME or state == PageState.SIGNUP_FORM:
            # Click signup button
            return self._handle_signup_click()
        
        elif state == PageState.EMAIL_FORM:
            # Fill email
            return self._handle_email_form()
        
        elif state == PageState.PASSWORD_FORM:
            # Fill password
            return self._handle_password_form()
        
        elif state == PageState.OTP_PAGE:
            # Handle OTP
            return self._handle_otp_page()
        
        elif state == PageState.ABOUT_YOU:
            # Fill about you
            return self._handle_about_you()
        
        elif state == PageState.UNKNOWN:
            # Wait and retry
            self.log("⚠️ Unknown state, waiting...")
            random_delay(2, 3)
            return {'error': True}
        
        else:
            self.log(f"ℹ️ Unhandled state: {state.value}")
            return {'error': True}
    
    def _handle_signup_click(self) -> Dict:
        """Click nút Sign up"""
        self.log("🔍 Looking for Sign up button...")
        
        signup_texts = ["Sign up for free", "Sign up", "Get started"]
        signup_btn = find_button_by_text(self.driver, signup_texts)
        
        if signup_btn:
            success, method = click_element(self.driver, signup_btn)
            if success:
                self.log(f"✅ Clicked signup button ({method})")
                random_delay(2, 3)
                return {}  # Continue to next state
        
        self.log("⚠️ Signup button not found")
        return {'error': True}
    
    def _handle_email_form(self) -> Dict:
        """Điền email form"""
        self.log(f"📝 Filling email: {self.account['email']}")
        
        email_selectors = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[autocomplete="email"]',
        ]
        
        email_input = None
        for sel in email_selectors:
            email_input = wait_for_element(self.driver, sel, timeout=10)
            if email_input:
                break
        
        if not email_input:
            self.log("⚠️ Email input not found")
            return {'error': True}
        
        # Type email
        email_input.clear()
        human_type(email_input, self.account['email'])
        
        # Trigger events
        self.driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
        """, email_input)
        
        random_delay(1, 1.5)
        
        # Click Continue
        if self._click_continue_button():
            self.log("✅ Email submitted")
            random_delay(2, 3)
            return {}
        
        # Fallback - Enter key
        email_input.send_keys(Keys.ENTER)
        self.log("✅ Email submitted (Enter)")
        random_delay(2, 3)
        return {}
    
    def _handle_password_form(self) -> Dict:
        """Điền password form"""
        self.log("📝 Filling password...")
        
        password_input = wait_for_element(self.driver, 'input[type="password"]', timeout=10)
        
        if not password_input:
            self.log("⚠️ Password input not found")
            return {'error': True}
        
        # Type password
        password_input.clear()
        human_type(password_input, self.account['password'])
        
        random_delay(1, 1.5)
        
        # Click Continue
        if self._click_continue_button():
            self.log("✅ Password submitted")
            random_delay(3, 4)
            return {}
        
        # Fallback
        password_input.send_keys(Keys.ENTER)
        self.log("✅ Password submitted (Enter)")
        random_delay(3, 4)
        return {}
    
    def _handle_otp_page(self) -> Dict:
        """
        Xử lý OTP page với logic:
        1. Chờ 10s cho email đến
        2. Lấy OTP
        3. Nhập OTP
        4. Check kết quả - nếu lỗi thì click Resend và thử lại
        """
        MAX_OTP_ATTEMPTS = 3
        
        for attempt in range(MAX_OTP_ATTEMPTS):
            self.log(f"📧 OTP attempt {attempt + 1}/{MAX_OTP_ATTEMPTS}")
            
            # Step 1: Wait 10s for email to arrive
            self.log("⏳ Waiting 10s for email to arrive...")
            time.sleep(10)
            
            # Step 2: Get OTP from email
            self.log("🌐 Getting OTP from email...")
            otp = get_otp_from_email(
                email_login=self.account.get('emailLogin', self.account['email']),
                email_password=self.account.get('passEmail', self.account['password']),
                refresh_token=self.account.get('refreshToken', ''),
                client_id=self.account.get('clientId', '')
            )
            
            if not otp:
                self.log("⚠️ Failed to get OTP")
                # Click resend and try again
                if attempt < MAX_OTP_ATTEMPTS - 1:
                    self._click_resend_email()
                continue
            
            self.log(f"✅ Got OTP: {otp}")
            
            # Step 3: Enter OTP
            entered = self._enter_otp(otp)
            if not entered:
                self.log("⚠️ Failed to enter OTP")
                continue
            
            # Step 4: Wait and check result
            time.sleep(3)
            
            # Check for errors
            error_detected = self._check_otp_error()
            
            if error_detected:
                self.log("❌ OTP incorrect, clicking Resend...")
                # Click resend
                if attempt < MAX_OTP_ATTEMPTS - 1:
                    self._click_resend_email()
                continue
            
            # Check if we moved to next page
            new_state, _ = self.state_detector.detect()
            
            if new_state != PageState.OTP_PAGE:
                self.log(f"✅ OTP accepted! Moved to: {new_state.value}")
                return {}  # Success
            
            # Still on OTP page - might need more time
            time.sleep(2)
            new_state, _ = self.state_detector.detect()
            if new_state != PageState.OTP_PAGE:
                return {}
        
        self.log("❌ All OTP attempts failed")
        return {'error': True}
    
    def _enter_otp(self, otp: str) -> bool:
        """Nhập OTP vào các ô input"""
        try:
            # Try individual boxes (6 boxes)
            boxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"][maxlength="1"]')
            if len(boxes) >= 6:
                for i, digit in enumerate(otp[:6]):
                    if i < len(boxes):
                        boxes[i].clear()
                        boxes[i].send_keys(digit)
                        time.sleep(0.1)
                self.log("✅ OTP entered in boxes")
                return True
        except Exception as e:
            self.log(f"⚠️ Error entering OTP in boxes: {e}")
        
        # Try single input
        otp_selectors = [
            'input[name*="code"]', 
            'input[autocomplete="one-time-code"]',
            'input[type="text"]'
        ]
        for sel in otp_selectors:
            try:
                otp_input = self.driver.find_element(By.CSS_SELECTOR, sel)
                if otp_input and is_visible(otp_input):
                    otp_input.clear()
                    human_type(otp_input, otp)
                    otp_input.send_keys(Keys.ENTER)
                    self.log("✅ OTP submitted in single input")
                    return True
            except:
                continue
        
        return False
    
    def _check_otp_error(self) -> bool:
        """Check nếu có lỗi OTP (incorrect code, expired, etc.)"""
        try:
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            
            error_indicators = [
                'incorrect code',
                'invalid code',
                'wrong code',
                'code is invalid',
                'code has expired',
                'expired', 
                'try again'
            ]
            
            for indicator in error_indicators:
                if indicator in body_text:
                    self.log(f"⚠️ Error detected: {indicator}")
                    return True
            
            return False
        except:
            return False
    
    def _click_resend_email(self) -> bool:
        """Click nút Resend email"""
        try:
            self.log("🔄 Clicking Resend email...")
            
            resend_selectors = [
                (By.XPATH, "//button[contains(text(), 'Resend')]"),
                (By.XPATH, "//a[contains(text(), 'Resend')]"),
                (By.XPATH, "//*[contains(text(), 'Resend email')]"),
                (By.XPATH, "//*[contains(text(), 'Send again')]"),
            ]
            
            for by, selector in resend_selectors:
                try:
                    element = self.driver.find_element(by, selector)
                    if element and element.is_displayed():
                        success, _ = click_element(self.driver, element)
                        if success:
                            self.log("✅ Clicked Resend")
                            time.sleep(2)  # Wait for resend
                            return True
                except:
                    continue
            
            self.log("⚠️ Resend button not found")
            return False
        except Exception as e:
            self.log(f"⚠️ Resend error: {e}")
            return False
    
    def _handle_about_you(self) -> Dict:
        """Điền About You page"""
        self.log("📝 Filling About You page...")
        
        try:
            name_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            
            for inp in name_inputs:
                if not is_visible(inp):
                    continue
                if inp.get_attribute('value'):
                    continue
                
                placeholder = (inp.get_attribute('placeholder') or '').lower()
                
                if 'first' in placeholder or 'name' in placeholder:
                    human_type(inp, self.account.get('first', 'User'))
                    random_delay(0.3, 0.5)
                elif 'last' in placeholder:
                    human_type(inp, self.account.get('last', 'Test'))
                    random_delay(0.3, 0.5)
            
            random_delay(1, 2)
            
            # Click Continue
            self._click_continue_button()
            self.log("✅ About You completed")
            random_delay(2, 3)
            return {}
            
        except Exception as e:
            self.log(f"⚠️ About You error: {e}")
            return {}  # Non-critical, continue
    
    def _click_continue_button(self) -> bool:
        """Click Continue button với V10 style selectors"""
        try:
            wait = WebDriverWait(self.driver, 5)
            
            selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, "//button[contains(., 'Continue')]"),
                (By.CSS_SELECTOR, 'button[data-dd-action-name="Continue"]'),
            ]
            
            for by, selector in selectors:
                try:
                    button = wait.until(EC.element_to_be_clickable((by, selector)))
                    if button and not button.get_attribute('disabled'):
                        btn_text = (button.text or '').lower()
                        # Skip social login buttons
                        if any(x in btn_text for x in ['google', 'microsoft', 'apple']):
                            continue
                        
                        success, _ = click_element(self.driver, button, scroll_first=False)
                        if success:
                            return True
                except:
                    continue
            
            return False
        except:
            return False
