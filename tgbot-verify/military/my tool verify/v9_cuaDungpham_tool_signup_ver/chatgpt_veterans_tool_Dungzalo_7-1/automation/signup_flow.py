"""
Signup Flow - Xử lý đăng ký/đăng nhập ChatGPT
"""

from PyQt6.QtCore import QObject, pyqtSignal
from playwright.async_api import Page
from utils.email_api import EmailAPI
import asyncio
import re


class SignupFlow(QObject):
    """Signup/Login flow handler"""
    
    log_message = pyqtSignal(str)
    
    def __init__(self, page: Page, account_data: dict):
        super().__init__()
        self.page = page
        self.account_data = account_data
        self.email_api = EmailAPI(
            email_login=account_data.get('emailLogin', ''),
            refresh_token=account_data.get('refreshToken', ''),
            client_id=account_data.get('clientId', '')
        )
    
    async def run(self):
        """Chạy signup flow - match với extension logic"""
        try:
            # Navigate to ChatGPT
            current_url = self.page.url
            if not ('chatgpt.com' in current_url or 'auth.openai.com' in current_url or 'openai.com' in current_url):
                await self.page.goto('https://chatgpt.com', wait_until='networkidle')
                await asyncio.sleep(5)
            
            # Check if already logged in
            if await self.is_logged_in():
                self.log_message.emit("✅ Already logged in")
                return {'success': True}
            
            # Start signup loop (similar to extension's startSignupLoop)
            await self.start_signup_loop()
            
            # Check if signup successful
            if await self.is_logged_in():
                self.log_message.emit("✅ Signup completed successfully")
                return {'success': True}
            else:
                return {'success': False, 'error': 'Signup not completed'}
                
        except Exception as e:
            self.log_message.emit(f"Signup error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def start_signup_loop(self):
        """Main signup loop - match với extension logic"""
        current_url = self.page.url
        
        # Check URL and handle accordingly
        if 'auth.openai.com/create-account/password' in current_url:
            # On password page
            await self.fill_password()
            await asyncio.sleep(3)
            await self.start_signup_loop()
        elif 'auth.openai.com/email-verification' in current_url or 'email-verification' in current_url:
            # On OTP page
            await asyncio.sleep(10)  # Wait for email to be sent
            await self.handle_otp_verification()
        elif 'auth.openai.com/about-you' in current_url or '/about-you' in current_url:
            # On About You page
            await asyncio.sleep(2)
            await self.handle_about_you()
        elif 'chatgpt.com/veterans-claim' in current_url:
            # On veterans page - check if logged in
            if await self.is_logged_in():
                self.log_message.emit("✅ Already logged in on veterans page")
                return
            else:
                # Not logged in, go back to signup
                await self.page.goto('https://chatgpt.com')
                await asyncio.sleep(5)
                await self.start_signup_loop()
        elif 'chatgpt.com' in current_url:
            # On ChatGPT page - check if logged in
            if await self.is_logged_in():
                self.log_message.emit("✅ Already logged in")
                return
            else:
                # Not logged in, start signup
                await self.click_signup_button()
                await asyncio.sleep(3)
                await self.start_signup_loop()
        else:
            # Not on ChatGPT, redirect
            await self.page.goto('https://chatgpt.com')
            await asyncio.sleep(5)
            await self.start_signup_loop()
    
    async def is_logged_in(self):
        """Kiểm tra xem đã đăng nhập chưa"""
        try:
            # Check for login indicators
            body_text = await self.page.inner_text('body')
            has_new_chat = 'New chat' in body_text or 'New conversation' in body_text
            has_textarea = await self.page.query_selector('textarea[placeholder*="Message"]')
            return has_new_chat or has_textarea is not None
        except:
            return False
    
    async def click_signup_button(self):
        """Click nút Sign up for free"""
        try:
            # Try multiple selectors
            selectors = [
                'button:has-text("Sign up")',
                'a:has-text("Sign up")',
                'button:has-text("Sign up for free")',
                'a:has-text("Sign up for free")'
            ]
            
            for selector in selectors:
                button = await self.page.query_selector(selector)
                if button:
                    await button.click()
                    self.log_message.emit("Clicked signup button")
                    return
            
            raise Exception("Signup button not found")
        except Exception as e:
            self.log_message.emit(f"Error clicking signup: {str(e)}")
            raise
    
    async def fill_email(self):
        """Điền email"""
        try:
            email = self.account_data.get('email', '')
            
            # Wait for email input
            email_input = await self.page.wait_for_selector(
                'input[type="email"], input[name*="email" i], input[id*="email" i]',
                timeout=10000
            )
            
            await email_input.fill(email)
            await email_input.dispatch_event('input')
            await email_input.dispatch_event('change')
            
            self.log_message.emit(f"Filled email: {email}")
        except Exception as e:
            self.log_message.emit(f"Error filling email: {str(e)}")
            raise
    
    async def fill_password(self):
        """Điền password"""
        try:
            password = self.account_data.get('password', '')
            
            # Wait for password input
            password_input = await self.page.wait_for_selector(
                'input[type="password"], input[name*="password" i]',
                timeout=10000
            )
            
            await password_input.fill(password)
            await password_input.dispatch_event('input')
            await password_input.dispatch_event('change')
            
            self.log_message.emit("Filled password")
        except Exception as e:
            self.log_message.emit(f"Error filling password: {str(e)}")
            raise
    
    async def click_continue(self):
        """Click nút Continue"""
        try:
            # Try multiple selectors
            selectors = [
                'button[type="submit"]',
                'button:has-text("Continue")',
                'button.btn-primary',
                'button[class*="primary"]'
            ]
            
            for selector in selectors:
                button = await self.page.query_selector(selector)
                if button and await button.is_enabled():
                    await button.click()
                    self.log_message.emit("Clicked Continue")
                    await asyncio.sleep(1)
                    return
            
            raise Exception("Continue button not found or disabled")
        except Exception as e:
            self.log_message.emit(f"Error clicking continue: {str(e)}")
            raise
    
    async def handle_otp_verification(self):
        """Xử lý OTP verification - match với extension logic"""
        try:
            self.log_message.emit("📧 Getting OTP code from email...")
            
            # Retry logic: thử lại 10 lần nếu không nhận được OTP
            MAX_OTP_RETRIES = 10
            otp_retry_count = 0
            otp_code = None
            
            while otp_retry_count < MAX_OTP_RETRIES and not otp_code:
                try:
                    # Check if refresh_token and client_id exist
                    if not self.account_data.get('refreshToken') or not self.account_data.get('clientId'):
                        raise Exception('Thiếu refresh_token hoặc client_id')
                    
                    if otp_retry_count > 0:
                        self.log_message.emit(f"📡 Retrying to read email from API... ({otp_retry_count}/{MAX_OTP_RETRIES})")
                        await asyncio.sleep(3)
                    else:
                        self.log_message.emit("📡 Reading email from API...")
                    
                    # Get messages from email API
                    messages = await self.email_api.get_messages()
                    
                    if not messages or len(messages) == 0:
                        otp_retry_count += 1
                        if otp_retry_count < MAX_OTP_RETRIES:
                            continue
                        else:
                            raise Exception('No emails found after ' + str(MAX_OTP_RETRIES) + ' attempts')
                    
                    # Sort messages by date - newest first
                    messages = sorted(messages, key=lambda x: x.get('date', 0), reverse=True)
                    
                    # Find email with OTP
                    found_email = None
                    for msg in messages:
                        subject = (msg.get('subject') or '').lower()
                        
                        # Tìm email có subject chứa "your chatgpt code is"
                        if 'your chatgpt code is' in subject or 'chatgpt code' in subject:
                            found_email = msg
                            
                            # Extract OTP từ SUBJECT trước
                            subject_otp_match = re.search(r'code\s*(?:is\s*)?(\d{6})', msg.get('subject', ''), re.IGNORECASE)
                            if subject_otp_match:
                                otp_code = subject_otp_match.group(1)
                                break
                            
                            # Fallback: tìm bất kỳ 6 số trong subject
                            subject_match = re.search(r'(\d{6})', msg.get('subject', ''))
                            if subject_match:
                                otp_code = subject_match.group(1)
                                break
                            
                            # Nếu không có trong subject, thử body
                            body = (msg.get('message', '') + msg.get('html_body', ''))
                            body_match = re.search(r'code\s*(?:is\s*)?(\d{6})', body, re.IGNORECASE) or re.search(r'(\d{6})', body)
                            if body_match:
                                otp_code = body_match.group(1)
                                break
                    
                    if not otp_code:
                        # Nếu không tìm thấy, thử tìm bất kỳ email nào có mã 6 số
                        for msg in messages:
                            body = (msg.get('message', '') + msg.get('html_body', ''))
                            subject = (msg.get('subject', '')).lower()
                            
                            # Tìm mã 6 số trong body hoặc subject
                            otp_match = re.search(r'\b(\d{6})\b', body + ' ' + subject)
                            if otp_match:
                                otp_code = otp_match.group(1)
                                found_email = msg
                                break
                    
                    if not otp_code:
                        otp_retry_count += 1
                        if otp_retry_count < MAX_OTP_RETRIES:
                            continue
                        else:
                            raise Exception('6-digit OTP code not found in email after ' + str(MAX_OTP_RETRIES) + ' attempts')
                    
                    # Nếu tìm thấy OTP, break khỏi loop
                    break
                    
                except Exception as e:
                    otp_retry_count += 1
                    if otp_retry_count >= MAX_OTP_RETRIES:
                        raise Exception(f"Failed to get OTP after {MAX_OTP_RETRIES} attempts: {str(e)}")
                    self.log_message.emit(f"⚠️ Error getting OTP, retrying... ({otp_retry_count}/{MAX_OTP_RETRIES}): {str(e)}")
                    await asyncio.sleep(3)
                    continue
            
            if not otp_code:
                raise Exception("Failed to get OTP code")
            
            self.log_message.emit(f"✅ Received OTP code, filling...")
            await asyncio.sleep(1)
            
            # Find OTP input - try multiple selectors
            otp_selectors = [
                'input[name="code"]',
                'input[id*="-code"]',
                'input[type="text"][name*="code"]',
                'input[type="text"][name*="otp"]',
                'input[type="text"][name*="verification"]',
                'input[id*="code"]',
                'input[id*="otp"]',
                'input[placeholder*="code" i]',
                'input[placeholder*="Code" i]',
                '#code',
                '#otp'
            ]
            
            otp_input = None
            for selector in otp_selectors:
                try:
                    otp_input = await self.page.query_selector(selector)
                    if otp_input:
                        break
                except:
                    continue
            
            if not otp_input:
                # Try to find by maxlength
                all_inputs = await self.page.query_selector_all('input[type="text"], input[type="number"]')
                for inp in all_inputs:
                    max_length = await inp.get_attribute('maxlength')
                    placeholder = await inp.get_attribute('placeholder') or ''
                    if (max_length and int(max_length) <= 10) or 'code' in placeholder.lower() or 'otp' in placeholder.lower():
                        otp_input = inp
                        break
            
            if not otp_input:
                raise Exception('OTP input not found')
            
            # Fill OTP
            await otp_input.fill(otp_code)
            await otp_input.dispatch_event('input')
            await otp_input.dispatch_event('change')
            await otp_input.dispatch_event('blur')
            await asyncio.sleep(1)
            
            # Find and click verify/submit button
            verify_button = None
            verify_selectors = [
                'button[type="submit"]',
                'button.btn-primary',
                'button[class*="primary"]'
            ]
            
            for selector in verify_selectors:
                try:
                    verify_button = await self.page.query_selector(selector)
                    if verify_button:
                        button_text = await verify_button.inner_text()
                        if 'verify' in button_text.lower() or 'continue' in button_text.lower() or 'xác thực' in button_text.lower() or 'tiếp tục' in button_text.lower():
                            break
                except:
                    continue
            
            if not verify_button:
                # Try to find by text
                all_buttons = await self.page.query_selector_all('button')
                for btn in all_buttons:
                    text = await btn.inner_text()
                    if 'verify' in text.lower() or 'continue' in text.lower() or btn.get_attribute('type') == 'submit':
                        verify_button = btn
                        break
            
            if not verify_button:
                raise Exception('OTP verify button not found')
            
            # Click verify button
            await verify_button.click()
            self.log_message.emit("✅ OTP code submitted, waiting for result...")
            await asyncio.sleep(5)
            
            # Check if signup was successful
            current_url = self.page.url
            if 'chatgpt.com' in current_url and 'signup' not in current_url and 'verify' not in current_url and 'auth' not in current_url:
                # Success - on main ChatGPT page
                self.log_message.emit("✅ Signup successful!")
                return
            else:
                # Check for error messages
                error_elements = await self.page.query_selector_all('.error, .alert, [role="alert"]')
                if error_elements:
                    error_text = ' '.join([await el.inner_text() for el in error_elements])
                    raise Exception('Verification error: ' + error_text)
                
                # Continue loop to check next state
                await asyncio.sleep(3)
                await self.start_signup_loop()
            
        except Exception as e:
            self.log_message.emit(f"Error handling OTP verification: {str(e)}")
            raise
    
    async def get_otp_from_email(self, max_retries=10):
        """Lấy OTP từ email"""
        for i in range(max_retries):
            try:
                messages = await self.email_api.get_messages()
                if not messages:
                    await asyncio.sleep(3)
                    continue
                
                # Find OTP email
                for msg in messages:
                    subject = msg.get('subject', '').lower()
                    if 'chatgpt code' in subject or 'chatgpt code is' in subject:
                        # Extract OTP
                        otp_match = re.search(r'code\s*(?:is\s*)?(\d{6})', subject, re.IGNORECASE)
                        if otp_match:
                            return otp_match.group(1)
                        
                        # Try body
                        body = msg.get('message', '') + msg.get('html_body', '')
                        otp_match = re.search(r'code\s*(?:is\s*)?(\d{6})', body, re.IGNORECASE)
                        if otp_match:
                            return otp_match.group(1)
                
                await asyncio.sleep(3)
            except Exception as e:
                self.log_message.emit(f"Error getting OTP (attempt {i+1}): {str(e)}")
                await asyncio.sleep(3)
        
        return None
    
    async def handle_about_you(self):
        """Xử lý trang About You - match với extension logic"""
        try:
            self.log_message.emit("📝 Filling personal information...")
            await asyncio.sleep(2)
            
            # Fill name - use email prefix
            name_input = await self.page.query_selector('input[name="name"], input[id*="name"], input[placeholder*="name" i]')
            if name_input:
                email_prefix = self.account_data.get('email', '').split('@')[0][:10]
                await name_input.fill(email_prefix)
                await name_input.dispatch_event('input')
                await name_input.dispatch_event('change')
                await asyncio.sleep(1)
            
            # Fill birthday
            await self.fill_birthday()
            await asyncio.sleep(1)
            
            # Click continue
            await self.click_continue()
            await asyncio.sleep(3)
            
            # Check if signup successful
            current_url = self.page.url
            if 'chatgpt.com' in current_url and 'signup' not in current_url and 'verify' not in current_url and 'auth' not in current_url:
                # Success - on main ChatGPT page
                self.log_message.emit("✅ Signup successful!")
                return
            else:
                # Continue loop
                await self.start_signup_loop()
            
        except Exception as e:
            self.log_message.emit(f"Error handling About You: {str(e)}")
            # Continue anyway
    
    async def fill_birthday(self):
        """Điền birthday"""
        try:
            # Generate random birthday
            import random
            year = random.randint(1960, 1980)
            month = random.randint(10, 12)
            day = random.randint(10, 28)
            
            # Fill month
            month_button = await self.page.query_selector('#sid-birthdate__month + button, [data-type="month"]')
            if month_button:
                await month_button.click()
                await asyncio.sleep(0.5)
                month_item = await self.page.query_selector(f'#sid-birthdate__month-item-{month}')
                if month_item:
                    await month_item.click()
                    await asyncio.sleep(0.5)
            
            # Fill day
            day_input = await self.page.query_selector('#sid-birthdate-day, [data-type="day"]')
            if day_input:
                await day_input.fill(str(day))
                await day_input.dispatch_event('input')
                await asyncio.sleep(0.5)
            
            # Fill year
            year_input = await self.page.query_selector('#sid-birthdate-year, [data-type="year"]')
            if year_input:
                await year_input.fill(str(year))
                await year_input.dispatch_event('input')
                await asyncio.sleep(0.5)
            
        except Exception as e:
            self.log_message.emit(f"Error filling birthday: {str(e)}")
            # Continue anyway

