"""
Browser Fingerprint Generator - Tạo fingerprint riêng cho mỗi browser
Để tránh bị phát hiện là bot
"""

import random
import os
import platform
from pathlib import Path


class BrowserFingerprint:
    """Generate unique browser fingerprint for each instance"""
    
    # User agents pool - Real Chrome user agents
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    # Viewport sizes - Common screen resolutions
    VIEWPORTS = [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900},
        {'width': 1600, 'height': 900},
        {'width': 1280, 'height': 720},
    ]
    
    # Languages
    LANGUAGES = [
        ['en-US', 'en'],
        ['en-GB', 'en'],
        ['en-CA', 'en'],
        ['en-AU', 'en'],
    ]
    
    # Timezones
    TIMEZONES = [
        'America/New_York',
        'America/Los_Angeles',
        'America/Chicago',
        'America/Denver',
        'Europe/London',
        'Europe/Paris',
        'Europe/Berlin',
        'Asia/Tokyo',
        'Asia/Shanghai',
        'Australia/Sydney',
    ]
    
    @staticmethod
    def generate_fingerprint(browser_id):
        """Generate unique fingerprint for a browser instance
        
        Args:
            browser_id: Unique ID for this browser (e.g., row index or account email)
            
        Returns:
            dict: Fingerprint configuration
        """
        # Use browser_id as seed for consistent fingerprint per browser
        random.seed(hash(str(browser_id)) % (2**32))
        
        fingerprint = {
            'user_agent': random.choice(BrowserFingerprint.USER_AGENTS),
            'viewport': random.choice(BrowserFingerprint.VIEWPORTS),
            'locale': random.choice(BrowserFingerprint.LANGUAGES),
            'timezone_id': random.choice(BrowserFingerprint.TIMEZONES),
            'permissions': ['geolocation', 'notifications'],
            'geolocation': {
                'latitude': round(random.uniform(-90, 90), 6),
                'longitude': round(random.uniform(-180, 180), 6),
                'accuracy': random.randint(10, 100)
            },
            'platform': random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
            'hardware_concurrency': random.choice([4, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16]),
        }
        
        # Reset random seed
        random.seed()
        
        return fingerprint
    
    @staticmethod
    def get_user_data_dir(browser_id):
        """Get unique user data directory for browser profile
        
        Args:
            browser_id: Unique ID for this browser
            
        Returns:
            str: Path to user data directory
        """
        # Lưu cookie tại cùng folder với tool (workspace root)
        # Tìm workspace root bằng cách tìm file main.py hoặc __init__.py
        current_file = Path(__file__).resolve()
        # Tìm thư mục chứa chatgpt_veterans_tool package
        workspace_root = current_file.parent.parent  # utils -> chatgpt_veterans_tool -> workspace root
        
        # Tạo thư mục browser_profiles trong workspace root
        base_dir = workspace_root / 'browser_profiles'
        profile_dir = base_dir / f'profile_{browser_id}'
        
        # Create directory if not exists
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        return str(profile_dir)
    
    @staticmethod
    def find_browser_executable():
        """Tìm browser thật trên máy: Brave -> Edge -> Chrome
        
        Returns:
            tuple: (executable_path, browser_name, channel) hoặc (None, None, None) nếu không tìm thấy
        """
        system = platform.system()
        executable_path = None
        browser_name = None
        channel = None
        
        if system == "Windows":
            # Try Brave first
            brave_paths = [
                os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
            ]
            for path in brave_paths:
                if os.path.exists(path):
                    return path, "Brave", None
            
            # Try Edge
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
            for path in edge_paths:
                if os.path.exists(path):
                    return path, "Edge", None
            
            # Edge might be available via channel
            try:
                # Check if Edge is installed (via channel)
                return None, "Edge", "msedge"
            except:
                pass
            
            # Try Chrome
            chrome_paths = [
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    return path, "Chrome", None
        
        elif system == "Linux":
            # Try Brave
            brave_paths = ["/usr/bin/brave-browser", "/usr/bin/brave"]
            for path in brave_paths:
                if os.path.exists(path):
                    return path, "Brave", None
            
            # Try Chrome
            chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"]
            for path in chrome_paths:
                if os.path.exists(path):
                    return path, "Chrome", None
        
        elif system == "Darwin":  # macOS
            # Try Brave
            brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            if os.path.exists(brave_path):
                return brave_path, "Brave", None
            
            # Try Chrome
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                return chrome_path, "Chrome", None
        
        return None, None, None
    
    @staticmethod
    def save_browser_info(browser_id, browser_name, executable_path=None, channel=None):
        """Lưu thông tin browser đã dùng cho browser_id này"""
        import json
        user_data_dir = BrowserFingerprint.get_user_data_dir(browser_id)
        info_file = Path(user_data_dir) / 'browser_info.json'
        
        info = {
            'browser_name': browser_name,
            'executable_path': executable_path,
            'channel': channel
        }
        
        with open(info_file, 'w') as f:
            json.dump(info, f)
    
    @staticmethod
    def load_browser_info(browser_id):
        """Load thông tin browser đã dùng cho browser_id này"""
        import json
        user_data_dir = BrowserFingerprint.get_user_data_dir(browser_id)
        info_file = Path(user_data_dir) / 'browser_info.json'
        
        if info_file.exists():
            try:
                with open(info_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    @staticmethod
    def get_stealth_script():
        """Get comprehensive stealth script to hide automation - Enhanced for Cloudflare bypass"""
        return """
        // Remove webdriver property completely
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Delete webdriver from navigator
        delete navigator.__proto__.webdriver;
        
        // Override plugins - return realistic plugin array
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [];
                plugins.push({
                    description: 'Portable Document Format',
                    filename: 'internal-pdf-viewer',
                    name: 'PDF Viewer',
                    length: 1,
                    'application/pdf': {
                        description: 'Portable Document Format',
                        suffixes: 'pdf',
                        type: 'application/pdf'
                    }
                });
                plugins.push({
                    description: 'Shockwave Flash',
                    filename: 'pepflashplayer.dll',
                    name: 'Shockwave Flash',
                    length: 1,
                    'application/x-shockwave-flash': {
                        description: 'Shockwave Flash',
                        suffixes: 'swf',
                        type: 'application/x-shockwave-flash'
                    }
                });
                return plugins;
            }
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override chrome object - make it look real
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Override permissions query
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
        
        // Override getBattery
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
        }
        
        // Override connection
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            })
        });
        
        // Override hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        
        // Override deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
        
        // Override maxTouchPoints
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0
        });
        
        // Hide automation indicators in window object
        Object.defineProperty(window, 'navigator', {
            value: new Proxy(navigator, {
                has: (target, key) => (key === 'webdriver' ? false : key in target),
                get: (target, key) => (key === 'webdriver' ? undefined : target[key])
            })
        });
        
        // Override toString to hide automation
        const originalToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === navigator.webdriver) {
                return 'function webdriver() { [native code] }';
            }
            return originalToString.call(this);
        };
        """
