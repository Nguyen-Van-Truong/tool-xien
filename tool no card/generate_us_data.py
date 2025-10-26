#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇺🇸 US PERSONAL DATA GENERATOR
Tạo thông tin cá nhân người Mỹ ngẫu nhiên cho đăng ký
"""

import random
import json
from faker import Faker
from datetime import datetime, timedelta

# Khởi tạo Faker với locale US
fake = Faker('en_US')

def generate_ssn():
    """Tạo SSN giả (không hợp lệ thực tế)"""
    # SSN format: XXX-XX-XXXX
    # Tránh các số bắt đầu bằng 000, 666, 900-999
    area = random.randint(1, 665)
    if area == 666:
        area = 667
    
    group = random.randint(1, 99)
    serial = random.randint(1, 9999)
    
    return f"{area:03d}-{group:02d}-{serial:04d}"

def generate_phone():
    """Tạo số điện thoại US"""
    # Format: (XXX) XXX-XXXX
    area_code = random.choice([
        201, 202, 203, 205, 206, 207, 208, 209, 210,
        212, 213, 214, 215, 216, 217, 218, 219, 224,
        225, 227, 228, 229, 231, 234, 239, 240, 248,
        251, 252, 253, 254, 256, 260, 262, 267, 269,
        270, 272, 274, 276, 281, 283, 301, 302, 303,
        304, 305, 307, 308, 309, 310, 312, 313, 314,
        315, 316, 317, 318, 319, 320, 321, 323, 325,
        327, 330, 331, 334, 336, 337, 339, 346, 347,
        351, 352, 360, 361, 364, 386, 401, 402, 404,
        405, 406, 407, 408, 409, 410, 412, 413, 414,
        415, 417, 419, 423, 424, 425, 430, 432, 434,
        435, 440, 442, 443, 445, 458, 463, 464, 469,
        470, 475, 478, 479, 480, 484, 501, 502, 503,
        504, 505, 507, 508, 509, 510, 512, 513, 515,
        516, 517, 518, 520, 530, 531, 534, 539, 540,
        541, 551, 559, 561, 562, 563, 564, 567, 570,
        571, 573, 574, 575, 580, 585, 586, 601, 602,
        603, 605, 606, 607, 608, 609, 610, 612, 614,
        615, 616, 617, 618, 619, 620, 623, 626, 628,
        629, 630, 631, 636, 641, 646, 650, 651, 657,
        660, 661, 662, 667, 669, 678, 681, 682, 701,
        702, 703, 704, 706, 707, 708, 712, 713, 714,
        715, 716, 717, 718, 719, 720, 724, 725, 727,
        731, 732, 734, 737, 740, 743, 747, 754, 757,
        760, 762, 763, 765, 769, 770, 772, 773, 774,
        775, 779, 781, 785, 786, 787, 801, 802, 803,
        804, 805, 806, 808, 810, 812, 813, 814, 815,
        816, 817, 818, 828, 830, 831, 832, 843, 845,
        847, 848, 850, 854, 856, 857, 858, 859, 860,
        862, 863, 864, 865, 870, 872, 878, 901, 903,
        904, 906, 907, 908, 909, 910, 912, 913, 914,
        915, 916, 917, 918, 919, 920, 925, 928, 929,
        930, 931, 934, 936, 937, 940, 941, 947, 949,
        951, 952, 954, 956, 959, 970, 971, 972, 973,
        978, 979, 980, 984, 985, 989
    ])
    
    exchange = random.randint(200, 999)  # Tránh 0XX, 1XX
    number = random.randint(0, 9999)
    
    return f"({area_code}) {exchange}-{number:04d}"

def generate_florida_address():
    """Tạo địa chỉ Florida (vì Santa Fe College ở Florida)"""
    florida_cities = [
        "Gainesville", "Miami", "Orlando", "Tampa", "Jacksonville",
        "Tallahassee", "Fort Lauderdale", "Saint Petersburg", "Hialeah",
        "Port Saint Lucie", "Cape Coral", "Pembroke Pines", "Hollywood",
        "Miramar", "Coral Springs", "Clearwater", "Miami Gardens",
        "Palm Bay", "West Palm Beach", "Pompano Beach", "Lakeland",
        "Davie", "Miami Beach", "Sunrise", "Plantation", "Boca Raton",
        "Deltona", "Largo", "Deerfield Beach", "Boynton Beach"
    ]
    
    street_number = random.randint(1, 9999)
    street_name = fake.street_name()
    street_suffix = random.choice(['St', 'Ave', 'Blvd', 'Dr', 'Ln', 'Rd', 'Way', 'Ct'])
    city = random.choice(florida_cities)
    zip_code = f"{random.randint(32000, 34999)}"  # Florida ZIP codes
    
    return {
        "street": f"{street_number} {street_name} {street_suffix}",
        "city": city,
        "state": "FL",
        "zip_code": zip_code,
        "full_address": f"{street_number} {street_name} {street_suffix}, {city}, FL {zip_code}"
    }

def generate_birth_date(min_age=18, max_age=65):
    """Tạo ngày sinh (18-65 tuổi)"""
    today = datetime.now()
    start_date = today - timedelta(days=max_age * 365)
    end_date = today - timedelta(days=min_age * 365)
    
    birth_date = fake.date_between(start_date=start_date, end_date=end_date)
    return birth_date

def generate_education_info():
    """Tạo thông tin học vấn"""
    education_levels = [
        "High School Diploma",
        "Some College",
        "Associate Degree",
        "Bachelor's Degree",
        "Master's Degree",
        "Some High School"
    ]
    
    high_schools = [
        "Washington High School",
        "Lincoln High School", 
        "Roosevelt High School",
        "Jefferson High School",
        "Madison High School",
        "Franklin High School",
        "Jackson High School",
        "Wilson High School",
        "Central High School",
        "North High School",
        "South High School",
        "East High School",
        "West High School"
    ]
    
    return {
        "education_level": random.choice(education_levels),
        "high_school": random.choice(high_schools),
        "graduation_year": random.randint(2000, 2024)
    }

def generate_employment_info():
    """Tạo thông tin việc làm"""
    employment_status = [
        "Employed Full-Time",
        "Employed Part-Time", 
        "Self-Employed",
        "Unemployed",
        "Retired",
        "Student"
    ]
    
    job_titles = [
        "Administrative Assistant", "Sales Associate", "Customer Service Representative",
        "Retail Worker", "Food Service Worker", "Healthcare Worker", "Teacher",
        "Accountant", "Manager", "Supervisor", "Technician", "Driver",
        "Warehouse Worker", "Security Guard", "Maintenance Worker"
    ]
    
    companies = [
        "Walmart", "Amazon", "McDonald's", "Target", "Home Depot",
        "CVS Health", "Starbucks", "FedEx", "UPS", "Bank of America",
        "Wells Fargo", "Publix", "Winn-Dixie", "Florida Hospital",
        "AdventHealth", "Orange County Public Schools"
    ]
    
    return {
        "employment_status": random.choice(employment_status),
        "job_title": random.choice(job_titles),
        "employer": random.choice(companies),
        "annual_income": random.choice([
            "Under $15,000", "$15,000 - $24,999", "$25,000 - $34,999",
            "$35,000 - $49,999", "$50,000 - $74,999", "$75,000 - $99,999",
            "$100,000 or more"
        ])
    }

def generate_emergency_contact():
    """Tạo thông tin liên hệ khẩn cấp"""
    relationships = ["Parent", "Spouse", "Sibling", "Friend", "Relative"]
    
    return {
        "name": fake.name(),
        "relationship": random.choice(relationships),
        "phone": generate_phone(),
        "email": fake.email()
    }

def generate_person():
    """Tạo extract gg from pdf người hoàn chỉnh"""
    gender = random.choice(['M', 'F'])
    first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
    last_name = fake.last_name()
    birth_date = generate_birth_date()
    address = generate_florida_address()
    
    person = {
        # Thông tin cơ bản
        "first_name": first_name,
        "middle_name": fake.first_name(),
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}",
        "gender": "Male" if gender == 'M' else "Female",
        "birth_date": birth_date.strftime("%m/%d/%Y"),
        "age": (datetime.now().date() - birth_date).days // 365,
        
        # Liên hệ
        "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@gmail.com",
        "phone": generate_phone(),
        "cell_phone": generate_phone(),
        
        # Địa chỉ
        "address": address,
        
        # Định danh
        "ssn": generate_ssn(),
        "driver_license": f"FL{random.randint(100000000, 999999999)}",
        
        # Học vấn
        "education": generate_education_info(),
        
        # Việc làm
        "employment": generate_employment_info(),
        
        # Liên hệ khẩn cấp
        "emergency_contact": generate_emergency_contact(),
        
        # Thông tin khác
        "citizenship": "US Citizen",
        "race_ethnicity": random.choice([
            "White", "Black or African American", "Hispanic or Latino",
            "Asian", "American Indian or Alaska Native", "Native Hawaiian or Other Pacific Islander",
            "Two or More Races", "Prefer not to answer"
        ]),
        "marital_status": random.choice(["Single", "Married", "Divorced", "Widowed"]),
        "military_status": random.choice(["Never Served", "Veteran", "Active Duty"]),
        
        # Tài chính
        "financial_aid_needed": random.choice([True, False]),
        "residency_status": "Florida Resident",
        
        # Thông tin y tế
        "health_insurance": random.choice([True, False]),
        "disabilities": random.choice([True, False]),
        
        # Mục tiêu học tập
        "degree_goal": random.choice([
            "Associate in Arts (A.A.)",
            "Associate in Science (A.S.)",
            "Associate in Applied Science (A.A.S.)",
            "Certificate Program",
            "Continuing Education"
        ]),
        "major_interest": random.choice([
            "Business", "Computer Science", "Nursing", "Education",
            "Engineering", "Liberal Arts", "Criminal Justice", "Psychology",
            "Biology", "Art", "Music", "Theatre", "Mathematics"
        ])
    }
    
    return person

def generate_multiple_people(count=2):
    """Tạo nhiều người"""
    people = []
    for i in range(count):
        person = generate_person()
        person["id"] = i + 1
        people.append(person)
    
    return people

def save_to_file(people, filename="sf_registration_data.txt"):
    """Lưu vào file txt dễ đọc"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("🇺🇸 SANTA FE COLLEGE REGISTRATION DATA\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total People: {len(people)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, person in enumerate(people, 1):
            f.write(f"👤 PERSON #{i}\n")
            f.write("-" * 40 + "\n")
            
            # Thông tin cơ bản
            f.write("📋 BASIC INFORMATION:\n")
            f.write(f"   Full Name: {person['full_name']}\n")
            f.write(f"   First Name: {person['first_name']}\n")
            f.write(f"   Middle Name: {person['middle_name']}\n")
            f.write(f"   Last Name: {person['last_name']}\n")
            f.write(f"   Gender: {person['gender']}\n")
            f.write(f"   Birth Date: {person['birth_date']}\n")
            f.write(f"   Age: {person['age']}\n")
            f.write(f"   SSN: {person['ssn']}\n")
            f.write(f"   Driver License: {person['driver_license']}\n")
            f.write(f"   Race/Ethnicity: {person['race_ethnicity']}\n")
            f.write(f"   Marital Status: {person['marital_status']}\n")
            f.write(f"   Citizenship: {person['citizenship']}\n")
            f.write(f"   Military Status: {person['military_status']}\n\n")
            
            # Liên hệ
            f.write("📞 CONTACT INFORMATION:\n")
            f.write(f"   Email: {person['email']}\n")
            f.write(f"   Phone: {person['phone']}\n")
            f.write(f"   Cell Phone: {person['cell_phone']}\n\n")
            
            # Địa chỉ
            f.write("🏠 ADDRESS:\n")
            f.write(f"   Street: {person['address']['street']}\n")
            f.write(f"   City: {person['address']['city']}\n")
            f.write(f"   State: {person['address']['state']}\n")
            f.write(f"   ZIP Code: {person['address']['zip_code']}\n")
            f.write(f"   Full Address: {person['address']['full_address']}\n")
            f.write(f"   Residency: {person['residency_status']}\n\n")
            
            # Học vấn
            f.write("🎓 EDUCATION:\n")
            f.write(f"   Education Level: {person['education']['education_level']}\n")
            f.write(f"   High School: {person['education']['high_school']}\n")
            f.write(f"   Graduation Year: {person['education']['graduation_year']}\n\n")
            
            # Việc làm
            f.write("💼 EMPLOYMENT:\n")
            f.write(f"   Status: {person['employment']['employment_status']}\n")
            f.write(f"   Job Title: {person['employment']['job_title']}\n")
            f.write(f"   Employer: {person['employment']['employer']}\n")
            f.write(f"   Annual Income: {person['employment']['annual_income']}\n\n")
            
            # Liên hệ khẩn cấp
            f.write("🚨 EMERGENCY CONTACT:\n")
            f.write(f"   Name: {person['emergency_contact']['name']}\n")
            f.write(f"   Relationship: {person['emergency_contact']['relationship']}\n")
            f.write(f"   Phone: {person['emergency_contact']['phone']}\n")
            f.write(f"   Email: {person['emergency_contact']['email']}\n\n")
            
            # Mục tiêu học tập
            f.write("🎯 ACADEMIC GOALS:\n")
            f.write(f"   Degree Goal: {person['degree_goal']}\n")
            f.write(f"   Major Interest: {person['major_interest']}\n\n")
            
            # Thông tin khác
            f.write("ℹ️ OTHER INFORMATION:\n")
            f.write(f"   Financial Aid Needed: {'Yes' if person['financial_aid_needed'] else 'No'}\n")
            f.write(f"   Health Insurance: {'Yes' if person['health_insurance'] else 'No'}\n")
            f.write(f"   Disabilities: {'Yes' if person['disabilities'] else 'No'}\n\n")
            
            f.write("=" * 60 + "\n\n")

def save_to_json(people, filename="sf_registration_data.json"):
    """Lưu vào file JSON để dễ xử lý"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(people, f, indent=2, ensure_ascii=False, default=str)

if __name__ == "__main__":
    print("🇺🇸 US PERSONAL DATA GENERATOR")
    print("=" * 50)
    print("🎯 Tạo dữ liệu người Mỹ cho Santa Fe College")
    print("-" * 50)
    
    # Tạo 2 người
    people = generate_multiple_people(2)
    
    # Lưu file
    save_to_file(people, "sf_registration_data.txt")
    save_to_json(people, "sf_registration_data.json")
    
    print(f"✅ Đã tạo {len(people)} người")
    print("📁 Files đã tạo:")
    print("   📄 sf_registration_data.txt - Dữ liệu dễ đọc")
    print("   📊 sf_registration_data.json - Dữ liệu JSON")
    print("\n🎉 Hoàn thành!") 