"""Utils package initialization"""

from .logger import log_info, log_success, log_warning, log_error, log_debug
from .email_service import generate_email, check_email_for_code

__all__ = [
    'log_info', 
    'log_success', 
    'log_warning', 
    'log_error', 
    'log_debug',
    'generate_email',
    'check_email_for_code'
]
