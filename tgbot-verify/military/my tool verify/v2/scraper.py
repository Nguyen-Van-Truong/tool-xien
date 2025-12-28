#!/usr/bin/env python3
"""
🎖️ VLM API Scraper V2 - Optimized for Young Veterans (1970+)
Lấy veterans sinh từ 1970 trở đi - có thông tin phục vụ đầy đủ hơn
"""

import httpx
import json
import random
import argparse
from datetime import datetime
import string

# ===================== CONFIG =====================
API_URL = "https://www.vlm.cem.va.gov/api/v1.1/gcio/profile/search/advanced"

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


def fetch_veterans(last_name: str, page: int = 1, dob_from: str = "1970-01-01") -> list:
    """Fetch veterans from API with young veteran filter"""
    
    params = {
        "lastName": last_name,
        "dobFrom": dob_from,
        "dobTo": "2025-12-25",
        # Remove date of death filter to get more veterans
        "limit": 25,
        "orderby": "date_of_death",
        "page": page
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(API_URL, json=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", {}).get("data", [])
    except Exception as e:
        print(f"   Error: {e}")
    
    return []


def parse_veteran(vet: dict) -> dict:
    """Parse API response to veteran data"""
    
    # Get service branch
    branches = vet.get("profileServiceBranches", [])
    branch = "Army"  # default
    end_date = None
    
    if branches:
        branch_info = branches[0]
        branch_id = branch_info.get("serviceBranch", {}).get("serviceBranchId", "AR")
        branch = BRANCH_MAP.get(branch_id, "Army")
        end_date = branch_info.get("endDate")
    
    # Parse dates
    dob = vet.get("date_of_birth", "1980-01-01")
    dod = vet.get("date_of_death", "2025-01-01")
    
    birth_month, birth_day, birth_year = parse_date(dob)
    
    # Discharge date logic:
    # - If died in 2025: use actual death date
    # - If not died in 2025: use December 1, 2025
    if dod and dod.startswith("2025"):
        # Died in 2025 - use actual death date
        discharge_month, discharge_day, discharge_year = parse_date(dod)
    else:
        # Not died in 2025 - use December 1, 2025
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


def scrape_all(last_names: list, start_page: int = 3, pages_per_name: int = 5, dob_from: str = "1970-01-01") -> list:
    """Scrape all veterans starting from start_page"""
    
    all_veterans = []
    
    for name in last_names:
        print(f"\n📥 Fetching lastName={name} (born after {dob_from})...")
        
        end_page = start_page + pages_per_name
        for page in range(start_page, end_page):
            print(f"   Page {page}...", end=" ")
            
            raw_data = fetch_veterans(name, page, dob_from)
            
            if not raw_data:
                print("No data")
                break
            
            for vet in raw_data:
                parsed = parse_veteran(vet)
                all_veterans.append(parsed)
            
            print(f"Got {len(raw_data)} veterans")
    
    return all_veterans


def main():
    parser = argparse.ArgumentParser(description="VLM API Scraper V2 - Young Veterans")
    parser.add_argument("-n", "--name", default="k", help="Last name letter to search")
    parser.add_argument("-s", "--start", type=int, default=3, help="Start page (default: 3)")
    parser.add_argument("-p", "--pages", type=int, default=5, help="Pages to fetch per letter")
    parser.add_argument("-o", "--output", default="v2/veterans.txt", help="Output file")
    parser.add_argument("--all", action="store_true", help="Scrape all letters a-z")
    parser.add_argument("--dob", default="1970-01-01", help="Date of birth from (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎖️  VLM API SCRAPER V2 - YOUNG VETERANS (1970+)")
    print("=" * 60)
    
    if args.all:
        names = list(string.ascii_lowercase)
        print(f"Letters: a-z")
    else:
        names = [args.name]
        print(f"Letter: {args.name}")
    
    print(f"Start page: {args.start}")
    print(f"Pages per letter: {args.pages}")
    print(f"Born after: {args.dob}")
    print("=" * 60)
    
    veterans = scrape_all(names, args.start, args.pages, args.dob)
    
    print(f"\n✅ Total veterans: {len(veterans)}")
    
    # Save
    if args.json:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(veterans, f, indent=2)
    else:
        lines = [format_veteran_line(v) for v in veterans]
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    
    print(f"📁 Saved to: {args.output}")


if __name__ == "__main__":
    main()
