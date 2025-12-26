#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Promo Code Checker v2 for Gamma/Stripe - Improved version with better error handling
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
CHECKOUT_SESSION_ID = "cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i"
STRIPE_PUBLISHABLE_KEY = "pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc"

API_BASE_URL = "https://api.stripe.com/v1/promotion_codes/"
DEFAULT_CODES_FILE = "promocode.txt"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds


def get_headers(cookie: Optional[str] = None) -> Dict[str, str]:
    """Build request headers for Stripe API"""
    headers = {
        "Authorization": f"Bearer {STRIPE_PUBLISHABLE_KEY}",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://billing.gamma.app",
        "Referer": f"https://billing.gamma.app/c/pay/{CHECKOUT_SESSION_ID}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
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
                # Stripe promotion code response
                if 'id' in data and data.get('active', False):
                    return True, "Valid", response.status_code
                else:
                    return False, "Inactive or invalid", response.status_code
            except json.JSONDecodeError:
                # Save HTML response for debugging
                with open(f"debug_response_{code}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                return False, "Invalid JSON response (saved to debug file)", response.status_code
        
        elif response.status_code == 404:
            return False, "Promo code not found", response.status_code
        
        elif response.status_code == 403:
            return False, "Access denied - may need valid authentication", response.status_code
        
        elif response.status_code == 401:
            return False, "Unauthorized - API key may be invalid", response.status_code
        
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
                # Stripe promotion code response
                if 'id' in json_data and json_data.get('active', False):
                    return True, "Valid", status_code
                else:
                    return False, "Inactive or invalid", status_code
            except json.JSONDecodeError:
                # Save HTML response for debugging
                with open(f"debug_response_{code}.html", "w", encoding="utf-8") as f:
                    f.write(data)
                return False, "Invalid JSON response (saved to debug file)", status_code
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "Promo code not found", e.code
        elif e.code == 403:
            return False, "Access denied - may need valid authentication", e.code
        elif e.code == 401:
            return False, "Unauthorized - API key may be invalid", e.code
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
    print("=== Gamma Promo Code Checker v2 ===\n")
    
    # Get cookie from environment if available
    cookie = os.environ.get("GAMMA_COOKIE", "")
    
    # Read codes
    codes = read_codes(DEFAULT_CODES_FILE)
    if not codes:
        print("No codes to check!")
        return 1
    
    print(f"Found {len(codes)} codes to check")
    print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS}s\n")
    
    # Prepare headers
    headers = get_headers(cookie)
    
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
    
    if any(r["reason"].startswith("Access denied") or r["reason"].startswith("Unauthorized") for r in all_results):
        print("\n⚠️  Note: Some requests were blocked. Stripe API may require authentication.")
        print("   The publishable key may not be sufficient for promo code validation.")
        print("   Consider using checkout session validation instead.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


