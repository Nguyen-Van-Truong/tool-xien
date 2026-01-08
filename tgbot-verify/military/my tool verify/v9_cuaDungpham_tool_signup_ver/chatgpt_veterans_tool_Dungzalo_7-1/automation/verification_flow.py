"""
Verification Flow - Xử lý verification trên SheerID
Sử dụng API trực tiếp thay vì fill form trên browser
"""

from PyQt6.QtCore import QObject, pyqtSignal
from playwright.async_api import Page
from utils.email_api import EmailAPI
import asyncio
import re
import sys
from pathlib import Path

# Import military verification module
sys.path.insert(0, str(Path(__file__).parent.parent))
from military.sheerid_verifier import SheerIDVerifier
from military.name_generator import generate_email as generate_random_email, generate_birth_date, generate_discharge_date
from military import config as military_config


class VerificationFlow(QObject):
    """Verification flow handler"""
    
    log_message = pyqtSignal(str)
    
    def __init__(self, page: Page, veteran_data: dict, account_data: dict = None):
        super().__init__()
        self.page = page
        self.veteran_data = veteran_data
        self.account_data = account_data  # Account data chứa emailLogin
        self.current_email = None
    
    async def run(self):
        """Chạy verification flow - Sử dụng API trực tiếp"""
        try:
            self.log_message.emit("🔄 [DEBUG] Starting verification flow...")
            
            # Kiểm tra URL hiện tại - không navigate nếu đã ở đúng page
            current_url = self.page.url
            self.log_message.emit(f"📍 [DEBUG] Current URL: {current_url}")
            
            if 'veterans-claim' not in current_url.lower() and 'sheerid' not in current_url.lower():
                self.log_message.emit("🌐 [DEBUG] Navigating to https://chatgpt.com/veterans-claim...")
                try:
                    await self.page.goto('https://chatgpt.com/veterans-claim', wait_until='domcontentloaded', timeout=60000)
                except Exception:
                    pass
                await asyncio.sleep(3)
                self.log_message.emit(f"📍 [DEBUG] After navigation: {self.page.url}")
            else:
                await asyncio.sleep(2)
            
            # Click verify button - Pass row_number để hiển thị trong error
            self.log_message.emit("🖱️ [DEBUG] Looking for Verify button...")
            row_number = getattr(self, 'row_number', None)
            await self.click_verify_button(row_number)
            self.log_message.emit("✅ [DEBUG] Clicked Verify button, waiting for SheerID redirect...")
            await asyncio.sleep(5)
            
            # Wait for redirect to SheerID
            await self.wait_for_sheerid()
            self.log_message.emit(f"📍 [DEBUG] SheerID page: {self.page.url}")
            await asyncio.sleep(3)
            
            # Extract verification ID from URL
            current_url = self.page.url
            verification_id = SheerIDVerifier.parse_verification_id(current_url)
            
            if not verification_id:
                raise Exception(f"Không thể extract verification_id từ URL: {current_url}")
            
            self.log_message.emit(f"🔑 [DEBUG] verification_id: {verification_id}")
            
            # Generate email from tinyhost.shop API (giống extension)
            if not self.current_email:
                self.current_email = await self.generate_email_from_tinyhost()
            
            # Prepare veteran data
            first_name = self.veteran_data.get('first', '').strip()
            last_name = self.veteran_data.get('last', '').strip()
            branch = self.veteran_data.get('branch', '').strip()
            
            # Parse date from veteran_data
            month_name = self.veteran_data.get('month', '').strip()
            day = self.veteran_data.get('day', '').strip()
            year = self.veteran_data.get('year', '').strip()
            
            # Convert month name to number
            month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                          'july', 'august', 'september', 'october', 'november', 'december']
            try:
                month_index = month_names.index(month_name.lower())
                month_num = str(month_index + 1).zfill(2)
            except:
                # Fallback: generate random date
                birth_date = generate_birth_date()
                discharge_date = generate_discharge_date()
            else:
                birth_date = f"{year}-{month_num}-{day.zfill(2)}"
                # Generate discharge date (within last 12 months)
                discharge_date = generate_discharge_date()
            
            # Create verifier
            verifier = SheerIDVerifier(verification_id)
            
            # Patch logger để dùng signal của chúng ta
            import logging
            original_logger = logging.getLogger('military.sheerid_verifier')
            
            class SignalLogger:
                def __init__(self, signal):
                    self.signal = signal
                def info(self, msg):
                    self.signal.emit(msg)
                def error(self, msg):
                    self.signal.emit(f"❌ {msg}")
            
            # Temporarily replace logger
            signal_logger = SignalLogger(self.log_message)
            original_logger.info = signal_logger.info
            original_logger.error = signal_logger.error
            
            try:
                result = verifier.verify(
                    first_name=first_name,
                    last_name=last_name,
                    email=self.current_email,
                    birth_date=birth_date,
                    discharge_date=discharge_date,
                    branch=branch,
                    military_status="VETERAN"
                )
                
                # Check verification status từ page content (giống extension)
                verification_status = await self.check_verification_status_from_page()
                
                if verification_status:
                    # Nếu có status từ page, ưu tiên dùng status này
                    return verification_status
                
                # Nếu không có status từ page, dùng result từ API
                if result.get('success'):
                    if result.get('pending'):
                        # Nếu cần email verification, đọc email và click link
                        if result.get('status', {}).get('currentStep') == 'emailLoop':
                            await self.read_email_and_click_verification_link()
                            # Check lại status sau khi click verification link
                            verification_status = await self.check_verification_status_from_page()
                            if verification_status:
                                return verification_status
                    else:
                        # Check lại page để chắc chắn
                        verification_status = await self.check_verification_status_from_page()
                        if verification_status:
                            return verification_status
                        return {
                            'success': True,
                            'status': 'Verified!',
                            'message': f"✓ Verified! {result.get('veteran_name', '')}",
                            'veteran_name': result.get('veteran_name')
                        }
                else:
                    error_msg = result.get('message', 'Verification failed')
                    # Check xem có phải limit exceeded không
                    if 'limit exceeded' in error_msg.lower() or 'verification limit exceeded' in error_msg.lower():
                        return {
                            'success': False,
                            'status': 'Limit Exceeded',
                            'message': '❌ Verification Limit Exceeded - data already verified'
                        }
                    return {
                        'success': False,
                        'status': 'Error',
                        'message': f"❌ {error_msg}"
                    }
                
                return result
            finally:
                # Restore original logger
                import logging
                original_logger = logging.getLogger('military.sheerid_verifier')
                original_logger.info = logging.Logger.info
                original_logger.error = logging.Logger.error
            
        except Exception as e:
            self.log_message.emit(f"Verification error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def check_cloudflare_captcha(self):
        """Kiểm tra xem có Cloudflare/CAPTCHA không"""
        try:
            # Check URL
            current_url = self.page.url
            if 'challenges.cloudflare.com' in current_url.lower() or 'cf-challenge' in current_url.lower():
                return True
            
            # Check page content
            body_text = await self.page.inner_text('body')
            page_content = body_text.lower()
            
            # Check for Cloudflare indicators
            cloudflare_indicators = [
                'cloudflare',
                'checking your browser',
                'just a moment',
                'ddos protection',
                'cf-browser-verification',
                'captcha',
                'verify you are human',
                'verify you\'re not a robot'
            ]
            
            for indicator in cloudflare_indicators:
                if indicator in page_content:
                    return True
            
            # Check for CAPTCHA iframe
            captcha_frame = await self.page.query_selector('iframe[src*="recaptcha"], iframe[src*="captcha"], iframe[src*="challenge"]')
            if captcha_frame:
                return True
            
            # Check for challenge elements
            challenge_elements = await self.page.query_selector('.cf-browser-verification, #challenge-form, .cf-challenge-form')
            if challenge_elements:
                return True
            
            return False
        except Exception as e:
            # If we can't check, assume no Cloudflare
            return False
    
    async def click_verify_button(self, row_number=None):
        """Click nút verify trên ChatGPT - Match extension logic"""
        try:
            # Wait for page to be ready
            await asyncio.sleep(2)
            
            # Check for Cloudflare/CAPTCHA first
            if await self.check_cloudflare_captcha():
                error_msg = f"⚠️ Cloudflare/CAPTCHA detected. Please check manually in browser #{row_number + 1 if row_number is not None else '?'} and complete the challenge."
                self.log_message.emit(error_msg)
                raise Exception(f"CLOUDFLARE_DETECTED:{error_msg}")
            
            # Try multiple selectors - Match extension
            selectors = [
                'button:has-text("Verify")',
                'button:has-text("Xác minh")',
                'button:has-text("Claim offer")',
                'button.btn-primary:has-text("Verify")',
                'button[class*="btn-primary"]',
                'a:has-text("Verify")',
                'a:has-text("Xác minh")'
            ]
            
            # Try query_selector first
            for selector in selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        button_text = await button.inner_text()
                        if 'verify' in button_text.lower() or 'xác minh' in button_text.lower() or 'claim' in button_text.lower():
                            await button.click()
                            return
                except:
                    continue
            
            # Try evaluate to find button by text content (like extension)
            button_found = await self.page.evaluate("""
                () => {
                    const allButtons = Array.from(document.querySelectorAll('button, a'));
                    for (let btn of allButtons) {
                        const text = (btn.innerText || btn.textContent || '').toLowerCase();
                        if (text.includes('verify') || text.includes('xác minh') || text.includes('claim offer')) {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if button_found:
                # Click using evaluate
                await self.page.evaluate("""
                    () => {
                        const allButtons = Array.from(document.querySelectorAll('button, a'));
                        for (let btn of allButtons) {
                            const text = (btn.innerText || btn.textContent || '').toLowerCase();
                            if (text.includes('verify') || text.includes('xác minh') || text.includes('claim offer')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                return
            
            # Button not found - might be Cloudflare/CAPTCHA
            error_msg = f"⚠️ Verify button not found. Possible Cloudflare/CAPTCHA. Please check manually in browser #{row_number + 1 if row_number is not None else '?'}."
            self.log_message.emit(error_msg)
            raise Exception(f"ELEMENT_NOT_FOUND:{error_msg}")
        except Exception as e:
            error_str = str(e)
            # If already formatted, just re-raise
            if error_str.startswith("CLOUDFLARE_DETECTED:") or error_str.startswith("ELEMENT_NOT_FOUND:"):
                raise
            # Otherwise, format the error
            self.log_message.emit(f"Error clicking verify: {error_str}")
            raise Exception(f"ELEMENT_NOT_FOUND:⚠️ Verify button not found. Possible Cloudflare/CAPTCHA. Please check manually in browser #{row_number + 1 if row_number is not None else '?'}.")
    
    async def wait_for_sheerid(self):
        """Đợi redirect đến SheerID"""
        max_wait = 30
        for i in range(max_wait):
            current_url = self.page.url
            if 'services.sheerid.com' in current_url:
                self.log_message.emit("Redirected to SheerID")
                return
            await asyncio.sleep(1)
        
        raise Exception("Timeout waiting for SheerID redirect")
    
    async def generate_email_from_tinyhost(self):
        """Generate email từ tinyhost.shop API - Giống extension"""
        try:
            import aiohttp
            import random
            import string
            
            self.log_message.emit("📧 Generating new email from tinyhost.shop...")
            
            # Get random domains
            async with aiohttp.ClientSession() as session:
                async with session.get('https://tinyhost.shop/api/random-domains/?limit=10') as resp:
                    if resp.status != 200:
                        raise Exception('Failed to fetch domains')
                    
                    data = await resp.json()
                    domains = data.get('domains', [])
                    
                    if len(domains) == 0:
                        raise Exception('No domains available')
                    
                    # Filter out blocked domains (giống extension)
                    blocked_domains = ['tempmail.com', 'guerrillamail.com']
                    filtered_domains = [d for d in domains if not any(d.endswith(bd) for bd in blocked_domains)]
                    
                    if len(filtered_domains) == 0:
                        raise Exception('No valid domains available')
                    
                    # Pick random domain
                    domain = random.choice(filtered_domains)
                    
                    # Generate random username (16 ký tự - giống extension)
                    chars = string.ascii_lowercase + string.digits
                    username = ''.join(random.choices(chars, k=16))
                    
                    email = f"{username}@{domain}"
                    
                    self.log_message.emit(f"✅ Email generated: {email}")
                    return email
                    
        except Exception as e:
            self.log_message.emit(f"❌ Failed to generate email: {str(e)}")
            raise
    
    # Các method fill form đã được thay thế bằng API calls
    # Giữ lại để tương thích, nhưng không được sử dụng nữa
        """Điền form verification"""
        try:
            # Select status (Veteran)
            await self.select_status()
            await asyncio.sleep(1)
            
            # Select branch
            await self.select_branch()
            await asyncio.sleep(1)
            
            # Fill name
            await self.fill_name()
            await asyncio.sleep(1)
            
            # Fill date of birth
            await self.fill_date_of_birth()
            await asyncio.sleep(1)
            
            # Fill discharge date
            await self.fill_discharge_date()
            await asyncio.sleep(1)
            
            # Fill email
            await self.fill_email()
            await asyncio.sleep(1)
            
        except Exception as e:
            self.log_message.emit(f"Error filling form: {str(e)}")
            raise
    
    async def select_status(self):
        """Chọn military status - Match extension logic"""
        try:
            # Wait for status button
            status_button = await self.page.wait_for_selector('#sid-military-status + button', timeout=10000, state='visible')
            await asyncio.sleep(0.5)
            
            # Check if menu is already open
            status_item = await self.page.query_selector('#sid-military-status-item-1')
            menu_already_open = status_item and await status_item.is_visible()
            
            if not menu_already_open:
                # Click to open menu
                await status_button.click()
                await asyncio.sleep(0.5)
                # Wait for menu item to appear
                status_item = await self.page.wait_for_selector('#sid-military-status-item-1', timeout=10000, state='visible')
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(0.5)
            
            # Check if already selected
            button_text = await status_button.inner_text()
            is_already_selected = 'veteran' in button_text.lower() or 'retiree' in button_text.lower()
            
            if not is_already_selected:
                # Lưu URL trước khi click (để detect reload)
                url_before = self.page.url
                await status_item.click()
                
                # Extension waits 3 seconds, và trang sẽ reload một nhịp
                await asyncio.sleep(3)
                
                # Đợi trang reload xong - đợi URL thay đổi hoặc element xuất hiện lại
                max_wait = 15
                reloaded = False
                for i in range(max_wait):
                    try:
                        current_url = self.page.url
                        # Nếu URL thay đổi hoặc branch button xuất hiện = trang đã reload
                        if current_url != url_before:
                            reloaded = True
                            break
                        
                        # Check if branch button exists (indicates page reloaded)
                        branch_button = await self.page.query_selector('#sid-branch-of-service + button')
                        if branch_button and await branch_button.is_visible():
                            reloaded = True
                            break
                    except:
                        pass
                    await asyncio.sleep(1)
                
                # Đợi thêm một chút để form ổn định
                await asyncio.sleep(2)
            else:
                await asyncio.sleep(3)
        except Exception as e:
            raise Exception(f"Error selecting status: {str(e)}")
    
    async def select_branch(self):
        """Chọn branch of service - Match extension logic EXACTLY"""
        try:
            branch = self.veteran_data.get('branch', '').strip()
            
            branch_button = await self.page.wait_for_selector('#sid-branch-of-service + button', timeout=10000, state='visible')
            await branch_button.click()
            await asyncio.sleep(0.5)
            
            # Thử đợi với nhiều state khác nhau
            menu_found = False
            for attempt in range(5):
                try:
                    # Thử đợi với state='attached' trước (element có trong DOM)
                    menu = await self.page.wait_for_selector('#sid-branch-of-service-menu', timeout=2000, state='attached')
                    if menu:
                        # Kiểm tra xem có visible không
                        is_visible = await menu.is_visible()
                        if is_visible:
                            self.log_message.emit("✓ [DEBUG] Branch menu appeared and visible")
                            menu_found = True
                            break
                        else:
                            self.log_message.emit(f"⚠️ [DEBUG] Menu found but not visible (attempt {attempt + 1})")
                            await asyncio.sleep(0.5)
                except:
                    self.log_message.emit(f"⚠️ [DEBUG] Menu not found yet (attempt {attempt + 1})")
                    await asyncio.sleep(0.5)
            
            if not menu_found:
                # Debug: kiểm tra xem có element nào liên quan không
                raise Exception('Branch menu not found after clicking')
            
            await asyncio.sleep(1)
            
            # Extension: document.querySelectorAll('#sid-branch-of-service-menu .sid-input-select-list__item')
            branch_items = await self.page.query_selector_all('#sid-branch-of-service-menu .sid-input-select-list__item')
            
            if len(branch_items) == 0:
                raise Exception('Branch items not found')
            
            # Extension matching logic:
            # const branchUpper = branch.toUpperCase().trim();
            # const branchNoPrefix = branchUpper.replace(/^US\s+/, '');
            # for (let item of branchItems) {
            #     let itemText = item.innerText.toUpperCase().trim();
            #     const itemTextNoPrefix = itemText.replace(/^US\s+/, '');
            #     if (itemText === branchUpper || 
            #         itemTextNoPrefix === branchNoPrefix ||
            #         itemText.includes(branchUpper) ||
            #         branchUpper.includes(itemTextNoPrefix) ||
            #         itemTextNoPrefix.includes(branchNoPrefix) ||
            #         branchNoPrefix.includes(itemTextNoPrefix)) {
            #         item.click();
            #         matched = true;
            #         break;
            #     }
            # }
            
            branch_upper = branch.upper().strip()
            branch_no_prefix = branch_upper.replace('US ', '')
            
            matched = False
            for item in branch_items:
                item_text = (await item.inner_text()).upper().strip()
                item_text_no_prefix = item_text.replace('US ', '')
                
                # Match extension logic EXACTLY:
                # itemText === branchUpper || 
                # itemTextNoPrefix === branchNoPrefix ||
                # itemText.includes(branchUpper) ||
                # branchUpper.includes(itemTextNoPrefix) ||
                # itemTextNoPrefix.includes(branchNoPrefix) ||
                # branchNoPrefix.includes(itemTextNoPrefix)
                if (item_text == branch_upper or 
                    item_text_no_prefix == branch_no_prefix or
                    branch_upper in item_text or  # itemText.includes(branchUpper)
                    item_text_no_prefix in branch_upper or  # branchUpper.includes(itemTextNoPrefix)
                    branch_no_prefix in item_text_no_prefix or  # itemTextNoPrefix.includes(branchNoPrefix)
                    item_text_no_prefix in branch_no_prefix):  # branchNoPrefix.includes(itemTextNoPrefix)
                    await item.click()
                    matched = True
                    break
            
            if not matched:
                raise Exception(f'Branch not found: {branch}')
            
            await asyncio.sleep(0.2)  # Extension: await delay(200)
            self.log_message.emit(f"Selected branch: {branch}")
        except Exception as e:
            self.log_message.emit(f"Error selecting branch: {str(e)}")
            raise
    
    async def fill_name(self):
        """Điền tên - Match extension logic"""
        try:
            first_name = self.veteran_data.get('first', '')
            last_name = self.veteran_data.get('last', '')
            
            first_input = await self.page.wait_for_selector('#sid-first-name', timeout=10000, state='visible')
            # Set value directly and dispatch events like extension
            await first_input.evaluate(f'el => {{ el.value = "{first_name}"; el.dispatchEvent(new Event("input", {{ bubbles: true }})); el.dispatchEvent(new Event("change", {{ bubbles: true }})); }}')
            await asyncio.sleep(0.2)
            
            last_input = await self.page.wait_for_selector('#sid-last-name', timeout=10000, state='visible')
            await last_input.evaluate(f'el => {{ el.value = "{last_name}"; el.dispatchEvent(new Event("input", {{ bubbles: true }})); el.dispatchEvent(new Event("change", {{ bubbles: true }})); }}')
            await asyncio.sleep(0.2)
            
            self.log_message.emit(f"Filled name: {first_name} {last_name}")
        except Exception as e:
            self.log_message.emit(f"Error filling name: {str(e)}")
            raise
    
    async def fill_date_of_birth(self):
        """Điền ngày sinh - Match extension logic"""
        try:
            month_name = self.veteran_data.get('month', '').strip()
            day = self.veteran_data.get('day', '').strip()
            year = self.veteran_data.get('year', '').strip()
            
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            
            month_index = -1
            for i, name in enumerate(month_names):
                if month_name.lower() == name.lower():
                    month_index = i
                    break
            
            if month_index == -1:
                raise Exception(f"Invalid month: {month_name}")
            
            # Select month (extension uses monthIndex, not monthIndex + 1)
            month_button = await self.page.wait_for_selector('#sid-birthdate__month + button', timeout=10000, state='visible')
            await month_button.click()
            await self.page.wait_for_selector('#sid-birthdate__month-menu', timeout=10000, state='visible')
            await asyncio.sleep(0.2)
            
            # Extension uses sid-birthdate__month-item-{monthIndex} (0-based)
            month_item = await self.page.wait_for_selector(f'#sid-birthdate__month-item-{month_index}', timeout=5000, state='visible')
            await month_item.click()
            await asyncio.sleep(0.2)
            
            # Fill day
            day_input = await self.page.wait_for_selector('#sid-birthdate-day', timeout=10000, state='visible')
            await day_input.evaluate(f'el => {{ el.value = "{int(day)}"; el.dispatchEvent(new Event("input", {{ bubbles: true }})); el.dispatchEvent(new Event("change", {{ bubbles: true }})); }}')
            await asyncio.sleep(0.2)
            
            # Fill year
            year_input = await self.page.wait_for_selector('#sid-birthdate-year', timeout=10000, state='visible')
            await year_input.evaluate(f'el => {{ el.value = "{year}"; el.dispatchEvent(new Event("input", {{ bubbles: true }})); el.dispatchEvent(new Event("change", {{ bubbles: true }})); }}')
            await asyncio.sleep(0.2)
            
            self.log_message.emit(f"Filled DOB: {month_name} {day}, {year}")
        except Exception as e:
            self.log_message.emit(f"Error filling DOB: {str(e)}")
            raise
    
    async def fill_discharge_date(self):
        """Điền ngày xuất ngũ - Match extension logic"""
        try:
            # Select month (January - item-1)
            month_button = await self.page.wait_for_selector('#sid-discharge-date__month + button', timeout=10000, state='visible')
            await month_button.click()
            await self.page.wait_for_selector('#sid-discharge-date__month-menu', timeout=10000, state='visible')
            await asyncio.sleep(0.2)
            
            month_item = await self.page.wait_for_selector('#sid-discharge-date__month-item-1', timeout=5000, state='visible')
            await month_item.click()
            await asyncio.sleep(0.2)
            
            # Fill day
            day_input = await self.page.wait_for_selector('#sid-discharge-date-day', timeout=10000, state='visible')
            await day_input.evaluate('el => { el.value = "1"; el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); }')
            await asyncio.sleep(0.2)
            
            # Fill year
            year_input = await self.page.wait_for_selector('#sid-discharge-date-year', timeout=10000, state='visible')
            await year_input.evaluate('el => { el.value = "2025"; el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); }')
            await asyncio.sleep(0.2)
            
            self.log_message.emit("Filled discharge date")
        except Exception as e:
            self.log_message.emit(f"Error filling discharge date: {str(e)}")
            raise
    
    async def fill_email(self):
        """Điền email - Match extension logic"""
        try:
            if not self.current_email:
                await self.generate_email()
            
            email_input = await self.page.wait_for_selector('#sid-email', timeout=10000, state='visible')
            await email_input.evaluate(f'el => {{ el.value = "{self.current_email}"; el.dispatchEvent(new Event("input", {{ bubbles: true }})); el.dispatchEvent(new Event("change", {{ bubbles: true }})); }}')
            await asyncio.sleep(0.2)
            
            self.log_message.emit(f"Filled email: {self.current_email}")
        except Exception as e:
            self.log_message.emit(f"Error filling email: {str(e)}")
            raise
    
    async def submit_form(self):
        """Submit form"""
        try:
            submit_button = await self.page.wait_for_selector('#sid-submit-btn-collect-info', timeout=10000)
            await submit_button.click()
            self.log_message.emit("Form submitted")
        except Exception as e:
            self.log_message.emit(f"Error submitting form: {str(e)}")
            raise
    
    async def check_verification_status_from_page(self):
        """Check verification status từ page content - Giống extension logic"""
        try:
            # Đợi page load
            await asyncio.sleep(2)
            
            # Get current URL
            current_url = self.page.url
            body_text = ""
            heading_text = ""
            page_html = ""
            
            try:
                body_text = await self.page.evaluate("() => document.body.innerText || document.body.textContent || ''")
                heading_text = await self.page.evaluate("""
                    () => {
                        const heading = document.querySelector('h1, h2, h3, .heading, [class*="heading"]');
                        return heading ? (heading.innerText || heading.textContent || '') : '';
                    }
                """)
                page_html = await self.page.evaluate("() => document.body.innerHTML || ''")
            except:
                pass
            
            # Check URL cho sourcesUnavailable (giống extension)
            if 'sourcesUnavailable' in current_url or 'Error sourcesUnavailable' in current_url:
                self.log_message.emit("🚫 VPN/PROXY Error: sourcesUnavailable detected")
                return {
                    'success': False,
                    'status': 'sourcesUnavailable',
                    'message': '🚫 VPN/PROXY Error: sourcesUnavailable detected. Please change VPN/PROXY and restart.'
                }
            
            # Check error div (giống extension)
            try:
                error_div = await self.page.query_selector('.sid-error-msg')
                if error_div:
                    error_text = await error_div.inner_text()
                    if 'Not approved' in error_text:
                        self.log_message.emit("❌ Not Approved detected")
                        return {
                            'success': False,
                            'status': 'Not Approved',
                            'message': '❌ Not Approved - trying next data...'
                        }
                    if 'sourcesUnavailable' in error_text:
                        self.log_message.emit("🚫 VPN/PROXY Error: sourcesUnavailable detected")
                        return {
                            'success': False,
                            'status': 'sourcesUnavailable',
                            'message': '🚫 VPN/PROXY Error: sourcesUnavailable detected. Please change VPN/PROXY and restart.'
                        }
            except:
                pass
            
            # Check body text (giống extension)
            body_lower = body_text.lower()
            
            # Check sourcesUnavailable
            if ('sourcesunavailable' in body_lower or 
                'sources unavailable' in body_lower or
                'unable to verify you at this time' in body_lower or
                'unable to verify you' in body_lower):
                self.log_message.emit("🚫 VPN/PROXY Error: Unable to verify")
                return {
                    'success': False,
                    'status': 'sourcesUnavailable',
                    'message': '🚫 VPN/PROXY Error: Unable to verify. Please change VPN/PROXY and restart.'
                }
            
            # Check Not Approved
            if ('not approved' in body_lower or 'not approved' in page_html.lower()):
                self.log_message.emit("❌ Not Approved detected")
                return {
                    'success': False,
                    'status': 'Not Approved',
                    'message': '❌ Not Approved - trying next data...'
                }
            
            # Check Limit Exceeded
            if ('verification limit exceeded' in body_lower or 
                'limit exceeded' in body_lower or
                'verification limit exceeded' in page_html.lower() or
                'limit exceeded' in page_html.lower()):
                self.log_message.emit("❌ Verification Limit Exceeded detected")
                return {
                    'success': False,
                    'status': 'Limit Exceeded',
                    'message': '❌ Verification Limit Exceeded - data already verified'
                }
            
            # Check Success
            if ("you've been verified" in body_lower or 
                'verified' in body_lower and 'not' not in body_lower[:body_lower.find('verified')+10]):
                # Extract veteran name if possible
                veteran_name = ""
                try:
                    # Try to find name in page
                    name_match = await self.page.evaluate("""
                        () => {
                            const text = document.body.innerText || '';
                            const match = text.match(/(?:verified|verified for)\\s+([A-Z][a-z]+\\s+[A-Z][a-z]+)/i);
                            return match ? match[1] : '';
                        }
                    """)
                    if name_match:
                        veteran_name = name_match
                except:
                    pass
                
                self.log_message.emit(f"✅ Verification successful!")
                return {
                    'success': True,
                    'status': 'Verified!',
                    'message': f"✓ Verified! {veteran_name}" if veteran_name else "✓ Verified!",
                    'veteran_name': veteran_name
                }
            
            # Check Error khác
            if ('error' in body_lower and 'not approved' not in body_lower and 'limit exceeded' not in body_lower):
                # Check heading text
                heading_lower = heading_text.lower()
                if ('error' in heading_lower or 'unable' in heading_lower):
                    error_msg = heading_text or "Unknown error"
                    self.log_message.emit(f"❌ Error detected: {error_msg}")
                    return {
                        'success': False,
                        'status': 'Error',
                        'message': f"❌ {error_msg}"
                    }
            
            return None  # Không tìm thấy status rõ ràng
        except Exception as e:
            self.log_message.emit(f"⚠️ Error checking verification status: {str(e)}")
            return None
    
    async def check_verification_result(self):
        """Kiểm tra kết quả verification"""
        try:
            await asyncio.sleep(5)
            
            # Check for email check page
            current_url = self.page.url
            body_text = await self.page.inner_text('body')
            
            if 'check your email' in body_text.lower():
                # Need to read email and click verification link
                await self.read_email_and_verify()
                await asyncio.sleep(5)
                body_text = await self.page.inner_text('body')
            
            # Check result
            if 'verified' in body_text.lower() or "you've been verified" in body_text.lower():
                return {'success': True}
            elif 'not approved' in body_text.lower():
                return {'success': False, 'error': 'Not approved'}
            elif 'limit exceeded' in body_text.lower():
                return {'success': False, 'error': 'Verification limit exceeded'}
            else:
                return {'success': False, 'error': 'Unknown result'}
                
        except Exception as e:
            self.log_message.emit(f"Error checking result: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def read_email_and_click_verification_link(self):
        """Đọc email từ tinyhost.shop và click verification link - Giống extension"""
        try:
            if not self.current_email:
                raise Exception("No email to check")
            
            username, domain = self.current_email.split('@')
            if not username or not domain:
                raise Exception('Invalid email format')
            
            self.log_message.emit(f"📧 Reading emails from tinyhost.shop...")
            
            # Call email API - giống extension
            import aiohttp
            max_retries = 10
            retry_count = 0
            
            while retry_count < max_retries:
                async with aiohttp.ClientSession() as session:
                    url = f'https://tinyhost.shop/api/email/{domain}/{username}/?page=1&limit=20'
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            emails = data.get('emails', [])
                            
                            if len(emails) == 0:
                                retry_count += 1
                                if retry_count >= max_retries:
                                    raise Exception("No emails found after max retries")
                                self.log_message.emit(f"📭 No emails found, retrying... ({retry_count}/{max_retries})")
                                await asyncio.sleep(5)
                                continue
                            
                            # Sort emails by date (newest first) - giống extension
                            emails.sort(key=lambda x: x.get('date', ''), reverse=True)
                            
                            # Find verification email
                            verification_link = None
                            for email in emails:
                                html_body = email.get('html_body', '') or email.get('body', '')
                                link_match = re.search(r'https://services\.sheerid\.com/verify/[^\s"\'<>()]+', html_body, re.IGNORECASE)
                                if link_match:
                                    verification_link = link_match.group(0).replace('&amp;', '&')
                                    break
                            
                            if verification_link:
                                self.log_message.emit(f"✅ Found verification link, opening...")
                                await self.page.goto(verification_link)
                                await asyncio.sleep(3)
                                return
                            else:
                                retry_count += 1
                                if retry_count >= max_retries:
                                    raise Exception("Verification link not found in email")
                                self.log_message.emit(f"📭 Verification link not found, retrying... ({retry_count}/{max_retries})")
                                await asyncio.sleep(5)
                        else:
                            raise Exception(f"Failed to fetch emails: {resp.status}")
        except Exception as e:
            self.log_message.emit(f"❌ Error reading email: {str(e)}")
            raise

