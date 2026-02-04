"""Browser automation handler using Playwright for Grok signup"""

import asyncio
import random
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout
from config import (
    GROK_SIGNUP_URL,
    BROWSER_HEADLESS,
    BROWSER_SLOW_MO,
    BROWSER_TIMEOUT,
    CLOUDFLARE_WAIT_TIMEOUT,
    SIGNUP_WAIT_AFTER_EMAIL,
    SIGNUP_WAIT_AFTER_CODE_SEND,
    SIGNUP_WAIT_AFTER_CODE_SUBMIT,
    USER_AGENTS
)
from utils.logger import log_info, log_success, log_error, log_warning


class GrokBrowser:
    """Browser automation handler for Grok account signup"""
    
    def __init__(self, headless: bool = BROWSER_HEADLESS):
        """
        Initialize browser handler
        
        Args:
            headless: Run browser in headless mode (default from config)
        """
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def start(self):
        """Start browser and create context"""
        try:
            log_info("🚀 Starting browser...")
            self.playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=BROWSER_SLOW_MO,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            # Create context with random user agent
            user_agent = random.choice(USER_AGENTS)
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Set extra headers to appear more human-like
            await self.context.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            })
            
            # Create page
            self.page = await self.context.new_page()
            self.page.set_default_timeout(BROWSER_TIMEOUT)
            
            log_success("✅ Browser started successfully")
            
        except Exception as e:
            log_error(f"❌ Failed to start browser: {str(e)}")
            raise
    
    async def navigate_to_signup(self):
        """Navigate to Grok signup page"""
        try:
            log_info(f"🌐 Navigating to {GROK_SIGNUP_URL}...")
            await self.page.goto(GROK_SIGNUP_URL, wait_until='domcontentloaded')
            log_success("✅ Loaded signup page")
            
        except Exception as e:
            log_error(f"❌ Failed to navigate: {str(e)}")
            raise
    
    async def wait_for_cloudflare(self, timeout: int = CLOUDFLARE_WAIT_TIMEOUT):
        """
        Wait for page to be ready (handles Cloudflare if present)
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        try:
            log_info("🔐 Waiting for page to load (checking for Cloudflare)...")
            
            # Wait a bit for page to load
            await asyncio.sleep(3)
            
            # Try to find signup form elements directly
            # If Cloudflare exists, Playwright will auto-solve it
            selectors_to_try = [
                'input[type="email"]',
                'input[name="email"]',
                'button:has-text("Continue")',
                'button:has-text("Get started")',
                'form',
                '[data-testid="email-input"]',
                'input[placeholder*="email" i]'
            ]
            
            form_found = False
            found_selector = None
            
            for selector in selectors_to_try:
                try:
                    log_info(f"🔍 Looking for: {selector}...")
                    await self.page.wait_for_selector(selector, timeout=10000, state='visible')
                    form_found = True
                    found_selector = selector
                    log_success(f"✅ Found signup form: {selector}")
                    break
                except PlaywrightTimeout:
                    continue
            
            if not form_found:
                # If no form found after trying all selectors
                # Check if there's a Cloudflare challenge
                page_content = await self.page.content()
                if 'cloudflare' in page_content.lower() or 'challenge' in page_content.lower():
                    log_warning("⚠️ Cloudflare challenge detected - waiting longer...")
                    # Wait extra time for Cloudflare to auto-solve
                    await asyncio.sleep(10)
                    
                    # Try again
                    for selector in selectors_to_try:
                        try:
                            await self.page.wait_for_selector(selector, timeout=30000, state='visible')
                            form_found = True
                            found_selector = selector
                            log_success(f"✅ Found after Cloudflare: {selector}")
                            break
                        except PlaywrightTimeout:
                            continue
                
                if not form_found:
                    log_error("❌ Could not find signup form - timeout")
                    raise Exception("Signup form not found - possible Cloudflare timeout")
            
            log_success("✅ Page ready for signup")
            
            # Extra wait to ensure page is stable
            await asyncio.sleep(2)
            
        except Exception as e:
            log_error(f"❌ Page loading failed: {str(e)}")
            raise
    
    async def fill_email_field(self, email: str):
        """
        Fill the email field on signup form
        
        Args:
            email: Temporary email for verification
        """
        try:
            log_info(f"📧 Filling email field with: {email}")
            
            # Wait for email input field
            email_input = await self.page.wait_for_selector('input[type="email"], input[name="email"]', timeout=10000)
            
            # Clear and fill email
            await email_input.click()
            await email_input.fill('')
            await asyncio.sleep(0.5)
            await email_input.type(email, delay=random.randint(50, 150))
            
            log_success(f"✅ Email filled: {email}")
            await asyncio.sleep(SIGNUP_WAIT_AFTER_EMAIL)
            
        except Exception as e:
            log_error(f"❌ Failed to fill email: {str(e)}")
            raise
    
    async def fill_name_fields(self, first_name: str, last_name: str):
        """
        Fill first name and last name fields
        
        Args:
            first_name: First name
            last_name: Last name
        """
        try:
            log_info(f"👤 Filling name: {first_name} {last_name}")
            
            # Try to find first name field
            try:
                first_name_input = await self.page.wait_for_selector(
                    'input[name="givenName"], input[placeholder*="First"], input[name="firstName"]',
                    timeout=5000
                )
                await first_name_input.click()
                await first_name_input.type(first_name, delay=random.randint(50, 150))
                log_success(f"✅ First name filled: {first_name}")
            except PlaywrightTimeout:
                log_warning("⚠️ First name field not found, might be optional")
            
            # Try to find last name field
            try:
                last_name_input = await self.page.wait_for_selector(
                    'input[name="familyName"], input[placeholder*="Last"], input[name="lastName"]',
                    timeout=5000
                )
                await last_name_input.click()
                await last_name_input.type(last_name, delay=random.randint(50, 150))
                log_success(f"✅ Last name filled: {last_name}")
            except PlaywrightTimeout:
                log_warning("⚠️ Last name field not found, might be optional")
                
        except Exception as e:
            log_error(f"❌ Failed to fill name fields: {str(e)}")
            raise
    
    async def request_verification_code(self):
        """Click button to send verification code to email"""
        try:
            log_info("📨 Requesting verification code...")
            
            # Look for "Continue" or "Send code" button
            # Try multiple possible selectors
            button_selectors = [
                'button:has-text("Continue")',
                'button:has-text("Send")',
                'button:has-text("Confirm")',
                'button[type="submit"]',
                'button.btn-primary'
            ]
            
            button_clicked = False
            for selector in button_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=3000)
                    if button:
                        await button.click()
                        button_clicked = True
                        log_success("✅ Clicked send code button")
                        break
                except PlaywrightTimeout:
                    continue
            
            if not button_clicked:
                log_error("❌ Could not find send code button")
                raise Exception("Send code button not found")
            
            await asyncio.sleep(SIGNUP_WAIT_AFTER_CODE_SEND)
            
        except Exception as e:
            log_error(f"❌ Failed to request verification code: {str(e)}")
            raise
    
    async def submit_verification_code(self, code: str):
        """
        Submit verification code
        
        Args:
            code: 6-digit verification code
        """
        try:
            log_info(f"🔑 Submitting verification code: {code}")
            
            # Wait for code input field (might be multiple inputs for each digit)
            # Try single input field first
            try:
                code_input = await self.page.wait_for_selector(
                    'input[name*="code"], input[placeholder*="code"], input[type="text"]',
                    timeout=5000
                )
                await code_input.click()
                await code_input.type(code, delay=random.randint(50, 150))
                log_success(f"✅ Code entered: {code}")
            except PlaywrightTimeout:
                # Try multiple digit inputs (6 separate inputs)
                log_info("🔍 Looking for separate digit inputs...")
                inputs = await self.page.query_selector_all('input[type="text"]')
                if len(inputs) >= 6:
                    for i, digit in enumerate(code):
                        await inputs[i].type(digit, delay=random.randint(50, 150))
                    log_success(f"✅ Code entered in separate fields: {code}")
                else:
                    raise Exception("Could not find code input fields")
            
            # Click confirm/continue button
            await asyncio.sleep(1)
            confirm_selectors = [
                'button:has-text("Confirm")',
                'button:has-text("Continue")',
                'button:has-text("Verify")',
                'button[type="submit"]'
            ]
            
            for selector in confirm_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        log_success("✅ Clicked confirm button")
                        break
                except PlaywrightTimeout:
                    continue
            
            await asyncio.sleep(SIGNUP_WAIT_AFTER_CODE_SUBMIT)
            
        except Exception as e:
            log_error(f"❌ Failed to submit verification code: {str(e)}")
            raise
    
    async def set_account_credentials(self, email: str, password: str):
        """
        Set Grok account email and password
        
        Args:
            email: Grok account email
            password: Grok account password
        """
        try:
            log_info(f"🔐 Setting account credentials for: {email}")
            
            # Wait for email field (for Grok account, not verification email)
            email_input = await self.page.wait_for_selector('input[type="email"]', timeout=10000)
            await email_input.click()
            await email_input.fill('')
            await asyncio.sleep(0.5)
            await email_input.type(email, delay=random.randint(50, 150))
            log_success(f"✅ Account email set: {email}")
            
            # Wait for password field
            password_input = await self.page.wait_for_selector('input[type="password"]', timeout=5000)
            await password_input.click()
            await password_input.type(password, delay=random.randint(50, 150))
            log_success("✅ Password set")
            
            # Submit form
            await asyncio.sleep(1)
            submit_button = await self.page.wait_for_selector(
                'button[type="submit"], button:has-text("Sign up"), button:has-text("Create")',
                timeout=5000
            )
            await submit_button.click()
            log_success("✅ Submitted signup form")
            
            # Wait for success or error
            await asyncio.sleep(3)
            
        except Exception as e:
            log_error(f"❌ Failed to set credentials: {str(e)}")
            raise
    
    async def check_signup_success(self) -> bool:
        """
        Check if signup was successful
        
        Returns:
            bool: True if signup succeeded, False otherwise
        """
        try:
            # Wait a bit for redirect or success message
            await asyncio.sleep(3)
            
            current_url = self.page.url
            page_content = await self.page.content()
            
            # Check for success indicators
            success_indicators = [
                'welcome' in current_url.lower(),
                'dashboard' in current_url.lower(),
                'success' in page_content.lower(),
                'welcome' in page_content.lower()
            ]
            
            # Check for error indicators
            error_indicators = [
                'error' in page_content.lower(),
                'invalid' in page_content.lower(),
                'failed' in page_content.lower()
            ]
            
            if any(success_indicators):
                log_success("✅ Signup appears successful!")
                return True
            elif any(error_indicators):
                log_error("❌ Signup appears to have failed")
                return False
            else:
                log_warning("⚠️ Signup status unclear")
                return False
                
        except Exception as e:
            log_error(f"❌ Failed to check signup status: {str(e)}")
            return False
    
    async def take_screenshot(self, filename: str):
        """Take screenshot for debugging"""
        try:
            await self.page.screenshot(path=filename)
            log_info(f"📸 Screenshot saved: {filename}")
        except Exception as e:
            log_error(f"❌ Failed to take screenshot: {str(e)}")
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            log_info("🔒 Browser closed")
        except Exception as e:
            log_error(f"❌ Error closing browser: {str(e)}")


# For testing
if __name__ == "__main__":
    async def test():
        browser = GrokBrowser(headless=False)
        try:
            await browser.start()
            await browser.navigate_to_signup()
            await browser.wait_for_cloudflare()
            await asyncio.sleep(5)
        finally:
            await browser.close()
    
    asyncio.run(test())
