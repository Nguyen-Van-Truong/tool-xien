# -*- coding: utf-8 -*-
"""
Page State Detector
Xác định trạng thái hiện tại của trang để biết đang ở bước nào
"""

from enum import Enum
from typing import Optional, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By


class PageState(Enum):
    """Các trạng thái có thể của trang"""
    UNKNOWN = "unknown"
    CHATGPT_HOME = "chatgpt_home"           # Trang chủ ChatGPT (chưa login)
    CHATGPT_LOGGED_IN = "chatgpt_logged_in" # Đã login (có sidebar)
    SIGNUP_FORM = "signup_form"              # Form đăng ký (nút Sign up)
    EMAIL_FORM = "email_form"                # Form nhập email
    PASSWORD_FORM = "password_form"          # Form nhập password
    OTP_PAGE = "otp_page"                    # Trang nhập OTP
    ABOUT_YOU = "about_you"                  # Trang About You
    VETERANS_PAGE = "veterans_page"          # Trang veterans-claim
    SHEERID_PAGE = "sheerid_page"            # Trang SheerID verification
    ERROR_PAGE = "error_page"                # Trang lỗi


class PageStateDetector:
    """Detect current page state"""
    
    def __init__(self, driver: WebDriver, logger=None):
        self.driver = driver
        self.log = logger or print
    
    def detect(self) -> Tuple[PageState, str]:
        """
        Detect current page state
        
        Returns:
            Tuple (PageState, description)
        """
        try:
            url = self.driver.current_url.lower()
            
            # Check URL patterns first
            if 'services.sheerid.com' in url:
                return PageState.SHEERID_PAGE, "On SheerID verification page"
            
            if 'email-verification' in url or '/verify' in url:
                return PageState.OTP_PAGE, "On OTP verification page"
            
            if 'veterans-claim' in url:
                return PageState.VETERANS_PAGE, "On veterans claim page"
            
            # Now check page elements
            body_text = ""
            try:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text or ""
            except:
                pass
            
            # Check for specific elements
            
            # 1. Check if logged in (has sidebar)
            has_sidebar = self._has_sidebar()
            has_textarea = self._has_textarea()
            
            if has_sidebar and has_textarea:
                return PageState.CHATGPT_LOGGED_IN, "Logged in (has sidebar + textarea)"
            
            # 2. Check for password form
            if self._has_password_input():
                return PageState.PASSWORD_FORM, "On password input page"
            
            # 3. Check for email form  
            if self._has_email_input():
                return PageState.EMAIL_FORM, "On email input page"
            
            # 4. Check for OTP inputs
            if self._has_otp_inputs():
                return PageState.OTP_PAGE, "On OTP input page"
            
            # 5. Check for About You page
            about_indicators = ['tell us about you', 'about you', 'về bạn', 'your name']
            if any(x in body_text.lower() for x in about_indicators):
                return PageState.ABOUT_YOU, "On About You page"
            
            # 6. Check for signup button
            if self._has_signup_button():
                return PageState.SIGNUP_FORM, "On signup form (has signup button)"
            
            # 7. ChatGPT home with textarea but no sidebar
            if has_textarea and not has_sidebar:
                return PageState.CHATGPT_HOME, "ChatGPT home (demo mode)"
            
            return PageState.UNKNOWN, "Unknown page state"
            
        except Exception as e:
            self.log(f"⚠️ State detection error: {e}")
            return PageState.UNKNOWN, f"Error: {e}"
    
    def _has_sidebar(self) -> bool:
        """Check if page has sidebar (logged in indicator)"""
        selectors = [
            '[data-testid="sidebar"]',
            'nav[aria-label="Chat history"]',
        ]
        for sel in selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                if elem and elem.is_displayed():
                    return True
            except:
                continue
        return False
    
    def _has_textarea(self) -> bool:
        """Check if page has prompt textarea"""
        try:
            textarea = self.driver.find_element(By.ID, "prompt-textarea")
            return textarea and textarea.is_displayed()
        except:
            return False
    
    def _has_email_input(self) -> bool:
        """Check if page has email input"""
        selectors = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[autocomplete="email"]',
        ]
        for sel in selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                if elem and elem.is_displayed():
                    return True
            except:
                continue
        return False
    
    def _has_password_input(self) -> bool:
        """Check if page has password input"""
        try:
            password_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            for inp in password_inputs:
                if inp.is_displayed():
                    return True
        except:
            pass
        return False
    
    def _has_otp_inputs(self) -> bool:
        """Check if page has OTP input boxes"""
        try:
            # Check for 6 individual boxes
            boxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"][maxlength="1"]')
            if len(boxes) >= 6:
                return True
            
            # Check for single OTP input
            otp_selectors = [
                'input[name*="code"]',
                'input[autocomplete="one-time-code"]',
            ]
            for sel in otp_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if elem and elem.is_displayed():
                        return True
                except:
                    continue
        except:
            pass
        return False
    
    def _has_signup_button(self) -> bool:
        """Check if page has signup button"""
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            
            for elem in buttons + links:
                try:
                    if not elem.is_displayed():
                        continue
                    text = (elem.text or '').lower()
                    if 'sign up' in text:
                        return True
                except:
                    continue
        except:
            pass
        return False
