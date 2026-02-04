"""
API Direct Mode - Grok Signup using Direct API Calls
This bypasses browser automation for faster signup (no Playwright needed)
"""

import httpx
import asyncio
import re
from typing import Optional, Dict
from datetime import datetime

from utils.logger import log_info, log_success, log_error, log_warning
from utils.email_service import generate_email, check_email_for_code


class GrokAPIClient:
    """Direct API client for Grok signup without browser"""
    
    def __init__(self):
        self.base_url = "https://accounts.x.ai"
        self.session = None
        self.cookies = {}
        self.turnstile_token = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'Accept': 'application/grpc-web+proto',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://accounts.x.ai',
                'Referer': 'https://accounts.x.ai/sign-up',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def get_turnstile_token(self) -> Optional[str]:
        """
        Get Cloudflare Turnstile token
        NOTE: This is the hardest part - Turnstile tokens are anti-bot protected
        You may need to use a service like 2captcha or manually solve
        """
        log_warning("⚠️ Turnstile token generation not fully automated")
        log_info("💡 Options:")
        log_info("  1. Use browser mode instead (auto-solves Turnstile)")
        log_info("  2. Integrate 2captcha API for token solving")
        log_info("  3. Manually get token from browser DevTools")
        
        # For now, return None - this will cause API to fail
        # You need to implement one of the options above
        return None
    
    async def create_email_validation_code(self, temp_email: str, first_name: str, last_name: str) -> bool:
        """
        Step 1: Request verification code to be sent to email
        
        API: POST /auth_mgmt.AuthManagement/CreateEmailValidationCode
        """
        try:
            log_info(f"📧 Requesting verification code for {temp_email}...")
            
            # Get Turnstile token (this is the bottleneck)
            turnstile_token = await self.get_turnstile_token()
            if not turnstile_token:
                log_error("❌ Cannot get Turnstile token - use browser mode instead")
                return False
            
            # API endpoint
            url = f"{self.base_url}/auth_mgmt.AuthManagement/CreateEmailValidationCode"
            
            # Protobuf data (binary format used by gRPC-Web)
            # This is a simplified version - actual protobuf encoding is needed
            data = {
                "email": temp_email,
                "givenName": first_name,
                "familyName": last_name,
                "turnstileToken": turnstile_token
            }
            
            response = await self.session.post(
                url,
                json=data,
                headers={
                    'Content-Type': 'application/grpc-web+proto',
                    'x-grpc-web': '1',
                    'x-user-agent': 'connect-es/2.1.1'
                }
            )
            
            if response.status_code == 200:
                log_success("✅ Verification code requested successfully")
                return True
            else:
                log_error(f"❌ Failed to request code: {response.status_code}")
                return False
                
        except Exception as e:
            log_error(f"❌ Error requesting verification code: {str(e)}")
            return False
    
    async def signup_with_code(
        self,
        temp_email: str,
        verification_code: str,
        account_email: str,
        password: str,
        first_name: str,
        last_name: str
    ) -> Dict:
        """
        Step 2: Submit verification code and create account
        
        API: POST /sign-up
        """
        try:
            log_info(f"🔑 Submitting code {verification_code} and creating account...")
            
            url = f"{self.base_url}/sign-up"
            
            # Get fresh Turnstile token
            turnstile_token = await self.get_turnstile_token()
            if not turnstile_token:
                return {'success': False, 'error': 'Cannot get Turnstile token'}
            
            # Request data (Next.js Server Action format)
            payload = [
                {
                    "emailValidationCode": verification_code,
                    "createUserAndSessionRequest": {
                        "email": account_email,
                        "password": password,
                        "givenName": first_name,
                        "familyName": last_name
                    },
                    "promptOnDuplicateEmail": True,
                    "turnstileToken": turnstile_token
                },
                {
                    "client": "$T",
                    "meta": "$undefined",
                    "mutationKey": "$undefined"
                }
            ]
            
            response = await self.session.post(
                url,
                json=payload,
                headers={
                    'Content-Type': 'text/plain;charset=UTF-8',
                    'Accept': 'text/x-component',
                    'next-action': '7fd6b9a73852b0057058b073330fde5a0e648a6bcf',
                }
            )
            
            if response.status_code == 200:
                log_success("✅ Account created successfully!")
                return {'success': True}
            else:
                log_error(f"❌ Signup failed: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            log_error(f"❌ Error during signup: {str(e)}")
            return {'success': False, 'error': str(e)}


async def signup_account_api(
    email: str,
    password: str,
    first_name: str,
    last_name: str
) -> Dict:
    """
    Signup using API Direct mode (faster but requires Turnstile solving)
    
    Returns:
        Dict with status, email, password, temp_email, verification_code or error
    """
    try:
        # Generate temp email
        log_info("📧 Generating temporary email...")
        temp_email = await generate_email()
        log_success(f"✅ Temp email: {temp_email}")
        
        async with GrokAPIClient() as api:
            # Step 1: Request verification code
            success = await api.create_email_validation_code(temp_email, first_name, last_name)
            if not success:
                return {
                    'status': 'failed',
                    'email': email,
                    'error': 'Failed to request verification code',
                    'temp_email': temp_email
                }
            
            # Step 2: Wait and retrieve code from email
            log_info("📬 Waiting for verification code...")
            await asyncio.sleep(5)  # Give email time to arrive
            
            verification_code = await check_email_for_code(temp_email)
            if not verification_code:
                return {
                    'status': 'failed',
                    'email': email,
                    'error': 'Failed to retrieve verification code from email',
                    'temp_email': temp_email
                }
            
            log_success(f"✅ Code received: {verification_code}")
            
            # Step 3: Submit code and create account
            result = await api.signup_with_code(
                temp_email=temp_email,
                verification_code=verification_code,
                account_email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            if result.get('success'):
                return {
                    'status': 'success',
                    'email': email,
                    'password': password,
                    'temp_email': temp_email,
                    'verification_code': verification_code
                }
            else:
                return {
                    'status': 'failed',
                    'email': email,
                    'error': result.get('error', 'Unknown error'),
                    'temp_email': temp_email
                }
    
    except Exception as e:
        return {
            'status': 'failed',
            'email': email,
            'error': str(e),
            'temp_email': None
        }


# Test function
if __name__ == "__main__":
    async def test():
        result = await signup_account_api(
            email="test@example.com",
            password="Password123!",
            first_name="Test",
            last_name="User"
        )
        print(result)
    
    asyncio.run(test())
