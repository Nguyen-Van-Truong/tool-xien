# -*- coding: utf-8 -*-
"""
V11 Multi-Profile Login Tool - Browser Manager
Quản lý browser instances với profile riêng biệt
"""

import os
import time
import shutil
from datetime import datetime
from typing import Optional, Callable

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

import config


class BrowserInstance:
    """Đại diện cho một browser instance"""
    
    def __init__(self, instance_id: int, account_email: str, 
                 profile_dir: str, logger: Callable = None):
        self.id = instance_id
        self.account_email = account_email
        self.profile_dir = profile_dir
        self.driver: Optional[webdriver.Chrome] = None
        self.status = "idle"  # idle, running, success, failed, exists
        self.error_message = ""
        self.logger = logger or print
        self.created_at = datetime.now()
    
    def log(self, message: str, level: str = "info"):
        """Log message với instance ID"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logger(f"[{timestamp}] [Browser {self.id}] [{level.upper()}] {message}")


class BrowserManager:
    """Quản lý tất cả browser instances"""
    
    def __init__(self, logger: Callable = None):
        self.instances: dict[int, BrowserInstance] = {}
        self.next_id = 1
        self.logger = logger or print
        self._driver_creation_lock = None  # Will be set by caller if needed
        
        # Ensure directories exist
        os.makedirs(config.PROFILE_DIR, exist_ok=True)
        os.makedirs(config.LOG_DIR, exist_ok=True)
    
    def log(self, message: str, level: str = "info"):
        """Log chung"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logger(f"[{timestamp}] [BrowserManager] [{level.upper()}] {message}")
    
    def create_browser(self, account_email: str, 
                       browser_path: str = None) -> Optional[BrowserInstance]:
        """
        Tạo browser instance mới với profile riêng
        
        Args:
            account_email: Email của account (dùng để đặt tên profile)
            browser_path: Đường dẫn browser (optional)
            
        Returns:
            BrowserInstance hoặc None nếu thất bại
        """
        instance_id = self.next_id
        self.next_id += 1
        
        # Tạo profile directory riêng cho account này
        safe_email = account_email.replace("@", "_at_").replace(".", "_")
        profile_dir = os.path.join(
            config.PROFILE_DIR, 
            f"profile_{instance_id}_{safe_email}_{int(time.time())}"
        )
        os.makedirs(profile_dir, exist_ok=True)
        
        instance = BrowserInstance(
            instance_id=instance_id,
            account_email=account_email,
            profile_dir=profile_dir,
            logger=self.logger
        )
        
        try:
            driver = self._create_driver(profile_dir, browser_path, instance_id)
            if driver:
                instance.driver = driver
                instance.status = "running"
                self.instances[instance_id] = instance
                
                # Arrange window position
                self._arrange_window(driver, instance_id)
                
                self.log(f"✅ Created browser {instance_id} for {account_email}", "success")
                return instance
            else:
                instance.status = "failed"
                instance.error_message = "Failed to create driver"
                return None
                
        except Exception as e:
            instance.status = "failed"
            instance.error_message = str(e)
            self.log(f"❌ Failed to create browser {instance_id}: {e}", "error")
            return None
    
    def _create_driver(self, profile_dir: str, browser_path: str = None, 
                       instance_id: int = 0) -> Optional[webdriver.Chrome]:
        """Tạo Chrome driver với anti-detection"""
        
        browser_path = browser_path or config.BROWSER_PATH
        
        # Auto-detect browser if not specified
        if not browser_path or not os.path.exists(browser_path):
            browser_path = self._auto_find_browser()
        
        try:
            if UC_AVAILABLE:
                self.log(f"🚀 Starting browser {instance_id} with undetected-chromedriver...")
                
                uc_options = uc.ChromeOptions()
                uc_options.add_argument(f'--user-data-dir={profile_dir}')
                uc_options.add_argument('--disable-dev-shm-usage')
                uc_options.add_argument('--no-sandbox')
                uc_options.add_argument('--disable-gpu')
                
                if browser_path:
                    driver = uc.Chrome(
                        browser_executable_path=browser_path,
                        user_data_dir=profile_dir,
                        options=uc_options,
                        version_main=None,
                        use_subprocess=True
                    )
                else:
                    driver = uc.Chrome(
                        user_data_dir=profile_dir,
                        options=uc_options,
                        version_main=None,
                        use_subprocess=True
                    )
                
                self.log(f"✅ Browser {instance_id} opened (undetected mode)", "success")
                
            else:
                # Fallback to regular Chrome
                self.log(f"⚠️ undetected-chromedriver not available, using regular Chrome", "warning")
                
                chrome_options = Options()
                chrome_options.add_argument(f'--user-data-dir={profile_dir}')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                if browser_path:
                    chrome_options.binary_location = browser_path
                
                driver = webdriver.Chrome(options=chrome_options)
            
            driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            return driver
            
        except Exception as e:
            self.log(f"❌ Driver creation failed: {e}", "error")
            
            # Fallback to basic Chrome
            try:
                self.log("⚠️ Trying fallback Chrome driver...", "warning")
                chrome_options = Options()
                chrome_options.add_argument(f'--user-data-dir={profile_dir}')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                
                if browser_path:
                    chrome_options.binary_location = browser_path
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
                return driver
            except Exception as e2:
                self.log(f"❌ Fallback also failed: {e2}", "error")
                return None
    
    def _auto_find_browser(self) -> Optional[str]:
        """Auto-detect browser path"""
        browser_paths = [
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
        
        for path in browser_paths:
            if os.path.exists(path):
                self.log(f"📍 Auto-detected browser: {path}")
                return path
        
        # Try PATH
        browser_exes = ["chrome.exe", "brave.exe", "msedge.exe"]
        for exe in browser_exes:
            found = shutil.which(exe)
            if found:
                self.log(f"📍 Found in PATH: {found}")
                return found
        
        return None
    
    def _arrange_window(self, driver: webdriver.Chrome, instance_id: int):
        """Maximize window for fullscreen operation (requested by user)"""
        try:
            driver.maximize_window()
            self.log(f"🪟 Window {instance_id} maximized for fullscreen")
        except Exception as e:
            self.log(f"⚠️ Could not maximize window: {e}", "warning")
    
    def close_browser(self, instance_id: int, keep_open: bool = None):
        """
        Đóng browser instance
        
        Args:
            instance_id: ID của browser
            keep_open: Override config.KEEP_BROWSER_OPEN
        """
        keep_open = keep_open if keep_open is not None else config.KEEP_BROWSER_OPEN
        
        if instance_id not in self.instances:
            return
        
        instance = self.instances[instance_id]
        
        if keep_open:
            self.log(f"🔓 Browser {instance_id} kept open (KEEP_BROWSER_OPEN=True)")
            return
        
        if instance.driver:
            try:
                instance.driver.quit()
                self.log(f"🔒 Browser {instance_id} closed")
            except:
                pass
        
        # Clean up profile directory
        try:
            if os.path.exists(instance.profile_dir):
                time.sleep(1)
                shutil.rmtree(instance.profile_dir, ignore_errors=True)
        except:
            pass
        
        del self.instances[instance_id]
    
    def close_all_browsers(self, keep_open: bool = None):
        """Đóng tất cả browsers"""
        instance_ids = list(self.instances.keys())
        for instance_id in instance_ids:
            self.close_browser(instance_id, keep_open)
    
    def get_instance(self, instance_id: int) -> Optional[BrowserInstance]:
        """Lấy browser instance theo ID"""
        return self.instances.get(instance_id)
    
    def get_active_count(self) -> int:
        """Đếm số browser đang active"""
        return sum(1 for inst in self.instances.values() 
                   if inst.status == "running")
    
    def cleanup_profiles(self):
        """Dọn dẹp tất cả profile directories"""
        try:
            if os.path.exists(config.PROFILE_DIR):
                for item in os.listdir(config.PROFILE_DIR):
                    item_path = os.path.join(config.PROFILE_DIR, item)
                    if os.path.isdir(item_path):
                        try:
                            shutil.rmtree(item_path, ignore_errors=True)
                        except:
                            pass
            self.log("🧹 Cleaned up all profile directories")
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {e}", "warning")


# Test
if __name__ == "__main__":
    manager = BrowserManager()
    
    # Test create browser
    instance = manager.create_browser("test@example.com")
    if instance:
        print(f"Created browser {instance.id}")
        time.sleep(5)
        manager.close_browser(instance.id, keep_open=False)
