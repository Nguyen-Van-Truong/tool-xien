#!/usr/bin/env python3
"""
🎖️ Military Verification GUI Tool
Giao diện đồ họa để xác thực Military SheerID - Landscape UI Version
Tối ưu cho màn hình độ phân giải thấp & Bố cục ngang
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import httpx
import json
import re
import os
import threading
import time
import webbrowser
from datetime import datetime

# Try to import tkinterdnd2 for Drag & Drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

# ===================== CONFIG =====================
SHEERID_BASE_URL = "https://services.sheerid.com/rest/v2/verification"

# API endpoint để đọc email
EMAIL_API_URL = "https://tools.dongvanfb.net/api/get_messages_oauth2"

ORGANIZATIONS = {
    "Army": {"id": 4070, "name": "Army"},
    "Navy": {"id": 4072, "name": "Navy"},
    "Air Force": {"id": 4073, "name": "Air Force"},
    "Marine Corps": {"id": 4071, "name": "Marine Corps"},
    "Coast Guard": {"id": 4074, "name": "Coast Guard"},
}

MONTH_TO_NUM = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
}

# ===================== THEME COLORS =====================
COLORS = {
    "bg": "#1e1e2e",           # Main Background
    "surface": "#313244",      # Card/Container Background
    "input_bg": "#45475a",     # Input Field Background
    "text": "#cdd6f4",         # Main Text
    "subtext": "#a6adc8",      # Secondary Text
    "primary": "#89b4fa",      # Blue (Buttons, Highlights)
    "success": "#a6e3a1",      # Green
    "warning": "#f9e2af",      # Yellow
    "error": "#f38ba8",        # Red
    "accent": "#cba6f7",       # Purple
    "border": "#585b70",       # Borders
    "drop_zone": "#585b70"     # Drop zone dashed border color
}

FONTS = {
    "h1": ("Segoe UI", 18, "bold"),
    "h2": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 9),
    "body_bold": ("Segoe UI", 9, "bold"),
    "mono": ("Consolas", 9),
    "small": ("Segoe UI", 8)
}

# ===================== FUNCTIONS =====================

def parse_veteran(line):
    """Parse veteran line to dict"""
    parts = line.split("|")
    if len(parts) < 10:
        return None
    return {
        "firstName": parts[0],
        "lastName": parts[1],
        "branch": parts[2],
        "birthMonth": parts[3],
        "birthDay": parts[4],
        "birthYear": parts[5],
        "dischargeMonth": parts[6],
        "dischargeDay": parts[7],
        "dischargeYear": parts[8],
        "email": parts[9]
    }


def format_date(year, month, day):
    """Format to YYYY-MM-DD"""
    month_num = MONTH_TO_NUM.get(month, "01")
    return f"{year}-{month_num.zfill(2)}-{day.zfill(2)}"


def extract_verification_id(url):
    """Extract verificationId from URL"""
    match = re.search(r'verificationId=([a-f0-9]+)', url)
    if match:
        return match.group(1)
    # Try path format
    match = re.search(r'/verify/[^/]+/?\?verificationId=([a-f0-9]+)', url)
    if match:
        return match.group(1)
    return None


def get_httpx_client(proxy=None):
    """
    Tạo httpx.Client với proxy nếu có.
    
    Args:
        proxy: Proxy URL (format: http://user:pass@host:port hoặc http://host:port)
               Nếu None, sẽ tắt proxy hoàn toàn (kể cả system proxy)
        
    Returns:
        httpx.Client instance
    """
    kwargs = {
        "timeout": 30.0,
        "verify": False,
        "follow_redirects": True
    }
    
    if proxy and proxy.strip() and proxy != "http://user:pass@host:port":
        # Có proxy: sử dụng proxy được chỉ định
        kwargs["proxy"] = proxy.strip()
    
    return httpx.Client(**kwargs)


def read_emails_via_api(user_email, refresh_token, client_id, proxy=None):
    """
    Đọc email qua API service của dongvanfb.net.
    KHÔNG sử dụng proxy để tránh bị chặn.
    
    Args:
        user_email: Email address
        refresh_token: Refresh token
        client_id: Client ID
        proxy: Không sử dụng (giữ lại để tương thích)
        
    Returns:
        Dictionary chứa thông tin email hoặc None nếu lỗi
    """
    try:
        payload = {
            "email": user_email,
            "refresh_token": refresh_token,
            "client_id": client_id
        }
        
        # KHÔNG sử dụng proxy khi đọc email - dùng httpx.post trực tiếp giống read_emails.py
        # để đảm bảo 100% không có proxy (kể cả system proxy)
        response = httpx.post(EMAIL_API_URL, json=payload, timeout=30, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") and data.get("messages"):
                messages = data.get("messages", [])
            if messages:
                    return {
                        "status": True,
                        "messages": messages,
                        "email": data.get("email", user_email)
                    }
            else:
                error_code = data.get("code", "")
                return {
                    "status": False,
                    "error": f"API trả về status false: {error_code}",
                    "data": data
                }
        else:
            return {
                "status": False,
                "error": f"API error: {response.status_code} - {response.text[:200]}"
            }
            
    except Exception as e:
        return {
            "status": False,
            "error": f"Exception: {str(e)}"
        }


def find_sheerid_verify_link(email_body):
    """
    Tìm link verify của SheerID từ nội dung email.
    
    Args:
        email_body: Nội dung email (HTML hoặc text)
        
    Returns:
        URL verify link hoặc None nếu không tìm thấy
    """
    if not email_body:
        return None
    
    # Regex tìm link https://services.sheerid.com/verify/
    pattern = r'(https://services\.sheerid\.com/verify/[^\s<>"]+)'
    match = re.search(pattern, email_body)
    
    if match:
        return match.group(1)
    
    return None


def parse_email_date(date_str):
    """
    Parse date string từ email thành datetime object.
    Hỗ trợ format: 'HH:MM - DD/MM/YYYY' (ví dụ: '14:26 - 26/12/2025')
    
    Args:
        date_str: Date string từ email
        
    Returns:
        datetime object hoặc datetime.min nếu không parse được
    """
    try:
        if date_str:
            # Format từ API: '14:26 - 26/12/2025' hoặc '14:32 - 26/12/2025'
            if ' - ' in date_str:
                try:
                    time_part, date_part = date_str.split(' - ')
                    # Parse: time_part = '14:26', date_part = '26/12/2025'
                    return datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %H:%M")
                except:
                    pass
            
            # Thử parse ISO format (2022-04-18T11:35:26.000Z)
            if 'T' in date_str:
                try:
                    date_part = date_str.split('T')[0]
                    time_part = date_str.split('T')[1].split('.')[0] if '.' in date_str.split('T')[1] else date_str.split('T')[1].split('Z')[0]
                    return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            # Thử parse các format khác
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
    except Exception as e:
        pass
    return datetime.min


def get_latest_verify_email(messages, start_time=None):
    """
    Chọn email verify mới nhất và chuẩn nhất từ danh sách email.
    Chỉ lấy email được gửi SAU thời điểm start_time (nếu có).
    
    Tiêu chí:
    1. Từ verify@sheerid.com
    2. Subject có chứa "verified" hoặc "verifired"
    3. Có link verify
    4. Email được gửi SAU start_time (nếu có)
    5. Email mới nhất (sắp xếp theo date)
    
    Args:
        messages: List các email từ API
        start_time: Thời điểm bắt đầu verification (chỉ lấy email sau thời điểm này)
        
    Returns:
        Email verify mới nhất hoặc None
    """
    verify_emails = []
    
    for msg in messages:
        # Parse from address
        from_info = msg.get("from", [])
        from_addr = "Unknown"
        
        if isinstance(from_info, list) and len(from_info) > 0:
            first_from = from_info[0]
            if isinstance(first_from, dict):
                from_addr = first_from.get("address", "Unknown")
            elif isinstance(first_from, str):
                from_addr = first_from
        elif isinstance(from_info, str):
            from_addr = from_info
        
        subject = msg.get("subject", "").lower()
        body = msg.get("message", "")
        email_date_str = msg.get("date", "")
        
        # Kiểm tra email từ verify@sheerid.com và subject có "verified" hoặc "verifired"
        if "verify@sheerid.com" in from_addr.lower() and ("verified" in subject or "verifired" in subject):
            # Kiểm tra có link verify không
            verify_link = find_sheerid_verify_link(body)
            if verify_link:
                # Parse date của email
                email_date = parse_email_date(email_date_str)
                
                # Nếu có start_time, chỉ lấy email được gửi SAU start_time
                if start_time:
                    if email_date <= start_time:
                        continue  # Bỏ qua email cũ
                
                verify_emails.append({
                    "email": msg,
                    "from": from_addr,
                    "subject": msg.get("subject", ""),
                    "date": email_date_str,
                    "date_obj": email_date,
                    "link": verify_link
                })
    
    if not verify_emails:
        return None
    
    # Sắp xếp theo date (mới nhất trước)
    verify_emails.sort(key=lambda x: x["date_obj"], reverse=True)
    
    # Trả về email mới nhất
    return verify_emails[0]


def read_verification_status_from_url(url, proxy=None, debug=False):
    """
    Đọc trạng thái verification từ URL bằng Selenium để đọc HTML sau khi JavaScript render.
    
    Args:
        url: URL của link verify
        proxy: Proxy URL (optional, chưa hỗ trợ với Selenium)
        debug: Nếu True, sẽ log HTML để debug
        
    Returns:
        Dictionary chứa status và message
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import re
        import time
        
        # Cấu hình Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Chạy ngầm
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Thử dùng Brave nếu có
        brave_paths = [
            "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            r"C:\Users\{}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe".format(
                os.getenv('USERNAME', '')
            )
        ]
        
        brave_path = None
        for path in brave_paths:
            if os.path.exists(path):
                brave_path = path
                break
        
        if brave_path:
            chrome_options.binary_location = brave_path
        
        # Khởi tạo driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Mở URL
            driver.get(url)
            
            # Đợi trang load (đợi có element sid-error hoặc sid-success xuất hiện)
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: "sid-error" in d.page_source.lower() or 
                             "sid-success" in d.page_source.lower() or
                             "not approved" in d.page_source.lower() or
                             "verified" in d.page_source.lower()
                )
            except:
                # Nếu không tìm thấy, đợi thêm 3 giây
                time.sleep(3)
            
            # Lấy HTML sau khi JavaScript render
            html = driver.page_source
            html_lower = html.lower()
            
            # Debug: Log một phần HTML để kiểm tra
            if debug:
                print(f"[DEBUG] HTML length: {len(html)}")
                print(f"[DEBUG] HTML preview (first 2000 chars): {html[:2000]}")
            
            # Tìm "Not approved" - nhiều cách khác nhau
            # Cách 1: Tìm "not approved" với khoảng trắng linh hoạt (có thể có nhiều khoảng trắng, tab, newline)
            if re.search(r'not\s+approved', html, re.IGNORECASE):
                return {
                    "success": True,
                    "status": "not_approved",
                    "message": "Not Approved"
                }
            
            # Cách 2: Tìm "not" và "approved" gần nhau (trong vòng 50 ký tự, không phân biệt chữ hoa/thường)
            if re.search(r'not[^a-z]{0,50}approved', html, re.IGNORECASE):
                return {
                    "success": True,
                    "status": "not_approved",
                    "message": "Not Approved"
                }
            
            # Cách 3: Tìm "not" và sau đó tìm "approved" hoặc "Approved" trong vòng 100 ký tự
            not_positions = [m.start() for m in re.finditer(r'\bnot\b', html, re.IGNORECASE)]
            for pos in not_positions:
                # Kiểm tra 100 ký tự sau "not"
                snippet = html[pos:pos+150]
                snippet_lower = snippet.lower()
                if "approved" in snippet_lower:
                    return {
                        "success": True,
                        "status": "not_approved",
                        "message": "Not Approved"
                    }
            
            # Cách 4: Nếu có "not" và có class/id chứa "error" thì có thể là not approved
            if "not" in html_lower and ("sid-error" in html_lower or "error" in html_lower or "sourcesunavailable" in html_lower):
                # Kiểm tra xem có từ "approved" ở đâu đó trong HTML không
                if "approved" in html_lower:
                    # Tìm vị trí của "not" và "approved"
                    not_positions = [m.start() for m in re.finditer(r'\bnot\b', html, re.IGNORECASE)]
                    approved_positions = [m.start() for m in re.finditer(r'\bapproved\b', html, re.IGNORECASE)]
                    
                    # Kiểm tra xem có "not" và "approved" gần nhau không (trong vòng 200 ký tự)
                    for not_pos in not_positions:
                        for approved_pos in approved_positions:
                            if abs(not_pos - approved_pos) < 200:
                                return {
                                    "success": True,
                                    "status": "not_approved",
                                    "message": "Not Approved"
                                }
            
            # Cách 5: Tìm "sourcesUnavailable" - đây là một loại lỗi
            if "sourcesunavailable" in html_lower:
                return {
                    "success": True,
                    "status": "not_approved",
                    "message": "Not Approved (sourcesUnavailable)"
                }
            
            # Cách 6: Tìm trong sid-error-msg hoặc sid-error-container
            if re.search(r'sid-error[^"]*".*?not[^a-z]{0,50}approved', html, re.IGNORECASE | re.DOTALL):
                return {
                    "success": True,
                    "status": "not_approved",
                    "message": "Not Approved"
                }
            
            # Cách 7: Tìm trong tag có class sid-error
            if re.search(r'<[^>]*class="[^"]*sid-error[^"]*"[^>]*>[\s\S]*?not[^a-z]{0,50}approved', html, re.IGNORECASE):
                return {
                    "success": True,
                    "status": "not_approved",
                    "message": "Not Approved"
                }
            
            # Tìm "You've been verified" hoặc "You have been verified" - đây là thông báo thành công
            if re.search(r"you'?ve\s+been\s+verified|you\s+have\s+been\s+verified", html, re.IGNORECASE):
                return {
                    "success": True,
                    "status": "verified",
                    "message": "Verified"
                }
            
            # Tìm "verified" kết hợp với "ChatGPT Plus" hoặc "enjoy"
            if "verified" in html_lower and ("chatgpt" in html_lower or "enjoy" in html_lower or "plus" in html_lower):
                return {
                    "success": True,
                    "status": "verified",
                    "message": "Verified"
                }
            
            # Tìm "Verified" hoặc "Approved" trong success container
            if re.search(r'sid-success[^"]*"', html, re.IGNORECASE):
                return {
                    "success": True,
                    "status": "verified",
                    "message": "Verified"
                }
            
            # Tìm "verified" và "approved" hoặc "success" cùng lúc
            if ("verified" in html_lower or "approv" in html_lower) and ("success" in html_lower or "complete" in html_lower):
                return {
                    "success": True,
                    "status": "verified",
                    "message": "Verified"
                }
            
            # Tìm "verified" đơn giản (nếu không có "not" ở gần)
            if "verified" in html_lower:
                # Kiểm tra xem có "not" ở gần "verified" không
                verified_positions = [m.start() for m in re.finditer(r'\bverified\b', html, re.IGNORECASE)]
                for pos in verified_positions:
                    # Kiểm tra 50 ký tự trước và sau "verified"
                    snippet = html[max(0, pos-50):pos+100].lower()
                    if "not" not in snippet:
                        return {
                            "success": True,
                            "status": "verified",
                            "message": "Verified"
                        }
            
            # Tìm "pending" hoặc "processing"
            if "pending" in html_lower or "processing" in html_lower:
                return {
                    "success": True,
                    "status": "pending",
                    "message": "Pending"
                }
            
            # Fallback: Nếu có "not" và "error" hoặc "sourcesUnavailable" nhưng không có "approved"
            # thì có thể là "Not approved" (trang web có thể không hiển thị từ "approved" trong HTML)
            if "not" in html_lower and ("error" in html_lower or "sourcesunavailable" in html_lower or "sid-error" in html_lower):
                # Kiểm tra xem có "approved" ở đâu đó không
                if "approved" not in html_lower:
                    # Nếu không có "approved", nhưng có "not" + "error", coi như "Not approved"
                    return {
                        "success": True,
                        "status": "not_approved",
                        "message": "Not Approved (detected: not + error)"
                    }
            
            # Debug: Thu thập thông tin debug
            debug_info = {}
            if debug:
                # Tìm các từ khóa liên quan
                keywords_found = []
                for keyword in ["error", "approved", "verified", "success", "pending", "not"]:
                    if keyword in html_lower:
                        keywords_found.append(keyword)
                debug_info = {
                    "html_length": len(html),
                    "keywords_found": keywords_found,
                    "has_not": "not" in html_lower,
                    "has_approved": "approved" in html_lower,
                    "html_preview": html[:500] if len(html) > 500 else html
                }
            
            # Không tìm thấy trạng thái rõ ràng
            result = {
                "success": True,
                "status": "unknown",
                "message": "Không xác định được trạng thái"
            }
            if debug_info:
                result["debug_info"] = debug_info
            return result
            
        finally:
            driver.quit()
            
    except ImportError:
        # Nếu không có Selenium, fallback về httpx
        return {
            "success": False,
            "status": "error",
            "message": "Selenium chưa được cài đặt. Vui lòng chạy: pip install selenium"
        }
    except Exception as e:
        import traceback
        if debug:
            print(f"[DEBUG] Exception: {str(e)}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "status": "error",
            "message": f"Lỗi đọc trạng thái: {str(e)}"
        }


def open_verify_link_in_browser(url, read_status=False, proxy=None):
    """
    Đọc trạng thái verification từ URL bằng Selenium.
    Không mở trình duyệt thật nữa, chỉ dùng Selenium để đọc HTML.
    
    Args:
        url: URL của link verify
        read_status: Nếu True, sẽ đọc trạng thái từ trang web (luôn True)
        proxy: Proxy URL (optional, chưa hỗ trợ với Selenium)
        
    Returns:
        Dictionary chứa thông tin về việc đọc trạng thái
    """
    try:
        # Luôn đọc trạng thái bằng Selenium
        status_result = read_verification_status_from_url(url, proxy, debug=True)
        
        return {
            "success": True,
            "message": f"Đã đọc trạng thái từ URL: {url}",
            "browser": "Selenium (Headless)",
            "status_info": status_result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi đọc trạng thái: {str(e)}"
        }



# ===================== GUI CLASS =====================

class MilitaryVerifyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Military Verification Tool")
        self.root.geometry("1000x600") # Landscape mode
        self.root.configure(bg=COLORS["bg"])
        
        # Data state
        self.data_file = None
        self.veterans = []
        self.current_index = 0
        
        # Account Data state
        self.account_file = None
        self.accounts = []
        self.current_acc_index = 0
        
        # Proxy configuration
        self.proxy = None
        self.config_file = "verify_config.json"
        
        self.setup_styles()
        self.setup_ui()
        
        # Load saved configuration (proxy, etc.)
        self.load_config()
        
        # Try to load default file if exists
        default_file = "all_veterans.txt"
        if os.path.exists(default_file):
            self.load_data_from_file(os.path.abspath(default_file))
        else:
            self.update_veteran_display() # Show empty state

        if not DND_SUPPORT:
            self.log("⚠️ Drag & Drop not supported. Install 'tkinterdnd2' to enable.")
    
    def setup_styles(self):
        """Configure ttk styles for a modern look"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame Styles
        style.configure("Main.TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["surface"], relief="flat")
        
        # Label Styles
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=FONTS["body"])
        style.configure("Card.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=FONTS["body"])
        style.configure("Header.TLabel", background=COLORS["bg"], foreground=COLORS["primary"], font=FONTS["h1"])
        style.configure("SubHeader.TLabel", background=COLORS["surface"], foreground=COLORS["accent"], font=FONTS["h2"])
        style.configure("Stats.TLabel", background=COLORS["bg"], foreground=COLORS["subtext"], font=FONTS["small"])
        style.configure("Status.TLabel", background=COLORS["bg"], foreground=COLORS["subtext"], font=FONTS["small"])
        style.configure("File.TLabel", background=COLORS["input_bg"], foreground=COLORS["text"], font=FONTS["mono"])
        
        # Button Styles
        style.configure(
            "Primary.TButton",
            background=COLORS["primary"],
            foreground=COLORS["bg"],
            font=FONTS["body_bold"],
            borderwidth=0,
            focuscolor=COLORS["primary"]
        )
        style.map("Primary.TButton", background=[('active', COLORS["accent"])])
        
        style.configure(
            "Action.TButton",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=FONTS["body"],
            borderwidth=1,
            bordercolor=COLORS["border"]
        )
        style.map("Action.TButton", background=[('active', COLORS["input_bg"])])
        
        style.configure(
            "Danger.TButton",
            background=COLORS["error"],
            foreground=COLORS["bg"],
            font=FONTS["body_bold"],
            borderwidth=0
        )
        style.map("Danger.TButton", background=[('active', "#d20f39")])

        style.configure(
            "Success.TButton",
            background=COLORS["success"],
            foreground="#1e1e2e",
            font=("Segoe UI", 11, "bold"),
            borderwidth=0
        )
        style.map("Success.TButton", background=[('active', "#8bd585")])

        style.configure(
            "Warning.TButton",
            background=COLORS["warning"],
            foreground="#1e1e2e",
            font=FONTS["body_bold"],
            borderwidth=0
        )
        style.map("Warning.TButton", background=[('active', "#f5d97e")])

        # Labelframe
        style.configure(
            "Card.TLabelframe",
            background=COLORS["surface"],
            foreground=COLORS["accent"],
            bordercolor=COLORS["border"],
            borderwidth=1,
            relief="solid"
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=COLORS["surface"],
            foreground=COLORS["accent"],
            font=FONTS["h2"]
        )

    def setup_ui(self):
        # Main Container - Grid Layout (2 Columns)
        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        main_container.columnconfigure(0, weight=4, uniform="group1") # Left Panel (40%)
        main_container.columnconfigure(1, weight=6, uniform="group1") # Right Panel (60%)
        main_container.rowconfigure(0, weight=1)

        # ================= LEFT PANEL (Controls) =================
        left_panel = ttk.Frame(main_container, style="Main.TFrame")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # --- HEADER ---
        header_frame = ttk.Frame(left_panel, style="Main.TFrame")
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_lbl = ttk.Label(header_frame, text="🎖️ MILITARY VERIFY", style="Header.TLabel")
        title_lbl.pack(anchor="w")
        
        self.stats_label = ttk.Label(header_frame, text="No Data Loaded", style="Stats.TLabel")
        self.stats_label.pack(anchor="w")

        # --- STEP 1: DATA SOURCE ---
        data_card = ttk.LabelFrame(left_panel, text=" 1. Veteran Data ", style="Card.TLabelframe", padding=10)
        data_card.pack(fill="x", pady=(0, 10))
        
        self.file_path_label = ttk.Label(
            data_card, 
            text="Drag & Drop file here...", 
            style="File.TLabel",
            relief="sunken",
            padding=5,
            wraplength=300
        )
        self.file_path_label.pack(fill="x", pady=(0, 5))
        
        ttk.Button(data_card, text="📂 Browse File", command=self.browse_file, style="Primary.TButton").pack(fill="x")

        # Drag & Drop Registration
        if DND_SUPPORT:
            self.file_path_label.drop_target_register(DND_FILES)
            self.file_path_label.dnd_bind('<<Drop>>', self.handle_drop)
            data_card.drop_target_register(DND_FILES)
            data_card.dnd_bind('<<Drop>>', self.handle_drop)

        # --- STEP 2: ACCOUNT SOURCE ---
        acc_card = ttk.LabelFrame(left_panel, text=" 2. Account Data ", style="Card.TLabelframe", padding=10)
        acc_card.pack(fill="x", pady=(0, 10))
        
        self.acc_path_label = ttk.Label(
            acc_card, 
            text="Drag & Drop account file...", 
            style="File.TLabel",
            relief="sunken",
            padding=5,
            wraplength=300
        )
        self.acc_path_label.pack(fill="x", pady=(0, 5))
        
        ttk.Button(acc_card, text="📂 Browse Account File", command=self.browse_account_file, style="Primary.TButton").pack(fill="x")

        # Account Info Display
        self.acc_info_label = ttk.Label(acc_card, text="No Account Loaded", style="Card.TLabel", foreground=COLORS["subtext"])
        self.acc_info_label.pack(pady=(5, 0))

        # Account Controls
        acc_controls = ttk.Frame(acc_card, style="Card.TFrame")
        acc_controls.pack(fill="x", pady=(5, 0))
        
        ttk.Button(acc_controls, text="←", command=self.prev_account, style="Action.TButton", width=4).pack(side="left")
        self.acc_count_label = ttk.Label(acc_controls, text="0/0", style="Card.TLabel")
        self.acc_count_label.pack(side="left", expand=True)
        ttk.Button(acc_controls, text="→", command=self.next_account, style="Action.TButton", width=4).pack(side="right")

        # Drag & Drop for Account
        if DND_SUPPORT:
            self.acc_path_label.drop_target_register(DND_FILES)
            self.acc_path_label.dnd_bind('<<Drop>>', self.handle_acc_drop)
            acc_card.drop_target_register(DND_FILES)
            acc_card.dnd_bind('<<Drop>>', self.handle_acc_drop)

        # --- STEP 3: CONFIGURATION ---
        input_card = ttk.LabelFrame(left_panel, text=" 3. Configuration ", style="Card.TLabelframe", padding=10)
        input_card.pack(fill="x", pady=(0, 10))
        
        ttk.Label(input_card, text="SheerID Link:", style="Card.TLabel").pack(anchor="w")
        self.link_entry = tk.Entry(
            input_card, 
            bg=COLORS["input_bg"], 
            fg=COLORS["text"], 
            insertbackground=COLORS["text"], 
            relief="flat", 
            font=FONTS["body"]
        )
        self.link_entry.pack(fill="x", pady=(2, 8), ipady=3)
        
        ttk.Label(input_card, text="Proxy (optional):", style="Card.TLabel").pack(anchor="w")
        self.proxy_entry = tk.Entry(
            input_card,
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=FONTS["body"]
        )
        self.proxy_entry.pack(fill="x", pady=(2, 8), ipady=3)
        self.proxy_entry.insert(0, "http://user:pass@host:port")
        self.proxy_entry.config(foreground=COLORS["subtext"])
        
        # Bind event để xóa placeholder khi focus
        def on_proxy_focus_in(event):
            if self.proxy_entry.get() == "http://user:pass@host:port":
                self.proxy_entry.delete(0, tk.END)
                self.proxy_entry.config(foreground=COLORS["text"])
        
        def on_proxy_focus_out(event):
            if not self.proxy_entry.get():
                self.proxy_entry.insert(0, "http://user:pass@host:port")
                self.proxy_entry.config(foreground=COLORS["subtext"])
        
        self.proxy_entry.bind("<FocusIn>", on_proxy_focus_in)
        self.proxy_entry.bind("<FocusOut>", on_proxy_focus_out)
        
        # Lưu proxy khi thay đổi
        def on_proxy_change(event=None):
            self.save_config()
        self.proxy_entry.bind("<KeyRelease>", on_proxy_change)

        # --- ACTION BUTTON (Bottom of Left Panel) ---
        # Spacer to push button down
        ttk.Frame(left_panel, style="Main.TFrame").pack(fill="both", expand=True)
        
        self.verify_btn = ttk.Button(
            left_panel,
            text="🚀 START VERIFICATION",
            command=self.run_verification,
            style="Success.TButton",
            cursor="hand2"
        )
        self.verify_btn.pack(fill="x", pady=(10, 0), ipady=8)


        # ================= RIGHT PANEL (Info & Logs) =================
        right_panel = ttk.Frame(main_container, style="Main.TFrame")
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # --- VETERAN CARD ---
        vet_card = ttk.LabelFrame(right_panel, text=" Veteran Profile ", style="Card.TLabelframe", padding=10)
        vet_card.pack(fill="x", pady=(0, 10))
        
        # Info Grid
        vet_info_frame = ttk.Frame(vet_card, style="Card.TFrame")
        vet_info_frame.pack(fill="x", pady=(0, 10))
        vet_info_frame.columnconfigure(1, weight=1)
        
        # Compact layout for landscape
        # Name
        row1 = ttk.Frame(vet_info_frame, style="Card.TFrame")
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Name:", style="Card.TLabel", font=FONTS["body_bold"], width=8).pack(side="left")
        self.vet_name_val = ttk.Label(row1, text="---", style="Card.TLabel")
        self.vet_name_val.pack(side="left")
        
        # Branch
        row2 = ttk.Frame(vet_info_frame, style="Card.TFrame")
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Branch:", style="Card.TLabel", font=FONTS["body_bold"], width=8).pack(side="left")
        self.vet_branch_val = ttk.Label(row2, text="---", style="Card.TLabel", foreground=COLORS["primary"])
        self.vet_branch_val.pack(side="left")
        
        # Birth & Discharge (Side by side)
        row3 = ttk.Frame(vet_info_frame, style="Card.TFrame")
        row3.pack(fill="x", pady=2)
        
        ttk.Label(row3, text="Birth:", style="Card.TLabel", font=FONTS["body_bold"], width=8).pack(side="left")
        self.vet_birth_val = ttk.Label(row3, text="---", style="Card.TLabel")
        self.vet_birth_val.pack(side="left", padx=(0, 20))
        
        ttk.Label(row3, text="Discharge:", style="Card.TLabel", font=FONTS["body_bold"]).pack(side="left")
        self.vet_discharge_val = ttk.Label(row3, text="---", style="Card.TLabel")
        self.vet_discharge_val.pack(side="left", padx=(5, 0))

        # Controls
        controls_frame = ttk.Frame(vet_card, style="Card.TFrame")
        controls_frame.pack(fill="x")
        
        ttk.Button(controls_frame, text="← Prev", command=self.prev_veteran, style="Action.TButton", width=8).pack(side="left", padx=(0, 5))
        ttk.Button(controls_frame, text="Next →", command=self.next_veteran, style="Action.TButton", width=8).pack(side="left", padx=5)
        
        ttk.Frame(controls_frame, style="Card.TFrame").pack(side="left", fill="x", expand=True) # Spacer
        
        ttk.Button(controls_frame, text="↻ Reload", command=self.reload_data, style="Action.TButton").pack(side="right", padx=5)
        ttk.Button(controls_frame, text="⏭️ Bỏ qua Email", command=self.skip_account, style="Warning.TButton").pack(side="right", padx=(5, 0))
        ttk.Button(controls_frame, text="⏭️ Bỏ qua Veteran", command=self.skip_veteran, style="Warning.TButton").pack(side="right", padx=(5, 0))

        # --- LOGS ---
        log_frame = ttk.LabelFrame(right_panel, text=" System Logs ", style="Card.TLabelframe", padding=10)
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5, # Min height, will expand
            font=FONTS["mono"],
            bg=COLORS["input_bg"],
            fg=COLORS["success"],
            insertbackground=COLORS["text"],
            relief="flat",
            padx=5, pady=5
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Status Bar (Bottom of Right Panel)
        self.status_label = ttk.Label(
            right_panel,
            text="Ready to verify",
            style="Status.TLabel"
        )
        self.status_label.pack(fill="x", pady=(5, 0))

    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    proxy = config.get("proxy", "")
                    if proxy and proxy != "http://user:pass@host:port":
                        if hasattr(self, 'proxy_entry'):
                            self.proxy_entry.delete(0, tk.END)
                            self.proxy_entry.insert(0, proxy)
                            self.proxy_entry.config(foreground=COLORS["text"])
            except Exception as e:
                self.log(f"⚠️ Không thể load config: {str(e)}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            proxy = ""
            if hasattr(self, 'proxy_entry'):
                proxy = self.proxy_entry.get().strip()
                if proxy == "http://user:pass@host:port":
                    proxy = ""
            
            config = {
                "proxy": proxy
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Không log lỗi để tránh spam
            pass
    
    def log(self, message, color=None):
        """Add message to log with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Nếu color là tên màu (string), convert sang giá trị màu từ COLORS
        if color and isinstance(color, str) and color in COLORS:
            color = COLORS[color]
        
        # Xác định màu dựa trên prefix của message
        if color is None:
            if message.startswith("✅") or message.startswith("🎉"):
                color = COLORS["success"]  # Xanh lá
            elif message.startswith("❌"):
                color = COLORS["error"]  # Đỏ
            elif message.startswith("⚠️"):
                color = COLORS["warning"]  # Vàng
            elif message.startswith("ℹ️") or message.startswith("📊") or message.startswith("📧") or message.startswith("📨") or message.startswith("📝") or message.startswith("🕐"):
                color = COLORS["primary"]  # Xanh dương
            elif message.startswith("🔄") or message.startswith("🔎") or message.startswith("🔗") or message.startswith("🌐") or message.startswith("⏳"):
                color = COLORS["accent"]  # Tím
            elif message.startswith("🚀") or message.startswith("📂") or message.startswith("🗑") or message.startswith("⏭️"):
                color = COLORS["subtext"]  # Xám nhạt
            else:
                color = COLORS["text"]  # Màu mặc định
        
        # Insert với màu
        # Tạo tag name duy nhất cho mỗi màu
        tag_name = f"color_{hash(color) % 10000}"
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", tag_name)
        self.log_text.tag_config("timestamp", foreground=COLORS["subtext"])
        self.log_text.tag_config(tag_name, foreground=color)
        self.log_text.see(tk.END)

    # ================= FILE HANDLING =================
    
    def browse_file(self):
        """Open file dialog to select data file"""
        filename = filedialog.askopenfilename(
            title="Select Veteran Data File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            self.load_data_from_file(filename)

    def handle_drop(self, event):
        """Handle dropped file"""
        file_path = event.data
        # Remove curly braces if path contains spaces (tkinterdnd quirk)
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        self.load_data_from_file(file_path)

    def load_data_from_file(self, filepath):
        """Load data from specified file path"""
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found: {filepath}")
            return

        try:
            new_veterans = []
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "|" in line:
                        new_veterans.append(line)
            
            if not new_veterans:
                messagebox.showwarning("Warning", "File is empty or invalid format!")
                return

            self.veterans = new_veterans
            self.data_file = filepath
            self.current_index = 0
            
            # Update UI
            self.file_path_label.config(text=filepath)
            self.update_veteran_display()
            self.log(f"📂 Loaded {len(self.veterans)} records from: {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def save_veterans(self):
        """Save current veterans list back to file"""
        if not self.data_file:
            return
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.veterans))
        except Exception as e:
            self.log(f"❌ Error saving file: {str(e)}")

    def browse_account_file(self):
        """Open file dialog to select account file"""
        filename = filedialog.askopenfilename(
            title="Select Account File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            self.load_accounts_from_file(filename)

    def handle_acc_drop(self, event):
        """Handle dropped account file"""
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.load_accounts_from_file(file_path)

    def load_accounts_from_file(self, filepath):
        """Load accounts from file"""
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found: {filepath}")
            return

        try:
            new_accounts = []
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 4: # email|pass|token|client_id
                            new_accounts.append({
                                "email": parts[0].strip(),
                                "password": parts[1].strip(),
                                "token": parts[2].strip(),
                                "client_id": parts[3].strip(),
                                "raw": line
                            })
                        elif len(parts) >= 3: # email|pass|token (backward compatibility)
                            new_accounts.append({
                                "email": parts[0].strip(),
                                "password": parts[1].strip(),
                                "token": parts[2].strip(),
                                "client_id": "",  # Empty nếu không có
                                "raw": line
                            })
            
            if not new_accounts:
                messagebox.showwarning("Warning", "File is empty or invalid format!")
                return

            self.accounts = new_accounts
            self.account_file = filepath
            self.current_acc_index = 0
            
            # Update UI
            self.acc_path_label.config(text=os.path.basename(filepath))
            self.update_account_display()
            self.log(f"📂 Loaded {len(self.accounts)} accounts from: {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load accounts: {str(e)}")

    def update_account_display(self):
        """Update account UI"""
        if not self.accounts:
            self.acc_info_label.config(text="No Account Loaded")
            self.acc_count_label.config(text="0/0")
            return
            
        if self.current_acc_index >= len(self.accounts):
            self.current_acc_index = 0
            
        acc = self.accounts[self.current_acc_index]
        self.acc_info_label.config(text=f"📧 {acc['email']}")
        self.acc_count_label.config(text=f"{self.current_acc_index + 1}/{len(self.accounts)}")

    def next_account(self):
        if self.accounts:
            self.current_acc_index = (self.current_acc_index + 1) % len(self.accounts)
            self.update_account_display()

    def prev_account(self):
        if self.accounts:
            self.current_acc_index = (self.current_acc_index - 1) % len(self.accounts)
            self.update_account_display()

    def remove_current_account(self):
        """Remove current account and save file"""
        if self.accounts:
            removed = self.accounts.pop(self.current_acc_index)
            
            # Save back to file
            try:
                with open(self.account_file, "w", encoding="utf-8") as f:
                    for acc in self.accounts:
                        f.write(acc["raw"] + "\n")
            except Exception as e:
                self.log(f"❌ Error saving account file: {str(e)}")

            if self.current_acc_index >= len(self.accounts):
                self.current_acc_index = 0
            self.update_account_display()


    # ================= VETERAN LOGIC =================
    
    def update_veteran_display(self):
        """Update current veteran display"""
        if not self.veterans:
            self.vet_name_val.config(text="NO DATA")
            self.vet_branch_val.config(text="---")
            self.vet_birth_val.config(text="---")
            self.vet_discharge_val.config(text="---")
            self.stats_label.config(text="No Data Loaded")
            return
        
        if self.current_index >= len(self.veterans):
            self.current_index = 0
        
        line = self.veterans[self.current_index]
        vet = parse_veteran(line)
        
        if vet:
            self.vet_name_val.config(text=f"{vet['firstName']} {vet['lastName']}")
            self.vet_branch_val.config(text=vet['branch'])
            self.vet_birth_val.config(text=f"{vet['birthMonth']} {vet['birthDay']}, {vet['birthYear']}")
            self.vet_discharge_val.config(text=f"{vet['dischargeMonth']} {vet['dischargeDay']}, {vet['dischargeYear']}")
        
        self.stats_label.config(text=f"Record {self.current_index + 1} of {len(self.veterans)}")
    
    def next_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index + 1) % len(self.veterans)
            self.update_veteran_display()
    
    def prev_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index - 1) % len(self.veterans)
            self.update_veteran_display()
    
    def remove_and_next(self):
        """Remove current veteran and move to next"""
        if self.veterans:
            removed = self.veterans.pop(self.current_index)
            self.save_veterans() # Save to current file
            self.log(f"🗑 Removed: {removed.split('|')[0]}...")
            
            if self.current_index >= len(self.veterans):
                self.current_index = 0
            self.update_veteran_display()
    
    def skip_veteran(self):
        """Bỏ qua veteran hiện tại - chỉ xóa veteran, giữ lại email"""
        if self.veterans:
            removed = self.veterans.pop(self.current_index)
            self.save_veterans()
            self.log(f"⏭️ Đã bỏ qua veteran: {removed.split('|')[0]}...")
            
            if self.current_index >= len(self.veterans):
                self.current_index = 0
            self.update_veteran_display()
        else:
            self.log("⚠️ Không có veteran để bỏ qua")
    
    def skip_account(self):
        """Bỏ qua email/account hiện tại - chỉ xóa account, giữ lại veteran"""
        if self.accounts:
            removed_acc = self.accounts.pop(self.current_acc_index)
            try:
                with open(self.account_file, "w", encoding="utf-8") as f:
                    for acc in self.accounts:
                        f.write(acc["raw"] + "\n")
                self.log(f"⏭️ Đã bỏ qua account: {removed_acc.get('email', 'Unknown')}")
            except Exception as e:
                self.log(f"❌ Error saving account file: {str(e)}")
            
            if self.current_acc_index >= len(self.accounts):
                self.current_acc_index = 0
            self.update_account_display()
        else:
            self.log("⚠️ Không có account để bỏ qua")
    
    def reload_data(self):
        """Reload veterans from current file"""
        if self.data_file:
            self.load_data_from_file(self.data_file)
        else:
            messagebox.showinfo("Info", "No file selected to reload.")
    
    def run_verification(self):
        """Run verification in background thread"""
        link = self.link_entry.get().strip()
        
        if not link:
            messagebox.showerror("Missing Input", "Please enter the SheerID link!")
            return
        
        if not self.accounts:
            messagebox.showerror("Missing Input", "Please load an Account file first!")
            return

        if not self.veterans:
            messagebox.showerror("No Data", "No veteran data loaded! Please select a file.")
            return

        # Get current account
        current_acc = self.accounts[self.current_acc_index]
        email = current_acc["email"]
        token = current_acc["token"]
        client_id = current_acc.get("client_id", "")
        
        verification_id = extract_verification_id(link)
        if not verification_id:
            messagebox.showerror("Invalid Link", "Could not find verificationId in the link provided.")
            return
        
        # Disable button
        self.verify_btn.config(state="disabled", text="⏳ PROCESSING...")
        self.status_label.config(text="Verifying...", foreground=COLORS["warning"])
        
        # Run in thread
        thread = threading.Thread(target=self.do_verification, args=(verification_id, email, token, client_id))
        thread.start()
    
    def do_verification(self, verification_id, email, token=None, client_id=None):
        """Perform verification (runs in thread)"""
        try:
            vet = parse_veteran(self.veterans[self.current_index])
            
            self.log(f"🚀 Bắt đầu xác minh: {vet['firstName']} {vet['lastName']}")
            
            # Step 1
            result1 = self.step1_military_status(verification_id)
            
            if not result1:
                self.log("❌ Step 1 (Status Check) FAILED!")
                self.on_verify_fail()
                return
            
            current_step = result1.get("currentStep", "")
            
            # Step 2
            if current_step == "collectInactiveMilitaryPersonalInfo":
                submission_url = result1.get("submissionUrl")
                result2 = self.step2_personal_info(verification_id, vet, email, submission_url)
                
                if result2:
                    final_step = result2.get("currentStep", "")
                    
                    if final_step == "success":
                        self.log("🎉 Verification Instant Success!")
                        self.on_verify_success()
                    elif final_step == "emailLoop":
                        self.log("📧 Đã điền thông tin và gửi email xác minh")
                        
                        email_start_time = datetime.now()
                        
                        if self.accounts and self.current_acc_index < len(self.accounts):
                            current_acc = self.accounts[self.current_acc_index]
                            acc_email = current_acc.get("email", email)
                            refresh_token = current_acc.get("token", token)
                            acc_client_id = current_acc.get("client_id", client_id)
                            
                            if refresh_token and acc_client_id:
                                self.process_email_verification(acc_email, refresh_token, acc_client_id, email_start_time)
                            else:
                                self.log("ℹ️ Vui lòng kiểm tra email thủ công")
                                self.on_verify_success()
                        else:
                            if token and client_id:
                                self.process_email_verification(email, token, client_id, email_start_time)
                            else:
                                self.log("ℹ️ Vui lòng kiểm tra email thủ công")
                                self.on_verify_success()
                    else:
                        self.log(f"⚠️ Unknown final state: {final_step}")
                        self.on_verify_fail()
                else:
                    self.log("❌ Step 2 (Personal Info) LIMITED!")
                    # Xóa link SheerID khỏi ô input khi Step 2 failed
                    self.root.after(0, lambda: self.link_entry.delete(0, tk.END))
                    # Xóa veteran profile khỏi file (giữ lại email)
                    if self.veterans:
                        removed = self.veterans.pop(self.current_index)
                        self.save_veterans()
                        self.log(f"🗑 Đã xóa veteran profile (giữ lại email)")
                        
                        if self.current_index >= len(self.veterans):
                            self.current_index = 0
                        # Cập nhật display trong GUI thread
                        self.root.after(0, self.update_veteran_display)
                    self.on_verify_fail()
            else:
                self.log(f"⚠️ Unexpected flow: {current_step}")
                self.on_verify_fail()
                
        except Exception as e:
            self.log(f"❌ System Error: {str(e)}")
            self.on_verify_fail()

    def process_email_verification(self, user_email, refresh_token, client_id, start_time=None):
        """
        Poll for email MỚI và mở link verify trong browser.
        Sử dụng API dongvanfb.net để đọc email.
        Phát hiện email mới bằng cách so sánh với start_time (thời điểm submit form).
        
        Args:
            user_email: Email address
            refresh_token: Refresh token
            client_id: Client ID
            start_time: Thời điểm submit form (dùng để phát hiện email mới)
        """
        self.log("🔄 Đang chờ email xác minh...")
        
        # Sử dụng start_time để phát hiện email mới (fix: dùng start_time thay vì so sánh count)
        if start_time is None:
            start_time = datetime.now()
        self.log(f"🕐 Start time: {start_time.strftime('%H:%M:%S')}")
        
        found_verify_email = None
        
        for i in range(12):
            if i > 0:
                time.sleep(5)
            
            self.log(f"🔎 Polling email lần {i+1}/12...")
            
            # Đọc email qua API
            result = read_emails_via_api(user_email, refresh_token, client_id)
            
            if result and result.get("status"):
                messages = result.get("messages", [])
                self.log(f"📨 Nhận được {len(messages)} emails")
                
                if messages:
                    # Tìm tất cả email verify hợp lệ
                    current_verify_emails = []
                    for msg in messages:
                        from_info = msg.get("from", [])
                        from_addr = "Unknown"
                        if isinstance(from_info, list) and len(from_info) > 0:
                            first_from = from_info[0]
                            if isinstance(first_from, dict):
                                from_addr = first_from.get("address", "Unknown")
                            elif isinstance(first_from, str):
                                from_addr = first_from
                        elif isinstance(from_info, str):
                            from_addr = from_info
                        subject = msg.get("subject", "").lower()
                        
                        if "verify@sheerid.com" in from_addr.lower() and ("verified" in subject or "verifired" in subject):
                            body = msg.get("message", "")
                            verify_link = find_sheerid_verify_link(body)
                            
                            if verify_link:
                                date_str = msg.get("date", "")
                                email_date = parse_email_date(date_str)
                                
                                current_verify_emails.append({
                                    "email": msg,
                                    "from": from_addr,
                                    "subject": msg.get("subject", ""),
                                    "date": date_str,
                                    "date_obj": email_date,
                                    "date_str": date_str,  # Lưu date string để so sánh
                                    "link": verify_link
                                })
                    
                    if current_verify_emails:
                        # Sắp xếp theo date (mới nhất trước)
                        current_verify_emails.sort(
                            key=lambda x: (x["date_obj"] if x["date_obj"] != datetime.min else datetime.min, x["date_str"]),
                            reverse=True
                        )
                        latest_email = current_verify_emails[0]
                        latest_date_obj = latest_email["date_obj"]
                        
                        self.log(f"📧 Email mới nhất: {latest_email['date']} - {latest_email['subject'][:30]}...")
                        
                        # FIX: So sánh với start_time, bỏ qua giây (vì API email chỉ trả về HH:MM)
                        # Coi email là MỚI nếu cùng phút hoặc sau start_time
                        start_time_no_sec = start_time.replace(second=0, microsecond=0)
                        if latest_date_obj != datetime.min and latest_date_obj >= start_time_no_sec:
                            self.log(f"✅ Phát hiện email MỚI! (sau {start_time_no_sec.strftime('%H:%M')})")
                            found_verify_email = latest_email
                            self.log(f"📨 Email: {found_verify_email['subject']}")
                            self.log(f"🔗 Link: {found_verify_email['link'][:80]}...")
                            break
                        else:
                            self.log(f"⏳ Email chưa đến (email cũ: {latest_email['date']})")
                else:
                    error_msg = result.get("error", "Unknown error") if result else "No response"
                    self.log(f"❌ Lỗi đọc email: {error_msg}")
        
        if found_verify_email:
            verify_link = found_verify_email["link"]
            self.log(f"🌐 Đang mở link trong trình duyệt...")
            
            # Lấy proxy nếu có
            proxy = self.proxy_entry.get().strip() if hasattr(self, 'proxy_entry') else None
            if proxy and proxy == "http://user:pass@host:port":
                proxy = None
            
            # Mở trình duyệt và đọc trạng thái
            browser_result = open_verify_link_in_browser(verify_link, read_status=True, proxy=proxy)
            
            if browser_result["success"]:
                self.log(f"✅ Đã mở trình duyệt!")
                
                # Hiển thị trạng thái nếu có
                if "status_info" in browser_result:
                    status_info = browser_result["status_info"]
                    if status_info.get("success"):
                        status = status_info.get("status", "unknown")
                        message = status_info.get("message", "")
                        
                        if status == "verified":
                            self.log(f"✅ Trạng thái: {message}")
                            self.on_verify_success()
                        elif status == "not_approved":
                            self.log(f"❌ Trạng thái: {message}")
                            # Xóa link SheerID khỏi ô input
                            self.root.after(0, lambda: self.link_entry.delete(0, tk.END))
                            self.log("🗑 Đã xóa link SheerID khỏi ô input")
                            
                            # Nếu NOT APPROVED, chuyển sang veteran tiếp theo
                            self.log("🔄 Chuyển sang veteran tiếp theo...")
                            if self.veterans:
                                # Xóa veteran hiện tại
                                removed = self.veterans.pop(self.current_index)
                                self.save_veterans()
                                self.log(f"🗑 Đã xóa veteran: {removed.split('|')[0] if '|' in removed else removed[:30]}...")
                                
                                # Chuyển sang veteran tiếp theo
                                if self.current_index >= len(self.veterans):
                                    self.current_index = 0
                                
                                if self.veterans:
                                    self.root.after(0, self.update_veteran_display)
                                    self.log(f"✅ Đã chuyển sang veteran tiếp theo")
                                else:
                                    self.log("⚠️ Không còn veteran nào")
                                    self.root.after(0, lambda: self.status_label.config(text="No more veterans", foreground=COLORS["warning"]))
                            self.on_verify_fail()
                        elif status == "pending":
                            self.log(f"⏳ Trạng thái: {message}")
                            self.on_verify_success()
                        else:
                            self.log(f"ℹ️ Trạng thái: {message}")
                            
                            # Hiển thị debug info nếu có
                            if "debug_info" in status_info:
                                debug_info = status_info["debug_info"]
                                self.log(f"   🔍 Debug: HTML length={debug_info.get('html_length', 0)}")
                                self.log(f"   🔍 Keywords: {', '.join(debug_info.get('keywords_found', []))}")
                                self.log(f"   🔍 Has 'not': {debug_info.get('has_not', False)}")
                                self.log(f"   🔍 Has 'approved': {debug_info.get('has_approved', False)}")
                                if debug_info.get("html_preview"):
                                    preview = debug_info["html_preview"].replace('\n', ' ').replace('\r', '')[:200]
                                    self.log(f"   🔍 HTML preview: {preview}...")
                            self.on_verify_success()
                    else:
                        self.log(f"⚠️ Không thể đọc trạng thái: {status_info.get('message', 'Unknown error')}")
                        self.on_verify_success()
            else:
                self.log(f"❌ Không thể mở trình duyệt")
                self.on_verify_fail()
        else:
            self.log("❌ Không tìm thấy email xác minh")
            self.on_verify_fail()
    
    def step1_military_status(self, verification_id):
        url = f"{SHEERID_BASE_URL}/{verification_id}/step/collectMilitaryStatus"
        try:
            proxy = self.proxy_entry.get().strip() if hasattr(self, 'proxy_entry') else None
            with get_httpx_client(proxy) as client:
                response = client.post(url, json={"status": "VETERAN"})
                self.log(f"ℹ️ Step 1 Response: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    # Log error details
                    try:
                        err = response.json()
                        self.log(f"❌ Error: {err.get('errorIds', err)}")
                    except:
                        self.log(f"❌ Error: {response.text[:200]}")
        except Exception as e:
            self.log(f"❌ Exception: {str(e)}")
        return None
    
    def step2_personal_info(self, verification_id, vet, email, submission_url=None):
        url = submission_url or f"{SHEERID_BASE_URL}/{verification_id}/step/collectInactiveMilitaryPersonalInfo"
        
        branch = vet.get("branch", "Navy")
        org = ORGANIZATIONS.get(branch, ORGANIZATIONS["Navy"])
        
        birth_date = format_date(vet["birthYear"], vet["birthMonth"], vet["birthDay"])
        
        # If discharge year is 2025, use actual date. Otherwise use December 1, 2025
        if vet["dischargeYear"] == "2025":
            discharge_date = format_date(vet["dischargeYear"], vet["dischargeMonth"], vet["dischargeDay"])
        else:
            discharge_date = "2025-12-01"
        
        payload = {
            "firstName": vet["firstName"],
            "lastName": vet["lastName"],
            "birthDate": birth_date,
            "email": email,
            "organization": org,
            "dischargeDate": discharge_date,
            "metadata": {}
        }
        
        try:
            proxy = self.proxy_entry.get().strip() if hasattr(self, 'proxy_entry') else None
            with get_httpx_client(proxy) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return None
    
    def on_verify_success(self):
        """Handle successful verification"""
        self.root.after(0, lambda: self.verify_btn.config(state="normal", text="🚀 START VERIFICATION"))
        self.root.after(0, lambda: self.status_label.config(text="✅ Verification Submitted Successfully!", foreground=COLORS["success"]))
        self.root.after(0, lambda: self.log("ℹ️ Email và veteran vẫn được giữ lại"))
    
    def on_verify_fail(self):
        """Handle failed verification"""
        self.root.after(0, lambda: self.verify_btn.config(state="normal", text="🚀 START VERIFICATION"))
        self.root.after(0, lambda: self.status_label.config(text="❌ Verification Failed", foreground=COLORS["error"]))
        self.root.after(0, lambda: self.log("ℹ️ Email và veteran vẫn được giữ lại"))

# ===================== MAIN =====================

if __name__ == "__main__":
    if DND_SUPPORT:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
        
    app = MilitaryVerifyApp(root)
    root.mainloop()
