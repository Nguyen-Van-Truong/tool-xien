"""
ChatGPT Automation - Main automation logic (DEPRECATED - Use RegLoginAutomation + VerificationOnlyAutomation instead)
File này được giữ lại để tham khảo, nhưng đã được thay thế bằng:
- RegLoginAutomation: Xử lý đăng ký/đăng nhập với browser thật
- VerificationOnlyAutomation: Xử lý verification với browser thật + CDP

Tất cả automation hiện tại đều dùng browser thật (Brave/Edge/Chrome) với fingerprint riêng cho mỗi browser_id.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from automation.signup_flow import SignupFlow
from automation.verification_flow import VerificationFlow
from utils.email_api import EmailAPI
from utils.browser_fingerprint import BrowserFingerprint
import asyncio
import os
import platform
import subprocess
import time
import random
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class ChatGPTAutomation(QObject):
    """Main automation class - DEPRECATED
    
    Sử dụng browser thật với CDP để automation.
    Mỗi browser_id có fingerprint riêng.
    """
    
    log_message = pyqtSignal(str)
    
    def __init__(self, account_data, veteran_data, use_proxy=False, proxy_data=None, headless=True, browser_id=None):
        super().__init__()
        self.account_data = account_data
        self.veteran_data = veteran_data
        self.use_proxy = use_proxy
        self.proxy_data = proxy_data
        self.headless = headless
        self.browser_id = browser_id or account_data.get('email', 'default')
        self.is_running = True
        
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.browser_process = None
        self.cdp_port = None
        
        # Generate unique fingerprint for this browser
        self.fingerprint = BrowserFingerprint.generate_fingerprint(self.browser_id)
        
        # Initialize flows
        self.signup_flow = None
        self.verification_flow = None
    
    def find_browser_executable(self):
        """Tìm browser thật trên máy: Brave -> Edge -> Chrome"""
        saved_info = BrowserFingerprint.load_browser_info(self.browser_id)
        if saved_info:
            executable_path = saved_info.get('executable_path')
            browser_name = saved_info.get('browser_name')
            channel = saved_info.get('channel')
            
            if executable_path and os.path.exists(executable_path):
                return executable_path, browser_name, channel
            elif channel:
                return None, browser_name, channel
        
        executable_path, browser_name, channel = BrowserFingerprint.find_browser_executable()
        if browser_name:
            BrowserFingerprint.save_browser_info(self.browser_id, browser_name, executable_path, channel)
        
        return executable_path, browser_name, channel
    
    def open_real_browser_with_cdp(self):
        """Mở browser thật với CDP"""
        user_data_dir = BrowserFingerprint.get_user_data_dir(self.browser_id)
        browser_path, browser_name, channel = self.find_browser_executable()
        
        if not browser_name:
            raise Exception("Không tìm thấy browser thật (Brave/Edge/Chrome) trên máy")
        
        # Random CDP port
        self.cdp_port = random.randint(9222, 9322)
        
        if browser_path:
            if platform.system() == "Windows":
                cmd = [
                    browser_path,
                    f'--user-data-dir={user_data_dir}',
                    f'--remote-debugging-port={self.cdp_port}',
                    '--start-maximized',
                    'https://chatgpt.com'
                ]
            else:
                cmd = [
                    browser_path,
                    f'--user-data-dir={user_data_dir}',
                    f'--remote-debugging-port={self.cdp_port}',
                    '--start-maximized',
                    'https://chatgpt.com'
                ]
        else:
            if platform.system() == "Windows":
                cmd = [
                    'start',
                    'msedge',
                    f'--user-data-dir={user_data_dir}',
                    f'--remote-debugging-port={self.cdp_port}',
                    '--start-maximized',
                    'https://chatgpt.com'
                ]
            else:
                raise Exception("Edge channel chỉ hỗ trợ Windows")
        
        if self.use_proxy and self.proxy_data:
            proxy_url = f"http://{self.proxy_data.get('host')}:{self.proxy_data.get('port')}"
            if browser_path:
                cmd.append(f'--proxy-server={proxy_url}')
        
        try:
            if platform.system() == "Windows":
                if browser_path:
                    self.browser_process = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    subprocess.Popen(cmd, shell=True)
                    self.browser_process = None
            else:
                self.browser_process = subprocess.Popen(cmd)
            
            time.sleep(3)
            self.log_message.emit(f"✓ Browser thật đã mở: {browser_name}")
            self.log_message.emit(f"📁 User data dir: {user_data_dir}")
            self.log_message.emit(f"🔌 CDP port: {self.cdp_port}")
            return browser_name
        except Exception as e:
            raise Exception(f"Không thể mở browser: {str(e)}")
    
    async def connect_to_browser_via_cdp(self):
        """Connect Playwright vào browser thật qua CDP"""
        self.playwright = await async_playwright().start()
        
        try:
            self.context = await self.playwright.chromium.connect_over_cdp(
                f"http://localhost:{self.cdp_port}"
            )
            
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()
            
            # Apply stealth script với fingerprint
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
            
            self.log_message.emit("✓ Connected to browser via CDP")
            return self.page
        except Exception as e:
            self.log_message.emit(f"❌ Failed to connect via CDP: {str(e)}")
            raise
    
    async def initialize_browser(self):
        """Khởi tạo browser thật và connect qua CDP"""
        browser_name = self.open_real_browser_with_cdp()
        await self.connect_to_browser_via_cdp()
        return self.page
    
    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.context:
                try:
                    await self.context.close()
                except:
                    pass
            if self.playwright:
                await self.playwright.stop()
            
            if self.browser_process:
                try:
                    self.browser_process.terminate()
                    self.browser_process.wait(timeout=5)
                except:
                    try:
                        self.browser_process.kill()
                    except:
                        pass
        except Exception as e:
            self.log_message.emit(f"Cleanup error: {str(e)}")
    
    def stop(self):
        """Stop automation"""
        self.is_running = False
        if self.browser_process:
            try:
                self.browser_process.terminate()
            except:
                pass
    
    def run(self):
        """Run automation (synchronous wrapper)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_async())
            loop.close()
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def run_async(self):
        """Run automation async"""
        try:
            if not self.is_running:
                return {'success': False, 'error': 'Stopped by user'}
            
            # Initialize browser (browser thật + CDP)
            await self.initialize_browser()
            self.log_message.emit("Browser initialized")
            
            if not self.is_running:
                return {'success': False, 'error': 'Stopped by user'}
            
            # Step 1: Signup/Login
            self.signup_flow = SignupFlow(self.page, self.account_data)
            self.signup_flow.log_message.connect(self.log_message.emit)
            
            signup_result = await self.signup_flow.run()
            if not signup_result['success']:
                return {'success': False, 'error': f"Signup failed: {signup_result.get('error', 'Unknown error')}"}
            
            if not self.is_running:
                return {'success': False, 'error': 'Stopped by user'}
            
            self.log_message.emit("Signup/Login completed")
            
            # Step 2: Verification
            self.verification_flow = VerificationFlow(self.page, self.veteran_data)
            self.verification_flow.log_message.connect(self.log_message.emit)
            
            verification_result = await self.verification_flow.run()
            if not verification_result['success']:
                return {'success': False, 'error': f"Verification failed: {verification_result.get('error', 'Unknown error')}"}
            
            # Success
            return {
                'success': True,
                'name': f"{self.veteran_data.get('first', '')} {self.veteran_data.get('last', '')}"
            }
            
        except Exception as e:
            self.log_message.emit(f"Automation error: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            await self.cleanup()
