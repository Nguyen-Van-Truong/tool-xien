# -*- coding: utf-8 -*-
"""
V11 Multi-Profile Login Tool - Signup Automation
Logic tự động hóa đăng ký/đăng nhập ChatGPT
"""

import time
import random
import re
from datetime import datetime
from typing import Callable, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config
from email_otp_handler import EmailOTPHandler


class SignupAutomation:
    """Class tự động hóa signup/login ChatGPT"""
    
    def __init__(self, driver: webdriver.Chrome, account: dict, 
                 logger: Callable = None, instance_id: int = 0):
        """
        Args:
            driver: Selenium WebDriver
            account: Dict chứa thông tin account:
                - email: Email ChatGPT
                - password: Password ChatGPT
                - emailLogin: Email login (để lấy OTP)
                - passEmail: Password email
                - refreshToken: Refresh token
                - clientId: Client ID
            logger: Function để log
            instance_id: ID của browser instance
        """
        self.driver = driver
        self.account = account
        self.logger = logger or print
        self.instance_id = instance_id
        self.otp_handler = EmailOTPHandler(logger=self._log_raw)
    
    def _log_raw(self, message: str):
        """Raw log without formatting"""
        self.logger(message)
    
    def log(self, message: str, level: str = "info"):
        """Log với instance ID"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logger(f"[{timestamp}] [Browser {self.instance_id}] [{level.upper()}] {message}")
    
    def human_delay(self, min_delay: float = None, max_delay: float = None):
        """Random delay để giống người thật"""
        min_d = min_delay or config.HUMAN_DELAY_MIN
        max_d = max_delay or config.HUMAN_DELAY_MAX
        time.sleep(random.uniform(min_d, max_d))
    
    def human_type(self, element, text: str):
        """Gõ text với human-like delay giữa các ký tự"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(
                config.TYPING_DELAY_MIN, 
                config.TYPING_DELAY_MAX
            ))
    
    def run_signup_flow(self) -> dict:
        """
        Chạy toàn bộ flow signup/login
        
        Returns:
            dict with keys:
                - success: bool
                - status: 'success' | 'exists' | 'failed'
                - message: str
        """
        try:
            # Step 0: Maximize window for fullscreen operation
            try:
                self.driver.maximize_window()
                self.log("🪟 Window maximized for fullscreen")
            except:
                pass
            
            # Step 1: Navigate to ChatGPT
            self.log("🌐 Navigating to ChatGPT...")
            self.driver.get(config.CHATGPT_URL)
            self.human_delay(3, 5)
            
            # Simulate human behavior
            self._simulate_human_scroll()
            
            # Step 2: Check if already logged in - IMPROVED DETECTION
            login_status = self._check_login_status()
            self.log(f"🔍 Login status: {login_status}")
            
            if login_status == 'logged_in':
                self.log("✅ Already logged in!", "success")
                return {'success': True, 'status': 'exists', 'message': 'Already logged in'}
            
            # Step 3: Click Sign Up button
            self.log("🔍 Looking for Sign up button...")
            if not self._click_signup_button():
                return {'success': False, 'status': 'failed', 'message': 'Sign up button not found'}
            
            self.human_delay(2, 3)
            
            # Step 4: Fill email
            self.log(f"📧 Filling email: {self.account['email']}")
            if not self._fill_email():
                return {'success': False, 'status': 'failed', 'message': 'Failed to fill email'}
            
            self.human_delay(2, 3)
            
            # Step 5: Check current URL and handle accordingly
            current_url = self.driver.current_url
            self.log(f"🔍 Current URL: {current_url[:60]}...")
            
            # Case: On OTP verification page
            if 'email-verification' in current_url or 'verify' in current_url.lower():
                self.log("📧 On OTP verification page")
                return self._handle_otp_flow()
            
            # Case: On password page
            if 'password' in current_url:
                is_login = 'log-in' in current_url
                self.log(f"🔐 On {'LOGIN' if is_login else 'SIGNUP'} password page")
                
                if not self._fill_password():
                    return {'success': False, 'status': 'failed', 'message': 'Failed to fill password'}
                
                self.human_delay(2, 3)
                
                # After password, check for OTP or success
                current_url = self.driver.current_url
                
                if 'email-verification' in current_url:
                    return self._handle_otp_flow()
                elif self._check_login_status() == 'logged_in':
                    return {'success': True, 'status': 'exists' if is_login else 'success', 
                            'message': 'Login successful' if is_login else 'Signup successful'}
            
            # Case: On About You page
            if 'about-you' in self.driver.current_url:
                self.log("📝 On About You page")
                if not self._fill_about_you():
                    return {'success': False, 'status': 'failed', 'message': 'Failed to fill About You'}
                self.human_delay(3, 5)
            
            # Final check
            return self._check_final_status()
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Error: {error_msg}", "error")
            return {'success': False, 'status': 'failed', 'message': error_msg}
    
    def _simulate_human_scroll(self):
        """Scroll như người thật"""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(random.uniform(0.5, 1))
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.3, 0.7))
        except:
            pass
    
    def _check_login_status(self) -> str:
        """
        Check login status theo logic như v10
        V10: Check for BOTH prompt-textarea AND sidebar to confirm logged in
        ChatGPT shows textarea even when not logged in (for demo), but sidebar only when logged in
        
        Returns:
            'logged_in' - Đã đăng nhập
            'not_logged_in' - Chưa đăng nhập
        """
        try:
            # V10 Logic: Check for BOTH textarea AND sidebar
            has_textarea = False
            has_sidebar = False
            
            # Check textarea
            try:
                textarea = self.driver.find_element(By.ID, "prompt-textarea")
                if textarea and textarea.is_displayed():
                    has_textarea = True
            except:
                pass
            
            # Check sidebar - QUAN TRỌNG: chỉ có khi đã login
            try:
                sidebar_selectors = [
                    '[data-testid="sidebar"]',
                    'nav[aria-label="Chat history"]',
                    '[class*="sidebar"]',
                    'div[class*="conversation-sidebar"]'
                ]
                for sel in sidebar_selectors:
                    try:
                        sidebar = self.driver.find_element(By.CSS_SELECTOR, sel)
                        if sidebar and sidebar.is_displayed():
                            has_sidebar = True
                            break
                    except:
                        continue
            except:
                pass
            
            self.log(f"🔍 Login check: Textarea={has_textarea}, Sidebar={has_sidebar}")
            
            # Phải có CẢ HAI mới coi là logged in (như v10)
            if has_textarea and has_sidebar:
                self.log("✅ Both textarea AND sidebar found = Already logged in")
                return 'logged_in'
            
            # Nếu có textarea nhưng không có sidebar = chưa login (có thể là demo mode)
            if has_textarea and not has_sidebar:
                self.log("ℹ️ Textarea found but NO sidebar = Not logged in (demo mode)")
                return 'not_logged_in'
            
            # Không có textarea = chưa login  
            return 'not_logged_in'
            
        except Exception as e:
            self.log(f"⚠️ Error checking login status: {e}", "warning")
            return 'not_logged_in'
    
    def _is_logged_in(self) -> bool:
        """Check xem đã login chưa (wrapper function)"""
        return self._check_login_status() == 'logged_in'
    
    def _click_signup_button(self) -> bool:
        """Tìm và click nút Sign up - giống extension v9"""
        try:
            # Wait a bit for page to load
            time.sleep(2)
            
            # Check if email form already visible
            email_selectors = [
                'input[type="email"]',
                'input[name*="email" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email address" i]'
            ]
            
            for selector in email_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if elem and elem.is_displayed():
                        self.log("ℹ️ Email form already visible")
                        return True
                except:
                    continue
            
            # Find Sign up button - giống v9 extension
            self.log("🔍 Looking for Sign up for free button...")
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            all_elements = all_buttons + all_links
            
            signup_btn = None
            
            # Cách 1: Tìm theo text "Sign up for free" (ưu tiên)
            for elem in all_elements:
                try:
                    if not elem.is_displayed():
                        continue
                    
                    text = (elem.text or elem.get_attribute("textContent") or "").lower()
                    
                    if 'sign up for free' in text:
                        signup_btn = elem
                        self.log("✅ Found 'Sign up for free' button")
                        break
                except:
                    continue
            
            # Cách 2: Tìm theo text "Sign up"
            if not signup_btn:
                for elem in all_elements:
                    try:
                        if not elem.is_displayed():
                            continue
                        
                        text = (elem.text or elem.get_attribute("textContent") or "").lower()
                        
                        if 'sign up' in text or 'signup' in text:
                            signup_btn = elem
                            self.log("✅ Found 'Sign up' button")
                            break
                    except:
                        continue
            
            # Cách 3: Try by href
            if not signup_btn:
                for elem in all_links:
                    try:
                        if not elem.is_displayed():
                            continue
                        href = elem.get_attribute("href") or ""
                        if 'signup' in href.lower() or 'register' in href.lower():
                            signup_btn = elem
                            self.log("✅ Found signup link by href")
                            break
                    except:
                        continue
            
            if signup_btn:
                self.log("✅ Found Sign up button, clicking...")
                
                # Scroll to button
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                    signup_btn
                )
                self.human_delay(0.8, 1.5)
                
                # Simulate mouse hover
                try:
                    ActionChains(self.driver).move_to_element(signup_btn).pause(0.3).perform()
                except:
                    pass
                
                # Try multiple click methods (like v10)
                clicked = False
                click_errors = []
                
                # Method 1: ActionChains with mouse movement (most human-like)
                try:
                    ActionChains(self.driver).move_to_element(signup_btn).pause(0.2).click().perform()
                    clicked = True
                    self.log("✅ Clicked using ActionChains (human-like)", "success")
                except Exception as e1:
                    click_errors.append(f"ActionChains: {e1}")
                
                # Method 2: JavaScript with mouse events (simulate real click)
                if not clicked:
                    try:
                        self.driver.execute_script("""
                            var element = arguments[0];
                            var rect = element.getBoundingClientRect();
                            var x = rect.left + rect.width / 2;
                            var y = rect.top + rect.height / 2;
                            
                            var mouseDown = new MouseEvent('mousedown', {
                                view: window, bubbles: true, cancelable: true,
                                clientX: x, clientY: y
                            });
                            var mouseUp = new MouseEvent('mouseup', {
                                view: window, bubbles: true, cancelable: true,
                                clientX: x, clientY: y
                            });
                            var click = new MouseEvent('click', {
                                view: window, bubbles: true, cancelable: true,
                                clientX: x, clientY: y
                            });
                            
                            element.dispatchEvent(mouseDown);
                            element.dispatchEvent(mouseUp);
                            element.dispatchEvent(click);
                        """, signup_btn)
                        time.sleep(0.2)
                        clicked = True
                        self.log("✅ Clicked using mouse events", "success")
                    except Exception as e2:
                        click_errors.append(f"Mouse events: {e2}")
                
                # Method 3: Regular click (fallback)
                if not clicked:
                    try:
                        signup_btn.click()
                        clicked = True
                        self.log("✅ Clicked using regular click()", "success")
                    except Exception as e3:
                        click_errors.append(f"Regular click: {e3}")
                
                # Method 4: Simple JavaScript click (last resort)                
                if not clicked:
                    try:
                        self.driver.execute_script("arguments[0].click();", signup_btn)
                        clicked = True
                        self.log("✅ Clicked using JavaScript", "success")
                    except Exception as e4:
                        click_errors.append(f"JS click: {e4}")
                
                if not clicked:
                    self.log(f"⚠️ All click methods failed: {click_errors}", "warning")
                    return False
                
                # Wait for email form to appear
                self.log("⏳ Waiting for email form...")
                time.sleep(3)
                
                max_attempts = 10
                for attempt in range(max_attempts):
                    # Check URL change
                    current_url = self.driver.current_url.lower()
                    if any(x in current_url for x in ['signup', 'auth', 'email']):
                        self.log("✅ URL changed to auth page")
                        return True
                    
                    for selector in email_selectors:
                        try:
                            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if elem and elem.is_displayed():
                                self.log("✅ Email form appeared")
                                return True
                        except:
                            continue
                    time.sleep(1)
                
                self.log("⚠️ Email form did not appear, but continuing...", "warning")
                return True
            
            self.log("❌ Sign up button not found", "error")
            return False
            
        except Exception as e:
            self.log(f"❌ Error clicking signup: {e}", "error")
            return False
    
    def _fill_email(self) -> bool:
        """Điền email và click Continue"""
        try:
            # Wait for email input
            email_input = WebDriverWait(self.driver, config.ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    'input[type="email"], input[name*="email" i], input[placeholder*="email" i]'))
            )
            
            self.log(f"📝 Typing email: {self.account['email']}")
            
            # Human-like typing
            self.human_type(email_input, self.account['email'])
            
            # Trigger events
            email_input.send_keys("")  # Focus
            self.driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """, email_input)
            
            self.human_delay(0.5, 1)
            
            # Find and click Continue button
            continue_btn = self._find_continue_button()
            if continue_btn:
                self.log("✅ Clicking Continue...")
                
                # Wait for button to be enabled
                max_wait = 10
                for _ in range(max_wait):
                    if not continue_btn.get_attribute("disabled"):
                        break
                    time.sleep(0.5)
                
                try:
                    ActionChains(self.driver).move_to_element(continue_btn).pause(0.2).click().perform()
                except:
                    continue_btn.click()
                
                self.log("✅ Email submitted", "success")
                return True
            
            self.log("❌ Continue button not found", "error")
            return False
            
        except Exception as e:
            self.log(f"❌ Error filling email: {e}", "error")
            return False
    
    def _fill_password(self) -> bool:
        """Điền password và click Continue"""
        try:
            # Wait for password input
            password_input = WebDriverWait(self.driver, config.ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    'input[type="password"], input[name*="password" i]'))
            )
            
            self.log(f"🔐 Typing password...")
            
            # Human-like typing
            self.human_type(password_input, self.account['password'])
            
            # Trigger events
            self.driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """, password_input)
            
            self.human_delay(0.5, 1)
            
            # Find and click Continue
            continue_btn = self._find_continue_button()
            if continue_btn:
                self.log("✅ Clicking Continue...")
                
                max_wait = 10
                for _ in range(max_wait):
                    if not continue_btn.get_attribute("disabled"):
                        break
                    time.sleep(0.5)
                
                try:
                    ActionChains(self.driver).move_to_element(continue_btn).pause(0.2).click().perform()
                except:
                    continue_btn.click()
                
                self.log("✅ Password submitted", "success")
                return True
            
            self.log("❌ Continue button not found after password", "error")
            return False
            
        except Exception as e:
            self.log(f"❌ Error filling password: {e}", "error")
            return False
    
    def _find_continue_button(self):
        """Tìm nút Continue/Submit"""
        selectors = [
            'button[data-dd-action-name="Continue"]',
            'button[type="submit"]',
            'button[class*="_primary"]',
        ]
        
        for selector in selectors:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if btn and btn.is_displayed():
                    return btn
            except:
                continue
        
        # Find by text
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for btn in all_buttons:
            try:
                text = (btn.text or "").upper().strip()
                if text == "CONTINUE" or "CONTINUE" in text:
                    return btn
            except:
                continue
        
        return None
    
    def _handle_otp_flow(self) -> dict:
        """Xử lý OTP verification"""
        self.log("📧 Waiting for OTP email...")
        time.sleep(10)  # Wait for email to be sent
        
        # Get OTP
        otp_result = self.otp_handler.get_otp_with_retry(
            email_login=self.account.get('emailLogin', self.account['email']),
            email_password=self.account.get('passEmail', self.account['password']),
            refresh_token=self.account.get('refreshToken', ''),
            client_id=self.account.get('clientId', '')
        )
        
        if not otp_result['success']:
            return {'success': False, 'status': 'failed', 
                    'message': f"OTP failed: {otp_result['message']}"}
        
        otp = otp_result['otp']
        self.log(f"✅ Got OTP: {otp}", "success")
        
        # Fill OTP
        try:
            # Find OTP inputs (6 separate inputs or one input)
            otp_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                'input[type="text"][maxlength="1"], input[type="tel"][maxlength="1"]')
            
            if len(otp_inputs) >= 6:
                # 6 separate inputs
                for i, digit in enumerate(otp[:6]):
                    self.human_type(otp_inputs[i], digit)
                    self.human_delay(0.1, 0.3)
            else:
                # Single input
                otp_input = self.driver.find_element(By.CSS_SELECTOR, 
                    'input[type="text"], input[type="tel"], input[placeholder*="code" i]')
                self.human_type(otp_input, otp)
            
            self.log("✅ OTP filled", "success")
            self.human_delay(2, 3)
            
            # Check for About You page
            if 'about-you' in self.driver.current_url:
                if not self._fill_about_you():
                    return {'success': False, 'status': 'failed', 
                            'message': 'Failed to fill About You'}
            
            return self._check_final_status()
            
        except Exception as e:
            return {'success': False, 'status': 'failed', 
                    'message': f"OTP fill error: {e}"}
    
    def _fill_about_you(self) -> bool:
        """Điền thông tin About You page"""
        try:
            self.log("📝 Filling About You form...")
            
            # Find name input
            name_input = self.driver.find_element(By.CSS_SELECTOR, 
                'input[name="name"], input[placeholder*="name" i], input[type="text"]')
            
            # Generate random name if not provided
            name = self.account.get('name', f"User{random.randint(1000, 9999)}")
            self.human_type(name_input, name)
            
            self.human_delay(0.5, 1)
            
            # Find birthday input (if exists)
            try:
                birthday_selectors = [
                    'input[name*="birth"]',
                    'input[type="date"]',
                    'select[name*="month"]'
                ]
                
                for selector in birthday_selectors:
                    try:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if elem:
                            # Fill with random valid date
                            month = random.randint(1, 12)
                            day = random.randint(1, 28)
                            year = random.randint(1980, 2000)
                            
                            if elem.tag_name == 'input':
                                elem.send_keys(f"{month:02d}/{day:02d}/{year}")
                            break
                    except:
                        continue
            except:
                pass
            
            # Click Continue
            continue_btn = self._find_continue_button()
            if continue_btn:
                try:
                    ActionChains(self.driver).move_to_element(continue_btn).pause(0.2).click().perform()
                except:
                    continue_btn.click()
                
                self.log("✅ About You submitted", "success")
                return True
            
            return False
            
        except Exception as e:
            self.log(f"❌ Error filling About You: {e}", "error")
            return False
    
    def _check_final_status(self) -> dict:
        """Kiểm tra trạng thái cuối cùng"""
        self.human_delay(2, 3)
        
        current_url = self.driver.current_url
        
        # Check for error page
        try:
            error_texts = ['banned', 'suspended', 'blocked', 'error', 'unable']
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            for error in error_texts:
                if error in body_text and 'chatgpt.com' in current_url:
                    # Make sure it's actually an error, not just text on page
                    if 'your account' in body_text and (error in body_text):
                        return {'success': False, 'status': 'failed', 
                                'message': f'Account error: {error}'}
        except:
            pass
        
        # Success: on ChatGPT homepage and logged in
        if 'chatgpt.com' in current_url and 'auth' not in current_url:
            if self._check_login_status() == 'logged_in':
                self.log("✅ Login/Signup successful!", "success")
                return {'success': True, 'status': 'success', 'message': 'Success'}
        
        # Still on auth page - wait more
        if 'auth.openai.com' in current_url or 'verify' in current_url:
            self.log("⏳ Still on auth page, waiting...")
            
            for _ in range(15):
                time.sleep(2)
                current_url = self.driver.current_url
                
                if 'chatgpt.com' in current_url and 'auth' not in current_url:
                    if self._check_login_status() == 'logged_in':
                        return {'success': True, 'status': 'success', 'message': 'Success'}
            
            return {'success': False, 'status': 'failed', 
                    'message': 'Stuck on auth page'}
        
        # Unknown state
        return {'success': False, 'status': 'failed', 
                'message': f'Unknown state: {current_url[:60]}'}
