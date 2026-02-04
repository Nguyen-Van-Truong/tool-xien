"""Logging utilities with colored output"""

import logging
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style
from config import OUTPUT_LOG_DIR

# Initialize colorama for Windows
init(autoreset=True)

# Create logs directory if it doesn't exist
Path(OUTPUT_LOG_DIR).mkdir(parents=True, exist_ok=True)

# Set up file logging
log_filename = f"{OUTPUT_LOG_DIR}/grok_signup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def log_info(message: str):
    """Log info message with blue color"""
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
    logger.info(message)


def log_success(message: str):
    """Log success message with green color"""
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
    logger.info(message)


def log_warning(message: str):
    """Log warning message with yellow color"""
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")
    logger.warning(message)


def log_error(message: str):
    """Log error message with red color"""
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")
    logger.error(message)


def log_debug(message: str):
    """Log debug message with magenta color"""
    print(f"{Fore.MAGENTA}{message}{Style.RESET_ALL}")
    logger.debug(message)


def get_log_filename() -> str:
    """Get the current log filename"""
    return log_filename
