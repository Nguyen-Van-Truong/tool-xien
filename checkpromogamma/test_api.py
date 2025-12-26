#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json

def test_stripe_api():
    print("Testing Stripe API...")

    url = 'https://api.stripe.com/v1/promotion_codes/RZZKK46F'
    print(f"URL: {url}")

    req = urllib.request.Request(url)
    req.add_header('Authorization', 'Bearer pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://billing.gamma.app')
    req.add_header('Referer', 'https://billing.gamma.app/c/pay/cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i')

    try:
        print("Making request...")
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            print(f'Status: {status_code}')
            data = response.read().decode('utf-8')
            print(f'Response length: {len(data)} chars')
            print('Response:', data[:1000])
            return True
    except urllib.error.HTTPError as e:
        print(f'HTTP Error: {e.code}')
        print(f'Reason: {e.reason}')
        if hasattr(e, 'read'):
            error_data = e.read().decode('utf-8')
            print(f'Error response: {error_data}')
        return False
    except Exception as e:
        print(f'Error: {str(e)}')
        return False

if __name__ == "__main__":
    test_stripe_api()

