#!/usr/bin/env python3
"""
Test Military Verification Script
Chạy thử xác thực Military SheerID với veteran data
"""

import httpx
import random
import json

# SheerID API
SHEERID_BASE_URL = "https://services.sheerid.com/rest/v2/verification"

# Military Organizations
ORGANIZATIONS = {
    "Army": {"id": 4070, "name": "Army"},
    "Navy": {"id": 4072, "name": "Navy"},
    "Air Force": {"id": 4073, "name": "Air Force"},
    "Marine Corps": {"id": 4071, "name": "Marine Corps"},
    "Coast Guard": {"id": 4074, "name": "Coast Guard"},
}

# Month mapping
MONTH_TO_NUM = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
}


def parse_veteran_line(line: str) -> dict:
    """Parse pipe-delimited veteran line"""
    parts = line.strip().split("|")
    if len(parts) < 10:
        return None
    
    return {
        "firstName": parts[0],
        "lastName": parts[1],
        "branch": parts[2],
        "birthMonth": parts[3],
        "birthDay": parts[4],
        "birthYear": parts[5],
        "dischargeMonth": parts[6],
        "dischargeDay": parts[7],
        "dischargeYear": parts[8],
        "email": parts[9]
    }


def format_date(year: str, month: str, day: str) -> str:
    """Format date to YYYY-MM-DD"""
    month_num = MONTH_TO_NUM.get(month, "01")
    day_padded = day.zfill(2)
    return f"{year}-{month_num}-{day_padded}"


def step1_collect_military_status(verification_id: str) -> dict:
    """Step 1: Submit military status"""
    url = f"{SHEERID_BASE_URL}/{verification_id}/step/collectMilitaryStatus"
    
    payload = {"status": "VETERAN"}
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print(f"\n📤 Step 1: collectMilitaryStatus")
    print(f"   URL: {url}")
    print(f"   Payload: {payload}")
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
            return data
        else:
            print(f"   Error: {response.text[:500]}")
            return None


def step2_collect_personal_info(verification_id: str, veteran: dict, email: str, submission_url: str = None) -> dict:
    """Step 2: Submit personal info"""
    
    if submission_url:
        url = submission_url
    else:
        url = f"{SHEERID_BASE_URL}/{verification_id}/step/collectInactiveMilitaryPersonalInfo"
    
    # Get organization
    branch = veteran.get("branch", "Navy")
    org = ORGANIZATIONS.get(branch, ORGANIZATIONS["Navy"])
    
    # Format dates
    birth_date = format_date(
        veteran.get("birthYear", "1950"),
        veteran.get("birthMonth", "January"),
        veteran.get("birthDay", "1")
    )
    
    discharge_date = format_date(
        veteran.get("dischargeYear", "2025"),
        veteran.get("dischargeMonth", "January"),
        veteran.get("dischargeDay", "1")
    )
    
    payload = {
        "firstName": veteran.get("firstName", "JOHN"),
        "lastName": veteran.get("lastName", "DOE"),
        "birthDate": birth_date,
        "email": email,
        "organization": org,
        "dischargeDate": discharge_date,
        "metadata": {}
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print(f"\n📤 Step 2: collectInactiveMilitaryPersonalInfo")
    print(f"   URL: {url}")
    print(f"   Veteran: {veteran.get('firstName')} {veteran.get('lastName')}")
    print(f"   Branch: {branch} (ID: {org['id']})")
    print(f"   Birth: {birth_date}")
    print(f"   Discharge: {discharge_date}")
    print(f"   Email: {email}")
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        print(f"\n   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"   Error: {response.text}")
            return None


def main():
    # Test parameters - NEW LINK
    verification_id = "694d4e6b12fb296cf454004a"
    email = "littlejohnjj2qesparza@outlook.com"
    
    # Different veteran from data (to avoid limit)
    veteran_line = "ROBERT|JOHNSON|Navy|September|26|1946|May|5|2025|test@gmail.com"
    veteran = parse_veteran_line(veteran_line)
    
    print("=" * 60)
    print("🎖️  MILITARY VERIFICATION TEST")
    print("=" * 60)
    print(f"Verification ID: {verification_id}")
    print(f"Email: {email}")
    print(f"Veteran: {veteran['firstName']} {veteran['lastName']} ({veteran['branch']})")
    print("=" * 60)
    
    # Step 1
    result1 = step1_collect_military_status(verification_id)
    
    if not result1:
        print("\n❌ Step 1 failed!")
        return
    
    # Get submission URL from step 1 response
    submission_url = result1.get("submissionUrl")
    current_step = result1.get("currentStep")
    
    print(f"\n   Current Step: {current_step}")
    print(f"   Submission URL: {submission_url}")
    
    # Step 2
    if current_step == "collectInactiveMilitaryPersonalInfo":
        result2 = step2_collect_personal_info(
            verification_id, 
            veteran, 
            email,
            submission_url
        )
        
        if result2:
            status = result2.get("currentStep")
            if status == "success":
                print("\n" + "=" * 60)
                print("✅ VERIFICATION SUCCESSFUL!")
                print("=" * 60)
            else:
                print(f"\n⚠️ Current step: {status}")
        else:
            print("\n❌ Step 2 failed!")
    else:
        print(f"\n⚠️ Unexpected step: {current_step}")


if __name__ == "__main__":
    main()
