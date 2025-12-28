"""
VLM API Scraper - Lấy dữ liệu veteran từ VLM API

Sử dụng:
    python vlm_api_scraper.py                    # Mặc định: lastName=b, năm 2025
    python vlm_api_scraper.py -n a -p 5          # lastName=a, 5 trang
    python vlm_api_scraper.py --all              # Tất cả chữ cái a-z
    python vlm_api_scraper.py -o veterans.txt   # Xuất ra file
"""

import argparse
import httpx
import json
import random
import sys
from datetime import datetime
from typing import List, Dict

# VLM API endpoint
VLM_API_URL = "https://www.vlm.cem.va.gov/api/v1.1/gcio/profile/search/advanced"

# Branch mapping
BRANCH_MAP = {
    "AR": "Army",
    "NA": "Navy", 
    "AF": "Air Force",
    "MC": "Marine Corps",
    "CG": "Coast Guard",
    "XR": "Army",  # Army Reserve
    "XN": "Navy",  # Navy Reserve
    "XF": "Air Force",  # Air Force Reserve
    "NG": "Army",  # National Guard
}

# Email domains
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com"]


def parse_date(date_str: str) -> Dict[str, str]:
    """Parse YYYY-MM-DD to month/day/year components"""
    if not date_str:
        return {"month": "January", "day": "1", "year": "1950"}
    
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return {
            "month": months[dt.month - 1],
            "day": str(dt.day),
            "year": str(dt.year)
        }
    except:
        return {"month": "January", "day": "1", "year": "1950"}


def get_branch_name(profile: Dict) -> str:
    """Extract branch name from profile"""
    branches = profile.get("profileServiceBranches", [])
    if branches:
        branch_id = branches[0].get("serviceBranch", {}).get("serviceBranchId", "AR")
        return BRANCH_MAP.get(branch_id, "Army")
    return "Army"


def generate_email(first_name: str, last_name: str) -> str:
    """Generate random email"""
    domain = random.choice(EMAIL_DOMAINS)
    rand = random.randint(100, 999)
    return f"{first_name.lower()}{last_name.lower()}{rand}@{domain}"


def fetch_veterans_page(
    last_name: str = "b",
    page: int = 1,
    limit: int = 25,
    dob_from: str = "1930-01-01",
    dob_to: str = "2010-12-31",
    dod_from: str = "2025-01-01",
    dod_to: str = "2025-12-31"
) -> List[Dict]:
    """Fetch one page of veterans from VLM API"""
    
    payload = {
        "lastName": last_name,
        "dobFrom": dob_from,
        "dobTo": dob_to,
        "dodFrom": dod_from,
        "dodTo": dod_to,
        "limit": limit,
        "page": page,
        "orderby": "date_of_death"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(VLM_API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", {}).get("data", [])
            else:
                print(f"Error: API returned {response.status_code}")
                return []
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return []


def process_veteran(profile: Dict) -> Dict:
    """Process API profile to veteran format"""
    first_name = profile.get("firstName", "").strip()
    last_name = profile.get("lastName", "").strip()
    
    # Skip invalid
    if not first_name or not last_name or first_name == "VET":
        return None
    
    birth = parse_date(profile.get("date_of_birth"))
    death = parse_date(profile.get("date_of_death"))
    branch = get_branch_name(profile)
    
    return {
        "firstName": first_name,
        "lastName": last_name,
        "branch": branch,
        "birthMonth": birth["month"],
        "birthDay": birth["day"],
        "birthYear": birth["year"],
        "dischargeMonth": death["month"],
        "dischargeDay": death["day"],
        "dischargeYear": death["year"],
        "email": generate_email(first_name, last_name)
    }


def format_veteran_line(vet: Dict) -> str:
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


def fetch_all_veterans(
    last_names: List[str] = None,
    max_pages: int = 5,
    dod_year: int = 2025
) -> List[Dict]:
    """Fetch veterans for multiple last name prefixes"""
    
    if not last_names:
        last_names = ["b"]
    
    dod_from = f"{dod_year}-01-01"
    dod_to = f"{dod_year}-12-31"
    
    all_veterans = []
    
    for last_name in last_names:
        print(f"\n📥 Fetching lastName={last_name}...")
        
        for page in range(1, max_pages + 1):
            print(f"   Page {page}/{max_pages}...", end=" ")
            
            profiles = fetch_veterans_page(
                last_name=last_name,
                page=page,
                dod_from=dod_from,
                dod_to=dod_to
            )
            
            if not profiles:
                print("No data")
                break
            
            count = 0
            for profile in profiles:
                vet = process_veteran(profile)
                if vet:
                    all_veterans.append(vet)
                    count += 1
            
            print(f"Got {count} veterans")
            
            if len(profiles) < 25:
                break
    
    # Remove duplicates
    seen = set()
    unique = []
    for vet in all_veterans:
        key = f"{vet['firstName']}_{vet['lastName']}"
        if key not in seen:
            seen.add(key)
            unique.append(vet)
    
    return unique


def main():
    parser = argparse.ArgumentParser(description="Fetch veteran data from VLM API")
    parser.add_argument("-n", "--name", default="b", help="Last name prefix (default: b)")
    parser.add_argument("-p", "--pages", type=int, default=5, help="Max pages per letter (default: 5)")
    parser.add_argument("-y", "--year", type=int, default=2025, help="Death year (default: 2025)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--all", action="store_true", help="Fetch all letters a-z")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("=" * 60)
        print("🎖️  VLM API VETERAN SCRAPER")
        print("=" * 60)
    
    # Determine letters to search
    if args.all:
        last_names = list("abcdefghijklmnopqrstuvwxyz")
    else:
        last_names = [args.name]
    
    if not args.quiet:
        print(f"Letters: {', '.join(last_names)}")
        print(f"Pages per letter: {args.pages}")
        print(f"Death year: {args.year}")
        print()
    
    # Fetch data
    veterans = fetch_all_veterans(
        last_names=last_names,
        max_pages=args.pages,
        dod_year=args.year
    )
    
    if not veterans:
        print("\n❌ No veterans found!")
        return 1
    
    if not args.quiet:
        print(f"\n✅ Total: {len(veterans)} veterans")
        print("=" * 60)
    
    # Format output
    if args.json:
        output = json.dumps(veterans, indent=2, ensure_ascii=False)
    else:
        output = "\n".join([format_veteran_line(v) for v in veterans])
    
    # Save or print
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        if not args.quiet:
            print(f"📁 Saved to: {args.output}")
    else:
        print("\n📋 DATA (copy this):")
        print("-" * 60)
        print(output)
        print("-" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
