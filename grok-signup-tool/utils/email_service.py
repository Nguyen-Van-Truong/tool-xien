"""Email service for generating temporary emails and retrieving verification codes"""

import httpx
import asyncio
import random
import string
from typing import Optional
from config import (
    TINYHOST_DOMAINS_API,
    BLOCKED_DOMAINS,
    EMAIL_USERNAME_LENGTH,
    EMAIL_CHECK_MAX_RETRIES,
    EMAIL_CHECK_INTERVAL
)
from utils.logger import log_info, log_error, log_success


async def get_random_domain() -> str:
    """
    Fetch random email domain from tinyhost.shop API
    
    Returns:
        str: A random email domain
        
    Raises:
        Exception: If unable to fetch domains
    """
    try:
        log_info("🌐 Fetching random email domains...")
        async with httpx.AsyncClient() as client:
            response = await client.get(TINYHOST_DOMAINS_API, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            domains = data.get('domains', [])
            
            if not domains:
                raise Exception("No domains returned from API")
            
            # Filter out blocked domains
            filtered_domains = [
                domain for domain in domains
                if not any(blocked in domain for blocked in BLOCKED_DOMAINS)
            ]
            
            if not filtered_domains:
                raise Exception("No valid domains after filtering")
            
            # Pick a random domain
            domain = random.choice(filtered_domains)
            log_success(f"✅ Selected domain: {domain}")
            return domain
            
    except Exception as e:
        log_error(f"❌ Failed to fetch domains: {str(e)}")
        raise


def generate_random_username(length: int = EMAIL_USERNAME_LENGTH) -> str:
    """
    Generate random alphanumeric username
    
    Args:
        length: Length of username (default from config)
        
    Returns:
        str: Random username
    """
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


async def generate_email() -> str:
    """
    Generate a random temporary email address
    
    Returns:
        str: Complete email address (username@domain.com)
    """
    domain = await get_random_domain()
    username = generate_random_username()
    email = f"{username}@{domain}"
    
    log_info(f"📧 Generated email: {email}")
    return email


async def check_email_for_code(email: str, max_retries: int = EMAIL_CHECK_MAX_RETRIES) -> Optional[str]:
    """
    Check email inbox for verification code using Tinyhost API
    
    Args:
        email: The email address to check
        max_retries: Maximum number of retries (default from config)
        
    Returns:
        str: Verification code (e.g., "OMK-QZN") or None if not found
    """
    log_info(f"📬 Checking email {email} for verification code...")
    
    # Extract username and domain
    username, domain = email.split('@')
    
    # Tinyhost inbox URL format: https://tinyhost.shop/{email}
    inbox_url = f"https://tinyhost.shop/{email}"
    
    for attempt in range(1, max_retries + 1):
        try:
            log_info(f"📨 Attempt {attempt}/{max_retries} to fetch code...")
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Get inbox page
                response = await client.get(inbox_url)
                response.raise_for_status()
                
                html_content = response.text
                
                # Look for verification code patterns in HTML
                # Grok sends codes like "OMK-QZN" (3 letters - hyphen - 3 letters/numbers)
                import re
                
                # Pattern 1: Standard code format XXX-XXX
                code_patterns = [
                    r'\b([A-Z]{3}-[A-Z0-9]{3})\b',  # Like OMK-QZN
                    r'\b([A-Z0-9]{6})\b',            # Like UCOX8L (6 chars)
                    r'code[:\s]+([A-Z0-9]{3}-[A-Z0-9]{3})',  # "code: XXX-XXX"
                    r'code[:\s]+([A-Z0-9]{6})',      # "code: XXXXXX"
                ]
                
                for pattern in code_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        # Get the first match
                        code = matches[0].upper()
                        log_success(f"✅ Found verification code: {code}")
                        return code
                
                # If no code found, wait and retry
                log_info(f"⏳ No code found yet, waiting {EMAIL_CHECK_INTERVAL}s...")
                await asyncio.sleep(EMAIL_CHECK_INTERVAL)
                
        except httpx.HTTPStatusError as e:
            log_error(f"⚠️ HTTP error {e.response.status_code} (attempt {attempt})")
            await asyncio.sleep(EMAIL_CHECK_INTERVAL)
        except Exception as e:
            log_error(f"⚠️ Error checking email (attempt {attempt}): {str(e)}")
            await asyncio.sleep(EMAIL_CHECK_INTERVAL)
    
    log_error(f"❌ Failed to retrieve code after {max_retries} attempts")
    return None


# For testing purposes
if __name__ == "__main__":
    async def test():
        # Test email generation
        email = await generate_email()
        print(f"Generated email: {email}")
        
        # Test code checking (will fail without implementation)
        # code = await check_email_for_code(email)
        # print(f"Retrieved code: {code}")
    
    asyncio.run(test())
