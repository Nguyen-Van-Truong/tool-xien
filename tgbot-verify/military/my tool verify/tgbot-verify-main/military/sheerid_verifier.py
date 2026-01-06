"""SheerID Military Verification
Based on ThanhNguyxn/SheerID-Verification-Tool
"""
import re
import random
import logging
import httpx
import uuid
from typing import Dict, Optional, Tuple

from . import config
from .name_generator import (
    NameGenerator, 
    generate_email, 
    generate_birth_date, 
    generate_discharge_date,
    generate_fingerprint,
    generate_newrelic_headers,
    get_random_branch
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class SheerIDVerifier:
    """SheerID Military Identity Verifier - Enhanced Version"""

    def __init__(self, verification_id: str):
        self.verification_id = verification_id
        self.fingerprint = generate_fingerprint()
        self.http_client = httpx.Client(timeout=30.0)

    def __del__(self):
        if hasattr(self, "http_client"):
            self.http_client.close()

    @staticmethod
    def parse_verification_id(url: str) -> Optional[str]:
        """Parse verificationId from URL"""
        # First try to match verificationId parameter (priority)
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        # Fallback: try to match verify/xxx (but not program ID)
        # Only use this if no verificationId parameter found
        match = re.search(r"verify/([a-f0-9]{24,})(?:\?|$)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _get_sheerid_headers(self) -> Dict:
        """Generate headers for SheerID API with NewRelic tracking"""
        nr = generate_newrelic_headers()
        
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "sec-ch-ua": '"Chromium";v="131", "Google Chrome";v="131"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "User-Agent": config.USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "clientversion": "2.157.0",
            "clientname": "jslib",
            "newrelic": nr["newrelic"],
            "traceparent": nr["traceparent"],
            "tracestate": nr["tracestate"],
            "Origin": "https://services.sheerid.com",
        }

    def _sheerid_request(
        self, method: str, url: str, body: Optional[Dict] = None
    ) -> Tuple[Dict, int]:
        """Send SheerID API request with proper headers"""
        headers = self._get_sheerid_headers()

        try:
            response = self.http_client.request(
                method=method, url=url, json=body, headers=headers
            )
            try:
                data = response.json()
            except Exception:
                data = {"text": response.text}
            return data, response.status_code
        except Exception as e:
            logger.error(f"SheerID request failed: {e}")
            raise

    def verify(
        self,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        birth_date: str = None,
        discharge_date: str = None,
        branch: str = None,
        military_status: str = "VETERAN",
    ) -> Dict:
        """Execute military verification flow - Enhanced version"""
        try:
            # Generate random info if not provided
            if not first_name or not last_name:
                name = NameGenerator.generate()
                first_name = name["first_name"]
                last_name = name["last_name"]

            # Get random branch if not provided
            if not branch:
                branch = get_random_branch()
            
            # Get organization from branch
            org = config.BRANCH_ORG_MAP.get(branch, config.BRANCH_ORG_MAP["Army"])

            if not email:
                email = generate_email()
            if not birth_date:
                birth_date = generate_birth_date()
            if not discharge_date:
                discharge_date = generate_discharge_date()

            logger.info(f"🎖️ Military Info: {first_name} {last_name}")
            logger.info(f"📧 Email: {email}")
            logger.info(f"🏛️ Branch: {org['name']}")
            logger.info(f"📅 Birth Date: {birth_date}")
            logger.info(f"📅 Discharge Date: {discharge_date}")
            logger.info(f"⚔️ Military Status: {military_status}")
            logger.info(f"🔗 Verification ID: {self.verification_id}")

            # Step 1: Collect Military Status
            logger.info("Step 1/2: Setting military status...")
            step1_body = {
                "status": military_status
            }

            step1_data, step1_status = self._sheerid_request(
                "POST",
                f"{config.SHEERID_API}/verification/{self.verification_id}/step/collectMilitaryStatus",
                step1_body,
            )

            if step1_status != 200:
                # Check for rate limit
                if step1_status == 429 or "verificationLimitExceeded" in str(step1_data.get("errorIds", [])):
                    return {
                        "success": False,
                        "message": "Verification limit exceeded - data already verified",
                        "verification_id": self.verification_id
                    }
                raise Exception(f"Step 1 failed (status {step1_status}): {step1_data}")
            
            current_step = step1_data.get("currentStep", "")
            submission_url = step1_data.get("submissionUrl", "")
            
            logger.info(f"✅ Step 1 complete: {current_step}")

            # Step 2: Collect Inactive Military Personal Info
            logger.info("Step 2/2: Submitting personal information...")
            
            # Construct referer URL
            referer_url = f"{config.SHEERID_BASE_URL}/verify/{config.PROGRAM_ID}/?verificationId={self.verification_id}"
            
            # Use the submission URL from step 1, or construct it
            if not submission_url:
                submission_url = f"{config.SHEERID_API}/verification/{self.verification_id}/step/collectInactiveMilitaryPersonalInfo"

            step2_body = {
                "firstName": first_name,
                "lastName": last_name,
                "birthDate": birth_date,
                "email": email,
                "phoneNumber": "",
                "organization": {
                    "id": org["id"],
                    "name": org["name"]
                },
                "dischargeDate": discharge_date,
                "deviceFingerprintHash": self.fingerprint,
                "locale": "en-US",
                "country": "US",
                "metadata": {
                    "marketConsentValue": False,
                    "refererUrl": referer_url,
                    "verificationId": self.verification_id,
                    "flags": '{"doc-upload-considerations":"default","doc-upload-may24":"default","doc-upload-redesign-use-legacy-message-keys":false,"docUpload-assertion-checklist":"default","include-cvec-field-france-student":"not-labeled-optional","org-search-overlay":"default","org-selected-display":"default"}',
                    "submissionOptIn": "By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount, and I understand that my personal information will be shared with SheerID as a processor/third-party service provider in order for SheerID to confirm my eligibility for a special offer."
                }
            }

            step2_data, step2_status = self._sheerid_request(
                "POST",
                submission_url,
                step2_body,
            )

            # Check for rate limit / already verified
            if step2_status == 429 or "verificationLimitExceeded" in str(step2_data.get("errorIds", [])):
                return {
                    "success": False,
                    "message": "Verification limit exceeded - data already verified",
                    "verification_id": self.verification_id
                }

            if step2_status != 200:
                raise Exception(f"Step 2 failed (status {step2_status}): {step2_data}")
            
            current_step = step2_data.get("currentStep", "")
            
            if current_step == "error":
                error_ids = step2_data.get("errorIds", [])
                error_msg = ", ".join(error_ids) if error_ids else "Unknown error"
                raise Exception(f"Step 2 error: {error_msg}")

            logger.info(f"✅ Step 2 complete: {current_step}")
            
            final_status = step2_data
            redirect_url = final_status.get("redirectUrl")

            # Check final status
            if current_step == "success":
                return {
                    "success": True,
                    "pending": False,
                    "message": "🎉 Military verification successful!",
                    "verification_id": self.verification_id,
                    "redirect_url": redirect_url,
                    "reward_code": final_status.get("rewardCode"),
                    "veteran_name": f"{first_name} {last_name}",
                    "branch": org["name"],
                    "status": final_status,
                }
            
            # Document upload required
            if current_step == "docUpload":
                return {
                    "success": False,
                    "pending": True,
                    "message": "📄 Document upload required - auto verification failed",
                    "verification_id": self.verification_id,
                    "status": final_status,
                }
            
            # Email loop required
            if current_step == "emailLoop":
                return {
                    "success": True,
                    "pending": True,
                    "message": "📧 Email verification required - check email inbox",
                    "verification_id": self.verification_id,
                    "email": email,
                    "status": final_status,
                }
            
            # Otherwise pending review
            return {
                "success": True,
                "pending": True,
                "message": "✨ Submitted, awaiting SheerID review",
                "verification_id": self.verification_id,
                "redirect_url": redirect_url,
                "veteran_name": f"{first_name} {last_name}",
                "branch": org["name"],
                "status": final_status,
            }

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return {"success": False, "message": str(e), "verification_id": self.verification_id}


def main():
    """Main function - CLI interface"""
    import sys

    print("=" * 60)
    print("SheerID Military Verification Tool")
    print("Based on ThanhNguyxn/SheerID-Verification-Tool")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter SheerID verification URL: ").strip()

    if not url:
        print("❌ Error: No URL provided")
        sys.exit(1)

    verification_id = SheerIDVerifier.parse_verification_id(url)
    if not verification_id:
        print("❌ Error: Invalid verification ID format")
        sys.exit(1)

    print(f"✅ Parsed verification ID: {verification_id}")
    print()

    verifier = SheerIDVerifier(verification_id)
    result = verifier.verify()

    print()
    print("=" * 60)
    print("Verification Result:")
    print("=" * 60)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Message: {result['message']}")
    if result.get("veteran_name"):
        print(f"Veteran: {result['veteran_name']}")
    if result.get("branch"):
        print(f"Branch: {result['branch']}")
    if result.get("redirect_url"):
        print(f"Redirect URL: {result['redirect_url']}")
    if result.get("reward_code"):
        print(f"Reward Code: {result['reward_code']}")
    print("=" * 60)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())
