# -*- coding: utf-8 -*-
"""
V11 Multi-Profile Login Tool - Email OTP Handler
Lấy OTP từ email qua API dongvanfb.net
"""

import requests
import re
import time
from datetime import datetime
import config


class EmailOTPHandler:
    """Class xử lý lấy OTP từ email"""
    
    # API endpoints
    API_GET_CODE = "https://tools.dongvanfb.net/api/get_code_oauth2"
    API_GET_MESSAGES = "https://tools.dongvanfb.net/api/get_messages_oauth2"
    
    def __init__(self, logger=None):
        self.logger = logger or print
    
    def log(self, message, level="info"):
        """Log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logger(f"[{timestamp}] [{level.upper()}] {message}")
    
    def get_otp(self, email_login: str, email_password: str, 
                refresh_token: str, client_id: str,
                otp_type: str = "openai") -> dict:
        """
        Lấy OTP code từ email
        
        Args:
            email_login: Email login (email@domain.com)
            email_password: Password email (không dùng cho OAuth2)
            refresh_token: Refresh token cho OAuth2
            client_id: Client ID cho OAuth2
            otp_type: Loại OTP cần lấy (openai, facebook, google, etc.)
            
        Returns:
            dict with keys:
                - success: bool
                - otp: str (6 digit code) or None
                - message: str
        """
        self.log(f"📧 Getting OTP for {email_login} (type={otp_type})...")
        
        # Method 1: Try get_code_oauth2 API (returns code directly)
        result = self._try_get_code_api(email_login, refresh_token, client_id, otp_type)
        if result['success']:
            return result
        
        # Method 2: Try get_messages_oauth2 and extract code
        result = self._try_get_messages_api(email_login, refresh_token, client_id)
        if result['success']:
            return result
        
        return {
            'success': False,
            'otp': None,
            'message': 'Failed to get OTP from all methods'
        }
    
    def _try_get_code_api(self, email: str, refresh_token: str, 
                          client_id: str, otp_type: str) -> dict:
        """
        Lấy OTP qua graph_code API - lấy mã MỚI NHẤT
        Sử dụng type 'all' để không bị cache
        """
        try:
            # Try graph_code API first (more reliable)
            graph_api_url = "https://tools.dongvanfb.net/api/graph_code"
            
            payload = {
                'email': email,
                'refresh_token': refresh_token,
                'client_id': client_id,
                'type': 'all'  # Get all codes, filter later
            }
            
            self.log(f"🌐 Calling graph_code API...")
            
            response = requests.post(
                graph_api_url,
                json=payload,
                timeout=config.OTP_API_TIMEOUT,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Cache-Control': 'no-cache'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and data.get('status') == True:
                    code = data.get('code', '')
                    content = data.get('content', '')
                    date_str = data.get('date', '')
                    
                    self.log(f"📨 API Response: code={code}, date={date_str}")
                    
                    # Check if code is valid 6-digit
                    if code and re.match(r'^\d{6}$', str(code)):
                        return {
                            'success': True,
                            'otp': str(code),
                            'message': f"Got code: {code} (date: {date_str})"
                        }
                    
                    # Extract from content
                    if content:
                        match = re.search(r'\b(\d{6})\b', content)
                        if match:
                            return {
                                'success': True,
                                'otp': match.group(1),
                                'message': f"Extracted from content: {match.group(1)}"
                            }
                
                self.log(f"⚠️ graph_code returned no valid code")
            
            # Fallback to get_code_oauth2
            self.log(f"🌐 Falling back to get_code_oauth2 API (type={otp_type})...")
            
            response = requests.post(
                self.API_GET_CODE,
                json={
                    'email': email,
                    'refresh_token': refresh_token,
                    'client_id': client_id,
                    'type': otp_type
                },
                timeout=config.OTP_API_TIMEOUT,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"📨 API Response: status={data.get('status')}, code={data.get('code')}")
                
                if data.get('status') == True and data.get('code'):
                    code = str(data['code'])
                    if re.match(r'^\d{6}$', code):
                        return {
                            'success': True,
                            'otp': code,
                            'message': f"Got code: {code}"
                        }
            
            return {
                'success': False,
                'otp': None,
                'message': 'No valid code from APIs'
            }
                
        except Exception as e:
            self.log(f"⚠️ get_code API error: {e}")
            return {
                'success': False,
                'otp': None,
                'message': str(e)
            }
    
    def _try_get_messages_api(self, email: str, refresh_token: str, 
                              client_id: str) -> dict:
        """
        Lấy OTP qua get_messages_oauth2 API và extract từ messages
        """
        try:
            payload = {
                'email': email,
                'refresh_token': refresh_token,
                'client_id': client_id
            }
            
            self.log("🌐 Calling get_messages_oauth2 API...")
            
            response = requests.post(
                self.API_GET_MESSAGES,
                json=payload,
                timeout=config.OTP_API_TIMEOUT,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'otp': None,
                    'message': f'HTTP {response.status_code}'
                }
            
            # Parse response - handle both JSON and string
            try:
                data = response.json()
            except:
                # Response might be plain text
                text = response.text
                match = re.search(r'\b(\d{6})\b', text)
                if match:
                    return {
                        'success': True,
                        'otp': match.group(1),
                        'message': 'Extracted from text response'
                    }
                return {
                    'success': False,
                    'otp': None,
                    'message': 'Response is not JSON'
                }
            
            # Check if data is dict
            if not isinstance(data, dict):
                self.log(f"⚠️ Response is not dict: {type(data)}")
                # Try extract code from string
                text = str(data)
                match = re.search(r'\b(\d{6})\b', text)
                if match:
                    return {
                        'success': True,
                        'otp': match.group(1),
                        'message': 'Extracted from string response'
                    }
                return {
                    'success': False,
                    'otp': None,
                    'message': 'Response is not dict'
                }
            
            # Check status
            if data.get('status') != True:
                return {
                    'success': False,
                    'otp': None,
                    'message': data.get('message', 'status=False')
                }
            
            # Check direct code field
            if data.get('code'):
                return {
                    'success': True,
                    'otp': str(data['code']),
                    'message': 'Got from code field'
                }
            
            # Search in messages for OpenAI/ChatGPT email
            messages = data.get('messages', [])
            if not isinstance(messages, list):
                messages = []
            
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                
                # Get sender - handle both list and string formats
                sender = ''
                from_field = msg.get('from', [])
                if isinstance(from_field, list) and len(from_field) > 0:
                    first_from = from_field[0]
                    if isinstance(first_from, dict):
                        sender = first_from.get('address', '')
                    elif isinstance(first_from, str):
                        sender = first_from
                elif isinstance(from_field, str):
                    sender = from_field
                
                subject = msg.get('subject', '') or ''
                code = msg.get('code', '')
                
                # Check if from OpenAI
                if 'openai' in sender.lower() or 'chatgpt' in subject.lower():
                    if code:
                        return {
                            'success': True,
                            'otp': str(code),
                            'message': f'From OpenAI email: {code}'
                        }
                    
                    # Extract from message content
                    content = msg.get('message', '') or ''
                    match = re.search(r'\b(\d{6})\b', content)
                    if match:
                        return {
                            'success': True,
                            'otp': match.group(1),
                            'message': 'Extracted from OpenAI email'
                        }
            
            # Fallback: get most recent 6-digit code
            for msg in messages[:5]:  # Check first 5 messages
                if not isinstance(msg, dict):
                    continue
                
                code = msg.get('code', '')
                if code and re.match(r'^\d{6}$', str(code)):
                    return {
                        'success': True,
                        'otp': str(code),
                        'message': 'Got from recent message'
                    }
                
                content = msg.get('message', '') or ''
                match = re.search(r'\b(\d{6})\b', content)
                if match:
                    return {
                        'success': True,
                        'otp': match.group(1),
                        'message': 'Extracted from recent message'
                    }
            
            return {
                'success': False,
                'otp': None,
                'message': 'No OTP found in messages'
            }
                
        except Exception as e:
            self.log(f"⚠️ get_messages_oauth2 error: {e}")
            return {
                'success': False,
                'otp': None,
                'message': str(e)
            }
    
    def get_otp_with_retry(self, email_login: str, email_password: str,
                           refresh_token: str, client_id: str,
                           max_retries: int = None, retry_delay: int = None,
                           otp_type: str = "openai") -> dict:
        """
        Lấy OTP với retry logic
        """
        max_retries = max_retries or config.OTP_RETRY_COUNT
        retry_delay = retry_delay or config.OTP_RETRY_DELAY
        
        for attempt in range(max_retries):
            if attempt > 0:
                self.log(f"⏳ Retry {attempt}/{max_retries}, waiting {retry_delay}s...")
                time.sleep(retry_delay)
            
            result = self.get_otp(email_login, email_password, 
                                  refresh_token, client_id, otp_type)
            
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
    Helper function để lấy OTP
    
    Returns:
        OTP string hoặc None
    """
    handler = EmailOTPHandler(logger=logger)
    result = handler.get_otp_with_retry(
        email_login=email_login,
        email_password=email_password,
        refresh_token=refresh_token,
        client_id=client_id,
        max_retries=max_retries,
        otp_type="openai"  # Default to OpenAI for ChatGPT
    )
    return result.get('otp')


# Test function
if __name__ == "__main__":
    handler = EmailOTPHandler()
    
    # Test with sample data
    result = handler.get_otp(
        email_login="test@outlook.com",
        email_password="password123",
        refresh_token="M.C518_BAY.0.U.-xxx",
        client_id="9e5f94bc-e8a4-4e73-b8be-63364c29d753"
    )
    print(f"Result: {result}")
