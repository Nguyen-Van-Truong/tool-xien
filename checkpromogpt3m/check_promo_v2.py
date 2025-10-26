#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Promo Code Checker v2 - Improved version with better error handling
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Try to use requests if available, otherwise fallback to urllib
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.parse
    import urllib.error
    USE_REQUESTS = False
    print("Note: 'requests' library not found. Using urllib instead.")
    print("For better performance, install: pip install requests\n")

# Configuration
API_BASE_URL = "https://chatgpt.com/backend-api/promotions/eligibility/"
DEFAULT_CODES_FILE = "promocode.txt"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# Default token provided by user
DEFAULT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc1NTQ3MjU1NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7InVzZXJfaWQiOiJ1c2VyLVdhOGZqbXlTeEFON0p5aFNkSFEwUWFxcyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJsYWdhMjEzNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImlhdCI6MTc1NDYwODU1NSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIwZWY5NDc0Mi1mMjU0LTQxMWEtODQ1Yy1iYzdkNDVlNTQ4YjIiLCJuYmYiOjE3NTQ2MDg1NTUsInB3ZF9hdXRoX3RpbWUiOjE3NTQ2MDg1NTMwMTMsInNjcCI6WyJvcGVuaWQiLCJlbWFpbCIsInByb2ZpbGUiLCJvZmZsaW5lX2FjY2VzcyIsIm1vZGVsLnJlcXVlc3QiLCJtb2RlbC5yZWFkIiwib3JnYW5pemF0aW9uLnJlYWQiLCJvcmdhbml6YXRpb24ud3JpdGUiXSwic2Vzc2lvbl9pZCI6ImF1dGhzZXNzX0s3Z0V1bmhNOE1mbU83TGh1YVdiOGRYWiIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MTgwODE5MDAzMjg4MzcxODEwIn0.GrYZm_mrbmB9mQdOoTgtUNUJh3sKC9I9LBY7vVmwuqOYivuaSV-UjGBHbbP-CeeZg-v0XWPeVMaOxVoz_Kf64ahUIewsmWQW2h-J0kZQatqY4bgnrergURjdExwNWjhzArSKzbcW8DX6fQDE9s4XQ3c9XNLq8XlE6EJQmX5HrmJVYlm2bhDZ4WdrdRGIXivSbLJAWNOhHHnFAvrnnzp_LbqyLld7913BGloj4jA_ss4CeHTzJIKM6DklFv6wT0lvtCsCCkMcUeKAEcRCGuQN8K0pm3-jm_ADxQ0m_JQivLKLTi6eBvwCkN6adEEanGZSOQKpLSoRUf-qwI2lwIJSJEWb_F4Qv-9J6eEPFvlRGg3vvkV45EE2Gr86BVQ2LJ29eoLJlTlYXqG7Lfy5zz08Lc5V2DNwPj94trmIYjTi9K-3uOLpJxdbPSQxvjgmivCwzr-bWIi3F1Fc_MEbYy1QHgRmAo3ksPiYoEHbQHYxPOWRD7TcQfAwAo97i25RtPJ4TQ8xYc0LK4hMCIal6CsCdG6bc3eoYPuEGnT65FQwjuzd3zD6Kt0g2Is3P0hpBAE2yz-9UvusX6Za8pDH9DYme03KgR76XsZjxIYUG_dvEmMTQyh2iPMywmAff8kwNeFbK0wbUcmuuykSDpo02psB81EJEPrLAd5xP6qfaLG0aWw"


def get_headers(token: str, cookie: Optional[str] = None) -> Dict[str, str]:
    """Build request headers"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://chatgpt.com",
        "Referer": "https://chatgpt.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    
    if cookie:
        headers["Cookie"] = cookie
    
    return headers


def check_promo_requests(code: str, headers: Dict[str, str]) -> Tuple[bool, str, int]:
    """Check promo code using requests library"""
    url = f"{API_BASE_URL}{code}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                is_eligible = data.get("is_eligible", False)
                reason = data.get("ineligible_reason", {})
                if isinstance(reason, dict):
                    reason = reason.get("message", "No reason provided")
                return is_eligible, reason or "Valid", response.status_code
            except json.JSONDecodeError:
                # Save HTML response for debugging
                with open(f"debug_response_{code}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                return False, "Invalid JSON response (saved to debug file)", response.status_code
        
        elif response.status_code == 403:
            return False, "Access denied - may need valid cookies", response.status_code
        
        elif response.status_code == 401:
            return False, "Unauthorized - token may be expired", response.status_code
        
        else:
            return False, f"HTTP {response.status_code}", response.status_code
            
    except requests.exceptions.Timeout:
        return False, "Request timeout", 0
    except requests.exceptions.ConnectionError:
        return False, "Connection error", 0
    except Exception as e:
        return False, f"Error: {str(e)}", 0


def check_promo_urllib(code: str, headers: Dict[str, str]) -> Tuple[bool, str, int]:
    """Check promo code using urllib"""
    url = f"{API_BASE_URL}{urllib.parse.quote(code)}"
    
    request = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read().decode('utf-8')
            status_code = response.getcode()
            
            try:
                json_data = json.loads(data)
                is_eligible = json_data.get("is_eligible", False)
                reason = json_data.get("ineligible_reason", {})
                if isinstance(reason, dict):
                    reason = reason.get("message", "No reason provided")
                return is_eligible, reason or "Valid", status_code
            except json.JSONDecodeError:
                # Save HTML response for debugging
                with open(f"debug_response_{code}.html", "w", encoding="utf-8") as f:
                    f.write(data)
                return False, "Invalid JSON response (saved to debug file)", status_code
                
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return False, "Access denied - may need valid cookies", e.code
        elif e.code == 401:
            return False, "Unauthorized - token may be expired", e.code
        else:
            return False, f"HTTP {e.code}", e.code
            
    except urllib.error.URLError as e:
        return False, f"URL Error: {str(e.reason)}", 0
    except Exception as e:
        return False, f"Error: {str(e)}", 0


def read_codes(filename: str) -> List[str]:
    """Read promo codes from file"""
    codes = []
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        return codes
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            code = line.strip()
            if code and not code.startswith('#'):
                codes.append(code)
    
    return codes


def save_results(valid_codes: List[str], all_results: List[Dict]) -> None:
    """Save results to files"""
    # Save valid codes
    with open("valid_codes.txt", "w", encoding="utf-8") as f:
        for code in valid_codes:
            f.write(f"{code}\n")
    
    # Save detailed results as JSON
    with open("check_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_checked": len(all_results),
            "valid_count": len(valid_codes),
            "results": all_results
        }, f, indent=2)


def main():
    """Main function"""
    print("=== Promo Code Checker v2 ===\n")
    
    # Get token from environment or use default
    token = os.environ.get("PROMO_TOKEN", DEFAULT_TOKEN)
    
    # Get cookie from environment if available
    cookie = os.environ.get("PROMO_COOKIE", "")
    
    # Read codes
    codes = read_codes(DEFAULT_CODES_FILE)
    if not codes:
        print("No codes to check!")
        return 1
    
    print(f"Found {len(codes)} codes to check")
    print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS}s\n")
    
    # Prepare headers
    headers = get_headers(token, cookie)
    
    # Check function based on available library
    check_function = check_promo_requests if USE_REQUESTS else check_promo_urllib
    
    # Results storage
    valid_codes = []
    all_results = []
    
    # Check each code
    for i, code in enumerate(codes, 1):
        print(f"[{i}/{len(codes)}] Checking {code}...", end=" ", flush=True)
        
        # Check the code
        is_eligible, reason, status_code = check_function(code, headers)
        
        # Store result
        result = {
            "code": code,
            "is_eligible": is_eligible,
            "reason": reason,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        all_results.append(result)
        
        # Print result
        if is_eligible:
            print(f"✓ VALID")
            valid_codes.append(code)
        else:
            print(f"✗ INVALID - {reason}")
        
        # Delay between requests (except for last one)
        if i < len(codes):
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Save results
    print(f"\n=== Summary ===")
    print(f"Total checked: {len(codes)}")
    print(f"Valid codes: {len(valid_codes)}")
    print(f"Invalid codes: {len(codes) - len(valid_codes)}")
    
    save_results(valid_codes, all_results)
    
    print(f"\nResults saved:")
    print(f"- valid_codes.txt (valid codes only)")
    print(f"- check_results.json (detailed results)")
    
    if any(r["reason"].startswith("Access denied") for r in all_results):
        print("\n⚠️  Note: Some requests were blocked. Try setting PROMO_COOKIE environment variable")
        print("   with your chatgpt.com cookies.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
