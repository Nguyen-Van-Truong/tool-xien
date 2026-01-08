"""
Reg/Login Automation - Mở browser thật để người dùng tự đăng ký/đăng nhập
"""

from PyQt6.QtCore import QObject, pyqtSignal
from utils.browser_fingerprint import BrowserFingerprint
import subprocess
import os
import platform
import time


class RegLoginAutomation(QObject):
    """Register/Login automation - chỉ làm register/login"""
    
    log_message = pyqtSignal(str)
    
    def __init__(self, account_data, use_proxy=False, proxy_data=None, browser_id=None):
        super().__init__()
        self.account_data = account_data
        self.use_proxy = use_proxy
        self.proxy_data = proxy_data
        self.browser_id = browser_id or account_data.get('email', 'default')
        self.is_running = True
        self.browser_process = None
    
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
    
    def open_real_browser(self):
        """Mở browser thật với user data dir riêng"""
        # Get unique user data directory
        user_data_dir = BrowserFingerprint.get_user_data_dir(self.browser_id)
        
        # Find browser executable (sẽ lưu info để Start Veri dùng sau)
        browser_path, browser_name, channel = self.find_browser_executable()
        
        if not browser_name:
            raise Exception("Không tìm thấy browser thật (Brave/Edge/Chrome) trên máy")
        
        # Build command to open browser
        if browser_path:
            # Use executable path
            if platform.system() == "Windows":
                cmd = [
                    browser_path,
                    f'--user-data-dir={user_data_dir}',
                    '--start-maximized',
                    'https://chatgpt.com'
                ]
            else:
                cmd = [
                    browser_path,
                    f'--user-data-dir={user_data_dir}',
                    '--start-maximized',
                    'https://chatgpt.com'
                ]
        else:
            # Edge via channel - use start command
            if platform.system() == "Windows":
                cmd = [
                    'start',
                    'msedge',
                    f'--user-data-dir={user_data_dir}',
                    '--start-maximized',
                    'https://chatgpt.com'
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
            
            self.log_message.emit(f"✓ Browser thật đã mở: {browser_name}")
            self.log_message.emit(f"📁 User data dir: {user_data_dir}")
            return browser_name
        except Exception as e:
            raise Exception(f"Không thể mở browser: {str(e)}")
    
    def run(self):
        """Run register/login - Mở browser thật, không giới hạn thời gian"""
        try:
            if not self.is_running:
                return {'success': False, 'error': 'Stopped by user'}
            
            # Open real browser
            browser_name = self.open_real_browser()
            self.log_message.emit("✓ Browser thật đã mở tại ChatGPT")
            self.log_message.emit("📋 Vui lòng hoàn thành các bước sau:")
            self.log_message.emit("   1. Xử lý Cloudflare challenge (nếu có)")
            self.log_message.emit("   2. Hoàn thành đăng ký/đăng nhập")
            self.log_message.emit("   3. Khi đến bước OTP, nhấn nút 'Code' để lấy OTP")
            self.log_message.emit("   4. Nhập OTP và hoàn thành login")
            self.log_message.emit("   5. Cookies sẽ được lưu tự động trong user data dir")
            self.log_message.emit("")
            self.log_message.emit("⚠️ Browser sẽ mở và đợi bạn hoàn thành - KHÔNG GIỚI HẠN THỜI GIAN")
            self.log_message.emit("⚠️ Đóng browser khi bạn đã hoàn thành login")
            
            # Wait indefinitely - no timeout
            # User will close browser when done
            while self.is_running:
                time.sleep(5)  # Check every 5 seconds
                
                # Check if browser process is still running
                if self.browser_process:
                    if self.browser_process.poll() is not None:
                        # Browser was closed
                        self.log_message.emit("✓ Browser đã được đóng")
                        self.log_message.emit("✓ Cookies đã được lưu trong user data dir")
                        return {'success': True}
            
            return {'success': False, 'error': 'Stopped by user'}
            
        except Exception as e:
            self.log_message.emit(f"Reg/Login error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def stop(self):
        """Stop - Close browser if still running"""
        self.is_running = False
        if self.browser_process:
            try:
                self.browser_process.terminate()
            except:
                pass

