"""Configuration settings for Grok Signup Tool"""

# API Endpoints
TINYHOST_DOMAINS_API = "https://tinyhost.shop/api/random-domains/?limit=10"
GROK_SIGNUP_URL = "https://accounts.x.ai/sign-up"
GROK_VALIDATION_API = "https://accounts.x.ai/auth_mgmt.AuthManagement/CreateEmailValidationCode"

# Email settings
BLOCKED_DOMAINS = ['tempmail.com', 'guerrillamail.com']
EMAIL_USERNAME_LENGTH = 16
EMAIL_CHECK_MAX_RETRIES = 10
EMAIL_CHECK_INTERVAL = 5  # seconds

# Browser settings
BROWSER_HEADLESS = False  # Set to True for production
BROWSER_SLOW_MO = 500  # ms delay between actions for stealth
BROWSER_TIMEOUT = 30000  # 30 seconds

# Cloudflare/Turnstile settings
CLOUDFLARE_WAIT_TIMEOUT = 60  # Increased from 30 to 60 seconds for better Cloudflare handling
CLOUDFLARE_RETRY_DELAY = 3# seconds to wait for challenge

# Signup flow timeouts
SIGNUP_WAIT_AFTER_EMAIL = 3  # seconds
SIGNUP_WAIT_AFTER_CODE_SEND = 2  # seconds
SIGNUP_WAIT_AFTER_CODE_SUBMIT = 3  # seconds

# Account processing
DELAY_BETWEEN_ACCOUNTS = 30  # seconds to avoid detection

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
]

# Default names for auto-generation
DEFAULT_FIRST_NAMES = [
    "John", "Jane", "Michael", "Sarah", "David", "Emily", 
    "James", "Emma", "Robert", "Olivia", "William", "Ava"
]

DEFAULT_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez"
]

# Output files
OUTPUT_SUCCESS_FILE = "output/success.txt"
OUTPUT_FAILED_FILE = "output/failed.txt"
OUTPUT_LOG_DIR = "output/logs"

# Input file
INPUT_ACCOUNTS_FILE = "input/accounts.txt"
