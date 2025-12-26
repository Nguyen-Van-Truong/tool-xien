#!/usr/bin/env python3
"""
Simple Promo Code Checker for Gamma/Stripe - Using only standard library
Checks each code slowly with 0.5s delay
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse
import os
from datetime import datetime

# Configuration
CHECKOUT_SESSION_ID = "cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i"
STRIPE_PUBLISHABLE_KEY = "pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc"

# Try different possible Stripe API endpoints
API_URL_BASE = "https://api.stripe.com/v1/promotion_codes/"
# Alternative: Checkout session with promo code
CHECKOUT_API_URL = f"https://api.stripe.com/v1/checkout/sessions/{CHECKOUT_SESSION_ID}"

# Delay between checks (seconds)
DELAY = 0.5


def check_code(code):
    """Check a single promo code using multiple approaches"""
    # Try promotion codes API first
    url = API_URL_BASE + urllib.parse.quote(code)
    
    # Create request with headers
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {STRIPE_PUBLISHABLE_KEY}')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://billing.gamma.app')
    req.add_header('Referer', f'https://billing.gamma.app/c/pay/{CHECKOUT_SESSION_ID}')
    
    try:
        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            result = json.loads(data)

            # Check if valid promotion code
            # Stripe returns object with 'id' and 'active' for valid codes
            if 'id' in result and result.get('active', False):
                return True, "Valid"
            else:
                return False, "Invalid"
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, f"Code not found (404)"
        elif e.code == 401:
            return False, f"Unauthorized (401) - API key may be invalid"
        elif e.code == 403:
            return False, f"Forbidden (403) - Access denied"
        else:
            return False, f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        # Try alternative approach - checkout session validation
        return check_code_alternative(code)
    except urllib.error.URLError as e:
        return False, f"Connection Error: {e.reason}"
    except json.JSONDecodeError:
        return False, "Invalid response format"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_code_alternative(code):
    """Alternative approach - try checkout session API"""
    url = f"{CHECKOUT_API_URL}?expand[]=line_items"

    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {STRIPE_PUBLISHABLE_KEY}')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://billing.gamma.app')
    req.add_header('Referer', f'https://billing.gamma.app/c/pay/{CHECKOUT_SESSION_ID}')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            result = json.loads(data)
            # This is just to test if API works - actual promo validation would be different
            return False, "Alternative API - need more research"
    except Exception as e:
        return False, f"Alternative API failed: {str(e)}"


def main():
    print("Simple Gamma Promo Code Checker")
    print("=" * 40)
    
    # Read codes from file
    try:
        with open('promocode.txt', 'r') as f:
            codes = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: promocode.txt not found!")
        return
    
    print(f"Found {len(codes)} codes to check")
    print(f"Checking with {DELAY}s delay between requests\n")
    
    valid_codes = []
    
    # Check each code
    for i, code in enumerate(codes, 1):
        print(f"[{i}/{len(codes)}] Checking {code}... ", end='', flush=True)
        
        is_valid, message = check_code(code)
        
        if is_valid:
            print("✓ VALID")
            valid_codes.append(code)
        else:
            print(f"✗ {message}")
        
        # Wait before next request
        if i < len(codes):
            time.sleep(DELAY)
    
    # Save valid codes
    with open('valid_codes.txt', 'w') as f:
        for code in valid_codes:
            f.write(code + '\n')
    
    # Summary
    print(f"\nDone! Found {len(valid_codes)} valid codes")
    print(f"Valid codes saved to: valid_codes.txt")


if __name__ == "__main__":
    main()

