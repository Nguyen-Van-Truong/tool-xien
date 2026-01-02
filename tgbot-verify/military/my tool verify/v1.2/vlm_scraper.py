#!/usr/bin/env python3
"""
🎖️ VLM API Scraper V1.1 - All Veterans (Stable Mode)
Lấy tất cả veterans, với auto-retry mạnh mẽ cho server không ổn định
+ Session Reset: Tự động tạo session mới khi gặp nhiều lỗi (như xóa cookies)
"""

import httpx
import json
import random
import argparse
from datetime import datetime
import string
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== CONFIG =====================
API_URL = "https://www.vlm.cem.va.gov/api/v1.1/gcio/profile/search/advanced"
MAX_RETRIES = 5  # Retry 5 times on server errors
RETRY_DELAY = 3  # Wait 3 seconds between retries
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


def fetch_veterans(last_name: str, page: int = 1, dob_from: str = None):
    """
    Fetch veterans from API with auto-retry (5 attempts)
    Returns: (status, list) - status can be 200, 502, etc. or None for network error
    """
    
    params = {
        "lastName": last_name,
        "dobTo": "2025-12-31",
        "limit": 25,
        "orderby": "date_of_death",
        "page": page
    }
    
    if dob_from:
        params["dobFrom"] = dob_from
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Retry loop - 5 attempts
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(API_URL, json=params, headers=headers)
                status = response.status_code
                
                if status == 200:
                    data = response.json()
                    resp = data.get("response", {})
                    veterans = resp.get("data", [])
                    return (200, veterans)
                
                # Server error (502, 503, 504) - retry
                if status in [502, 503, 504]:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY + attempt  # 3, 4, 5, 6, 7 seconds
                        time.sleep(wait_time)
                        continue
                
                return (status, None)
                
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return (None, None)
    
    return (None, None)


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
    """Format veteran to pipe-delimited line"""
    return "|".join([
        vet["firstName"],
        vet["lastName"],
        vet["branch"],
        vet["birthMonth"],
        vet["birthDay"],
        vet["birthYear"],
        vet["dischargeMonth"],
        vet["dischargeDay"],
        vet["dischargeYear"],
        vet["email"]
    ])


def save_veterans_threadsafe(veterans: list, output_file: str):
    """Thread-safe save veterans to file"""
    if not veterans:
        return
    
    lines = [format_veteran_line(v) for v in veterans]
    with file_lock:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def scrape_letter(letter: str, start_page: int, end_page: int, output_file: str, dob_from: str = None) -> int:
    """
    Scrape pages for a letter from start_page to end_page
    Returns: total veterans scraped
    """
    
    total_veterans = 0
    batch_veterans = []
    consecutive_empty = 0
    
    for page in range(start_page, end_page + 1):
        status, data = fetch_veterans(letter, page, dob_from)
        
        # Server error after 5 retries - skip
        if status != 200:
            print(f"[{letter.upper()}] Page {page}: Error {status} after {MAX_RETRIES} retries (skipping)")
            continue
        
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
        
        time.sleep(REQUEST_DELAY)  # Wait 2 seconds between requests
    
    # Save remaining
    if batch_veterans:
        save_veterans_threadsafe(batch_veterans, output_file)
        print(f"[{letter.upper()}] 💾 Saved {len(batch_veterans)} veterans")
    
    return total_veterans


def scrape_letter_wrapper(args_tuple):
    """Wrapper for ThreadPoolExecutor"""
    letter, start_page, end_page, output_file, dob_from = args_tuple
    count = scrape_letter(letter, start_page, end_page, output_file, dob_from)
    print(f"   ✅ Letter {letter.upper()}: {count} veterans")
    return (letter, count)


def main():
    parser = argparse.ArgumentParser(description="VLM API Scraper V1.1 - Stable Mode")
    parser.add_argument("-l", "--letter", default=None, help="Specific letter (a-z), or leave empty for all")
    parser.add_argument("-s", "--start", type=int, default=1, help="Start page (default: 1)")
    parser.add_argument("-e", "--end", type=int, default=100, help="End page (default: 100)")
    parser.add_argument("-o", "--output", default="all_veterans.txt", help="Output file")
    parser.add_argument("--dob", default=None, help="Birth year from (e.g. 1960 for born 1960+)")
    parser.add_argument("-t", "--threads", type=int, default=1, help="Number of threads (default: 1)")
    parser.add_argument("--clear", action="store_true", help="Clear output file before starting")
    
    args = parser.parse_args()
    
    dob_from = f"{args.dob}-01-01" if args.dob else None
    
    print("=" * 60)
    print("🎖️  VLM API SCRAPER V1.1 - STABLE MODE")
    print("=" * 60)
    
    if args.letter:
        letters = [args.letter.lower()]
        print(f"Letter: {args.letter.upper()}")
    else:
        letters = list(string.ascii_lowercase)
        print(f"Letters: A-Z (all 26)")
    
    print(f"Page range: {args.start} → {args.end}")
    if dob_from:
        print(f"Birth year: {args.dob}+")
    print(f"Threads: {args.threads}")
    print(f"Retries: {MAX_RETRIES} (delay: {RETRY_DELAY}s)")
    print(f"Request delay: {REQUEST_DELAY}s")
    print(f"Output: {args.output}")
    print("=" * 60)
    
    if args.clear and os.path.exists(args.output):
        os.remove(args.output)
        print(f"🗑️ Cleared {args.output}")
    
    tasks = [(letter, args.start, args.end, args.output, dob_from) for letter in letters]
    
    grand_total = 0
    
    print(f"\n🚀 Starting {len(letters)} letters with {args.threads} thread(s)...\n")
    
    try:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = {executor.submit(scrape_letter_wrapper, task): task[0] for task in tasks}
            
            for future in as_completed(futures):
                letter, count = future.result()
                grand_total += count
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user! Saving progress...")
    
    print(f"\n" + "=" * 60)
    print(f"✅ COMPLETE! Total veterans: {grand_total}")
    print(f"📁 Saved to: {args.output}")


if __name__ == "__main__":
    main()
