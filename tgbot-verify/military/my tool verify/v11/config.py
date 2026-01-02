# -*- coding: utf-8 -*-
"""
V11 Multi-Profile Login Tool - Configuration
Các tham số có thể tùy chỉnh
"""

import os

# =============================================================================
# BROWSER SETTINGS
# =============================================================================
MAX_CONCURRENT_BROWSERS = 3          # Số browser tối đa chạy cùng lúc
BROWSER_PATH = ""                     # Đường dẫn browser (để trống = auto-detect)
KEEP_BROWSER_OPEN = True              # Giữ browser mở sau khi hoàn thành

# =============================================================================
# TIMEOUT SETTINGS (giây)
# =============================================================================
PAGE_LOAD_TIMEOUT = 30                # Timeout load trang
ELEMENT_TIMEOUT = 10                  # Timeout tìm element
OTP_TIMEOUT = 60                      # Timeout chờ OTP
OTP_RETRY_COUNT = 3                   # Số lần retry lấy OTP
OTP_RETRY_DELAY = 10                  # Delay giữa các lần retry OTP (giây)

# =============================================================================
# HUMAN-LIKE BEHAVIOR SETTINGS
# =============================================================================
HUMAN_DELAY_MIN = 0.5                 # Delay tối thiểu giữa các action (giây)
HUMAN_DELAY_MAX = 1.5                 # Delay tối đa giữa các action (giây)
TYPING_DELAY_MIN = 0.05               # Delay tối thiểu giữa các ký tự
TYPING_DELAY_MAX = 0.15               # Delay tối đa giữa các ký tự

# =============================================================================
# DIRECTORIES
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
PROFILE_DIR = os.path.join(BASE_DIR, "profiles")

# Tạo thư mục nếu chưa tồn tại
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

# =============================================================================
# OTP EMAIL API SETTINGS
# =============================================================================
# API endpoints để lấy OTP từ email
OTP_API_ENDPOINTS = [
    "https://tools.dongvanfb.net/api/get-code",  # Primary
    "https://tinyhost.shop/api/get-code",         # Backup
]
OTP_API_TIMEOUT = 30                              # Timeout cho API request

# =============================================================================
# URLS
# =============================================================================
CHATGPT_URL = "https://chatgpt.com"
AUTH_URL_PREFIX = "https://auth.openai.com"

# =============================================================================
# WINDOW LAYOUT
# =============================================================================
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
