#!/usr/bin/env python3
"""
Smart Promo Code Hunter - Generate and check promo codes intelligently
Analyzes patterns and generates codes with highest probability of being valid
"""

import json
import time
import urllib.request
import urllib.error
import os
import random
import string
import threading
from datetime import datetime
from collections import Counter, defaultdict
import itertools

# API Configuration
API_URL = "https://chatgpt.com/backend-api/promotions/eligibility/"
TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc1NTQ3MjU1NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7InVzZXJfaWQiOiJ1c2VyLVdhOGZqbXlTeEFON0p5aFNkSFEwUWFxcyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJsYWdhMjEzNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImlhdCI6MTc1NDYwODU1NSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIwZWY5NDc0Mi1mMjU0LTQxMWEtODQ1Yy1iYzdkNDVlNTQ4YjIiLCJuYmYiOjE3NTQ2MDg1NTUsInB3ZF9hdXRoX3RpbWUiOjE3NTQ2MDg1NTMwMTMsInNjcCI6WyJvcGVuaWQiLCJlbWFpbCIsInByb2ZpbGUiLCJvZmZsaW5lX2FjY2VzcyIsIm1vZGVsLnJlcXVlc3QiLCJtb2RlbC5yZWFkIiwib3JnYW5pemF0aW9uLnJlYWQiLCJvcmdhbml6YXRpb24ud3JpdGUiXSwic2Vzc2lvbl9pZCI6ImF1dGhzZXNzX0s3Z0V1bmhNOE1mbU83TGh1YVdiOGRYWiIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MTgwODE5MDAzMjg4MzcxODEwIn0.GrYZm_mrbmB9mQdOoTgtUNUJh3sKC9I9LBY7vVmwuqOYivuaSV-UjGBHbbP-CeeZg-v0XWPeVMaOxVoz_Kf64ahUIewsmWQW2h-J0kZQatqY4bgnrergURjdExwNWjhzArSKzbcW8DX6fQDE9s4XQ3c9XNLq8XlE6EJQmX5HrmJVYlm2bhDZ4WdrdRGIXivSbLJAWNOhHHnFAvrnnzp_LbqyLld7913BGloj4jA_ss4CeHTzJIKM6DklFv6wT0lvtCsCCkMcUeKAEcRCGuQN8K0pm3-jm_ADxQ0m_JQivLKLTi6eBvwCkN6adEEanGZSOQKpLSoRUf-qwI2lwIJSJEWb_F4Qv-9J6eEPFvlRGg3vvkV45EE2Gr86BVQ2LJ29eoLJlTlYXqG7Lfy5zz08Lc5V2DNwPj94trmIYjTi9K-3uOLpJxdbPSQxvjgmivCwzr-bWIi3F1Fc_MEbYy1QHgRmAo3ksPiYoEHbQHYxPOWRD7TcQfAwAo97i25RtPJ4TQ8xYc0LK4hMCIal6CsCdG6bc3eoYPuEGnT65FQwjuzd3zD6Kt0g2Is3P0hpBAE2yz-9UvusX6Za8pDH9DYme03KgR76XsZjxIYUG_dvEmMTQyh2iPMywmAff8kwNeFbK0wbUcmuuykSDpo02psB81EJEPrLAd5xP6qfaLG0aWw"

# Generation parameters
CODE_LENGTH = 16
CHARSET = string.ascii_uppercase + string.digits  # A-Z, 0-9
DELAY_BETWEEN_CHECKS = 0.3  # seconds
MAX_ATTEMPTS_PER_SESSION = 1000

# Statistics
stats = {
    'total_generated': 0,
    'total_checked': 0,
    'valid_found': 0,
    'error_count': 0,
    'start_time': None,
    'patterns_analyzed': {}
}

valid_codes = []
checked_codes = set()


class PatternAnalyzer:
    """Analyze patterns in known codes to improve generation"""
    
    def __init__(self):
        self.known_codes = []
        self.char_frequencies = defaultdict(int)
        self.position_frequencies = defaultdict(lambda: defaultdict(int))
        self.bigram_frequencies = defaultdict(int)
        
    def add_known_code(self, code):
        """Add a known code for pattern analysis"""
        self.known_codes.append(code)
        
        # Analyze character frequencies
        for char in code:
            self.char_frequencies[char] += 1
            
        # Analyze position-specific frequencies
        for i, char in enumerate(code):
            self.position_frequencies[i][char] += 1
            
        # Analyze bigram frequencies
        for i in range(len(code) - 1):
            bigram = code[i:i+2]
            self.bigram_frequencies[bigram] += 1
    
    def get_weighted_char_for_position(self, position):
        """Get character with highest probability for given position"""
        pos_freq = self.position_frequencies[position]
        if not pos_freq:
            return random.choice(CHARSET)
        
        # Weight by frequency but still allow randomness
        chars = list(pos_freq.keys())
        weights = list(pos_freq.values())
        
        # Add some randomness - mix known patterns with random
        if random.random() < 0.7:  # 70% chance to use pattern
            return random.choices(chars, weights=weights)[0]
        else:  # 30% chance for pure randomness
            return random.choice(CHARSET)
    
    def generate_pattern_based_code(self):
        """Generate code based on analyzed patterns"""
        code = ""
        for i in range(CODE_LENGTH):
            code += self.get_weighted_char_for_position(i)
        return code


def load_known_codes():
    """Load known codes from various sources"""
    analyzer = PatternAnalyzer()
    
    # Load from promocode.txt
    if os.path.exists('promocode.txt'):
        with open('promocode.txt', 'r') as f:
            for line in f:
                code = line.strip()
                if code and len(code) == CODE_LENGTH:
                    analyzer.add_known_code(code)
    
    # Load from valid_codes.txt
    if os.path.exists('valid_codes.txt'):
        with open('valid_codes.txt', 'r') as f:
            for line in f:
                code = line.strip()
                if code and len(code) == CODE_LENGTH:
                    analyzer.add_known_code(code)
    
    # Add some hypothetical patterns based on common promo code formats
    common_patterns = [
        "PROMO2024WINTER",
        "SAVE50PERCENT1",
        "DISCOUNT2024A",
        "NEWUSER202401"
    ]
    
    for pattern in common_patterns:
        if len(pattern) == CODE_LENGTH:
            analyzer.add_known_code(pattern)
    
    return analyzer


def check_code(code):
    """Check if a promo code is valid"""
    url = API_URL + code
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
    req.add_header('Origin', 'https://chatgpt.com')
    req.add_header('Referer', 'https://chatgpt.com/')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            result = json.loads(data)
            return result.get('is_eligible', False)
            
    except Exception as e:
        stats['error_count'] += 1
        return False


def generate_random_code():
    """Generate purely random code"""
    return ''.join(random.choices(CHARSET, k=CODE_LENGTH))


def generate_smart_variations(base_code):
    """Generate smart variations of a base code"""
    variations = []
    
    # Character substitution (similar looking chars)
    substitutions = {
        '0': ['O', 'Q'],
        'O': ['0', 'Q'],
        'I': ['1', 'L'],
        '1': ['I', 'L'],
        'S': ['5'],
        '5': ['S'],
        'B': ['8'],
        '8': ['B']
    }
    
    # Generate variations by substituting similar characters
    for i, char in enumerate(base_code):
        if char in substitutions:
            for sub_char in substitutions[char]:
                variation = base_code[:i] + sub_char + base_code[i+1:]
                variations.append(variation)
    
    # Generate variations by changing 1-2 characters
    for _ in range(5):
        variation = list(base_code)
        # Change 1-2 random positions
        positions = random.sample(range(CODE_LENGTH), random.randint(1, 2))
        for pos in positions:
            variation[pos] = random.choice(CHARSET)
        variations.append(''.join(variation))
    
    return variations


def save_progress():
    """Save current progress and statistics"""
    progress_data = {
        'timestamp': datetime.now().isoformat(),
        'stats': stats,
        'valid_codes': valid_codes,
        'checked_count': len(checked_codes)
    }
    
    with open('hunter_progress.json', 'w') as f:
        json.dump(progress_data, f, indent=2)
    
    # Update valid_codes.txt
    with open('valid_codes.txt', 'w') as f:
        for code in valid_codes:
            f.write(code + '\n')


def print_stats():
    """Print current statistics"""
    elapsed = time.time() - stats['start_time'] if stats['start_time'] else 0
    rate = stats['total_checked'] / elapsed if elapsed > 0 else 0
    
    print(f"\n{'='*50}")
    print(f"HUNTING STATISTICS")
    print(f"{'='*50}")
    print(f"Time elapsed: {elapsed:.1f}s")
    print(f"Total generated: {stats['total_generated']}")
    print(f"Total checked: {stats['total_checked']}")
    print(f"Valid found: {stats['valid_found']}")
    print(f"Error count: {stats['error_count']}")
    print(f"Check rate: {rate:.2f} codes/sec")
    print(f"Success rate: {(stats['valid_found']/stats['total_checked']*100):.4f}%" if stats['total_checked'] > 0 else "N/A")
    print(f"Valid codes: {valid_codes}")
    print(f"{'='*50}")


def main():
    """Main hunting function"""
    print("🎯 SMART PROMO CODE HUNTER")
    print("=" * 50)
    
    stats['start_time'] = time.time()
    
    # Load and analyze known patterns
    print("📊 Loading known codes and analyzing patterns...")
    analyzer = load_known_codes()
    print(f"Analyzed {len(analyzer.known_codes)} known codes")
    
    # Load previous progress if exists
    if os.path.exists('hunter_progress.json'):
        try:
            with open('hunter_progress.json', 'r') as f:
                prev_data = json.load(f)
                valid_codes.extend(prev_data.get('valid_codes', []))
                print(f"Loaded {len(valid_codes)} previously found valid codes")
        except:
            pass
    
    print(f"\n🎲 Starting hunt for valid promo codes...")
    print(f"Target: {MAX_ATTEMPTS_PER_SESSION} attempts this session")
    print(f"Delay: {DELAY_BETWEEN_CHECKS}s between checks\n")
    
    try:
        for attempt in range(MAX_ATTEMPTS_PER_SESSION):
            # Choose generation strategy
            if random.random() < 0.4:  # 40% pattern-based
                code = analyzer.generate_pattern_based_code()
                strategy = "pattern"
            elif random.random() < 0.3 and valid_codes:  # 30% variation of valid
                base_code = random.choice(valid_codes)
                variations = generate_smart_variations(base_code)
                code = random.choice(variations) if variations else generate_random_code()
                strategy = "variation"
            else:  # 30% pure random
                code = generate_random_code()
                strategy = "random"
            
            # Skip if already checked
            if code in checked_codes:
                continue
                
            checked_codes.add(code)
            stats['total_generated'] += 1
            stats['total_checked'] += 1
            
            # Check the code
            print(f"[{attempt+1}/{MAX_ATTEMPTS_PER_SESSION}] ({strategy}) {code}...", end=" ", flush=True)
            
            is_valid = check_code(code)
            
            if is_valid:
                print("🎉 VALID!")
                valid_codes.append(code)
                stats['valid_found'] += 1
                
                # Analyze new valid code
                analyzer.add_known_code(code)
                
                # Save immediately when found
                save_progress()
                
            else:
                print("❌")
            
            # Print stats every 50 attempts
            if (attempt + 1) % 50 == 0:
                print_stats()
                save_progress()
            
            # Delay between requests
            time.sleep(DELAY_BETWEEN_CHECKS)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Hunt interrupted by user")
    
    # Final statistics and save
    print_stats()
    save_progress()
    
    print(f"\n💾 Progress saved to: hunter_progress.json")
    print(f"📝 Valid codes saved to: valid_codes.txt")
    
    if valid_codes:
        print(f"\n🎊 HUNT SUCCESSFUL! Found {len(valid_codes)} valid codes:")
        for i, code in enumerate(valid_codes, 1):
            print(f"  {i}. {code}")
    else:
        print(f"\n😔 No valid codes found this session. Keep hunting!")


if __name__ == "__main__":
    main()
