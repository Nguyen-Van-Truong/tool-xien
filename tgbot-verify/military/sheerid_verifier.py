"""SheerID Military Verification Module

Handles ChatGPT Military (Veteran) verification through SheerID API.
"""

import re
import random
import logging
import httpx
from typing import Dict, Optional, Tuple, List

from . import config
from .vlm_scraper import scrape_veterans_sync, scrape_veterans_bulk_sync

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class MilitaryVerifier:
    """SheerID Military Verification Handler"""
    
    def __init__(self, verification_id: str):
        self.verification_id = verification_id
        self.http_client = httpx.Client(timeout=30.0)
    
    def __del__(self):
        if hasattr(self, "http_client"):
            self.http_client.close()
    
    @staticmethod
    def parse_verification_id(url: str) -> Optional[str]:
        """Extract verificationId from URL"""
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def get_organization_by_branch(branch: str) -> Dict:
        """Get organization info by branch name"""
        for org in config.ORGANIZATIONS:
            if org['name'].upper() == branch.upper():
                return {"id": org['id'], "name": org['name']}
        # Default to Army if not found
        return {"id": 4070, "name": "Army"}
    
    @staticmethod
    def format_date(month: str, day: str, year: str) -> str:
        """Format date to YYYY-MM-DD"""
        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        month_num = month_map.get(month, '01')
        day_str = str(day).zfill(2)
        return f"{year}-{month_num}-{day_str}"
    
    def _sheerid_request(
        self, method: str, url: str, body: Optional[Dict] = None
    ) -> Tuple[Dict, int]:
        """Send SheerID API request"""
        headers = {"Content-Type": "application/json"}
        
        try:
            response = self.http_client.request(
                method=method, url=url, json=body, headers=headers
            )
            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}
            return data, response.status_code
        except Exception as e:
            logger.error(f"SheerID request failed: {e}")
            raise
    
    def verify_with_veteran_data(self, veteran: Dict) -> Dict:
        """
        Perform military verification with veteran data
        
        Args:
            veteran: Dictionary containing veteran info:
                - firstName, lastName
                - birthMonth, birthDay, birthYear
                - dischargeMonth, dischargeDay, dischargeYear
                - branch
                - email
                
        Returns:
            Result dictionary with success status
        """
        try:
            first_name = veteran.get('firstName', '')
            last_name = veteran.get('lastName', '')
            branch = veteran.get('branch', 'Army')
            email = veteran.get('email', '')
            
            # Format dates
            birth_date = self.format_date(
                veteran.get('birthMonth', 'January'),
                veteran.get('birthDay', '1'),
                veteran.get('birthYear', '1950')
            )
            discharge_date = self.format_date(
                veteran.get('dischargeMonth', 'January'),
                veteran.get('dischargeDay', '1'),
                veteran.get('dischargeYear', '2025')
            )
            
            organization = self.get_organization_by_branch(branch)
            
            logger.info(f"Military verification: {first_name} {last_name}")
            logger.info(f"Branch: {branch}, Birth: {birth_date}")
            logger.info(f"Discharge: {discharge_date}")
            logger.info(f"Email: {email}")
            logger.info(f"Verification ID: {self.verification_id}")
            
            # Step 1: Collect Military Status
            logger.info("Step 1/2: Setting military status...")
            step1_body = {"status": "VETERAN"}
            step1_data, step1_status = self._sheerid_request(
                "POST",
                f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/collectMilitaryStatus",
                step1_body
            )
            
            if step1_status != 200:
                raise Exception(f"Step 1 failed (status {step1_status}): {step1_data}")
            
            if step1_data.get("currentStep") == "error":
                error_msg = ", ".join(step1_data.get("errorIds", ["Unknown error"]))
                raise Exception(f"Step 1 error: {error_msg}")
            
            submission_url = step1_data.get("submissionUrl")
            if not submission_url:
                submission_url = f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/collectInactiveMilitaryPersonalInfo"
            
            logger.info(f"✅ Step 1 complete: {step1_data.get('currentStep')}")
            
            # Step 2: Submit Personal Info
            logger.info("Step 2/2: Submitting personal info...")
            step2_body = {
                "firstName": first_name,
                "lastName": last_name,
                "birthDate": birth_date,
                "email": email,
                "phoneNumber": "",
                "organization": organization,
                "dischargeDate": discharge_date,
                "locale": "en-US",
                "country": "US",
                "metadata": {
                    "marketConsentValue": False,
                    "refererUrl": f"{config.SHEERID_BASE_URL}/verify/{config.PROGRAM_ID}/?verificationId={self.verification_id}",
                    "verificationId": self.verification_id,
                    "flags": '{"doc-upload-considerations":"default","doc-upload-may24":"default","doc-upload-redesign-use-legacy-message-keys":false,"docUpload-assertion-checklist":"default","include-cvec-field-france-student":"not-labeled-optional","org-search-overlay":"default","org-selected-display":"default"}',
                    "submissionOptIn": "By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount, and I understand that my personal information will be shared with SheerID as a processor/third-party service provider in order for SheerID to confirm my eligibility for a special offer."
                }
            }
            
            step2_data, step2_status = self._sheerid_request(
                "POST",
                submission_url,
                step2_body
            )
            
            if step2_status != 200:
                raise Exception(f"Step 2 failed (status {step2_status}): {step2_data}")
            
            if step2_data.get("currentStep") == "error":
                error_msg = ", ".join(step2_data.get("errorIds", ["Unknown error"]))
                raise Exception(f"Step 2 error: {error_msg}")
            
            logger.info(f"✅ Step 2 complete: {step2_data.get('currentStep')}")
            
            # Check result
            current_step = step2_data.get("currentStep", "")
            
            if current_step == "success":
                return {
                    "success": True,
                    "pending": False,
                    "message": "Military verification successful!",
                    "verification_id": self.verification_id,
                    "redirect_url": step2_data.get("redirectUrl"),
                    "reward_code": step2_data.get("rewardCode"),
                    "status": step2_data
                }
            elif current_step in ["docUpload", "pending"]:
                return {
                    "success": True,
                    "pending": True,
                    "message": "Submitted, pending document review",
                    "verification_id": self.verification_id,
                    "redirect_url": step2_data.get("redirectUrl"),
                    "status": step2_data
                }
            else:
                return {
                    "success": True,
                    "pending": True,
                    "message": f"Status: {current_step}",
                    "verification_id": self.verification_id,
                    "redirect_url": step2_data.get("redirectUrl"),
                    "status": step2_data
                }
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "verification_id": self.verification_id
            }
    
    def verify(self) -> Dict:
        """
        Perform verification with auto-scraped veteran data
        
        Returns:
            Result dictionary with success status
        """
        try:
            # Scrape a random veteran
            logger.info("Scraping veteran data from VLM...")
            veterans = scrape_veterans_sync(
                last_name=random.choice(['a', 'b', 'c', 'd', 'e', 's', 'm', 'j', 'w']),
                death_year=2025,
                max_results=10
            )
            
            if not veterans:
                raise Exception("Failed to scrape veteran data from VLM")
            
            # Pick random veteran
            veteran = random.choice(veterans)
            logger.info(f"Selected veteran: {veteran.get('firstName')} {veteran.get('lastName')}")
            
            # Verify with scraped data
            return self.verify_with_veteran_data(veteran)
            
        except Exception as e:
            logger.error(f"❌ Auto verification failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "verification_id": self.verification_id
            }


class BulkMilitaryVerifier:
    """Bulk military verification handler"""
    
    def __init__(self):
        self.veterans: List[Dict] = []
        self.results: List[Dict] = []
    
    def load_veterans_from_vlm(
        self,
        last_names: List[str] = None,
        branches: List[str] = None,
        death_year: int = 2025,
        max_total: int = 100
    ):
        """Load veterans from VLM"""
        logger.info("Loading veterans from VLM...")
        self.veterans = scrape_veterans_bulk_sync(
            last_names=last_names,
            branches=branches,
            death_year=death_year,
            max_total=max_total
        )
        logger.info(f"Loaded {len(self.veterans)} veterans")
        return len(self.veterans)
    
    def load_veterans_from_text(self, text: str):
        """
        Load veterans from pipe-delimited text
        Format: FirstName|LastName|Branch|BirthMonth|BirthDay|BirthYear|DischargeMonth|DischargeDay|DischargeYear|Email
        """
        lines = text.strip().split('\n')
        self.veterans = []
        
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) >= 6:
                vet = {
                    'firstName': parts[0],
                    'lastName': parts[1],
                    'branch': parts[2] if len(parts) > 2 else 'Army',
                    'birthMonth': parts[3] if len(parts) > 3 else 'January',
                    'birthDay': parts[4] if len(parts) > 4 else '1',
                    'birthYear': parts[5] if len(parts) > 5 else '1950',
                    'dischargeMonth': parts[6] if len(parts) > 6 else 'January',
                    'dischargeDay': parts[7] if len(parts) > 7 else '1',
                    'dischargeYear': parts[8] if len(parts) > 8 else '2025',
                    'email': parts[9] if len(parts) > 9 else f"{parts[0].lower()}{parts[1].lower()}{random.randint(100,999)}@gmail.com",
                    'status': 'VETERAN'
                }
                self.veterans.append(vet)
        
        logger.info(f"Loaded {len(self.veterans)} veterans from text")
        return len(self.veterans)
    
    def verify_all(self, verification_ids: List[str], delay: float = 2.0) -> List[Dict]:
        """
        Verify multiple verification IDs with available veterans
        
        Args:
            verification_ids: List of verification IDs
            delay: Delay between verifications (seconds)
            
        Returns:
            List of results
        """
        import time
        
        if not self.veterans:
            raise Exception("No veterans loaded. Call load_veterans_* first.")
        
        self.results = []
        
        for i, vid in enumerate(verification_ids):
            veteran = self.veterans[i % len(self.veterans)]
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Verification {i+1}/{len(verification_ids)}")
            logger.info(f"ID: {vid}")
            logger.info(f"Veteran: {veteran.get('firstName')} {veteran.get('lastName')}")
            
            try:
                verifier = MilitaryVerifier(vid)
                result = verifier.verify_with_veteran_data(veteran)
                result['veteran'] = veteran
                self.results.append(result)
                
                if result['success']:
                    logger.info(f"✅ Success!")
                else:
                    logger.warning(f"❌ Failed: {result.get('message')}")
                    
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                self.results.append({
                    'success': False,
                    'message': str(e),
                    'verification_id': vid,
                    'veteran': veteran
                })
            
            if i < len(verification_ids) - 1:
                time.sleep(delay)
        
        success_count = sum(1 for r in self.results if r['success'])
        logger.info(f"\n{'='*50}")
        logger.info(f"Results: {success_count}/{len(self.results)} successful")
        
        return self.results
    
    def get_stats(self) -> Dict:
        """Get verification statistics"""
        total = len(self.results)
        success = sum(1 for r in self.results if r['success'])
        pending = sum(1 for r in self.results if r.get('pending'))
        failed = total - success
        
        return {
            'total': total,
            'success': success,
            'pending': pending,
            'failed': failed,
            'success_rate': f"{(success/total*100):.1f}%" if total > 0 else "0%"
        }


def main():
    """CLI interface for military verification"""
    import sys
    
    print("=" * 60)
    print("SheerID Military Verification Tool")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter SheerID verification URL: ").strip()
    
    if not url:
        print("❌ Error: No URL provided")
        sys.exit(1)
    
    verification_id = MilitaryVerifier.parse_verification_id(url)
    if not verification_id:
        print("❌ Error: Invalid verification ID format")
        sys.exit(1)
    
    print(f"✅ Verification ID: {verification_id}")
    print()
    
    verifier = MilitaryVerifier(verification_id)
    result = verifier.verify()
    
    print()
    print("=" * 60)
    print("Result:")
    print("=" * 60)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Message: {result['message']}")
    if result.get("redirect_url"):
        print(f"Redirect URL: {result['redirect_url']}")
    if result.get("reward_code"):
        print(f"Reward Code: {result['reward_code']}")
    print("=" * 60)
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())
