#!/usr/bin/env python3
"""
Simple Promo Code Checker - Using only standard library
Checks each code slowly with 0.5s delay
"""

import json
import time
import urllib.request
import urllib.error
import os
from datetime import datetime

# API endpoint
API_URL = "https://chatgpt.com/backend-api/promotions/eligibility/"

# Your token
TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc1NTQ3MjU1NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7InVzZXJfaWQiOiJ1c2VyLVdhOGZqbXlTeEFON0p5aFNkSFEwUWFxcyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJsYWdhMjEzNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImlhdCI6MTc1NDYwODU1NSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIwZWY5NDc0Mi1mMjU0LTQxMWEtODQ1Yy1iYzdkNDVlNTQ4YjIiLCJuYmYiOjE3NTQ2MDg1NTUsInB3ZF9hdXRoX3RpbWUiOjE3NTQ2MDg1NTMwMTMsInNjcCI6WyJvcGVuaWQiLCJlbWFpbCIsInByb2ZpbGUiLCJvZmZsaW5lX2FjY2VzcyIsIm1vZGVsLnJlcXVlc3QiLCJtb2RlbC5yZWFkIiwib3JnYW5pemF0aW9uLnJlYWQiLCJvcmdhbml6YXRpb24ud3JpdGUiXSwic2Vzc2lvbl9pZCI6ImF1dGhzZXNzX0s3Z0V1bmhNOE1mbU83TGh1YVdiOGRYWiIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MTgwODE5MDAzMjg4MzcxODEwIn0.GrYZm_mrbmB9mQdOoTgtUNUJh3sKC9I9LBY7vVmwuqOYivuaSV-UjGBHbbP-CeeZg-v0XWPeVMaOxVoz_Kf64ahUIewsmWQW2h-J0kZQatqY4bgnrergURjdExwNWjhzArSKzbcW8DX6fQDE9s4XQ3c9XNLq8XlE6EJQmX5HrmJVYlm2bhDZ4WdrdRGIXivSbLJAWNOhHHnFAvrnnzp_LbqyLld7913BGloj4jA_ss4CeHTzJIKM6DklFv6wT0lvtCsCCkMcUeKAEcRCGuQN8K0pm3-jm_ADxQ0m_JQivLKLTi6eBvwCkN6adEEanGZSOQKpLSoRUf-qwI2lwIJSJEWb_F4Qv-9J6eEPFvlRGg3vvkV45EE2Gr86BVQ2LJ29eoLJlTlYXqG7Lfy5zz08Lc5V2DNwPj94trmIYjTi9K-3uOLpJxdbPSQxvjgmivCwzr-bWIi3F1Fc_MEbYy1QHgRmAo3ksPiYoEHbQHYxPOWRD7TcQfAwAo97i25RtPJ4TQ8xYc0LK4hMCIal6CsCdG6bc3eoYPuEGnT65FQwjuzd3zD6Kt0g2Is3P0hpBAE2yz-9UvusX6Za8pDH9DYme03KgR76XsZjxIYUG_dvEmMTQyh2iPMywmAff8kwNeFbK0wbUcmuuykSDpo02psB81EJEPrLAd5xP6qfaLG0aWw"

# Delay between checks (seconds)
DELAY = 0.5


def check_code(code):
    """Check a single promo code"""
    url = API_URL + code
    
    # Create request with headers
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://chatgpt.com')
    req.add_header('Referer', 'https://chatgpt.com/')
    
    try:
        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            result = json.loads(data)
            
            # Check if eligible
            is_eligible = result.get('is_eligible', False)
            return is_eligible, "Valid" if is_eligible else "Invalid"
            
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection Error: {e.reason}"
    except json.JSONDecodeError:
        return False, "Invalid response format"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    print("Simple Promo Code Checker")
    print("=" * 30)
    
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
