"""
Improved API Direct Mode with Multiple Turnstile Solving Options
Supports: 
1. Browser-based solving (recommended, free)
2. 2Captcha API integration (paid, faster)
3. Manual token input (for testing)
"""

import httpx
import asyncio
import os
from typing import Optional, Dict
from datetime import datetime

from utils.logger import log_info, log_success, log_error, log_warning
from utils.email_service import generate_email, check_email_for_code


class TurnstileSolver:
    """Handles Cloudflare Turnstile solving with multiple methods"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CAPTCHA_API_KEY')
        self.method = 'browser'  # 'browser', '2captcha', or 'manual'
        
    async def solve_with_2captcha(self, sitekey: str, page_url: str) -> Optional[str]:
        """
        Solve Turnstile using 2Captcha service
        Doc: https://2captcha.com/2captcha-api#turnstile
        """
        if not self.api_key:
            log_error("❌ 2Captcha API key not set")
            return None
            
        try:
            log_info("📡 Submitting Turnstile to 2Captcha...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Submit CAPTCHA
                submit_url = "http://2captcha.com/in.php"
                submit_data = {
                    'key': self.api_key,
                    'method': 'turnstile',
                    'sitekey': sitekey,
                    'pageurl': page_url,
                    'json': 1
                }
                
                response = await client.post(submit_url, data=submit_data)
                result = response.json()
                
                if result.get('status') != 1:
                    log_error(f"❌ 2Captcha submit failed: {result.get('request')}")
                    return None
                
                captcha_id = result.get('request')
                log_info(f"✅ CAPTCHA submitted, ID: {captcha_id}")
                
                # Step 2: Wait and retrieve solution
                log_info("⏳ Waiting for solution (30-60s)...")
                check_url = "http://2captcha.com/res.php"
                
                for attempt in range(20):  # Max 60 seconds
                    await asyncio.sleep(3)
                    
                    check_data = {
                        'key': self.api_key,
                        'action': 'get',
                        'id': captcha_id,
                        'json': 1
                    }
                    
                    response = await client.get(check_url, params=check_data)
                    result = response.json()
                    
                    if result.get('status') == 1:
                        token = result.get('request')
                        log_success(f"✅ Got Turnstile token!")
                        return token
                    elif result.get('request') != 'CAPCHA_NOT_READY':
                        log_error(f"❌ Solution failed: {result.get('request')}")
                        return None
                
                log_error("❌ Timeout waiting for solution")
                return None
                
        except Exception as e:
            log_error(f"❌ 2Captcha error: {str(e)}")
            return None
    
    async def solve_with_browser(self, page_url: str) -> Optional[str]:
        """
        Solve Turnstile using browser automation with stealth
        MORE RELIABLE and FREE
        """
        try:
            from playwright.async_api import async_playwright
            
            log_info("🌐 Starting browser for Turnstile solving...")
            
            async with async_playwright() as p:
                # Launch with stealth settings
                browser = await p.chromium.launch(
                    headless=False,  # Must be visible for Turnstile
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-site-isolation-trials'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width':1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                
                # Remove automation indicators
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = {runtime: {}};
                """)
                
                page = await context.new_page()
                
                log_info(f"🔗 Navigating to: {page_url}")
                await page.goto(page_url, wait_until='networkidle')
                
                # Wait for Turnstile to auto-solve (usually works in visible mode)
                log_info("⏳ Waiting for Turnstile auto-solve (30s)...")
                await asyncio.sleep(30)
                
                # Extract token (implementation depends on how Grok embeds it)
                # Usually it's in a hidden input or passed via JavaScript
                token = await page.evaluate("""
                    () => {
                        const turnstileInput = document.querySelector('[name="cf-turnstile-response"]');
                        if (turnstileInput) return turnstileInput.value;
                        
                        // Alternative: check for turnstile callback
                        if (window.turnstileToken) return window.turnstileToken;
                        
                        return null;
                    }
                """)
                
                await browser.close()
                
                if token:
                    log_success("✅ Got Turnstile token from browser!")
                    return token
                else:
                    log_error("❌ Could not extract Turnstile token")
                    return None
                    
        except Exception as e:
            log_error(f"❌ Browser solving failed: {str(e)}")
            return None


async def signup_account_api_improved(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    solver_method: str = 'browser',  # 'browser', '2captcha', or 'manual'
    api_key: Optional[str] = None
) -> Dict:
    """
    Improved API Direct signup with multiple Turnstile solving options
    
    Args:
        email: Grok account email
        password: Grok account password
        first_name: First name
        last_name: Last name
        solver_method: 'browser' (free, recommended), '2captcha' (paid, fast), or 'manual'
        api_key: 2Captcha API key (required if using 2captcha method)
    
    Returns:
        Dict with status, email, password, or error
    """
    try:
        # Step 1: Generate temp email
        log_info("📧 Generating temporary email...")
        temp_email = await generate_email()
        log_success(f"✅ Temp email: {temp_email}")
        
        # Step 2: Solve Turnstile
        solver = TurnstileSolver(api_key=api_key)
        
        if solver_method == '2captcha':
            turnstile_token = await solver.solve_with_2captcha(
                sitekey='0x4AAAAAAAxxxx',  # Get from Grok page
                page_url='https://accounts.x.ai/sign-up'
            )
        elif solver_method == 'browser':
            log_warning("⚠️ Browser method requires visible browser")
            log_info("💡 Recommendation: Use Browser Mode instead of API Direct")
            turnstile_token = await solver.solve_with_browser(
                page_url='https://accounts.x.ai/sign-up'
            )
        else:
            log_info("🔑 Manual token mode - get token manually and update code")
            turnstile_token = None
        
        if not turnstile_token:
            return {
                'status': 'failed',
                'email': email,
                'error': 'Failed to solve Turnstile - use Browser Mode instead',
                'temp_email': temp_email
            }
        
        # Step 3: Submit signup with token
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create verification code request
            url = "https://accounts.x.ai/api/signup/request-code"
            data = {
                'email': temp_email,
                'givenName': first_name,
                'familyName': last_name,
                'turnstileToken': turnstile_token
            }
            
            response = await client.post(url, json=data)
            
            if response.status_code != 200:
                return {
                    'status': 'failed',
                    'email': email,
                    'error': f'Request code failed: {response.status_code}',
                    'temp_email': temp_email
                }
            
            # Step 4: Get verification code
            log_info("📬 Waiting for verification code...")
            await asyncio.sleep(5)
            verification_code = await check_email_for_code(temp_email)
            
            if not verification_code:
                return {
                    'status': 'failed',
                    'email': email,
                    'error': 'Failed to get verification code',
                    'temp_email': temp_email
                }
            
            # Step 5: Complete signup
            url = "https://accounts.x.ai/api/signup/complete"
            data = {
                'code': verification_code,
                'email': email,
                'password': password,
                'givenName': first_name,
                'familyName': last_name,
                'turnstileToken': turnstile_token  # May need fresh token
            }
            
            response = await client.post(url, json=data)
            
            if response.status_code == 200:
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
                    'error': f'Signup failed: {response.status_code}',
                    'temp_email': temp_email
                }
    
    except Exception as e:
        return {
            'status': 'failed',
            'email': email,
            'error': str(e),
            'temp_email': None
        }


# For backward compatibility
async def signup_account_api(email, password, first_name, last_name):
    """Original function - now uses improved version with browser method"""
    log_warning("⚠️ Using legacy API Direct - recommend Browser Mode instead")
    return await signup_account_api_improved(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        solver_method='browser'
    )
