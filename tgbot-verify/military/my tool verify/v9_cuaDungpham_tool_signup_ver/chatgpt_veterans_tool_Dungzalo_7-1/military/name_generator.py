"""Random Name Generator for Military Verification
Based on ThanhNguyxn/SheerID-Verification-Tool
"""
import random
import hashlib
import uuid
import time
import base64
import json
from datetime import datetime, timedelta


class NameGenerator:
    """English Name Generator"""
    
    FIRST_NAMES = [
        'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph',
        'Thomas', 'Charles', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark',
        'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian',
        'George', 'Timothy', 'Ronald', 'Edward', 'Jason', 'Jeffrey', 'Ryan',
        'Jacob', 'Nicholas', 'Gary', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin',
        'Scott', 'Brandon', 'Benjamin', 'Samuel', 'Raymond', 'Gregory', 'Frank'
    ]
    
    LAST_NAMES = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
        'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen',
        'Hill', 'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera'
    ]
    
    @classmethod
    def generate(cls):
        """
        Generate random English name
        
        Returns:
            dict: Contains first_name, last_name, full_name
        """
        first_name = random.choice(cls.FIRST_NAMES)
        last_name = random.choice(cls.LAST_NAMES)
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}"
        }


def generate_email(domain='gmail.com'):
    """
    Generate random email address
    
    Args:
        domain: Email domain
    
    Returns:
        str: Email address
    """
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    username = ''.join(random.choice(chars) for _ in range(10))
    return f"{username}@{domain}"


def generate_birth_date(min_age=25, max_age=55):
    """
    Generate random birth date for veteran
    
    Args:
        min_age: Minimum age
        max_age: Maximum age
    
    Returns:
        str: Birth date in YYYY-MM-DD format
    """
    today = datetime.now()
    min_date = today - timedelta(days=max_age * 365)
    max_date = today - timedelta(days=min_age * 365)
    
    random_days = random.randint(0, (max_date - min_date).days)
    birth_date = min_date + timedelta(days=random_days)
    
    return birth_date.strftime('%Y-%m-%d')


def generate_discharge_date():
    """
    Generate random discharge date for veteran
    Optimized for SheerID: within 12 months for better auto-approval
    
    Returns:
        str: Discharge date in YYYY-MM-DD format
    """
    today = datetime.now()
    # Generate date within last 11 months (for better success rate)
    # SheerID targets veterans discharged within 12 months
    min_days_ago = 30  # At least 1 month ago
    max_days_ago = 330  # Less than 11 months ago
    
    random_days = random.randint(min_days_ago, max_days_ago)
    discharge_date = today - timedelta(days=random_days)
    
    return discharge_date.strftime('%Y-%m-%d')


def generate_fingerprint():
    """
    Generate device fingerprint for SheerID API
    Based on ThanhNguyxn implementation
    
    Returns:
        str: MD5 hash fingerprint
    """
    screens = ["1920x1080", "2560x1440", "1366x768", "1440x900", "1536x864"]
    screen = random.choice(screens)
    raw = f"{screen}|{time.time()}|{uuid.uuid4()}"
    return hashlib.md5(raw.encode()).hexdigest()


def generate_newrelic_headers():
    """
    Generate NewRelic tracking headers for SheerID API
    Based on ThanhNguyxn implementation
    
    Returns:
        dict: NewRelic headers (newrelic, traceparent, tracestate)
    """
    trace_id = uuid.uuid4().hex + uuid.uuid4().hex[:8]
    trace_id = trace_id[:32]
    span_id = uuid.uuid4().hex[:16]
    timestamp = int(time.time() * 1000)
    
    payload = {
        "v": [0, 1],
        "d": {
            "ty": "Browser",
            "ac": "364029",
            "ap": "134291347",
            "id": span_id,
            "tr": trace_id,
            "ti": timestamp
        }
    }
    
    return {
        "newrelic": base64.b64encode(json.dumps(payload).encode()).decode(),
        "traceparent": f"00-{trace_id}-{span_id}-01",
        "tracestate": f"364029@nr=0-1-364029-134291347-{span_id}----{timestamp}"
    }


def get_random_branch():
    """
    Get a random military branch (main branches for better success rate)
    
    Returns:
        str: Branch name
    """
    from . import config
    return random.choice(config.MAIN_BRANCHES)
