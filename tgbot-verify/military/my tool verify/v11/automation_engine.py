# -*- coding: utf-8 -*-
"""
Automation Engine
Điều phối toàn bộ flow: Login → Signup → Verify
"""

import time
from typing import Callable, Dict, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from handlers.login_handler import LoginHandler
from handlers.signup_handler import SignupHandler
from handlers.verify_handler import VerifyHandler
from utils.human_behavior import random_delay

import config


class AutomationEngine:
    """
    Main automation engine
    Điều phối: Detection → Signup (nếu cần) → Verify (nếu có data)
    """
    
    CHATGPT_URL = "https://chatgpt.com"
    
    def __init__(
        self,
        driver: WebDriver,
        account: Dict,
        veteran_data: Optional[Dict] = None,
        logger: Callable = None,
        instance_id: int = 0
    ):
        """
        Args:
            driver: Selenium WebDriver
            account: Dict với signup data (email, password, emailLogin, passEmail, etc.)
            veteran_data: Optional Dict với verify data (first, last, branch, month, day, year)
            logger: Log function
            instance_id: Browser instance ID for logging
        """
        self.driver = driver
        self.account = account
        self.veteran_data = veteran_data
        self.instance_id = instance_id
        self.log_func = logger or print
        
        # Initialize handlers
        self.login_handler = LoginHandler(driver, self._log)
        self.signup_handler = SignupHandler(driver, account, self._log)
        
        if veteran_data:
            self.verify_handler = VerifyHandler(driver, veteran_data, self._log)
        else:
            self.verify_handler = None
    
    def _log(self, message: str, level: str = "info"):
        """Log với instance ID"""
        self.log_func(f"[Browser {self.instance_id}] [{level.upper()}] {message}")
    
    def run(self, skip_verify: bool = False) -> Dict:
        """
        Chạy toàn bộ automation flow
        
        Args:
            skip_verify: True để skip verification step
            
        Returns:
            Dict với keys: success, status, message
        """
        try:
            # Step 1: Navigate to ChatGPT
            self._log("🌐 Navigating to ChatGPT...")
            self.driver.get(self.CHATGPT_URL)
            random_delay(3, 5)
            
            # Maximize window
            try:
                self.driver.maximize_window()
                self._log("🪟 Window maximized")
            except:
                pass
            
            # Step 2: Check login status
            self._log("🔍 Checking login status...")
            
            if self.login_handler.is_logged_in():
                self._log("✅ Already logged in!")
                
                # If has veteran data and not skipping, go to verify
                if self.veteran_data and not skip_verify:
                    return self._run_verification()
                
                return {
                    "success": True,
                    "status": "exists",
                    "message": "Already logged in"
                }
            
            # Step 3: Not logged in - try signup
            self._log("🔐 Not logged in, starting signup...")
            signup_result = self._run_signup()
            
            if not signup_result.get("success"):
                return signup_result
            
            # Step 4: Signup success - verify if has data
            if self.veteran_data and not skip_verify:
                return self._run_verification()
            
            return {
                "success": True,
                "status": "success",
                "message": "Signup successful"
            }
            
        except Exception as e:
            self._log(f"❌ Error: {e}", "error")
            return {
                "success": False,
                "status": "error",
                "message": str(e)
            }
    
    def _run_signup(self) -> Dict:
        """
        Chạy signup flow
        
        Returns:
            Dict result
        """
        try:
            # Click signup button
            if not self.login_handler.click_signup_button():
                return {
                    "success": False,
                    "status": "failed",
                    "message": "Signup button not found"
                }
            
            random_delay(2, 3)
            
            # Fill email
            if not self.signup_handler.fill_email():
                return {
                    "success": False,
                    "status": "failed",
                    "message": "Failed to fill email"
                }
            
            random_delay(2, 3)
            
            # Fill password
            if not self.signup_handler.fill_password():
                return {
                    "success": False,
                    "status": "failed",
                    "message": "Failed to fill password"
                }
            
            random_delay(3, 5)
            
            # Check if need OTP
            current_url = self.driver.current_url.lower()
            
            if "email-verification" in current_url or "verify" in current_url:
                self._log("📧 OTP verification required")
                if not self.signup_handler.handle_otp():
                    return {
                        "success": False,
                        "status": "failed",
                        "message": "OTP verification failed"
                    }
            
            random_delay(3, 5)
            
            # Check for About You page
            self.signup_handler.fill_about_you()
            
            random_delay(2, 3)
            
            # Final check - are we logged in now?
            if self.login_handler.is_logged_in():
                self._log("✅ Signup successful!", "success")
                return {
                    "success": True,
                    "status": "success",
                    "message": "Signup successful"
                }
            
            # Check for common errors
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text or ""
            
            if "already" in body_text.lower() and "exist" in body_text.lower():
                return {
                    "success": False,
                    "status": "exists",
                    "message": "Account already exists"
                }
            
            return {
                "success": False,
                "status": "unknown",
                "message": "Signup completed but status unclear"
            }
            
        except Exception as e:
            self._log(f"❌ Signup error: {e}", "error")
            return {
                "success": False,
                "status": "error",
                "message": str(e)
            }
    
    def _run_verification(self) -> Dict:
        """
        Chạy verification flow
        
        Returns:
            Dict result
        """
        if not self.verify_handler:
            return {
                "success": True,
                "status": "skipped",
                "message": "No veteran data provided"
            }
        
        self._log("🎖️ Starting military verification...")
        return self.verify_handler.run_verification_flow()
    
    def run_signup_only(self) -> Dict:
        """Chỉ chạy signup, không verify"""
        return self.run(skip_verify=True)
    
    def run_verify_only(self) -> Dict:
        """Chỉ chạy verify (assume đã login)"""
        if not self.verify_handler:
            return {
                "success": False,
                "status": "error",
                "message": "No veteran data provided"
            }
        
        return self._run_verification()


# Helper function for compatibility with old code
def create_automation(
    driver: WebDriver,
    account: Dict,
    logger: Callable = None,
    instance_id: int = 0
) -> AutomationEngine:
    """
    Factory function để tạo AutomationEngine
    
    Tự động parse veteran data từ account nếu có
    """
    # Extract veteran data if present in account
    veteran_data = None
    
    if all(key in account for key in ['first', 'last', 'branch', 'month', 'day', 'year']):
        veteran_data = {
            'first': account['first'],
            'last': account['last'],
            'branch': account['branch'],
            'month': account['month'],
            'day': account['day'],
            'year': account['year'],
        }
    
    return AutomationEngine(
        driver=driver,
        account=account,
        veteran_data=veteran_data,
        logger=logger,
        instance_id=instance_id
    )
