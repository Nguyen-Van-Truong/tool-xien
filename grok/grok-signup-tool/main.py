"""
Grok Account Signup Automation Tool
Main entry point for automated account creation
"""

import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config import (
    DEFAULT_FIRST_NAMES,
    DEFAULT_LAST_NAMES,
    OUTPUT_SUCCESS_FILE,
    OUTPUT_FAILED_FILE,
    INPUT_ACCOUNTS_FILE,
    DELAY_BETWEEN_ACCOUNTS
)
from utils.logger import log_info, log_success, log_error, log_warning
from utils.email_service import generate_email, check_email_for_code
from utils.browser_handler import GrokBrowser


class GrokSignupBot:
    """Main bot class for Grok account signup automation"""
    
    def __init__(self):
        """Initialize the signup bot"""
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0
        }
        
        # Ensure output directories exist
        Path(OUTPUT_SUCCESS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(OUTPUT_FAILED_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    async def signup_single_account(self, account_data: Dict[str, str]) -> Dict[str, any]:
        """
        Signup a single Grok account
        
        Args:
            account_data: Dictionary containing:
                - email: Grok account email
                - password: Grok account password
                - first_name: (optional) First name
                - last_name: (optional) Last name
        
        Returns:
            Dictionary with signup result
        """
        email = account_data['email']
        password = account_data['password']
        first_name = account_data.get('first_name', random.choice(DEFAULT_FIRST_NAMES))
        last_name = account_data.get('last_name', random.choice(DEFAULT_LAST_NAMES))
        
        log_info(f"\n{'='*60}")
        log_info(f"🚀 Starting signup for: {email}")
        log_info(f"{'='*60}")
        
        browser = None
        temp_email = None
        
        try:
            # Step 1: Generate temporary email
            log_info("📧 Step 1/6: Generating temporary email...")
            temp_email = await generate_email()
            
            # Step 2: Start browser
            log_info("🌐 Step 2/6: Launching browser...")
            browser = GrokBrowser(headless=False)  # Set to True for production
            await browser.start()
            
            # Step 3: Navigate to signup page
            log_info("🔗 Step 3/6: Navigating to signup page...")
            await browser.navigate_to_signup()
            
            # Step 4: Handle Cloudflare and fill initial form
            log_info("🔐 Step 4/6: Handling Cloudflare & filling form...")
            await browser.wait_for_cloudflare()
            
            # Fill email and name fields
            await browser.fill_email_field(temp_email)
            await browser.fill_name_fields(first_name, last_name)
            
            # Request verification code
            await browser.request_verification_code()
            
            # Step 5: Get verification code from email
            log_info("📬 Step 5/6: Waiting for verification code...")
            verification_code = await check_email_for_code(temp_email)
            
            if not verification_code:
                raise Exception("Failed to retrieve verification code from email")
            
            # Submit verification code
            await browser.submit_verification_code(verification_code)
            
            # Step 6: Set account credentials and complete signup
            log_info("🔑 Step 6/6: Setting account credentials...")
            await browser.set_account_credentials(email, password)
            
            # Check if signup was successful
            await asyncio.sleep(3)
            success = await browser.check_signup_success()
            
            if success:
                result = {
                    'status': 'success',
                    'email': email,
                    'password': password,
                    'temp_email': temp_email,
                    'verification_code': verification_code
                }
                log_success(f"✅ Successfully created account: {email}")
                self.stats['success'] += 1
            else:
                # Take screenshot for debugging
                screenshot_path = f"output/logs/failed_{email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await browser.take_screenshot(screenshot_path)
                
                raise Exception("Signup validation failed")
            
        except Exception as e:
            log_error(f"❌ Failed to signup {email}: {str(e)}")
            result = {
                'status': 'failed',
                'email': email,
                'error': str(e),
                'temp_email': temp_email
            }
            self.stats['failed'] += 1
            
        finally:
            # Always close browser
            if browser:
                await browser.close()
        
        return result
    
    def save_result(self, result: Dict[str, any]):
        """Save result to appropriate output file"""
        try:
            if result['status'] == 'success':
                with open(OUTPUT_SUCCESS_FILE, 'a', encoding='utf-8') as f:
                    line = f"{result['email']}|{result['password']}|{result['temp_email']}|{result['verification_code']}|{datetime.now().isoformat()}\n"
                    f.write(line)
                log_info(f"💾 Saved to {OUTPUT_SUCCESS_FILE}")
            else:
                with open(OUTPUT_FAILED_FILE, 'a', encoding='utf-8') as f:
                    line = f"{result['email']}|{result.get('error', 'Unknown error')}|{datetime.now().isoformat()}\n"
                    f.write(line)
                log_info(f"💾 Saved to {OUTPUT_FAILED_FILE}")
        except Exception as e:
            log_error(f"❌ Failed to save result: {str(e)}")
    
    async def process_accounts(self, accounts: List[Dict[str, str]]):
        """
        Process multiple accounts sequentially
        
        Args:
            accounts: List of account dictionaries
        """
        self.stats['total'] = len(accounts)
        
        log_info(f"\n🎯 Processing {len(accounts)} accounts...")
        
        for i, account in enumerate(accounts, 1):
            log_info(f"\n📊 Progress: {i}/{len(accounts)}")
            
            # Process account
            result = await self.signup_single_account(account)
            self.save_result(result)
            
            # Delay between accounts (except for last one)
            if i < len(accounts):
                log_info(f"⏳ Waiting {DELAY_BETWEEN_ACCOUNTS}s before next account...")
                await asyncio.sleep(DELAY_BETWEEN_ACCOUNTS)
        
        # Show summary
        self.show_summary()
    
    def show_summary(self):
        """Display final statistics"""
        log_info(f"\n{'='*60}")
        log_info("📊 SIGNUP SUMMARY")
        log_info(f"{'='*60}")
        log_info(f"Total accounts: {self.stats['total']}")
        log_success(f"✅ Successful: {self.stats['success']}")
        log_error(f"❌ Failed: {self.stats['failed']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            log_info(f"Success rate: {success_rate:.1f}%")
        
        log_info(f"{'='*60}\n")


def parse_accounts_file(filepath: str) -> List[Dict[str, str]]:
    """
    Parse accounts from input file
    
    Format: email|password
    
    Args:
        filepath: Path to accounts file
        
    Returns:
        List of account dictionaries
    """
    accounts = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) < 2:
                    log_warning(f"⚠️ Skipping invalid line {line_num}: {line}")
                    continue
                
                account = {
                    'email': parts[0].strip(),
                    'password': parts[1].strip()
                }
                
                # Optional: first name and last name
                if len(parts) >= 3:
                    account['first_name'] = parts[2].strip()
                if len(parts) >= 4:
                    account['last_name'] = parts[3].strip()
                
                accounts.append(account)
        
        log_success(f"✅ Loaded {len(accounts)} accounts from {filepath}")
        
    except FileNotFoundError:
        log_error(f"❌ File not found: {filepath}")
    except Exception as e:
        log_error(f"❌ Error reading file: {str(e)}")
    
    return accounts


def generate_accounts(count: int) -> List[Dict[str, str]]:
    """
    Auto-generate accounts
    
    Args:
        count: Number of accounts to generate
        
    Returns:
        List of generated account dictionaries
    """
    accounts = []
    
    for i in range(1, count + 1):
        account = {
            'email': f'grok_user_{i}@example.com',
            'password': f'GrokPass{i}!2024',
            'first_name': random.choice(DEFAULT_FIRST_NAMES),
            'last_name': random.choice(DEFAULT_LAST_NAMES)
        }
        accounts.append(account)
    
    log_success(f"✅ Generated {count} accounts")
    return accounts


async def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════════╗
    ║   Grok Account Signup Automation Tool      ║
    ║   Created by: Your Name                    ║
    ╚════════════════════════════════════════════╝
    """)
    
    # Ask user for mode
    print("\n📋 Select mode:")
    print("1. Read from file (input/accounts.txt)")
    print("2. Auto-generate accounts")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        accounts = []
        
        if choice == '1':
            # Read from file
            if not Path(INPUT_ACCOUNTS_FILE).exists():
                log_error(f"❌ Input file not found: {INPUT_ACCOUNTS_FILE}")
                log_info("Creating sample file...")
                
                # Create sample file
                Path(INPUT_ACCOUNTS_FILE).parent.mkdir(parents=True, exist_ok=True)
                with open(INPUT_ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
                    f.write("# Format: email|password|first_name|last_name\n")
                    f.write("# Example:\n")
                    f.write("user1@example.com|Password123\n")
                    f.write("user2@example.com|Password456|John|Doe\n")
                
                log_info(f"✅ Created sample file: {INPUT_ACCOUNTS_FILE}")
                log_info("Please edit the file and run again.")
                return
            
            accounts = parse_accounts_file(INPUT_ACCOUNTS_FILE)
            
        elif choice == '2':
            # Auto-generate
            count = int(input("How many accounts to generate? "))
            if count <= 0:
                log_error("❌ Invalid count")
                return
            
            accounts = generate_accounts(count)
        
        else:
            log_error("❌ Invalid choice")
            return
        
        if not accounts:
            log_error("❌ No accounts to process")
            return
        
        # Confirm before starting
        print(f"\n⚠️ About to process {len(accounts)} accounts")
        confirm = input("Continue? (y/n): ").strip().lower()
        
        if confirm != 'y':
            log_info("Cancelled by user")
            return
        
        # Start processing
        bot = GrokSignupBot()
        await bot.process_accounts(accounts)
        
    except KeyboardInterrupt:
        log_warning("\n⚠️ Interrupted by user")
    except Exception as e:
        log_error(f"❌ Fatal error: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Program stopped by user (Ctrl+C)")
        print("👋 Goodbye!")
    except Exception as e:
        log_error(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

