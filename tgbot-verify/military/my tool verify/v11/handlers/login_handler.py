# -*- coding: utf-8 -*-
"""
Login Handler
Xử lý login detection và click signup button
"""

import time
from typing import Callable, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from utils.element_finder import find_button_by_text, wait_for_element, is_visible
from utils.click_helper import click_element, scroll_to_element
from utils.human_behavior import random_delay


class LoginHandler:
    """Xử lý login/signup detection"""
    
    def __init__(self, driver: WebDriver, logger: Callable = None):
        self.driver = driver
        self.log = logger or print
    
    def is_logged_in(self) -> bool:
        """
        Check xem đã login chưa
        Logic từ v10: Phải có CẢ textarea VÀ sidebar
        
        Returns:
            True nếu đã login
        """
        try:
            has_textarea = False
            has_sidebar = False
            
            # Check prompt textarea
            try:
                textarea = self.driver.find_element(By.ID, "prompt-textarea")
                has_textarea = textarea and is_visible(textarea)
            except:
                pass
            
            # Check sidebar (chỉ có khi đã login)
            sidebar_selectors = [
                '[data-testid="sidebar"]',
                'nav[aria-label="Chat history"]',
            ]
            for sel in sidebar_selectors:
                try:
                    sidebar = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if sidebar and is_visible(sidebar):
                        has_sidebar = True
                        break
                except:
                    continue
            
            self.log(f"🔍 Login check: Textarea={has_textarea}, Sidebar={has_sidebar}")
            
            return has_textarea and has_sidebar
            
        except Exception as e:
            self.log(f"⚠️ Error checking login: {e}")
            return False
    
    def click_signup_button(self) -> bool:
        """
        Tìm và click nút "Sign up for free"
        
        Returns:
            True nếu thành công
        """
        self.log("🔍 Looking for Sign up button...")
        random_delay(1, 2)
        
        # Check if email form already visible
        email_selectors = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[placeholder*="email" i]',
        ]
        for sel in email_selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                if elem and is_visible(elem):
                    self.log("ℹ️ Email form already visible")
                    return True
            except:
                continue
        
        # Find signup button
        signup_texts = [
            "Sign up for free",
            "Sign up",
            "Get started",
        ]
        
        signup_btn = find_button_by_text(self.driver, signup_texts)
        
        if signup_btn:
            self.log("✅ Found signup button, clicking...")
            success, method = click_element(self.driver, signup_btn)
            
            if success:
                self.log(f"✅ Clicked using {method}")
                
                # Wait for email form
                random_delay(2, 3)
                
                max_attempts = 10
                for _ in range(max_attempts):
                    for sel in email_selectors:
                        try:
                            elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                            if elem and is_visible(elem):
                                self.log("✅ Email form appeared")
                                return True
                        except:
                            continue
                    time.sleep(1)
                
                self.log("⚠️ Email form not found, but continuing...")
                return True
            else:
                self.log(f"❌ Click failed: {method}")
                return False
        
        self.log("❌ Signup button not found")
        return False
    
    def click_login_button(self) -> bool:
        """
        Click nút Login (nếu cần login thay vì signup)
        
        Returns:
            True nếu thành công
        """
        login_texts = ["Log in", "Login", "Sign in"]
        
        login_btn = find_button_by_text(self.driver, login_texts)
        
        if login_btn:
            self.log("✅ Found login button, clicking...")
            success, method = click_element(self.driver, login_btn)
            return success
        
        return False
