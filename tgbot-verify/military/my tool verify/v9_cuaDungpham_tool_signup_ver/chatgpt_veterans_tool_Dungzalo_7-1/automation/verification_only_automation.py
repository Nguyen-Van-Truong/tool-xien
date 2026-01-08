"""
Verification Only Automation - Chỉ verify veterans, đóng browser sau khi xong
Sử dụng browser thật (Brave/Edge/Chrome) và connect qua CDP để automation
"""

from PyQt6.QtCore import QObject, pyqtSignal
from automation.verification_flow import VerificationFlow
from automation.signup_flow import SignupFlow
from utils.browser_fingerprint import BrowserFingerprint
import asyncio
import os
import platform
import subprocess
import time
import random
from playwright.async_api import async_playwright


class VerificationOnlyAutomation(QObject):
    """Verification only automation - chỉ làm verify
    Sử dụng browser thật và connect qua CDP để automation
    """
    
    log_message = pyqtSignal(str)
    
    def __init__(self, account_data, veteran_data, use_proxy=False, proxy_data=None, browser_id=None):
        super().__init__()
        self.account_data = account_data
        self.veteran_data = veteran_data
        self.use_proxy = use_proxy
        self.proxy_data = proxy_data
        self.browser_id = browser_id or account_data.get('email', 'default')
        self.is_running = True
        self.playwright = None
        self.browser = None  # Browser object from CDP connection
        self.context = None  # BrowserContext
        self.page = None
        self.browser_process = None
        self.cdp_port = None
        self.fingerprint = BrowserFingerprint.generate_fingerprint(self.browser_id)
    
    def find_browser_executable(self):
        """Tìm browser thật trên máy: Brave -> Edge -> Chrome - Sử dụng method chung"""
        # Check if browser info was saved before
        saved_info = BrowserFingerprint.load_browser_info(self.browser_id)
        if saved_info:
            executable_path = saved_info.get('executable_path')
            browser_name = saved_info.get('browser_name')
            channel = saved_info.get('channel')
            
            # Verify executable still exists
            if executable_path and os.path.exists(executable_path):
                return executable_path, browser_name, channel
            elif channel:  # Edge via channel
                return None, browser_name, channel
        
        # Find browser using common method
        executable_path, browser_name, channel = BrowserFingerprint.find_browser_executable()
        
        # Save browser info for future use
        if browser_name:
            BrowserFingerprint.save_browser_info(self.browser_id, browser_name, executable_path, channel)
        
        return executable_path, browser_name, channel
    
    def close_browser_if_running(self):
        """Đóng browser process nếu đang chạy"""
        if self.browser_process:
            try:
                if platform.system() == "Windows":
                    self.browser_process.terminate()
                    time.sleep(1)
                    # Force kill nếu vẫn còn
                    if self.browser_process.poll() is None:
                        self.browser_process.kill()
                else:
                    self.browser_process.terminate()
                    time.sleep(1)
                    if self.browser_process.poll() is None:
                        self.browser_process.kill()
                self.log_message.emit("✓ Đã đóng browser cũ")
            except Exception as e:
                self.log_message.emit(f"⚠️ Lỗi khi đóng browser: {str(e)}")
            finally:
                self.browser_process = None
        
        # Đóng Playwright connection nếu có
        if hasattr(self, 'browser') and self.browser:
            try:
                # Note: Không close browser context vì nó sẽ đóng browser thật
                # Chỉ disconnect
                pass
            except:
                pass
    
    def open_real_browser_with_cdp(self):
        """Mở browser thật với CDP (Chrome DevTools Protocol) để Playwright có thể control"""
        # Đóng browser cũ nếu đang chạy
        self.close_browser_if_running()
        
        # Get unique user data directory
        user_data_dir = BrowserFingerprint.get_user_data_dir(self.browser_id)
        
        # Find browser executable (sẽ lưu info để dùng sau)
        browser_path, browser_name, channel = self.find_browser_executable()
        
        if not browser_name:
            raise Exception("Không tìm thấy browser thật (Brave/Edge/Chrome) trên máy")
        
        # Random CDP port (9222-9322)
        self.cdp_port = random.randint(9222, 9322)
        
        # Kích thước cửa sổ nhỏ hơn (640x480) để mở nhiều cửa sổ cùng lúc
        # Tính toán vị trí để các cửa sổ không chồng lên nhau
        window_width = 640
        window_height = 480
        # Sử dụng browser_id để tạo vị trí khác nhau (ví dụ: row * 50)
        window_x = (hash(self.browser_id) % 10) * 50
        window_y = (hash(self.browser_id) % 10) * 50
        
        # Build command to open browser với remote debugging port
        if browser_path:
            # Use executable path
            if platform.system() == "Windows":
                cmd = [
                    browser_path,
                    f'--user-data-dir={user_data_dir}',
                    f'--remote-debugging-port={self.cdp_port}',
                    f'--window-size={window_width},{window_height}',
                    f'--window-position={window_x},{window_y}',
                    'https://chatgpt.com/veterans-claim'
                ]
            else:
                cmd = [
                    browser_path,
                    f'--user-data-dir={user_data_dir}',
                    f'--remote-debugging-port={self.cdp_port}',
                    f'--window-size={window_width},{window_height}',
                    f'--window-position={window_x},{window_y}',
                    'https://chatgpt.com/veterans-claim'
                ]
        else:
            # Edge via channel - use start command
            if platform.system() == "Windows":
                cmd = [
                    'start',
                    'msedge',
                    f'--user-data-dir={user_data_dir}',
                    f'--remote-debugging-port={self.cdp_port}',
                    f'--window-size={window_width},{window_height}',
                    f'--window-position={window_x},{window_y}',
                    'https://chatgpt.com/veterans-claim'
                ]
            else:
                raise Exception("Edge channel chỉ hỗ trợ Windows")
        
        # Add proxy if needed
        if self.use_proxy and self.proxy_data:
            proxy_url = f"http://{self.proxy_data.get('host')}:{self.proxy_data.get('port')}"
            if browser_path:
                cmd.append(f'--proxy-server={proxy_url}')
            else:
                # For Edge via start command, need different approach
                pass
        
        # Open browser
        try:
            if platform.system() == "Windows":
                if browser_path:
                    self.browser_process = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    # Edge via start
                    subprocess.Popen(cmd, shell=True)
                    self.browser_process = None  # Can't track Edge via start
            else:
                self.browser_process = subprocess.Popen(cmd)
            
            # Wait for browser to start and CDP to be ready
            time.sleep(5)
            
            return browser_name
        except Exception as e:
            raise Exception(f"Không thể mở browser: {str(e)}")
    
    async def connect_to_browser_via_cdp(self):
        """Connect Playwright vào browser thật đã mở qua CDP"""
        self.playwright = await async_playwright().start()
        
        # Connect to browser via CDP
        try:
            # Đợi thêm một chút để browser sẵn sàng
            await asyncio.sleep(2)
            
            # connect_over_cdp returns Browser, not BrowserContext
            self.browser = await self.playwright.chromium.connect_over_cdp(
                f"http://localhost:{self.cdp_port}"
            )
            
            # Đợi browser contexts sẵn sàng
            await asyncio.sleep(1)
            
            # Get all contexts from the browser
            contexts = self.browser.contexts
            if contexts:
                # Use existing context
                self.context = contexts[0]
                # Đợi pages load
                await asyncio.sleep(1)
                
                # Dùng tab hiện có (không đóng tabs cũ để tránh browser crash)
                pages = self.context.pages
                if pages:
                    # Dùng tab đầu tiên (tab đã mở với veterans-claim)
                    self.page = pages[0]
                else:
                    # Nếu không có tab, tạo tab mới
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            self.page = await self.context.new_page()
                            break
                        except Exception as e:
                            if retry < max_retries - 1:
                                await asyncio.sleep(2)
                            else:
                                raise
            else:
                # Create new context if none exists
                self.context = await self.browser.new_context(
                    viewport=self.fingerprint['viewport'],
                    user_agent=self.fingerprint['user_agent'],
                    locale=self.fingerprint['locale'][0],
                    timezone_id=self.fingerprint['timezone_id'],
                    permissions=self.fingerprint['permissions'],
                    geolocation=self.fingerprint['geolocation'],
                    extra_http_headers={
                        'Accept-Language': f"{self.fingerprint['locale'][0]},{self.fingerprint['locale'][1]}",
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0'
                    }
                )
                await asyncio.sleep(1)
                self.page = await self.context.new_page()
            
            # Apply stealth script
            stealth_script = BrowserFingerprint.get_stealth_script()
            await self.page.add_init_script(stealth_script)
            
            # Apply fingerprint-specific overrides
            await self.page.add_init_script(f"""
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {self.fingerprint['hardware_concurrency']}
                }});
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {self.fingerprint['device_memory']}
                }});
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{self.fingerprint['platform']}'
                }});
            """)
            
            return self.page
        except Exception as e:
            self.log_message.emit(f"❌ Failed to connect via CDP: {str(e)}")
            raise
    
    async def initialize_browser_headless(self):
        """Khởi tạo browser bằng Playwright - VISIBLE MODE để debug"""
        self.log_message.emit("🚀 [DEBUG] Starting browser (VISIBLE mode for debugging)...")
        # Đóng browser cũ nếu đang chạy
        self.close_browser_if_running()
        
        # Get unique user data directory để load cookies
        user_data_dir = BrowserFingerprint.get_user_data_dir(self.browser_id)
        
        # Find browser executable để dùng channel nếu có
        browser_path, browser_name, channel = self.find_browser_executable()
        
        # Start Playwright
        self.playwright = await async_playwright().start()
        
        # Get fingerprint
        fingerprint = BrowserFingerprint.generate_fingerprint(self.browser_id)
        
        # Browser options với stealth flags
        browser_options = {
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        }
        
        # Use channel if available (Edge)
        if channel:
            browser_options['channel'] = channel
        
        # Launch browser với persistent context để load cookies
        # Note: locale phải là string, không phải list
        locale_str = fingerprint['locale'][0] if isinstance(fingerprint['locale'], list) else fingerprint['locale']
        
        self.log_message.emit(f"🚀 [DEBUG] Launching browser with user_data_dir: {user_data_dir}")
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # VISIBLE mode for debugging - set to True for production
            viewport=fingerprint['viewport'],
            user_agent=fingerprint['user_agent'],
            locale=locale_str,
            timezone_id=fingerprint['timezone_id'],
            permissions=fingerprint['permissions'],
            geolocation=fingerprint['geolocation'],
            **browser_options
        )
        
        # Get or create page
        pages = self.context.pages
        if pages:
            self.page = pages[0]
        else:
            self.page = await self.context.new_page()
        
        # Inject stealth scripts
        stealth_script = BrowserFingerprint.get_stealth_script()
        await self.page.add_init_script(stealth_script)
        
        # Apply fingerprint-specific overrides
        await self.page.add_init_script(f"""
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fingerprint['hardware_concurrency']}
            }});
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint['device_memory']}
            }});
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint['platform']}'
            }});
        """)
        
        # Navigate to ChatGPT để load cookies từ session trước đó
        # Điều này đảm bảo cookies được load trước khi navigate đến veterans-claim
        self.log_message.emit(f"📁 [DEBUG] Loading cookies from: {user_data_dir}")
        try:
            self.log_message.emit("🌐 [DEBUG] Navigating to https://chatgpt.com...")
            await self.page.goto('https://chatgpt.com', wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)  # Đợi cookies được load
            current_url = self.page.url
            self.log_message.emit(f"✓ [DEBUG] Current URL: {current_url}")
            self.log_message.emit("✓ Cookies loaded from previous session")
        except Exception as e:
            self.log_message.emit(f"⚠️ [DEBUG] Warning loading cookies: {str(e)}")
        
        self.log_message.emit(f"✓ Browser VISIBLE mode initialized (for debugging)")
        
        return browser_name or "Chromium"
    
    async def initialize_browser(self):
        """Khởi tạo browser - Sử dụng CDP với browser thật để load cookies đúng cách"""
        try:
            # Mở browser thật với CDP để load cookies từ Reg/Login
            browser_name = self.open_real_browser_with_cdp()
            await self.connect_to_browser_via_cdp()
            return browser_name
        except Exception as e:
            self.log_message.emit(f"❌ Failed to initialize browser: {str(e)}")
            raise
    
    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            # Close CDP connection
            if self.playwright:
                await self.playwright.stop()
            # Đóng browser process nếu có
            self.close_browser_if_running()
        except Exception as e:
            self.log_message.emit(f"Cleanup error: {str(e)}")
    
    def stop(self):
        """Stop automation - Close browser if still running"""
        self.is_running = False
        if self.browser_process:
            try:
                self.browser_process.terminate()
            except:
                pass
    
    async def check_if_logged_in(self):
        """Kiểm tra xem đã đăng nhập ChatGPT chưa"""
        try:
            current_url = self.page.url
            
            # If on auth page, not logged in
            if 'auth' in current_url.lower() or 'login' in current_url.lower():
                return False
            
            # If on ChatGPT page, check for login indicators
            if 'chatgpt.com' in current_url.lower():
                # Check for elements that indicate logged in
                body_text = await self.page.inner_text('body')
                
                # Login indicators
                has_new_chat = 'new chat' in body_text.lower() or 'new conversation' in body_text.lower()
                has_textarea = await self.page.query_selector('textarea[placeholder*="Message"], textarea#prompt-textarea')
                has_sidebar = await self.page.query_selector('[data-testid="sidebar"], nav[aria-label*="chat"]')
                
                # Not logged in indicators
                has_signup = 'sign up' in body_text.lower() and 'log in' in body_text.lower()
                has_login_button = await self.page.query_selector('button:has-text("Log in"), a:has-text("Log in")')
                
                if has_signup or has_login_button:
                    self.log_message.emit("🔍 [DEBUG] Found login/signup buttons - not logged in")
                    return False
                
                if has_new_chat or has_textarea or has_sidebar:
                    self.log_message.emit("🔍 [DEBUG] Found logged-in indicators")
                    return True
            
            return False
        except Exception as e:
            self.log_message.emit(f"⚠️ [DEBUG] Error checking login status: {str(e)}")
            return False
    
    def run(self):
        """Run verification only (synchronous wrapper)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_async())
            loop.close()
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def run_async(self):
        """Run verification only async - WITH AUTO-LOGIN"""
        try:
            if not self.is_running:
                return {'success': False, 'error': 'Stopped by user'}
            
            # Initialize browser (mở browser thật và connect qua CDP)
            await self.initialize_browser()
            
            if not self.is_running:
                return {'success': False, 'error': 'Stopped by user'}
            
            # Kiểm tra URL hiện tại
            current_url = self.page.url
            self.log_message.emit(f"📍 [DEBUG] Current URL: {current_url}")
            
            # === AUTO-LOGIN LOGIC ===
            # Check if logged in by looking for login indicators
            is_logged_in = await self.check_if_logged_in()
            
            if not is_logged_in:
                self.log_message.emit("🔐 [LOGIN] Not logged in, starting auto-login...")
                
                # Chạy SignupFlow để tự động đăng nhập
                signup_flow = SignupFlow(self.page, self.account_data)
                signup_flow.log_message.connect(self.log_message.emit)
                
                signup_result = await signup_flow.run()
                
                if not signup_result.get('success'):
                    error_msg = signup_result.get('error', 'Login failed')
                    self.log_message.emit(f"❌ [LOGIN] Auto-login failed: {error_msg}")
                    return {'success': False, 'error': f'Auto-login failed: {error_msg}'}
                
                self.log_message.emit("✅ [LOGIN] Auto-login successful!")
                await asyncio.sleep(2)
                
                # Verify login success
                is_logged_in = await self.check_if_logged_in()
                if not is_logged_in:
                    return {'success': False, 'error': 'Login appeared to succeed but not logged in'}
            else:
                self.log_message.emit("✅ [LOGIN] Already logged in")
            
            # === NAVIGATE TO VETERANS PAGE ===
            current_url = self.page.url
            if 'veterans-claim' not in current_url.lower():
                self.log_message.emit("🌐 [DEBUG] Navigating to veterans-claim page...")
                try:
                    await self.page.goto('https://chatgpt.com/veterans-claim', wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(3)
                except Exception:
                    pass
            
            # Run verification flow - Pass account_data để dùng emailLogin
            verification_flow = VerificationFlow(self.page, self.veteran_data, self.account_data)
            verification_flow.log_message.connect(self.log_message.emit)
            # Pass row_number để hiển thị trong error message
            row_number = getattr(self, 'row_number', None)
            if row_number is not None:
                verification_flow.row_number = row_number
            
            verification_result = await verification_flow.run()
            
            # Return result với status từ verification_result
            if verification_result.get('success'):
                status = verification_result.get('status', 'Verified!')
                message = verification_result.get('message', f"✓ Verified! {self.veteran_data.get('first', '')} {self.veteran_data.get('last', '')}")
                self.log_message.emit(message)
                # Wait a bit before closing
                await asyncio.sleep(2)
                return {
                    'success': True,
                    'status': status,
                    'message': message,
                    'name': verification_result.get('veteran_name', f"{self.veteran_data.get('first', '')} {self.veteran_data.get('last', '')}")
                }
            else:
                status = verification_result.get('status', 'Failed')
                message = verification_result.get('message', verification_result.get('error', 'Unknown error'))
                self.log_message.emit(message)
                return {
                    'success': False,
                    'status': status,
                    'message': message,
                    'error': message
                }
            
        except Exception as e:
            error_str = str(e)
            self.log_message.emit(f"Verification error: {error_str}")
            
            # Check if it's Cloudflare/CAPTCHA or element not found error
            if 'CLOUDFLARE_DETECTED:' in error_str or 'ELEMENT_NOT_FOUND:' in error_str:
                # Extract the formatted error message
                if ':' in error_str:
                    error_msg = error_str.split(':', 1)[1]
                else:
                    error_msg = error_str
                
                # DON'T close browser - let user check manually
                self.log_message.emit("⚠️ Browser will remain open for manual check")
                return {
                    'success': False,
                    'status': 'Cloudflare Detected',
                    'message': error_msg,
                    'keep_browser_open': True  # Flag để không đóng browser
                }
            
            return {'success': False, 'error': error_str}
        finally:
            # Only cleanup if not Cloudflare/CAPTCHA error
            if 'keep_browser_open' not in locals() or not locals().get('keep_browser_open', False):
                await self.cleanup()
