# -*- coding: utf-8 -*-
"""
V11 Multi-Profile Login Tool - Email OTP Handler
Xử lý lấy OTP từ email thông qua API
"""

import requests
import re
import time
from datetime import datetime
import config


class EmailOTPHandler:
    """Class xử lý lấy OTP từ email"""
    
    def __init__(self, logger=None):
        """
        Args:
            logger: Function để log messages (optional)
        """
        self.logger = logger or print
    
    def log(self, message, level="info"):
        """Log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logger(f"[{timestamp}] [{level.upper()}] {message}")
    
    def get_otp(self, email_login: str, email_password: str, 
                refresh_token: str, client_id: str) -> dict:
        """
        Lấy OTP code từ email
        
        Args:
            email_login: Email login (email@domain.com)
            email_password: Password email
            refresh_token: Refresh token cho OAuth
            client_id: Client ID cho OAuth
            
        Returns:
            dict with keys:
                - success: bool
                - otp: str (6 digit code) or None
                - message: str (error message if failed)
        """
        self.log(f"📧 Getting OTP for {email_login}...")
        
        # Thử từng API endpoint
        for endpoint in config.OTP_API_ENDPOINTS:
            result = self._try_get_otp(
                endpoint, email_login, email_password, 
                refresh_token, client_id
            )
            if result['success']:
                return result
        
        return {
            'success': False,
            'otp': None,
            'message': 'Failed to get OTP from all endpoints'
        }
    
    def get_otp_with_retry(self, email_login: str, email_password: str,
                           refresh_token: str, client_id: str,
                           max_retries: int = None, retry_delay: int = None) -> dict:
        """
        Lấy OTP với retry logic
        
        Args:
            email_login, email_password, refresh_token, client_id: Credentials
            max_retries: Số lần retry (default từ config)
            retry_delay: Delay giữa các lần retry (default từ config)
            
        Returns:
            dict with success, otp, message
        """
        max_retries = max_retries or config.OTP_RETRY_COUNT
        retry_delay = retry_delay or config.OTP_RETRY_DELAY
        
        for attempt in range(max_retries):
            if attempt > 0:
                self.log(f"⏳ Retry {attempt}/{max_retries}, waiting {retry_delay}s...")
                time.sleep(retry_delay)
            
            result = self.get_otp(email_login, email_password, 
                                  refresh_token, client_id)
            
            if result['success']:
                self.log(f"✅ Got OTP: {result['otp']}", "success")
                return result
            else:
                self.log(f"⚠️ Attempt {attempt + 1} failed: {result['message']}", "warning")
        
        return {
            'success': False,
            'otp': None,
            'message': f'Failed to get OTP after {max_retries} retries'
        }
    
    def _try_get_otp(self, endpoint: str, email_login: str, email_password: str,
                     refresh_token: str, client_id: str) -> dict:
        """
        Thử lấy OTP từ một endpoint cụ thể
        """
        try:
            # Prepare request data
            data = {
                'email': email_login,
                'password': email_password,
                'refresh_token': refresh_token,
                'client_id': client_id,
                'type': 'openai'  # Loại email cần lấy OTP
            }
            
            self.log(f"🌐 Trying endpoint: {endpoint}")
            
            response = requests.post(
                endpoint,
                json=data,
                timeout=config.OTP_API_TIMEOUT,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse OTP from response
                if result.get('success') or result.get('status') == 'success':
                    otp = result.get('otp') or result.get('code') or result.get('data', {}).get('otp')
                    
                    if otp:
                        # Validate OTP format (6 digits)
                        otp_str = str(otp)
                        if re.match(r'^\d{6}$', otp_str):
                            return {
                                'success': True,
                                'otp': otp_str,
                                'message': 'OK'
                            }
                        else:
                            return {
                                'success': False,
                                'otp': None,
                                'message': f'Invalid OTP format: {otp_str}'
                            }
                    else:
                        # Thử extract OTP từ body/content nếu có
                        body = result.get('body') or result.get('content') or ''
                        otp_match = re.search(r'\b(\d{6})\b', str(body))
                        if otp_match:
                            return {
                                'success': True,
                                'otp': otp_match.group(1),
                                'message': 'OK (extracted from body)'
                            }
                        
                        return {
                            'success': False,
                            'otp': None,
                            'message': result.get('message') or 'No OTP in response'
                        }
                else:
                    return {
                        'success': False,
                        'otp': None,
                        'message': result.get('message') or 'API returned error'
                    }
            else:
                return {
                    'success': False,
                    'otp': None,
                    'message': f'HTTP {response.status_code}: {response.text[:100]}'
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'otp': None,
                'message': f'Timeout connecting to {endpoint}'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'otp': None,
                'message': f'Request error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'otp': None,
                'message': f'Error: {str(e)}'
            }


# Helper function for simple import
def get_otp_from_email(
    email_login: str,
    email_password: str,
    refresh_token: str,
    client_id: str,
    max_retries: int = None,
    logger=None
) -> str:
    """
    Helper function để lấy OTP (wrapper cho EmailOTPHandler)
    
    Returns:
        OTP string hoặc None nếu thất bại
    """
    handler = EmailOTPHandler(logger=logger)
    result = handler.get_otp_with_retry(
        email_login=email_login,
        email_password=email_password,
        refresh_token=refresh_token,
        client_id=client_id,
        max_retries=max_retries
    )
    return result.get('otp')


# Test function
if __name__ == "__main__":
    handler = EmailOTPHandler()
    
    # Test with sample data
    result = handler.get_otp(
        email_login="test@example.com",
        email_password="password123",
        refresh_token="token123",
        client_id="client123"
    )
    print(f"Result: {result}")
