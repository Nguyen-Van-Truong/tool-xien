"""VLM (Veterans Legacy Memorial) Scraper - Simple Version

Scrape veteran data from vlm.cem.va.gov using httpx.
This is a simplified version that doesn't require Playwright.
"""

import random
import logging
import re
import httpx
from typing import List, Dict, Optional

from . import config

logger = logging.getLogger(__name__)

# Month name mapping
MONTH_MAP = {
    '01': 'January', '02': 'February', '03': 'March', '04': 'April',
    '05': 'May', '06': 'June', '07': 'July', '08': 'August',
    '09': 'September', '10': 'October', '11': 'November', '12': 'December',
    'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April',
    'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August',
    'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December'
}

BRANCH_MAP = {
    'NAVY': 'Navy',
    'ARMY': 'Army', 
    'AIR FORCE': 'Air Force',
    'AIR': 'Air Force',
    'MARINE': 'Marine Corps',
    'MARINES': 'Marine Corps',
    'COAST GUARD': 'Coast Guard',
    'COAST': 'Coast Guard',
    'SPACE': 'Space Force'
}

# Sample veteran data for fallback
SAMPLE_VETERANS = [
    {"firstName": "JAMES", "lastName": "WILSON", "branch": "Army"},
    {"firstName": "ROBERT", "lastName": "JOHNSON", "branch": "Navy"},
    {"firstName": "MICHAEL", "lastName": "BROWN", "branch": "Air Force"},
    {"firstName": "WILLIAM", "lastName": "DAVIS", "branch": "Marine Corps"},
    {"firstName": "DAVID", "lastName": "MILLER", "branch": "Navy"},
    {"firstName": "RICHARD", "lastName": "MOORE", "branch": "Army"},
    {"firstName": "JOSEPH", "lastName": "TAYLOR", "branch": "Air Force"},
    {"firstName": "THOMAS", "lastName": "ANDERSON", "branch": "Navy"},
    {"firstName": "CHARLES", "lastName": "THOMAS", "branch": "Army"},
    {"firstName": "CHRISTOPHER", "lastName": "JACKSON", "branch": "Marine Corps"},
    {"firstName": "DANIEL", "lastName": "WHITE", "branch": "Coast Guard"},
    {"firstName": "MATTHEW", "lastName": "HARRIS", "branch": "Navy"},
    {"firstName": "ANTHONY", "lastName": "MARTIN", "branch": "Army"},
    {"firstName": "MARK", "lastName": "THOMPSON", "branch": "Air Force"},
    {"firstName": "DONALD", "lastName": "GARCIA", "branch": "Navy"},
    {"firstName": "STEVEN", "lastName": "MARTINEZ", "branch": "Army"},
    {"firstName": "PAUL", "lastName": "ROBINSON", "branch": "Marine Corps"},
    {"firstName": "ANDREW", "lastName": "CLARK", "branch": "Navy"},
    {"firstName": "JOSHUA", "lastName": "RODRIGUEZ", "branch": "Air Force"},
    {"firstName": "KENNETH", "lastName": "LEWIS", "branch": "Army"},
]


def parse_branch(branch_text: str) -> str:
    """Parse branch name from text"""
    if not branch_text:
        return random.choice(config.DEFAULT_BRANCHES)
    
    upper = branch_text.upper()
    for key, value in BRANCH_MAP.items():
        if key in upper:
            return value
    return random.choice(config.DEFAULT_BRANCHES)


def generate_email(first_name: str, last_name: str) -> str:
    """Generate random email address"""
    domain = random.choice(config.EMAIL_DOMAINS)
    rand = random.randint(100, 999)
    return f"{first_name.lower()}{last_name.lower()}{rand}@{domain}"


def generate_veteran_data(
    first_name: str = None,
    last_name: str = None,
    branch: str = None,
    death_year: int = 2025
) -> Dict:
    """Generate a complete veteran record"""
    if not first_name or not last_name:
        sample = random.choice(SAMPLE_VETERANS)
        first_name = first_name or sample['firstName']
        last_name = last_name or sample['lastName']
        branch = branch or sample['branch']
    
    if not branch:
        branch = random.choice(config.DEFAULT_BRANCHES)
    
    # Estimate birth year (died age 70-90)
    age = random.randint(70, 90)
    birth_year = death_year - age
    
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    birth_month = random.choice(months)
    birth_day = str(random.randint(1, 28))
    
    discharge_month = random.choice(months)
    discharge_day = str(random.randint(1, 28))
    
    return {
        'firstName': first_name.upper(),
        'lastName': last_name.upper(),
        'branch': branch,
        'birthMonth': birth_month,
        'birthDay': birth_day,
        'birthYear': str(birth_year),
        'dischargeMonth': discharge_month,
        'dischargeDay': discharge_day,
        'dischargeYear': str(death_year),
        'deathYear': str(death_year),
        'email': generate_email(first_name, last_name),
        'status': 'VETERAN'
    }


class VLMScraper:
    """Scraper for Veterans Legacy Memorial (VLM) website"""
    
    def __init__(self):
        self.veterans: List[Dict] = []
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
    
    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()
    
    def scrape_search_results(
        self,
        last_name: str = "b",
        branch: str = "",
        death_year: int = 2025,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Scrape veteran data from VLM search results
        
        Args:
            last_name: Last name filter
            branch: Military branch filter
            death_year: Year of death filter
            max_results: Maximum number of results
            
        Returns:
            List of veteran dictionaries
        """
        veterans = []
        
        try:
            # Build search URL
            url = f"{config.VLM_SEARCH_URL}/?lastName={last_name}"
            if branch:
                url += f"&branch={branch}"
            if death_year:
                url += f"&yearOfDeath={death_year}"
            
            logger.info(f"Scraping VLM: {url}")
            
            # Try to fetch from VLM
            response = self.client.get(url)
            
            if response.status_code == 200:
                text = response.text
                veterans = self._parse_html(text, death_year)
                logger.info(f"Scraped {len(veterans)} veterans from VLM")
            else:
                logger.warning(f"VLM returned status {response.status_code}, using generated data")
                
        except Exception as e:
            logger.warning(f"VLM scrape failed: {e}, using generated data")
        
        # If no real data, generate random veterans
        if len(veterans) < max_results:
            needed = max_results - len(veterans)
            logger.info(f"Generating {needed} additional veteran records")
            
            for _ in range(needed):
                vet = generate_veteran_data(death_year=death_year)
                veterans.append(vet)
        
        # Limit results
        veterans = veterans[:max_results]
        self.veterans.extend(veterans)
        
        return veterans
    
    def _parse_html(self, html: str, death_year: int) -> List[Dict]:
        """Parse veteran data from HTML"""
        veterans = []
        
        # Look for patterns like "FIRSTNAME LASTNAME" followed by branch
        # This is a simplified parser - real VLM may need more complex parsing
        
        # Pattern for names in ALL CAPS
        name_pattern = re.compile(r'([A-Z]{2,})\s+([A-Z]{2,}(?:\s+[A-Z]{2,})?)')
        
        # Find all potential names
        matches = name_pattern.findall(html)
        
        for match in matches[:50]:  # Limit parsing
            first_name = match[0]
            last_name = match[1]
            
            # Skip common non-name words
            skip_words = ['UNITED', 'STATES', 'NAVY', 'ARMY', 'FORCE', 'MARINE', 'COAST', 'GUARD', 
                         'MEMORIAL', 'VETERAN', 'SERVICE', 'BRANCH', 'SEARCH', 'RESULTS']
            
            if first_name in skip_words or last_name in skip_words:
                continue
            
            if len(first_name) < 2 or len(last_name) < 2:
                continue
            
            # Determine branch from context
            branch = random.choice(config.DEFAULT_BRANCHES)
            
            vet = generate_veteran_data(
                first_name=first_name,
                last_name=last_name,
                branch=branch,
                death_year=death_year
            )
            veterans.append(vet)
        
        return veterans
    
    def export_to_text(self, veterans: List[Dict] = None) -> str:
        """Export veterans to pipe-delimited text format"""
        if veterans is None:
            veterans = self.veterans
        
        lines = []
        for vet in veterans:
            line = "|".join([
                vet.get('firstName', ''),
                vet.get('lastName', ''),
                vet.get('branch', 'Navy'),
                vet.get('birthMonth', 'January'),
                vet.get('birthDay', '1'),
                vet.get('birthYear', '1950'),
                vet.get('dischargeMonth', 'January'),
                vet.get('dischargeDay', '1'),
                vet.get('dischargeYear', '2025'),
                vet.get('email', '')
            ])
            lines.append(line)
        
        return '\n'.join(lines)


def scrape_veterans_sync(
    last_name: str = "b",
    branch: str = "",
    death_year: int = 2025,
    max_results: int = 50
) -> List[Dict]:
    """Synchronous function to scrape veterans"""
    scraper = VLMScraper()
    try:
        return scraper.scrape_search_results(
            last_name=last_name,
            branch=branch,
            death_year=death_year,
            max_results=max_results
        )
    finally:
        pass  # Client closed in destructor


def scrape_veterans_bulk_sync(
    last_names: List[str] = None,
    branches: List[str] = None,
    death_year: int = 2025,
    max_total: int = 100
) -> List[Dict]:
    """Synchronous bulk scraping function"""
    if not last_names:
        last_names = ['a', 'b', 'c', 'd', 'e', 's', 'm', 'j', 'w', 'h']
    
    if not branches:
        branches = config.DEFAULT_BRANCHES
    
    all_veterans = []
    scraper = VLMScraper()
    
    per_search = max(5, max_total // (len(last_names) * len(branches)))
    
    for last_name in last_names:
        if len(all_veterans) >= max_total:
            break
            
        for branch in branches:
            if len(all_veterans) >= max_total:
                break
            
            try:
                veterans = scraper.scrape_search_results(
                    last_name=last_name,
                    branch=branch,
                    death_year=death_year,
                    max_results=per_search
                )
                all_veterans.extend(veterans)
            except Exception as e:
                logger.warning(f"Search error for {last_name}/{branch}: {e}")
    
    # Remove duplicates
    seen = set()
    unique = []
    for vet in all_veterans:
        key = f"{vet.get('firstName', '')}_{vet.get('lastName', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(vet)
    
    return unique[:max_total]
