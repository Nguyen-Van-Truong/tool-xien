#!/usr/bin/env python3
"""
🎖️ VLM API Scraper V2 - All Veterans (Session Reset Mode)
Lấy tất cả veterans, với auto-retry mạnh mẽ cho server không ổn định
+ Session Reset: Tự động tạo session mới khi gặp nhiều lỗi (như xóa cookies/ẩn danh mới)
"""

import httpx
import json
import random
import argparse
from datetime import datetime
import string
import time
import os
import sys
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== CONFIG =====================
# Global shutdown flag - để dừng tất cả threads khi Ctrl+C
shutdown_event = threading.Event()
API_URL = "https://www.vlm.cem.va.gov/api/v1.1/gcio/profile/search/advanced"
MAX_RETRIES = 3  # Retry 3 times per request
RETRY_DELAY = 2  # Wait 2 seconds between retries
REQUEST_DELAY = 2  # Wait 2 seconds between requests
SESSION_RESET_THRESHOLD = 5  # Reset session after 5 consecutive server errors
SESSION_RESET_WAIT = 60  # Wait 60 seconds after session reset

# Service Branch mapping
BRANCH_MAP = {
    "AR": "Army",
    "NA": "Navy", 
    "AF": "Air Force",
    "MC": "Marine Corps",
    "CG": "Coast Guard"
}

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "aol.com"]

MONTH_MAP = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

# Lock for thread-safe file writing
file_lock = threading.Lock()

# Random User-Agents để tránh bị phát hiện
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def generate_email(first_name: str, last_name: str) -> str:
    """Generate random email"""
    num = random.randint(100, 999)
    domain = random.choice(EMAIL_DOMAINS)
    return f"{first_name.lower()}{last_name.lower()}{num}@{domain}"


def parse_date(date_str: str) -> tuple:
    """Parse YYYY-MM-DD to (Month, Day, Year)"""
    if not date_str:
        return ("January", "1", "2025")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return (MONTH_MAP[dt.month], str(dt.day), str(dt.year))
    except:
        return ("January", "1", "2025")


class SessionManager:
    """Quản lý HTTP session với khả năng reset (như xóa cookies)"""
    
    def __init__(self, letter: str):
        self.letter = letter.upper()
        self.client = None
        self.session_count = 0
        self.create_new_session()
    
    def create_new_session(self):
        """Tạo session mới (như mở tab ẩn danh mới)"""
        if self.client:
            try:
                self.client.close()
            except:
                pass
        
        self.session_count += 1
        self.client = httpx.Client(
            timeout=60.0,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": random.choice(USER_AGENTS),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )
        print(f"[{self.letter}] 🆕 Session #{self.session_count} created (fresh cookies)")
    
    def reset_session(self):
        """Reset session khi gặp nhiều lỗi (như xóa cookies và mở ẩn danh mới)"""
        print(f"[{self.letter}] 🔄 Resetting session... waiting {SESSION_RESET_WAIT}s")
        # Use interruptible sleep
        for _ in range(SESSION_RESET_WAIT * 10):
            if shutdown_event.is_set():
                break
            time.sleep(0.1)
        self.create_new_session()
    
    def fetch(self, params: dict) -> tuple:
        """Fetch với retry logic"""
        for attempt in range(MAX_RETRIES):
            # Check shutdown flag
            if shutdown_event.is_set():
                return (None, None)
                
            try:
                response = self.client.post(API_URL, json=params)
                status = response.status_code
                
                if status == 200:
                    data = response.json()
                    resp = data.get("response", {})
                    veterans = resp.get("data", [])
                    return (200, veterans)
                
                # Server error - retry
                if status in [502, 503, 504]:
                    if attempt < MAX_RETRIES - 1:
                        # Interruptible delay
                        for _ in range(int((RETRY_DELAY + attempt) * 10)):
                            if shutdown_event.is_set():
                                return (None, None)
                            time.sleep(0.1)
                        continue
                
                return (status, None)
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    for _ in range(RETRY_DELAY * 10):
                        if shutdown_event.is_set():
                            return (None, None)
                        time.sleep(0.1)
                    continue
                return (None, None)
        
        return (None, None)
    
    def close(self):
        """Close session"""
        if self.client:
            try:
                self.client.close()
            except:
                pass


def parse_veteran(vet: dict) -> dict:
    """Parse API response to veteran data"""
    
    branches = vet.get("profileServiceBranches", [])
    branch = "Army"
    
    if branches:
        branch_info = branches[0]
        branch_id = branch_info.get("serviceBranch", {}).get("serviceBranchId", "AR")
        branch = BRANCH_MAP.get(branch_id, "Army")
    
    dob = vet.get("date_of_birth", "1980-01-01")
    dod = vet.get("date_of_death", "2025-01-01")
    
    birth_month, birth_day, birth_year = parse_date(dob)
    
    if dod and dod.startswith("2025"):
        discharge_month, discharge_day, discharge_year = parse_date(dod)
    else:
        discharge_month, discharge_day, discharge_year = ("December", "1", "2025")
    
    first_name = vet.get("firstName", "JOHN")
    last_name = vet.get("lastName", "DOE")
    
    return {
        "firstName": first_name,
        "lastName": last_name,
        "branch": branch,
        "birthMonth": birth_month,
        "birthDay": birth_day,
        "birthYear": birth_year,
        "dischargeMonth": discharge_month,
        "dischargeDay": discharge_day,
        "dischargeYear": discharge_year,
        "email": generate_email(first_name, last_name)
    }


def format_veteran_line(vet: dict) -> str:
    """Format veteran to pipe-delimited line (6 fields: FirstName|LastName|Branch|BirthMonth|BirthDay|BirthYear)"""
    return "|".join([
        vet["firstName"],
        vet["lastName"],
        vet["branch"],
        vet["birthMonth"],
        vet["birthDay"],
        vet["birthYear"]
    ])


def save_veterans_threadsafe(veterans: list, output_file: str):
    """Thread-safe save veterans to file"""
    if not veterans:
        return
    
    lines = [format_veteran_line(v) for v in veterans]
    with file_lock:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def scrape_letter(letter: str, start_page: int, end_page: int, output_file: str, dob_from: str = None, dob_to: str = None) -> int:
    """
    Scrape pages for a letter from start_page to end_page
    Returns: total veterans scraped
    """
    
    session = SessionManager(letter)
    
    total_veterans = 0
    batch_veterans = []
    consecutive_empty = 0
    consecutive_errors = 0  # Track consecutive server errors
    
    for page in range(start_page, end_page + 1):
        # Check shutdown flag
        if shutdown_event.is_set():
            print(f"[{letter.upper()}] ⛔ Stopping due to shutdown signal...")
            break
            
        params = {
            "lastName": letter,
            "dobTo": "2025-12-31",
            "limit": 25,
            "orderby": "date_of_death",
            "page": page
        }
        
        if dob_from:
            params["dobFrom"] = dob_from
        
        if dob_to:
            params["dobTo"] = dob_to
        
        status, data = session.fetch(params)
        
        # Server error
        if status != 200:
            consecutive_errors += 1
            print(f"[{letter.upper()}] Page {page}: Error {status} ({consecutive_errors}/{SESSION_RESET_THRESHOLD})")
            
            # Reset session after too many consecutive errors
            if consecutive_errors >= SESSION_RESET_THRESHOLD:
                session.reset_session()
                consecutive_errors = 0
                # Retry current page with new session
                status, data = session.fetch(params)
                if status != 200:
                    print(f"[{letter.upper()}] Page {page}: Still error after reset, skipping")
                    continue
            else:
                continue
        
        consecutive_errors = 0  # Reset error counter on success
        
        # Empty data (status 200 but no veterans)
        if len(data) == 0:
            consecutive_empty += 1
            print(f"[{letter.upper()}] Page {page}: No data ({consecutive_empty}/5)")
            if consecutive_empty >= 5:
                print(f"[{letter.upper()}] ⚠️ 5 consecutive empty, stopping")
                break
            continue
        
        consecutive_empty = 0  # Reset on success
        
        for vet in data:
            parsed = parse_veteran(vet)
            batch_veterans.append(parsed)
        
        total_veterans += len(data)
        print(f"[{letter.upper()}] Page {page}: +{len(data)} veterans (total: {total_veterans})")
        
        # Save every 5 pages
        if page % 5 == 0:
            save_veterans_threadsafe(batch_veterans, output_file)
            print(f"[{letter.upper()}] 💾 Saved {len(batch_veterans)} veterans")
            batch_veterans = []
        
        # Use interruptible sleep
        for _ in range(REQUEST_DELAY * 10):
            if shutdown_event.is_set():
                break
            time.sleep(0.1)
    
    # Save remaining
    if batch_veterans:
        save_veterans_threadsafe(batch_veterans, output_file)
        print(f"[{letter.upper()}] 💾 Saved {len(batch_veterans)} veterans")
    
    session.close()
    return total_veterans


def scrape_letter_wrapper(args_tuple):
    """Wrapper for ThreadPoolExecutor"""
    letter, start_page, end_page, output_file, dob_from, dob_to = args_tuple
    count = scrape_letter(letter, start_page, end_page, output_file, dob_from, dob_to)
    print(f"   ✅ Letter {letter.upper()}: {count} veterans")
    return (letter, count)


def main():
    parser = argparse.ArgumentParser(description="VLM API Scraper V2 - Session Reset Mode")
    parser.add_argument("-l", "--letter", default=None, help="Specific letter (a-z), or leave empty for all")
    parser.add_argument("-s", "--start", type=int, default=1, help="Start page (default: 1)")
    parser.add_argument("-e", "--end", type=int, default=100, help="End page (default: 100)")
    parser.add_argument("-o", "--output", default="all_veterans.txt", help="Output file")
    parser.add_argument("--dob", default=None, help="Birth year from (e.g. 1963)")
    parser.add_argument("--dob-to", default=None, help="Birth year to (e.g. 1990)")
    parser.add_argument("-t", "--threads", type=int, default=1, help="Number of threads (default: 1)")
    parser.add_argument("--clear", action="store_true", help="Clear output file before starting")
    
    args = parser.parse_args()
    
    dob_from = f"{args.dob}-01-01" if args.dob else None
    dob_to = f"{args.dob_to}-12-31" if args.dob_to else None
    
    print("=" * 60)
    print("🎖️  VLM API SCRAPER V2 - SESSION RESET MODE")
    print("=" * 60)
    
    if args.letter:
        letters = [args.letter.lower()]
        print(f"Letter: {args.letter.upper()}")
    else:
        letters = list(string.ascii_lowercase)
        print(f"Letters: A-Z (all 26)")
    
    print(f"Page range: {args.start} → {args.end}")
    if dob_from:
        print(f"Birth year from: {args.dob}")
    if dob_to:
        print(f"Birth year to: {args.dob_to}")
    print(f"Threads: {args.threads}")
    print(f"Session reset: After {SESSION_RESET_THRESHOLD} errors, wait {SESSION_RESET_WAIT}s")
    print(f"Output: {args.output}")
    print("=" * 60)
    
    if args.clear and os.path.exists(args.output):
        os.remove(args.output)
        print(f"🗑️ Cleared {args.output}")
    
    tasks = [(letter, args.start, args.end, args.output, dob_from, dob_to) for letter in letters]
    
    grand_total = 0
    
    print(f"\n🚀 Starting {len(letters)} letters with {args.threads} thread(s)...\n")
    print("💡 Press Ctrl+C to stop gracefully\n")
    
    # Signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n\n⚠️ Ctrl+C detected! Signaling all threads to stop...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = {executor.submit(scrape_letter_wrapper, task): task[0] for task in tasks}
            
            for future in as_completed(futures):
                if shutdown_event.is_set():
                    # Cancel pending futures
                    for f in futures:
                        f.cancel()
                    break
                try:
                    letter, count = future.result(timeout=1)
                    grand_total += count
                except Exception:
                    pass
    except KeyboardInterrupt:
        print("\n\n⚠️ Force interrupted! Setting shutdown flag...")
        shutdown_event.set()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        shutdown_event.set()
    
    print(f"\n" + "=" * 60)
    print(f"✅ COMPLETE! Total veterans: {grand_total}")
    print(f"📁 Saved to: {args.output}")


if __name__ == "__main__":
    main()
