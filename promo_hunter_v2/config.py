#!/usr/bin/env python3
"""
Cấu hình cho Promo Hunter V2
"""

# API Configuration
API_URL = "https://chatgpt.com/backend-api/promotions/eligibility/"
BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc1NTQ3MjU1NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7InVzZXJfaWQiOiJ1c2VyLVdhOGZqbXlTeEFON0p5aFNkSFEwUWFxcyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJsYWdhMjEzNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImlhdCI6MTc1NDYwODU1NSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIwZWY5NDc0Mi1mMjU0LTQxMWEtODQ1Yy1iYzdkNDVlNTQ4YjIiLCJuYmYiOjE3NTQ2MDg1NTUsInB3ZF9hdXRoX3RpbWUiOjE3NTQ2MDg1NTMwMTMsInNjcCI6WyJvcGVuaWQiLCJlbWFpbCIsInByb2ZpbGUiLCJvZmZsaW5lX2FjY2VzcyIsIm1vZGVsLnJlcXVlc3QiLCJtb2RlbC5yZWFkIiwib3JnYW5pemF0aW9uLnJlYWQiLCJvcmdhbml6YXRpb24ud3JpdGUiXSwic2Vzc2lvbl9pZCI6ImF1dGhzZXNzX0s3Z0V1bmhNOE1mbU83TGh1YVdiOGRYWiIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MTgwODE5MDAzMjg4MzcxODEwIn0.GrYZm_mrbmB9mQdOoTgtUNUJh3sKC9I9LBY7vVmwuqOYivuaSV-UjGBHbbP-CeeZg-v0XWPeVMaOxVoz_Kf64ahUIewsmWQW2h-J0kZQatqY4bgnrergURjdExwNWjhzArSKzbcW8DX6fQDE9s4XQ3c9XNLq8XlE6EJQmX5HrmJVYlm2bhDZ4WdrdRGIXivSbLJAWNOhHHnFAvrnnzp_LbqyLld7913BGloj4jA_ss4CeHTzJIKM6DklFv6wT0lvtCsCCkMcUeKAEcRCGuQN8K0pm3-jm_ADxQ0m_JQivLKLTi6eBvwCkN6adEEanGZSOQKpLSoRUf-qwI2lwIJSJEWb_F4Qv-9J6eEPFvlRGg3vvkV45EE2Gr86BVQ2LJ29eoLJlTlYXqG7Lfy5zz08Lc5V2DNwPj94trmIYjTi9K-3uOLpJxdbPSQxvjgmivCwzr-bWIi3F1Fc_MEbYy1QHgRmAo3ksPiYoEHbQHYxPOWRD7TcQfAwAo97i25RtPJ4TQ8xYc0LK4hMCIal6CsCdG6bc3eoYPuEGnT65FQwjuzd3zD6Kt0g2Is3P0hpBAE2yz-9UvusX6Za8pDH9DYme03KgR76XsZjxIYUG_dvEmMTQyh2iPMywmAff8kwNeFbK0wbUcmuuykSDpo02psB81EJEPrLAd5xP6qfaLG0aWw"

# Promo Code Settings
CODE_LENGTH = 16
CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Performance Settings
REQUEST_DELAY = 0.3  # giây giữa các request
REQUEST_TIMEOUT = 10  # timeout cho mỗi request
MAX_RETRIES = 2  # số lần retry khi lỗi
BATCH_SIZE = 100  # số codes tạo mỗi batch

# Threading Settings
MAX_WORKERS = 2  # số thread concurrent (tăng nếu muốn nhanh hơn)

# Output Files
VALID_CODES_FILE = "valid_codes.txt"
ALL_RESULTS_FILE = "results.json"
PROGRESS_FILE = "progress.json"
LOG_FILE = "hunt.log"

# Generator Settings
GENERATION_STRATEGIES = {
    'pattern_based': 0.40,    # 40% dựa trên pattern học được
    'prefix_based': 0.25,     # 25% dựa trên prefix phổ biến
    'variation': 0.20,        # 20% biến thể của valid codes
    'random': 0.15           # 15% random hoàn toàn
}

# Common promo prefixes và patterns
COMMON_PREFIXES = [
    "SAVE", "DISC", "PROM", "GIFT", "FREE", "COUP", "DEAL", "SPEC",
    "NEW", "HOT", "VIP", "MEGA", "SUPER", "BEST", "TOP", "MAX"
]

COMMON_SUFFIXES = [
    "2024", "2025", "NOW", "OFF", "WIN", "GET", "BUY", "USE"
]

YEAR_PATTERNS = ["2024", "2025", "24", "25"]

# Character substitution map (similar looking chars)
CHAR_SUBSTITUTIONS = {
    '0': ['O', 'Q'],
    'O': ['0', 'Q'], 
    'I': ['1', 'L'],
    '1': ['I', 'L'],
    'S': ['5'],
    '5': ['S'],
    'B': ['8'],
    '8': ['B'],
    'G': ['6'],
    '6': ['G']
}

# Headers cho HTTP requests
HTTP_HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://chatgpt.com",
    "Referer": "https://chatgpt.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors", 
    "Sec-Fetch-Site": "same-origin"
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}
