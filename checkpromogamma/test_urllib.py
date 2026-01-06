#!/usr/bin/env python3
import urllib.request
import json

print("Testing Gamma Promo Code API with urllib...")

code = "RZZKK46F"
url = f"https://api.stripe.com/v1/promotion_codes/{code}"

print(f"Testing code: {code}")
print(f"URL: {url}")

try:
    req = urllib.request.Request(url)
    req.add_header('Authorization', 'Bearer pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://billing.gamma.app')
    req.add_header('Referer', 'https://billing.gamma.app/c/pay/cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i')

    print("\nMaking request...")
    with urllib.request.urlopen(req, timeout=10) as response:
        status_code = response.getcode()
        data = response.read().decode('utf-8')
        
        print(f"\n✅ Status: {status_code}")
        print(f"Response:\n{data}")
        
        # Parse JSON
        result = json.loads(data)
        print(f"\nParsed JSON:")
        print(f"  id: {result.get('id')}")
        print(f"  active: {result.get('active')}")
        print(f"  code: {result.get('code')}")
        
except urllib.error.HTTPError as e:
    print(f"\n❌ HTTP Error: {e.code}")
    error_data = e.read().decode('utf-8')
    print(f"Error Response:\n{error_data}")
    
    try:
        error_json = json.loads(error_data)
        print(f"\nError Message: {error_json}")
    except:
        pass
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")

print("\nTest completed.")



